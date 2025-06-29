from app import app, db
from account_calculator import AccountCalculator
import logging

# ロガーの設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def initialize_bs_formulas():
    """貸借対照表（BS）の合計勘定科目の計算式を初期化する"""
    logger.info("Initializing BS account formulas...")
    
    # 資産の部合計（科目2900）の計算式を作成
    asset_component_codes = [
        "1000",  # 現金預け金
        "1100",  # コールローン
        "1200",  # 買現先勘定
        "1300",  # 債券貸借取引支払保証金
        "1400",  # 買入手形
        "1500",  # 買入金銭債権
        "1600",  # 有価証券
        "1700",  # 貸出金
        "1800",  # 外国為替
        "1900",  # その他資産
        "2000",  # 有形固定資産
        "2100",  # 無形固定資産
        "2200",  # 前払年金費用
        "2300",  # 繰延税金資産
        "2400",  # 支払承諾見返
        "2500"   # 貸倒引当金
    ]
    
    AccountCalculator.create_formula(
        target_code="2900",
        target_name="資産の部合計",
        financial_statement="bs",
        formula_type="sum",
        component_codes=asset_component_codes,
        description="資産の部合計 = 現金預け金 + コールローン + ... + 貸倒引当金",
        priority=10
    )
    
    # 負債の部合計（科目4900）の計算式を作成
    liability_component_codes = [
        "3000",  # 預金
        "3100",  # 譲渡性預金
        "3200",  # 債券
        "3300",  # コールマネー
        "3400",  # 売現先勘定
        "3500",  # 債券貸借取引受入担保金
        "3600",  # 借用金
        "3700",  # 外国為替(負債)
        "3800",  # 社債
        "3900",  # その他負債
        "4000",  # 賞与引当金
        "4100",  # 退職給付引当金
        "4200",  # 役員退職慰労引当金
        "4300",  # 繰延税金負債
        "4400",  # 再評価に係る繰延税金負債
        "4500"   # 支払承諾
    ]
    
    AccountCalculator.create_formula(
        target_code="4900",
        target_name="負債の部合計",
        financial_statement="bs",
        formula_type="sum",
        component_codes=liability_component_codes,
        description="負債の部合計 = 預金 + 譲渡性預金 + ... + 支払承諾",
        priority=10
    )
    
    # 純資産の部合計（科目5900）の計算式を作成
    equity_component_codes = [
        "5000",  # 資本金
        "5100",  # 資本剰余金
        "5200",  # 利益剰余金
        "5300",  # その他有価証券評価差額金
        "5400",  # 繰延ヘッジ損益
        "5500"   # 土地再評価差額金
    ]
    
    AccountCalculator.create_formula(
        target_code="5900",
        target_name="純資産の部合計",
        financial_statement="bs",
        formula_type="sum",
        component_codes=equity_component_codes,
        description="純資産の部合計 = 資本金 + 資本剰余金 + ... + 土地再評価差額金",
        priority=10
    )
    
    # 負債及び純資産の部合計（科目5950）の計算式を作成（負債＋純資産）
    # 優先度が高いため先に計算される
    liab_equity_component_codes = [
        "4900",  # 負債の部合計
        "5900"   # 純資産の部合計
    ]
    
    AccountCalculator.create_formula(
        target_code="5950",
        target_name="負債及び純資産の部合計",
        financial_statement="bs",
        formula_type="sum",
        component_codes=liab_equity_component_codes,
        description="負債及び純資産の部合計 = 負債の部合計 + 純資産の部合計",
        priority=20  # 優先度高め
    )
    
    # 負債及び純資産の部合計（バランスチェック: 資産合計と一致するはず）
    # この計算式はデバッグ用
    total_check_component_codes = [
        "2900",  # 資産の部合計
    ]
    
    AccountCalculator.create_formula(
        target_code="5951",
        target_name="バランスチェック（資産合計）",
        financial_statement="bs",
        formula_type="sum",
        component_codes=total_check_component_codes,
        description="バランスチェック = 資産の部合計（チェック用）",
        priority=30  # 最も優先度高め
    )
    
    logger.info("BS account formulas initialized successfully")

def main():
    """メイン関数"""
    with app.app_context():
        try:
            # 貸借対照表（BS）の合計勘定科目の計算式を初期化
            initialize_bs_formulas()
            
            logger.info("Account formulas initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing account formulas: {str(e)}")

if __name__ == "__main__":
    main()