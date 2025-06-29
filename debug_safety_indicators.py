"""
安全性指標の計算をデバッグするスクリプト
該当のJAの残高データを確認し、適切に値が取得できているか検証
"""

from main import app
from models import db, StandardAccount, StandardAccountBalance
import logging

# ロギングの設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_account_value(ja_code, year, statement_type, account_code):
    """
    指定されたコードの勘定科目の値を取得する
    FinancialIndicatorsクラスのget_account_valueメソッドの簡易版
    """
    # 文字列型に変換（数字で受け取った場合も対応）
    if not isinstance(account_code, str):
        account_code = str(account_code)
        
    # 旧コードのハードコードされた処理はスキップする（実際のデータを検証するため）
    
    # 直接の勘定科目を取得（同じコードを持つ複数のレコードがある場合、合計する）
    accounts = StandardAccountBalance.query.filter_by(
        ja_code=ja_code,
        year=year,
        statement_type=statement_type,
        standard_account_code=account_code
    ).all()
    
    if accounts:
        # 複数のレコードの合計を計算
        total_value = sum(acc.current_value for acc in accounts if acc.current_value is not None)
        # 最初のレコードから名前を取得
        account_name = accounts[0].standard_account_name or f"科目{account_code}"
        account_count = len(accounts)
        logger.info(f"勘定科目 {account_code} ({account_name}) の値: {total_value:,.0f} (レコード数: {account_count})")
        return total_value, account_name
        
    # 標準勘定科目マスタから科目名を取得
    std_account = StandardAccount.query.filter_by(code=account_code).first()
    account_name = std_account.name if std_account else f"科目{account_code}"
    
    # 親科目の場合は子科目の合計を計算
    try:
        # データベースから親子関係を検索
        standard_accounts = StandardAccount.query.filter_by(parent_code=account_code).all()
        if standard_accounts:
            child_codes = [sa.code for sa in standard_accounts]
            
            child_accounts = StandardAccountBalance.query.filter(
                StandardAccountBalance.ja_code == ja_code,
                StandardAccountBalance.year == year,
                StandardAccountBalance.statement_type == statement_type,
                StandardAccountBalance.standard_account_code.in_(child_codes)
            ).all()
            
            # 子科目が見つかった場合は合計を計算
            if child_accounts:
                total_value = sum(acc.current_value for acc in child_accounts 
                              if acc.current_value is not None)
                logger.info(f"親勘定科目 {account_code} ({account_name}) の子勘定科目合計: {total_value:,.0f} (子科目数: {len(child_accounts)})")
                return total_value, account_name
    except Exception as e:
        logger.warning(f"親子関係検索エラー: {str(e)}")
    
    # 値が見つからない場合
    logger.warning(f"勘定科目 {account_code} ({account_name}) の値が見つかりません")
    return 0, account_name

def calculate_safety_indicators_for_debug(ja_code, year):
    """
    安全性指標の計算をデバッグする
    """
    logger.info(f"### {ja_code}の{year}年の安全性指標計算デバッグ ###")
    
    # BS計算で使用する科目コード
    BS_ASSET_TOTAL = "2900"  # 資産の部合計
    BS_LIABILITY_TOTAL = "4900"  # 負債の部合計
    BS_EQUITY_TOTAL = "5900"  # 純資産の部合計
    
    # 総資産を取得（資産の部合計）
    total_assets, total_assets_name = get_account_value(ja_code, year, "bs", BS_ASSET_TOTAL)
    logger.info(f"取得した資産の部合計: コード={BS_ASSET_TOTAL}, 金額={total_assets:,.0f}")
    
    # 負債の部合計を取得
    total_liabilities, total_liabilities_name = get_account_value(ja_code, year, "bs", BS_LIABILITY_TOTAL)
    logger.info(f"取得した負債の部合計: コード={BS_LIABILITY_TOTAL}, 金額={total_liabilities:,.0f}")
    
    # 純資産の部合計（直接）
    equity_direct, equity_direct_name = get_account_value(ja_code, year, "bs", BS_EQUITY_TOTAL)
    logger.info(f"取得した純資産の部合計（直接）: コード={BS_EQUITY_TOTAL}, 金額={equity_direct:,.0f}")
    
    # 純資産の部合計（コード5000）
    equity_5000, equity_5000_name = get_account_value(ja_code, year, "bs", "5000")
    logger.info(f"取得した純資産（5000）: 金額={equity_5000:,.0f}")
    
    # 純資産の構成要素
    capital, capital_name = get_account_value(ja_code, year, "bs", "5100")  # 資本金
    retained_earnings, retained_earnings_name = get_account_value(ja_code, year, "bs", "5200")  # 利益剰余金
    valuation, valuation_name = get_account_value(ja_code, year, "bs", "5300")  # 評価差額金
    
    equity_sum = capital + retained_earnings + valuation
    logger.info(f"純資産構成要素の合計: 資本金({capital:,.0f}) + 利益剰余金({retained_earnings:,.0f}) + 評価差額金({valuation:,.0f}) = {equity_sum:,.0f}")
    
    # 実際に使用される純資産の値を決定
    total_equity = 0
    total_equity_name = ""
    
    if equity_direct > 0:
        total_equity = equity_direct
        total_equity_name = equity_direct_name
        logger.info(f"使用する純資産: 直接取得した純資産の部合計 = {total_equity:,.0f}")
    elif equity_5000 > 0:
        total_equity = equity_5000
        total_equity_name = equity_5000_name
        logger.info(f"使用する純資産: 科目5000の値 = {total_equity:,.0f}")
    elif equity_sum > 0:
        total_equity = equity_sum
        total_equity_name = "純資産合計（資本金・利益剰余金等の合計）"
        logger.info(f"使用する純資産: 構成要素の合計 = {total_equity:,.0f}")
    else:
        # 最後の手段として、資産 - 負債 から計算
        total_equity = total_assets - total_liabilities
        total_equity_name = "純資産（資産 - 負債の計算値）"
        logger.info(f"使用する純資産: 資産({total_assets:,.0f}) - 負債({total_liabilities:,.0f})の計算により算出 = {total_equity:,.0f}")

    # 自己資本比率（Equity Ratio）の計算
    equity_ratio = 0
    if total_assets != 0:
        equity_ratio = (total_equity / total_assets) * 100
        logger.info(f"自己資本比率: ({total_equity:,.0f} ÷ {total_assets:,.0f}) × 100 = {equity_ratio:.2f}%")
    else:
        logger.warning("自己資本比率: 総資産がゼロのため計算できません")
    
    # 負債比率（Debt Ratio）の計算
    debt_ratio = 0
    if total_assets != 0:
        debt_ratio = (total_liabilities / total_assets) * 100
        logger.info(f"負債比率: ({total_liabilities:,.0f} ÷ {total_assets:,.0f}) × 100 = {debt_ratio:.2f}%")
    else:
        logger.warning("負債比率: 総資産がゼロのため計算できません")
    
    # 負債資本比率（Debt-to-Equity Ratio）の計算
    debt_to_equity = 0
    if total_equity != 0:
        debt_to_equity = (total_liabilities / total_equity) * 100
        logger.info(f"負債資本比率: ({total_liabilities:,.0f} ÷ {total_equity:,.0f}) × 100 = {debt_to_equity:.2f}%")
    else:
        logger.warning("負債資本比率: 純資産がゼロのため計算できません")
    
    return {
        'total_assets': total_assets,
        'total_liabilities': total_liabilities,
        'total_equity': total_equity,
        'equity_ratio': equity_ratio,
        'debt_ratio': debt_ratio,
        'debt_to_equity': debt_to_equity
    }

# アプリケーションコンテキスト内で実行
with app.app_context():
    # 複数のJAコードでテスト
    ja_codes = ["JA002", "JA004"]
    year = 2025
    
    for ja_code in ja_codes:
        # 安全性指標を計算
        results = calculate_safety_indicators_for_debug(ja_code, year)
        
        # 指標の値をログに出力
        logger.info(f"\n{ja_code}の{year}年の安全性指標計算結果:")
        logger.info(f"総資産: {results['total_assets']:,.0f}")
        logger.info(f"負債合計: {results['total_liabilities']:,.0f}")
        logger.info(f"純資産: {results['total_equity']:,.0f}")
        logger.info(f"自己資本比率: {results['equity_ratio']:.2f}%")
        logger.info(f"負債比率: {results['debt_ratio']:.2f}%")
        logger.info(f"負債資本比率: {results['debt_to_equity']:.2f}%")
        logger.info("="*50)