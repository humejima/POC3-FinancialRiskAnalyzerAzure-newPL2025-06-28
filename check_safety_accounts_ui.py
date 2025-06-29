"""
安全性指標の表示部分で使用されている科目コードと値の確認スクリプト
UIに表示されているデータと実際のデータベースの内容を比較
"""

from main import app
from models import db, StandardAccount, StandardAccountBalance, AnalysisResult
import json
import logging

# ロギングの設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_safety_ui_data(ja_code, year):
    """安全性指標の表示に関連するデータを確認"""
    logger.info(f"=== JA{ja_code}, {year}年の安全性指標データチェック ===")
    
    # 1. 安全性指標の分析結果レコードを確認
    logger.info("\n[1] 安全性指標の分析結果")
    results = AnalysisResult.query.filter_by(
        ja_code=ja_code,
        year=year,
        analysis_type='safety'
    ).all()
    
    if not results:
        logger.warning(f"JA{ja_code}の{year}年の安全性指標分析結果がありません")
        return
    
    logger.info(f"- 安全性指標レコード数: {len(results)}")
    for result in results:
        logger.info(f"指標: {result.indicator_name}, 値: {result.indicator_value:.2f}, リスクスコア: {result.risk_score}")
        
        # accounts_usedを詳しく解析
        if result.accounts_used:
            try:
                accounts_data = json.loads(result.accounts_used)
                logger.info(f"  使用勘定科目:")
                for account_name, account_info in accounts_data.items():
                    if isinstance(account_info, dict):
                        code = account_info.get('code', 'N/A')
                        value = account_info.get('value', 0)
                        logger.info(f"    - {account_name}: コード={code}, 値={value:,.0f}")
                    else:
                        logger.info(f"    - {account_name}: {account_info}")
            except json.JSONDecodeError:
                logger.warning(f"  accounts_usedの解析に失敗: {result.accounts_used}")
    
    # 2. 科目コード2900と4900の残高データを確認
    logger.info("\n[2] 科目コード2900と4900の残高データ")
    account_codes = ['2900', '4900', '5900', '5000', '5100', '5200', '5300']
    balances = db.session.query(StandardAccountBalance).filter(
        StandardAccountBalance.ja_code == ja_code,
        StandardAccountBalance.year == year,
        StandardAccountBalance.statement_type == 'bs',
        StandardAccountBalance.standard_account_code.in_(account_codes)
    ).all()
    
    if not balances:
        logger.warning(f"JA{ja_code}の{year}年のBS主要科目残高がありません")
    else:
        for balance in balances:
            logger.info(f"科目: {balance.standard_account_code} ({balance.standard_account_name}), 値: {balance.current_value:,.0f}")
    
    # 3. テンプレートで使用されるAPIデータを模擬
    logger.info("\n[3] /api/indicator_dataエンドポイントの返すデータ")
    results = AnalysisResult.query.filter_by(
        ja_code=ja_code,
        year=year,
        analysis_type='safety'
    ).all()
    
    # Format data for charts (similar to routes.py)
    data = {
        'labels': [],
        'values': [],
        'benchmarks': [],
    }
    
    for result in results:
        # Skip indicators without proper numeric values
        if result.indicator_value is None or result.indicator_name == 'working_capital':
            continue
        
        # Format indicator name for display
        display_name = result.indicator_name
        if result.indicator_name == 'equity_ratio':
            display_name = '自己資本比率'
        elif result.indicator_name == 'debt_ratio':
            display_name = '負債比率'
        elif result.indicator_name == 'debt_to_equity':
            display_name = '負債資本比率'
        elif result.indicator_name == 'interest_coverage_ratio':
            display_name = 'インタレストカバレッジレシオ'
        
        data['labels'].append(display_name)
        data['values'].append(result.indicator_value)
        data['benchmarks'].append(result.benchmark if result.benchmark else 0)
    
    logger.info(f"APIレスポンスデータ:")
    for i in range(len(data['labels'])):
        logger.info(f"  - {data['labels'][i]}: 値={data['values'][i]:.2f}, 基準値={data['benchmarks'][i]}")
    
    # 4. 安全性指標計算に使用する勘定科目の親子関係を確認
    logger.info("\n[4] 安全性指標計算に使用する勘定科目の親子関係")
    parent_codes = ['2900', '4900', '5900', '5000']
    for parent_code in parent_codes:
        child_accounts = StandardAccount.query.filter_by(
            parent_code=parent_code,
            financial_statement='bs'
        ).all()
        
        if child_accounts:
            logger.info(f"親科目 {parent_code} の子科目:")
            for child in child_accounts:
                logger.info(f"  - {child.code}: {child.name}")
        else:
            logger.info(f"親科目 {parent_code} に子科目はありません")

# アプリケーションコンテキスト内で実行
with app.app_context():
    # JA002とJA004の両方をチェック
    check_safety_ui_data('JA002', 2025)
    check_safety_ui_data('JA004', 2025)