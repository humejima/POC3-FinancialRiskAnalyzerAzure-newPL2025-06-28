import logging
import json
from app import db
from models import StandardAccountBalance, AccountFormula, StandardAccount
from sqlalchemy import func

# ロガーの設定
logger = logging.getLogger(__name__)

class AccountCalculator:
    """
    勘定科目の合計値を計算するためのクラス
    StandardAccountBalanceテーブルのデータを使用して、定義された計算式に基づいて勘定科目の合計値を計算する
    
    使用例:
    - 資産の部合計 = 現金預け金 + コールローン + ... + 貸倒引当金
    - 負債の部合計 = 預金 + 譲渡性預金 + ... + 支払承諾
    - 純資産の部合計 = 資本金 + 資本剰余金 + ... + 土地再評価差額金
    - 負債及び純資産の部合計 = 負債の部合計 + 純資産の部合計
    """
    
    @staticmethod
    def calculate_account_totals(ja_code, year, financial_statement="bs"):
        """
        指定されたJA、年度、財務諸表タイプに対して、計算式に基づいて勘定科目の合計値を計算する
        
        Args:
            ja_code: JA code
            year: Financial year
            financial_statement: Type of financial statement (bs, pl, cf)
            
        Returns:
            int: 計算した科目数
        """
        try:
            # 計算式を取得（優先度順）
            formulas = AccountFormula.query.filter_by(
                financial_statement=financial_statement
            ).order_by(
                AccountFormula.priority.desc()
            ).all()
            
            if not formulas:
                logger.info(f"No formulas found for {financial_statement}")
                return 0
                
            processed_count = 0
                
            # 各計算式について処理
            for formula in formulas:
                logger.info(f"Processing formula: {formula.target_code} ({formula.target_name})")
                
                # 計算式のタイプに応じた処理
                if formula.formula_type == "sum":
                    # 科目の合計を計算
                    total_value, total_prev_value = AccountCalculator._calculate_sum(
                        ja_code, year, financial_statement, formula
                    )
                elif formula.formula_type == "diff":
                    # 科目の差分を計算
                    total_value, total_prev_value = AccountCalculator._calculate_diff(
                        ja_code, year, financial_statement, formula
                    )
                else:
                    logger.warning(f"Unsupported formula type: {formula.formula_type}")
                    continue
                
                # カテゴリ（BS資産、BS負債など）を決定
                statement_subtype = AccountCalculator._determine_statement_subtype(
                    financial_statement, formula.target_code
                )
                
                # 既存の計算結果があれば更新、なければ新規作成
                existing_balance = StandardAccountBalance.query.filter_by(
                    ja_code=ja_code,
                    year=year,
                    statement_type=financial_statement,
                    standard_account_code=formula.target_code
                ).first()
                
                if existing_balance:
                    # 既存レコードを更新
                    existing_balance.current_value = total_value
                    existing_balance.previous_value = total_prev_value
                    logger.info(f"Updated balance: {formula.target_code}, current: {total_value}, previous: {total_prev_value}")
                else:
                    # 既存の標準勘定科目から名前を取得
                    standard_account = StandardAccount.query.filter_by(
                        code=formula.target_code,
                        financial_statement=financial_statement
                    ).first()
                    
                    account_name = standard_account.name if standard_account else formula.target_name
                    
                    # 新規レコードを作成
                    new_balance = StandardAccountBalance(
                        ja_code=ja_code,
                        year=year,
                        statement_type=financial_statement,
                        statement_subtype=statement_subtype,
                        standard_account_code=formula.target_code,
                        standard_account_name=account_name,
                        current_value=total_value,
                        previous_value=total_prev_value
                    )
                    db.session.add(new_balance)
                    logger.info(f"Created new balance: {formula.target_code}, current: {total_value}, previous: {total_prev_value}")
                
                processed_count += 1
            
            # 変更をコミット
            db.session.commit()
            logger.info(f"Processed {processed_count} account formulas")
            return processed_count
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error calculating account totals: {str(e)}")
            return 0
    
    @staticmethod
    def _calculate_sum(ja_code, year, financial_statement, formula):
        """科目の合計を計算"""
        component_codes = formula.component_codes
        
        if not component_codes:
            logger.warning(f"No component codes found for formula: {formula.target_code}")
            return 0, 0
            
        # コンポーネント科目の値を取得
        component_balances = StandardAccountBalance.query.filter(
            StandardAccountBalance.ja_code == ja_code,
            StandardAccountBalance.year == year,
            StandardAccountBalance.statement_type == financial_statement,
            StandardAccountBalance.standard_account_code.in_(component_codes)
        ).all()
        
        # 合計を計算
        total_value = sum(balance.current_value for balance in component_balances if balance.current_value is not None)
        total_prev_value = sum(balance.previous_value for balance in component_balances if balance.previous_value is not None)
        
        # 詳細をログに記録
        for balance in component_balances:
            logger.debug(f"Component: {balance.standard_account_code} ({balance.standard_account_name}), current: {balance.current_value}, previous: {balance.previous_value}")
        
        logger.info(f"Sum calculation result: {total_value} (prev: {total_prev_value})")
        return total_value, total_prev_value
    
    @staticmethod
    def _calculate_diff(ja_code, year, financial_statement, formula):
        """科目の差分を計算（最初の科目から残りを引く）"""
        component_codes = formula.component_codes
        
        if not component_codes or len(component_codes) < 2:
            logger.warning(f"Insufficient component codes for diff formula: {formula.target_code}")
            return 0, 0
            
        # コンポーネント科目の値を取得（順序を保持）
        component_balances = {}
        for code in component_codes:
            balance = StandardAccountBalance.query.filter_by(
                ja_code=ja_code,
                year=year,
                statement_type=financial_statement,
                standard_account_code=code
            ).first()
            
            if balance:
                component_balances[code] = balance
        
        # 差分を計算（最初の要素から他の要素を引く）
        if not component_balances:
            return 0, 0
            
        first_code = component_codes[0]
        first_balance = component_balances.get(first_code)
        
        if not first_balance:
            return 0, 0
            
        total_value = first_balance.current_value if first_balance.current_value is not None else 0
        total_prev_value = first_balance.previous_value if first_balance.previous_value is not None else 0
        
        # 最初の要素以外の要素を引く
        for code in component_codes[1:]:
            balance = component_balances.get(code)
            if balance:
                if balance.current_value is not None:
                    total_value -= balance.current_value
                if balance.previous_value is not None:
                    total_prev_value -= balance.previous_value
        
        logger.info(f"Diff calculation result: {total_value} (prev: {total_prev_value})")
        return total_value, total_prev_value
    
    @staticmethod
    def _determine_statement_subtype(financial_statement, account_code):
        """
        勘定科目コードから適切なstatement_subtypeを決定する
        例：BSの場合、資産か負債か純資産か
        """
        if financial_statement == "bs":
            code_prefix = account_code[0] if account_code else "0"
            
            if code_prefix in ["1", "2"]:
                return "BS資産"
            elif code_prefix in ["3", "4"]:
                return "BS負債"
            elif code_prefix in ["5"]:
                return "BS純資産"
            else:
                return "BS"
        elif financial_statement == "pl":
            code_prefix = account_code[0] if account_code else "0"
            
            if code_prefix in ["6"]:
                return "PL収益"
            elif code_prefix in ["7", "8"]:
                return "PL費用"
            else:
                return "PL"
        elif financial_statement == "cf":
            code_prefix = account_code[0] if account_code else "0"
            
            if code_prefix in ["9"]:
                if account_code.startswith("90"):
                    return "CF営業活動"
                elif account_code.startswith("91"):
                    return "CF投資活動"
                elif account_code.startswith("92"):
                    return "CF財務活動"
                elif account_code.startswith("93"):
                    return "CF現金同等物"
                else:
                    return "CF"
            else:
                return "CF"
        else:
            return financial_statement.upper()
    
    @staticmethod
    def create_formula(target_code, target_name, financial_statement, formula_type, component_codes, operator='+', description=None, priority=0):
        """
        新しい計算式を作成する
        
        Args:
            target_code: 計算結果の科目コード
            target_name: 計算結果の科目名
            financial_statement: 財務諸表のタイプ (bs, pl, cf)
            formula_type: 計算式のタイプ (sum, diff, product, ratio)
            component_codes: 計算に使用する科目コードのリスト
            operator: 演算子 (+, -, *, /)
            description: 計算式の説明
            priority: 計算優先順位
            
        Returns:
            AccountFormula: 作成された計算式オブジェクト
        """
        try:
            # 既存の計算式をチェック
            existing_formula = AccountFormula.query.filter_by(
                target_code=target_code,
                financial_statement=financial_statement
            ).first()
            
            # JSONに変換
            components_json = json.dumps(component_codes)
            
            if existing_formula:
                # 既存の計算式を更新
                existing_formula.target_name = target_name
                existing_formula.formula_type = formula_type
                existing_formula.components = components_json
                existing_formula.operator = operator
                existing_formula.description = description
                existing_formula.priority = priority
                formula = existing_formula
                logger.info(f"Updated formula: {target_code} ({target_name})")
            else:
                # 新規計算式を作成
                formula = AccountFormula(
                    target_code=target_code,
                    target_name=target_name,
                    financial_statement=financial_statement,
                    formula_type=formula_type,
                    components=components_json,
                    operator=operator,
                    description=description,
                    priority=priority
                )
                db.session.add(formula)
                logger.info(f"Created new formula: {target_code} ({target_name})")
            
            db.session.commit()
            return formula
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating formula: {str(e)}")
            return None