"""
流動性指標の計算と表示を修正するスクリプト
このスクリプトは流動性指標の計算に使用される流動資産と流動負債の値を直接修正し、
financial_indicators.pyの計算ロジックと一致させます。
"""
from app import app, db
from models import StandardAccountBalance, AnalysisResult, StandardAccount
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_liquidity_values_and_indicators(ja_code, year):
    """
    流動資産（コード：11000）と流動負債（コード：21000）の値を修正し、
    それに基づいて流動性指標を再計算します。
    """
    with app.app_context():
        try:
            # 流動資産（コード：11000）と流動負債（コード：21000）のデータを確認・更新
            update_current_assets(ja_code, year)
            update_current_liabilities(ja_code, year)
            
            # 流動性指標を再計算
            recalculate_liquidity_indicators(ja_code, year)
            
            return True
        except Exception as e:
            logger.error(f"流動性指標の更新中にエラーが発生しました: {str(e)}")
            return False

def update_current_assets(ja_code, year):
    """流動資産の値を更新する"""
    try:
        # 設定済みのコードを使用して直接データを取得
        code = '11000'
        # check if existing data is available first
        existing_value = get_account_value(ja_code, year, code)
        if existing_value > 0:
            logger.info(f"既存の流動資産データを使用: {existing_value}")
            return existing_value
        
        # 現金預け金（現金+預け金）
        cash = get_account_value(ja_code, year, "1010")  # 現金
        deposits = get_account_value(ja_code, year, "1020")  # 預け金
        cash_deposits = cash + deposits
        
        securities = get_account_value(ja_code, year, "1600")  # 有価証券
        loans = get_account_value(ja_code, year, "1700")  # 貸出金
        foreign_exchange = get_account_value(ja_code, year, "1800")  # 外国為替
        other_assets = get_account_value(ja_code, year, "1900")  # その他資産
        
        # 流動資産の合計を計算
        current_assets_value = cash_deposits + securities + loans + foreign_exchange + other_assets
        
        # 流動資産情報をログに出力
        logger.info(f"現金: {cash}")
        logger.info(f"預け金: {deposits}")
        logger.info(f"現金預け金: {cash_deposits}")
        logger.info(f"有価証券: {securities}")
        logger.info(f"貸出金: {loans}")
        logger.info(f"外国為替: {foreign_exchange}")
        logger.info(f"その他資産: {other_assets}")
        logger.info(f"流動資産合計: {current_assets_value}")
        
        # データベースの流動資産(11000)を更新または作成
        current_assets = StandardAccountBalance.query.filter_by(
            ja_code=ja_code,
            year=year,
            standard_account_code='11000'
        ).first()
        
        if current_assets:
            logger.info(f"流動資産(11000)を更新: {current_assets_value}")
            current_assets.current_value = current_assets_value
        else:
            logger.info(f"流動資産(11000)を新規作成: {current_assets_value}")
            new_assets = StandardAccountBalance(
                ja_code=ja_code,
                year=year,
                statement_type='bs',
                statement_subtype='BS資産',
                standard_account_code='11000',
                standard_account_name='流動資産',
                current_value=current_assets_value
            )
            db.session.add(new_assets)
        
        db.session.commit()
        return current_assets_value
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"流動資産の更新中にエラーが発生しました: {str(e)}")
        return 0

def update_current_liabilities(ja_code, year):
    """流動負債の値を更新する"""
    try:
        # 設定済みのコードを使用して直接データを取得
        code = '21000'
        # check if existing data is available first
        existing_value = get_account_value(ja_code, year, code)
        if existing_value > 0:
            logger.info(f"既存の流動負債データを使用: {existing_value}")
            return existing_value
            
        # 流動負債の定義：預金（3000）+ 譲渡性預金（3100）+ 債券（3200）+ コールマネー（3300）
        # + 売現先勘定（3400）+ 債券貸借取引受入担保金（3500）+ 借用金（3600）+ 割引手形（3605）
        deposits = get_account_value(ja_code, year, "3000")  # 預金
        negotiable_deposits = get_account_value(ja_code, year, "3100")  # 譲渡性預金
        bonds = get_account_value(ja_code, year, "3200")  # 債券
        call_money = get_account_value(ja_code, year, "3300")  # コールマネー
        sales_repurchase = get_account_value(ja_code, year, "3400")  # 売現先勘定
        securities_lending = get_account_value(ja_code, year, "3500")  # 債券貸借取引受入担保金
        borrowed_money = get_account_value(ja_code, year, "3600")  # 借用金
        discounted_notes = get_account_value(ja_code, year, "3605")  # 割引手形
        
        # 流動負債の合計を計算
        current_liabilities_value = deposits + negotiable_deposits + bonds + call_money + \
                                    sales_repurchase + securities_lending + borrowed_money + \
                                    discounted_notes
        
        # 流動負債情報をログに出力
        logger.info(f"預金: {deposits}")
        logger.info(f"譲渡性預金: {negotiable_deposits}")
        logger.info(f"債券: {bonds}")
        logger.info(f"コールマネー: {call_money}")
        logger.info(f"売現先勘定: {sales_repurchase}")
        logger.info(f"債券貸借取引受入担保金: {securities_lending}")
        logger.info(f"借用金: {borrowed_money}")
        logger.info(f"割引手形: {discounted_notes}")
        logger.info(f"流動負債合計: {current_liabilities_value}")
        
        # 流動負債が0の場合は代替的な値を取得する試み
        if current_liabilities_value == 0:
            deposits_alt = get_account_value(ja_code, year, "3000")  # 預金のみで代用
            if deposits_alt > 0:
                current_liabilities_value = deposits_alt
                logger.info(f"流動負債がゼロのため預金値を使用: {current_liabilities_value}")
        
        # データベースの流動負債(21000)を更新または作成
        current_liabilities = StandardAccountBalance.query.filter_by(
            ja_code=ja_code,
            year=year,
            standard_account_code='21000'
        ).first()
        
        if current_liabilities:
            logger.info(f"流動負債(21000)を更新: {current_liabilities_value}")
            current_liabilities.current_value = current_liabilities_value
        else:
            logger.info(f"流動負債(21000)を新規作成: {current_liabilities_value}")
            new_liabilities = StandardAccountBalance(
                ja_code=ja_code,
                year=year,
                statement_type='bs',
                statement_subtype='BS負債',
                standard_account_code='21000',
                standard_account_name='流動負債',
                current_value=current_liabilities_value
            )
            db.session.add(new_liabilities)
        
        db.session.commit()
        return current_liabilities_value
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"流動負債の更新中にエラーが発生しました: {str(e)}")
        return 0

def get_account_value(ja_code, year, account_code):
    """勘定科目の値を取得する"""
    try:
        account = StandardAccountBalance.query.filter_by(
            ja_code=ja_code,
            year=year,
            standard_account_code=account_code
        ).first()
        
        if account and account.current_value is not None:
            return account.current_value
        
        return 0
    except Exception as e:
        logger.warning(f"勘定科目 {account_code} の取得中にエラー: {str(e)}")
        return 0

def recalculate_liquidity_indicators(ja_code, year):
    """流動性指標を再計算する"""
    try:
        # 必要な勘定科目の値を取得
        current_assets = get_account_value(ja_code, year, "11000")  # 流動資産
        current_liabilities = get_account_value(ja_code, year, "21000")  # 流動負債
        
        # 現金預け金
        cash = get_account_value(ja_code, year, "1010")  # 現金
        deposits = get_account_value(ja_code, year, "1020")  # 預け金
        cash_deposits = cash + deposits
        
        # コールローン
        call_loans = get_account_value(ja_code, year, "1110")  # コールローン
        
        # 流動性指標の計算
        
        # 流動比率 = (流動資産 ÷ 流動負債) × 100
        current_ratio = 0
        if current_liabilities != 0:
            current_ratio = (current_assets / current_liabilities) * 100
        
        # 当座比率 = (現金預け金 + コールローン) ÷ 流動負債 × 100
        quick_assets = cash_deposits + call_loans
        quick_ratio = 0
        if current_liabilities != 0:
            quick_ratio = (quick_assets / current_liabilities) * 100
        
        # 現金比率 = 現金預け金 ÷ 流動負債 × 100
        cash_ratio = 0
        if current_liabilities != 0:
            cash_ratio = (cash_deposits / current_liabilities) * 100
        
        # 運転資本 = 流動資産 - 流動負債
        working_capital = current_assets - current_liabilities
        
        logger.info(f"流動比率: {current_ratio:.2f}%")
        logger.info(f"当座比率: {quick_ratio:.2f}%")
        logger.info(f"現金比率: {cash_ratio:.2f}%")
        logger.info(f"運転資本: {working_capital:,.0f}円")
        
        # 分析結果をデータベースに保存
        
        # 流動比率
        update_analysis_result(
            ja_code=ja_code,
            year=year,
            category='liquidity',
            indicator_id='current_ratio',
            indicator_name='流動比率',
            value=current_ratio,
            unit='%',
            formula='(流動資産 ÷ 流動負債) × 100',
            calculation_details={
                '流動資産': {'name': '流動資産（合計）', 'value': current_assets},
                '流動負債': {'name': '流動負債（合計）', 'value': current_liabilities}
            }
        )
        
        # 当座比率
        update_analysis_result(
            ja_code=ja_code,
            year=year,
            category='liquidity',
            indicator_id='quick_ratio',
            indicator_name='当座比率',
            value=quick_ratio,
            unit='%',
            formula='(現金預け金 + コールローン) ÷ 流動負債 × 100',
            calculation_details={
                '当座資産': {'name': '現金預け金+コールローン', 'value': quick_assets},
                '流動負債': {'name': '流動負債（合計）', 'value': current_liabilities}
            }
        )
        
        # 現金比率
        update_analysis_result(
            ja_code=ja_code,
            year=year,
            category='liquidity',
            indicator_id='cash_ratio',
            indicator_name='現金比率',
            value=cash_ratio,
            unit='%',
            formula='現金預け金 ÷ 流動負債 × 100',
            calculation_details={
                '現金預け金': {'name': '現金預け金', 'value': cash_deposits},
                '流動負債': {'name': '流動負債（合計）', 'value': current_liabilities}
            }
        )
        
        # 運転資本
        update_analysis_result(
            ja_code=ja_code,
            year=year,
            category='liquidity',
            indicator_id='working_capital',
            indicator_name='運転資本',
            value=working_capital,
            unit='円',
            formula='流動資産 - 流動負債',
            calculation_details={
                '流動資産': {'name': '流動資産（合計）', 'value': current_assets},
                '流動負債': {'name': '流動負債（合計）', 'value': current_liabilities}
            }
        )
        
        return True
    except Exception as e:
        logger.error(f"流動性指標の再計算中にエラーが発生しました: {str(e)}")
        return False

def update_analysis_result(ja_code, year, category, indicator_id, indicator_name, value, unit, formula, calculation_details):
    """分析結果を更新または作成する"""
    try:
        # 既存の分析結果を検索
        result = AnalysisResult.query.filter_by(
            ja_code=ja_code,
            year=year,
            category=category,
            indicator_id=indicator_id
        ).first()
        
        details_json = {
            'formula': formula,
            'calculation': calculation_details
        }
        
        if result:
            # 既存の分析結果を更新
            result.indicator_name = indicator_name
            result.value = value
            result.unit = unit
            result.details = details_json
        else:
            # 新しい分析結果を作成
            new_result = AnalysisResult(
                ja_code=ja_code,
                year=year,
                category=category,
                indicator_id=indicator_id,
                indicator_name=indicator_name,
                value=value,
                unit=unit,
                details=details_json
            )
            db.session.add(new_result)
        
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        logger.error(f"分析結果の更新中にエラーが発生しました: {str(e)}")
        return False

# JA001の2021年を修正
if __name__ == "__main__":
    update_liquidity_values_and_indicators('JA001', 2021)