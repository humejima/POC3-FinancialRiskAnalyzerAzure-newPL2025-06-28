from main import app
from models import db, StandardAccount, StandardAccountBalance
import logging

# ロギングの設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# アプリケーションコンテキスト内で実行
with app.app_context():
    # 対象のJAコードと年度
    ja_code = "JA004"
    year = 2025
    
    # コード2900（資産合計）と4900（負債合計）のデータをチェック
    logger.info("### 安全性指標の計算に必要な科目データの詳細確認 ###")
    
    # 1. 標準勘定科目マスタのデータを確認
    logger.info("\n[1] 標準勘定科目マスタのデータ確認")
    bs_codes = ["2900", "4900", "5900", "5000", "5100", "5200", "5300"]
    accounts = db.session.query(StandardAccount).filter(
        StandardAccount.code.in_(bs_codes),
        StandardAccount.financial_statement == "bs"
    ).all()
    
    if accounts:
        for account in accounts:
            logger.info(f"科目マスタ: コード={account.code}, 名前={account.name}, 財務諸表={account.financial_statement}")
    else:
        logger.warning("該当する標準勘定科目が見つかりません")
    
    # 2. 勘定科目残高の確認
    logger.info("\n[2] 勘定科目残高の確認")
    balances = db.session.query(StandardAccountBalance).filter(
        StandardAccountBalance.ja_code == ja_code,
        StandardAccountBalance.year == year,
        StandardAccountBalance.statement_type == "bs",
        StandardAccountBalance.standard_account_code.in_(bs_codes)
    ).all()
    
    if balances:
        for balance in balances:
            logger.info(f"残高データ: JAコード={balance.ja_code}, 年度={balance.year}, " +
                       f"科目コード={balance.standard_account_code}, 科目名={balance.standard_account_name}, " +
                       f"残高={balance.current_value}")
    else:
        logger.warning(f"JA{ja_code}、{year}年度のBS科目残高データが見つかりません")
    
    # 3. 古いコード2999と4999のデータも確認
    logger.info("\n[3] 古いコード2999と4999のデータも確認")
    old_codes = ["2999", "4999"]
    old_balances = db.session.query(StandardAccountBalance).filter(
        StandardAccountBalance.ja_code == ja_code,
        StandardAccountBalance.year == year,
        StandardAccountBalance.statement_type == "bs",
        StandardAccountBalance.standard_account_code.in_(old_codes)
    ).all()
    
    if old_balances:
        for balance in old_balances:
            logger.info(f"残高データ(旧コード): JAコード={balance.ja_code}, 年度={balance.year}, " +
                       f"科目コード={balance.standard_account_code}, 科目名={balance.standard_account_name}, " +
                       f"残高={balance.current_value}")
    else:
        logger.info("旧コード2999/4999のデータはありません")
    
    # 4. 資産勘定（コード1000～2999）と負債勘定（コード3000～4999）の合計額を算出
    logger.info("\n[4] 資産勘定と負債勘定の実際の合計額")
    asset_balances = db.session.query(StandardAccountBalance).filter(
        StandardAccountBalance.ja_code == ja_code,
        StandardAccountBalance.year == year,
        StandardAccountBalance.statement_type == "bs",
        StandardAccountBalance.standard_account_code >= "1000",
        StandardAccountBalance.standard_account_code < "3000"
    ).all()
    
    liability_balances = db.session.query(StandardAccountBalance).filter(
        StandardAccountBalance.ja_code == ja_code,
        StandardAccountBalance.year == year,
        StandardAccountBalance.statement_type == "bs",
        StandardAccountBalance.standard_account_code >= "3000",
        StandardAccountBalance.standard_account_code < "5000"
    ).all()
    
    total_assets = sum(balance.current_value for balance in asset_balances if balance.current_value is not None)
    total_liabilities = sum(balance.current_value for balance in liability_balances if balance.current_value is not None)
    
    logger.info(f"資産勘定の合計(1000-2999): {total_assets:,.0f}")
    logger.info(f"負債勘定の合計(3000-4999): {total_liabilities:,.0f}")
    
    # 5. 資本金、利益剰余金、評価差額金のデータ確認
    logger.info("\n[5] 資本関連科目の確認")
    equity_codes = ["5100", "5200", "5300"]
    equity_balances = db.session.query(StandardAccountBalance).filter(
        StandardAccountBalance.ja_code == ja_code,
        StandardAccountBalance.year == year,
        StandardAccountBalance.statement_type == "bs",
        StandardAccountBalance.standard_account_code.in_(equity_codes)
    ).all()
    
    if equity_balances:
        equity_sum = sum(balance.current_value for balance in equity_balances if balance.current_value is not None)
        for balance in equity_balances:
            logger.info(f"純資産項目: コード={balance.standard_account_code}, 名前={balance.standard_account_name}, 残高={balance.current_value:,.0f}")
        logger.info(f"純資産項目の合計: {equity_sum:,.0f}")
    else:
        logger.warning("純資産項目のデータが見つかりません")

    # 6. financial_indicators.pyのget_account_valueメソッドの模擬実装で値の取得テスト
    logger.info("\n[6] get_account_valueメソッドの動作確認")
    
    def test_get_account_value(account_code):
        accounts = db.session.query(StandardAccountBalance).filter(
            StandardAccountBalance.ja_code == ja_code,
            StandardAccountBalance.year == year,
            StandardAccountBalance.statement_type == "bs",
            StandardAccountBalance.standard_account_code == account_code
        ).all()
        
        if accounts:
            total_value = sum(acc.current_value for acc in accounts if acc.current_value is not None)
            account_name = accounts[0].standard_account_name
            logger.info(f"get_account_value: コード={account_code}, 名前={account_name}, 合計値={total_value:,.0f}, レコード数={len(accounts)}")
            return total_value, account_name
        else:
            logger.warning(f"get_account_value: コード={account_code}の勘定科目残高がありません")
            return 0, f"科目{account_code}"
    
    for code in ["2900", "4900", "5900", "5000", "5100", "5200", "5300"]:
        test_get_account_value(code)