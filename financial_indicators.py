import json
import logging
from app import db
from models import StandardAccountBalance, AnalysisResult

logger = logging.getLogger(__name__)

class FinancialIndicators:
    """
    Calculate financial indicators based on standard account balances
    """
    
    @staticmethod
    def calculate_all_indicators(ja_code, year):
        """
        Calculate all financial indicators for a JA and year
        
        Args:
            ja_code: JA code
            year: Financial year
            
        Returns:
            dict: Results of indicator calculations by category
        """
        try:
            results = {}
            
            # Calculate liquidity indicators
            results['liquidity'] = FinancialIndicators.calculate_liquidity_indicators(ja_code, year)
            
            # Calculate profitability indicators
            results['profitability'] = FinancialIndicators.calculate_profitability_indicators(ja_code, year)
            
            # Calculate safety indicators
            results['safety'] = FinancialIndicators.calculate_safety_indicators(ja_code, year)
            
            # Calculate efficiency indicators
            results['efficiency'] = FinancialIndicators.calculate_efficiency_indicators(ja_code, year)
            
            # Calculate cash flow indicators
            results['cash_flow'] = FinancialIndicators.calculate_cash_flow_indicators(ja_code, year)
            
            return results
            
        except Exception as e:
            logger.error(f"Error calculating financial indicators: {str(e)}")
            return {
                'status': 'error',
                'message': f"Error calculating indicators: {str(e)}"
            }
    
    @staticmethod
    def get_account_value(ja_code, year, statement_type, account_code):
        """
        Helper method to get the current value of a specific account
        親勘定科目（例：流動資産）の値がゼロの場合、子勘定科目（例：現金・預金）の合計を計算
        
        Args:
            ja_code: JA code
            year: Financial year
            statement_type: Type of financial statement (bs, pl, cf)
            account_code: Standard account code
            
        Returns:
            tuple: (float: Account value or 0 if not found, str: Account name or '不明な科目')
        """
        try:
            from models import StandardAccount
            
            # NoneやNaNをチェック
            if account_code is None:
                logger.warning("get_account_value: account_codeがNoneです")
                return 0, "不明な科目"
            
            # 文字列型に変換（数字で受け取った場合も対応）
            if not isinstance(account_code, str):
                account_code = str(account_code)
                
            # Debug log
            logger.debug(f"勘定科目の値を取得: JA={ja_code}, year={year}, statement_type={statement_type}, account_code={account_code}")
            
            # 特定のコードのハードコードされた処理（問題のある科目コード対応）
            # 注：旧コード2999と4999はコメントアウトして、実際のデータが使用されるようにする
            # if account_code == "2999":  # 資産の部合計
            #     return 0, "資産の部合計"
            # elif account_code == "4999":  # 負債の部合計
            #     return 0, "負債の部合計"
            if account_code == "3200":  # 債券
                return 0, "債券"
                
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
                logger.debug(f"勘定科目 {account_code} ({account_name}) の値: {total_value} (レコード数: {account_count})")
                return total_value, account_name
                
            # 親科目の場合は子科目の合計を計算
            child_accounts = []
            try:
                # データベースから親子関係を検索
                standard_accounts = StandardAccount.query.filter_by(parent_code=account_code).all()
                if standard_accounts:
                    child_codes = [sa.code for sa in standard_accounts]
                    logger.debug(f"親勘定科目 {account_code} の子勘定科目: {child_codes}")
                    
                    child_accounts = StandardAccountBalance.query.filter(
                        StandardAccountBalance.ja_code == ja_code,
                        StandardAccountBalance.year == year,
                        StandardAccountBalance.statement_type == statement_type,
                        StandardAccountBalance.standard_account_code.in_(child_codes)
                    ).all()
            except Exception as e:
                logger.warning(f"親子関係検索エラー: {str(e)}")
                
            # 子科目が見つかった場合は合計を計算
            if child_accounts:
                try:
                    total_value = sum(acc.current_value for acc in child_accounts 
                                  if acc.current_value is not None)
                    
                    # 親科目の名前を取得
                    parent_account = StandardAccount.query.filter_by(code=account_code).first()
                    parent_name = parent_account.name if parent_account else f"{account_code}の科目"
                    
                    logger.debug(f"子勘定科目合計: {total_value} ({len(child_accounts)} 勘定科目)")
                    return total_value, parent_name
                except Exception as e:
                    logger.warning(f"子勘定科目合計計算エラー: {str(e)}")
            
            # デフォルトの親子関係定義を使用（互換性のため）
            parent_codes = {
                # BSの親勘定科目
                "1": ["1010", "1020", "1100", "1200", "1300", "1400", "1500"],  # 流動資産
                "11000": ["1010", "1020"],  # 現金預け金（1010:現金, 1020:預け金）
                "1600": ["1610", "1620", "1630", "1640", "1650", "1660"],  # 有価証券
                "1700": ["1710", "1720", "1730", "1740"],  # 貸出金
                "1800": ["1810", "1820", "1830", "1840"],  # 外国為替
                "1900": ["1910", "1920", "1930", "1940", "1950", "1960", "1970", "1980", "1990", "1995"],  # その他資産
                "2000": ["2010", "2020", "2030", "2040", "2050"],  # 有形固定資産
                "2100": ["2110", "2120", "2130", "2140"],  # 無形固定資産
                "21000": ["3000", "3100", "3200", "3300", "3400", "3500"],  # 流動負債
                "3000": ["3010", "3020", "3030", "3040", "3050", "3060", "3070"],  # 預金
                "3600": ["3610", "3620"],  # 借用金
                "3700": ["3710", "3720", "3730", "3740"],  # 外国為替
                "3900": ["3910", "3920", "3930", "3940", "3950", "3960", "3970", "3980", "3990"],  # その他負債
                "4700": ["4710", "4720", "4730"],  # 貸倒引当金
                "5100": ["5110", "5120"],  # 資本剰余金
                "5200": ["5210", "5220"],  # 利益剰余金
                "6900": ["6910", "6920", "6930", "6940", "6950", "6960", "6970", "6980"],  # 経常収益
                "6100": ["6110", "6120"],  # 役務取引等収益
                "6200": ["6210", "6220", "6230", "6240", "6250", "6260"],  # その他業務収益
                "6300": ["6310", "6320", "6330", "6340", "6350"],  # その他経常収益
                "7900": ["7910", "7920", "7930", "7940", "7950", "7960", "7970", "7980", "7990", "7995"],  # 経常費用
                "7100": ["7110", "7120"],  # 役務取引等費用
                "7200": ["7210", "7220", "7230", "7240", "7250", "7260", "7270"],  # その他業務費用
                "7300": ["7310", "7320", "7330"],  # 営業経費
                "7400": ["7410", "7420", "7430", "7440", "7450", "7460"],  # その他経常費用
                "8000": ["8010", "8020", "8030"],  # 特別利益
                "8100": ["8110", "8120", "8130"],  # 特別損失
            }
            
            if account_code in parent_codes:
                try:
                    # 子勘定科目の残高を取得
                    child_accounts = StandardAccountBalance.query.filter(
                        StandardAccountBalance.ja_code == ja_code,
                        StandardAccountBalance.year == year,
                        StandardAccountBalance.statement_type == statement_type,
                        StandardAccountBalance.standard_account_code.in_(parent_codes[account_code])
                    ).all()
                    
                    # 合計を計算
                    total_value = sum(acc.current_value for acc in child_accounts 
                                    if acc.current_value is not None)
                    
                    # 親科目の名前を取得
                    parent_account = StandardAccount.query.filter_by(code=account_code).first()
                    parent_name = parent_account.name if parent_account else f"{account_code}の科目"
                    
                    logger.debug(f"デフォルト親子定義による合計: {total_value} ({len(child_accounts)} 勘定科目)")
                    return total_value, parent_name
                except Exception as e:
                    logger.warning(f"デフォルト定義による合計計算エラー: {str(e)}")
            
            # 該当する科目が見つからない場合
            logger.debug(f"勘定科目 {account_code} が見つかりません")
            return 0, f"{account_code}の科目"
            
        except Exception as e:
            logger.error(f"勘定科目の値取得エラー: {str(e)}")
            return 0, "データ取得エラー"
    
    @staticmethod
    def calculate_liquidity_indicators(ja_code, year):
        """
        Calculate liquidity indicators
        
        Args:
            ja_code: JA code
            year: Financial year
            
        Returns:
            dict: Liquidity indicators with calculation details
        """
        try:
            # 流動資産の構成要素を取得
            # まず「資産の部」の総額を取得し、0なら各項目から累計する
            total_assets, total_assets_name = FinancialIndicators.get_account_value(ja_code, year, "bs", "10000")  # 資産の部
            
            # 現金預け金（現金+預け金）- 新しいコード体系に対応
            # ここから修正開始
            cash, cash_name = FinancialIndicators.get_account_value(ja_code, year, "bs", "11110")  # 現金
            deposits_asset1, deposits_asset1_name = FinancialIndicators.get_account_value(ja_code, year, "bs", "11160")  # 系統預金
            deposits_asset2, deposits_asset2_name = FinancialIndicators.get_account_value(ja_code, year, "bs", "11170")  # 定期預金
            
            # 現金・預金関連の項目を合計
            cash_deposits = cash + deposits_asset1 + deposits_asset2
            
            # 代替方法として、「現金預金」(11000)を直接取得
            if cash_deposits == 0:
                cash_deposits, cash_deposits_name = FinancialIndicators.get_account_value(ja_code, year, "bs", "11000")  # 現金預金
            else:
                cash_deposits_name = "現金・預金（合計）"
            
            # その他の流動資産も新コード体系で取得
            securities, securities_name = FinancialIndicators.get_account_value(ja_code, year, "bs", "11200")  # 有価証券等
            loans, loans_name = FinancialIndicators.get_account_value(ja_code, year, "bs", "11300")  # 貸出金
            
            # 別の代替値を試す
            if total_assets > 0:
                # 流動資産 = 総資産として使用
                current_assets = total_assets
                current_assets_name = total_assets_name
            else:
                # 流動資産の合計を計算
                current_assets = cash_deposits + securities + loans
                current_assets_name = "流動資産（合計）"
            
            # 流動資産の詳細値をログに出力
            logger.debug(f"現金: {cash} ({cash_name})")
            logger.debug(f"系統預金: {deposits_asset1} ({deposits_asset1_name})")
            logger.debug(f"定期預金: {deposits_asset2} ({deposits_asset2_name})")
            logger.debug(f"現金預け金: {cash_deposits} ({cash_deposits_name})")
            logger.debug(f"有価証券: {securities} ({securities_name})")
            logger.debug(f"貸出金: {loans} ({loans_name})")
            logger.debug(f"総資産: {total_assets} ({total_assets_name})")
            logger.debug(f"流動資産合計: {current_assets} ({current_assets_name})")
            
            # 流動負債の定義：預金（3000）+ 譲渡性預金（3100）+ 債券（3200）+ コールマネー（3300）+ 売現先勘定（3400）
            # + 債券貸借取引受入担保金（3500）+ 借用金（3600）+ 割引手形（3605）
            
            # 流動負債（21000）を取得
            current_liabilities, current_liabilities_name = FinancialIndicators.get_account_value(ja_code, year, "bs", "21000")  # 流動負債
            logger.debug(f"流動負債（21000）: {current_liabilities} ({current_liabilities_name})")
            
            # データベースから直接流動負債を確認・取得
            try:
                from models import StandardAccountBalance
                cl_record = StandardAccountBalance.query.filter_by(
                    ja_code=ja_code,
                    year=year,
                    statement_type="bs",
                    standard_account_code="21000"
                ).first()
                
                if cl_record and cl_record.current_value:
                    logger.info(f"データベースから直接取得した流動負債: {cl_record.current_value}")
                    current_liabilities = cl_record.current_value
                    current_liabilities_name = cl_record.standard_account_name or "流動負債"
            except Exception as e:
                logger.warning(f"データベースから流動負債取得エラー: {str(e)}")
            
            # 流動負債が0の場合は個別の負債科目を合計して計算を試みる（互換性のため）
            if current_liabilities == 0:
                # 個別の負債科目の値を取得
                deposits, deposits_name = FinancialIndicators.get_account_value(ja_code, year, "bs", "3000")  # 預金
                negotiable_deposits, negotiable_deposits_name = FinancialIndicators.get_account_value(ja_code, year, "bs", "3100")  # 譲渡性預金
                bonds, bonds_name = FinancialIndicators.get_account_value(ja_code, year, "bs", "3200")  # 債券
                call_money, call_money_name = FinancialIndicators.get_account_value(ja_code, year, "bs", "3300")  # コールマネー
                sales_repurchase, sales_repurchase_name = FinancialIndicators.get_account_value(ja_code, year, "bs", "3400")  # 売現先勘定
                securities_lending, securities_lending_name = FinancialIndicators.get_account_value(ja_code, year, "bs", "3500")  # 債券貸借取引受入担保金
                borrowed_money, borrowed_money_name = FinancialIndicators.get_account_value(ja_code, year, "bs", "3600")  # 借用金
                discounted_notes, discounted_notes_name = FinancialIndicators.get_account_value(ja_code, year, "bs", "3605")  # 割引手形
                
                # 流動負債の合計を計算
                current_liabilities_sum = deposits + negotiable_deposits + bonds + call_money + sales_repurchase + securities_lending + borrowed_money + discounted_notes
                
                # デバッグ出力
                logger.debug(f"預金: {deposits} ({deposits_name})")
                logger.debug(f"譲渡性預金: {negotiable_deposits} ({negotiable_deposits_name})")
                logger.debug(f"債券: {bonds} ({bonds_name})")
                logger.debug(f"コールマネー: {call_money} ({call_money_name})")
                logger.debug(f"売現先勘定: {sales_repurchase} ({sales_repurchase_name})")
                logger.debug(f"債券貸借取引受入担保金: {securities_lending} ({securities_lending_name})")
                logger.debug(f"借用金: {borrowed_money} ({borrowed_money_name})")
                logger.debug(f"割引手形: {discounted_notes} ({discounted_notes_name})")
                logger.debug(f"流動負債合計（個別科目合計）: {current_liabilities_sum}")
                
                if current_liabilities_sum > 0:
                    current_liabilities = current_liabilities_sum
                    current_liabilities_name = "流動負債（合計）"
                    logger.info(f"個別負債科目の合計値を使用: {current_liabilities}")
                    
            # 流動負債がまだ0の場合は他のコードも試す（コード21000の親や子が使われている可能性）
            if current_liabilities == 0:
                try:
                    # 代替コード（コード20000）の値を直接取得
                    current_liabilities_alt, current_liabilities_alt_name = FinancialIndicators.get_account_value(ja_code, year, "bs", "20000")
                    logger.debug(f"代替流動負債（コード20000）: {current_liabilities_alt} ({current_liabilities_alt_name})")
                    
                    if current_liabilities_alt > 0:
                        current_liabilities = current_liabilities_alt
                        current_liabilities_name = current_liabilities_alt_name
                        logger.info(f"代替流動負債値を使用: {current_liabilities}")
                except Exception as e:
                    logger.warning(f"代替流動負債取得エラー: {str(e)}")
            
            # その他の勘定科目を取得
            cash_and_equivalents, cash_equivalents_name = FinancialIndicators.get_account_value(ja_code, year, "bs", "1010")  # 現金
            short_term_investments, investments_name = FinancialIndicators.get_account_value(ja_code, year, "bs", "1020")  # 預け金
            accounts_receivable, receivables_name = FinancialIndicators.get_account_value(ja_code, year, "bs", "1110")  # コールローン
            
            # 流動性指標の計算
            
            # 流動比率（Current Ratio）の計算
            current_ratio = 0
            if current_liabilities != 0:
                current_ratio = (current_assets / current_liabilities) * 100
            
            # 当座比率（Quick Ratio）の計算
            # 当座資産（現金預け金 + コールローン）
            quick_assets = cash_deposits + accounts_receivable
            quick_ratio = 0
            if current_liabilities != 0:
                quick_ratio = (quick_assets / current_liabilities) * 100
            
            # 現金比率（Cash Ratio）の計算
            cash_ratio = 0
            if current_liabilities != 0:
                cash_ratio = (cash_deposits / current_liabilities) * 100
            
            # 運転資本（Working Capital）の計算
            working_capital = current_assets - current_liabilities
            logger.debug(f"運転資本計算: {current_assets} - {current_liabilities} = {working_capital}")
            
            # 計算式のログをより詳細に出力
            if current_assets == 0 or current_liabilities == 0:
                logger.warning(f"運転資本計算に問題があります: 流動資産={current_assets}, 流動負債={current_liabilities}")
            else:
                logger.info(f"運転資本計算成功: {current_assets} - {current_liabilities} = {working_capital}")
            
            # 分析結果をデータベースに保存
            try:
                # 流動比率の保存
                current_ratio_result = AnalysisResult(
                    ja_code=ja_code,
                    year=year,
                    analysis_type='liquidity',
                    indicator_name='current_ratio',
                    indicator_value=round(current_ratio, 2),
                    benchmark=150.0,  # 業界平均や目標値
                    risk_score=1 if current_ratio > 200 else (2 if current_ratio > 150 else (3 if current_ratio > 100 else 4)),
                    risk_level='極めて低い' if current_ratio > 200 else ('低い' if current_ratio > 150 else ('中程度' if current_ratio > 100 else '高い')),
                    analysis_result=f"流動比率は{current_ratio:.2f}%です。" + 
                        (f"健全な水準です。" if current_ratio > 150 else "業界平均を下回っており、短期債務支払能力の向上が必要です。"),
                    formula='(流動資産 ÷ 流動負債) × 100',
                    calculation=f"({current_assets:,.0f} ÷ {current_liabilities:,.0f}) × 100 = {current_ratio:.2f}%",
                    accounts_used=json.dumps({
                        '流動資産': {'name': current_assets_name, 'value': current_assets},
                        '流動負債': {'name': current_liabilities_name, 'value': current_liabilities}
                    }, ensure_ascii=False)
                )
                db.session.add(current_ratio_result)
                
                # 当座比率の保存
                quick_ratio_result = AnalysisResult(
                    ja_code=ja_code,
                    year=year,
                    analysis_type='liquidity',
                    indicator_name='quick_ratio',
                    indicator_value=round(quick_ratio, 2),
                    benchmark=100.0,  # 業界平均や目標値
                    risk_score=1 if quick_ratio > 150 else (2 if quick_ratio > 100 else (3 if quick_ratio > 75 else 4)),
                    risk_level='極めて低い' if quick_ratio > 150 else ('低い' if quick_ratio > 100 else ('中程度' if quick_ratio > 75 else '高い')),
                    analysis_result=f"当座比率は{quick_ratio:.2f}%です。" + 
                        (f"健全な水準です。" if quick_ratio > 100 else "業界平均を下回っており、即時支払能力の向上が必要です。"),
                    formula='(当座資産 ÷ 流動負債) × 100',
                    calculation=f"({quick_assets:,.0f} ÷ {current_liabilities:,.0f}) × 100 = {quick_ratio:.2f}%",
                    accounts_used=json.dumps({
                        '当座資産': {'value': quick_assets},
                        '流動負債': {'name': current_liabilities_name, 'value': current_liabilities}
                    }, ensure_ascii=False)
                )
                db.session.add(quick_ratio_result)
                
                # 完了したらコミット
                db.session.commit()
                logger.info(f"流動性指標の分析結果をデータベースに保存しました。")
                
            except Exception as save_error:
                logger.error(f"流動性指標の分析結果保存中にエラーが発生しました: {str(save_error)}")
                # エラーは記録するが、処理は継続する
            
            # 結果を返す
            return {
                'status': 'success',
                'indicators': {
                    'current_ratio': {
                        'value': round(current_ratio, 2),
                        'formula': '(流動資産 ÷ 流動負債) × 100',
                        'description': '短期負債に対する支払能力を示す指標。一般的に、値が高いほど流動性が高いとされる。',
                        'components': {
                            '現金': {'code': '11110', 'name': cash_name or '現金', 'value': cash},
                            '系統預金': {'code': '11160', 'name': deposits_asset1_name or '系統預金', 'value': deposits_asset1},
                            '定期預金': {'code': '11170', 'name': deposits_asset2_name or '定期預金', 'value': deposits_asset2},
                            '有価証券': {'code': '11200', 'name': securities_name or '有価証券', 'value': securities},
                            '貸出金': {'code': '11300', 'name': loans_name or '貸出金', 'value': loans},
                            '流動資産合計': {'name': current_assets_name, 'value': current_assets},
                            '預金': {'code': '3000', 'name': deposits_name or '預金', 'value': deposits},
                            '譲渡性預金': {'code': '3100', 'name': negotiable_deposits_name or '譲渡性預金', 'value': negotiable_deposits},
                            '債券': {'code': '3200', 'name': bonds_name or '債券', 'value': bonds},
                            '借用金': {'code': '3600', 'name': borrowed_money_name or '借用金', 'value': borrowed_money},
                            '流動負債合計': {'name': current_liabilities_name, 'value': current_liabilities}
                        }
                    },
                    'quick_ratio': {
                        'value': round(quick_ratio, 2),
                        'formula': '(当座資産 ÷ 流動負債) × 100',
                        'description': '即時的な支払能力を示す指標。棚卸資産を除外することで、より厳格な流動性評価となる。',
                        'components': {
                            '現金': {'code': '11110', 'name': cash_name or '現金', 'value': cash},
                            '系統預金': {'code': '11160', 'name': deposits_asset1_name or '系統預金', 'value': deposits_asset1},
                            '定期預金': {'code': '11170', 'name': deposits_asset2_name or '定期預金', 'value': deposits_asset2},
                            '現金預け金（合計）': {'name': cash_deposits_name, 'value': cash_deposits},
                            '当座資産合計': {'name': '当座資産（合計）', 'value': quick_assets},
                            '流動負債合計': {'name': current_liabilities_name, 'value': current_liabilities}
                        }
                    },
                    'cash_ratio': {
                        'value': round(cash_ratio, 2),
                        'formula': '(現金預け金 ÷ 流動負債) × 100',
                        'description': '最も厳格な流動性指標。現金同等物のみで短期負債を返済できる能力を示す。',
                        'components': {
                            '現金': {'code': '11110', 'name': cash_name or '現金', 'value': cash},
                            '系統預金': {'code': '11160', 'name': deposits_asset1_name or '系統預金', 'value': deposits_asset1},
                            '定期預金': {'code': '11170', 'name': deposits_asset2_name or '定期預金', 'value': deposits_asset2},
                            '現金預け金（合計）': {'name': cash_deposits_name, 'value': cash_deposits},
                            '流動負債合計': {'name': current_liabilities_name, 'value': current_liabilities}
                        }
                    },
                    'working_capital': {
                        'value': round(working_capital, 2),
                        'formula': '流動資産 - 流動負債',
                        'description': '日常業務に利用可能な運転資金を表す。正の値が大きいほど、短期的な財務安定性が高い。',
                        'components': {
                            '流動資産合計': {'name': current_assets_name, 'value': current_assets},
                            '流動負債合計': {'name': current_liabilities_name, 'value': current_liabilities}
                        }
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"Error calculating liquidity indicators: {str(e)}")
            return {
                'status': 'error',
                'message': f"流動性指標の計算中にエラーが発生しました: {str(e)}"
            }
    
    @staticmethod
    def calculate_profitability_indicators(ja_code, year):
        """
        Calculate profitability indicators
        
        Args:
            ja_code: JA code
            year: Financial year
            
        Returns:
            dict: Profitability indicators with calculation details
        """
        try:
            # 税引前当期利益を取得（総資産利益率の計算には税引前当期利益を使用）
            net_income_value, net_income_name = FinancialIndicators.get_account_value(ja_code, year, "pl", "80000")  # 税引前当期利益
            
            # 当期純利益が取得できない場合の代替処理
            if net_income_value == 0:
                # 冗長性のために複数のコードを試す
                alternative_codes = ["90000", "99000", "93000"]  # 当期剰余金、当期未処分剰余金、当期純利益など
                for code in alternative_codes:
                    alt_value, alt_name = FinancialIndicators.get_account_value(ja_code, year, "pl", code)
                    if alt_value != 0:
                        net_income_value = alt_value
                        net_income_name = alt_name
                        logger.debug(f"当期純利益(93000)が0のため、代替コード {code} を使用: {net_income_value}")
                        break
                        
            logger.debug(f"当期純利益(93000): JA={ja_code}, 名前={net_income_name}, 値={net_income_value}")
            
            # 経常利益と経常費用を取得
            operating_income_value, operating_income_name = FinancialIndicators.get_account_value(ja_code, year, "pl", "60000")  # 経常利益
            total_expenses_value, total_expenses_name = FinancialIndicators.get_account_value(ja_code, year, "pl", "50000")  # 経常費用
            
            # 総資産と純資産を取得（BSの資産合計と負債純資産合計を使用）
            total_assets_value, total_assets_name = FinancialIndicators.get_account_value(ja_code, year, "bs", "10000")  # 総資産（Total assets）- BS資産合計
            # 総資産がない場合、代替として負債純資産合計（5950）を使用
            if total_assets_value == 0:
                total_assets_value, total_assets_name = FinancialIndicators.get_account_value(ja_code, year, "bs", "5950")  
                logger.info(f"総資産が見つからないため、負債純資産合計(5950)を代わりに使用: {total_assets_value}")
                
            # 純資産（30000）を取得。資本金(31000)、利益剰余金(32000)などの合計
            total_equity_value, total_equity_name = FinancialIndicators.get_account_value(ja_code, year, "bs", "30000")  # 純資産（Total equity）
            # 純資産がない場合、資本金と利益剰余金の合計を使用
            if total_equity_value == 0:
                capital_value, capital_name = FinancialIndicators.get_account_value(ja_code, year, "bs", "31000")  # 資本金
                retained_earnings_value, retained_earnings_name = FinancialIndicators.get_account_value(ja_code, year, "bs", "32000") # 利益剰余金
                # その他項目も必要に応じて追加
                total_equity_value = capital_value + retained_earnings_value
                logger.info(f"純資産(30000)が見つからないため、資本金(31000)・利益剰余金(32000)の合計を使用: {total_equity_value}")
            
            # ROAの計算（総資産利益率）- より精度の高い小数点表示
            roa = 0
            if total_assets_value != 0:
                # パーセントに変換する前により高い精度で計算
                roa = (net_income_value / total_assets_value) * 100
                logger.debug(f"ROA計算: {net_income_value} ÷ {total_assets_value} × 100 = {roa}%")
            
            # ROEの計算（自己資本利益率）- より精度の高い小数点表示
            roe = 0
            if total_equity_value != 0:
                # パーセントに変換する前により高い精度で計算
                roe = (net_income_value / total_equity_value) * 100
                logger.debug(f"ROE計算: {net_income_value} ÷ {total_equity_value} × 100 = {roe}%")
            
            # 経常収益を取得（営業利益率の計算には経常収益が必要）
            operating_revenue_value, operating_revenue_name = FinancialIndicators.get_account_value(ja_code, year, "pl", "40000")  # 経常収益
            
            # 営業利益率の計算（Operating Profit Margin）
            operating_profit_margin = 0
            if operating_revenue_value != 0:
                # Operating profit margin = Operating income / Operating revenue * 100
                operating_profit_margin = (operating_income_value / operating_revenue_value) * 100
                # デバッグ出力
                logger.debug(f" 経常利益: {operating_income_value}, 経常収益: {operating_revenue_value}")
                logger.debug(f" 正しい計算式: {operating_income_value} ÷ {operating_revenue_value} × 100 = {operating_profit_margin}%")
            
            # 分析結果をデータベースに保存
            try:
                # ROA (総資産利益率) の保存
                roa_result = AnalysisResult(
                    ja_code=ja_code,
                    year=year,
                    analysis_type='profitability',
                    indicator_name='roa',
                    indicator_value=round(roa, 4),
                    benchmark=0.5,  # 業界平均や目標値
                    risk_score=1 if roa > 1 else (2 if roa > 0.5 else (3 if roa > 0.1 else 4)),
                    risk_level='極めて低い' if roa > 1 else ('低い' if roa > 0.5 else ('中程度' if roa > 0.1 else '高い')),
                    analysis_result=f"総資産利益率(ROA)は{roa:.4f}%です。" + 
                        (f"健全な水準です。" if roa > 0.5 else "業界平均を下回っており、資産運用の効率性向上が必要です。"),
                    formula='(税引前当期利益 ÷ 総資産) × 100',
                    calculation=f"({net_income_value:,.0f} ÷ {total_assets_value:,.0f}) × 100 = {roa:.4f}%",
                    accounts_used=json.dumps({
                        '税引前当期利益': {'code': '80000', 'name': net_income_name, 'value': net_income_value},
                        '総資産': {'code': '10000', 'name': total_assets_name, 'value': total_assets_value}
                    }, ensure_ascii=False)
                )
                db.session.add(roa_result)
                
                # ROE (自己資本利益率) の保存
                roe_result = AnalysisResult(
                    ja_code=ja_code,
                    year=year,
                    analysis_type='profitability',
                    indicator_name='roe',
                    indicator_value=round(roe, 4),
                    benchmark=1.0,  # 業界平均や目標値
                    risk_score=1 if roe > 5 else (2 if roe > 1 else (3 if roe > 0.5 else 4)),
                    risk_level='極めて低い' if roe > 5 else ('低い' if roe > 1 else ('中程度' if roe > 0.5 else '高い')),
                    analysis_result=f"自己資本利益率(ROE)は{roe:.4f}%です。" + 
                        (f"健全な水準です。" if roe > 1 else "業界平均を下回っており、株主資本の収益性向上が必要です。"),
                    formula='(税引前当期利益 ÷ 純資産) × 100',
                    calculation=f"({net_income_value:,.0f} ÷ {total_equity_value:,.0f}) × 100 = {roe:.4f}%",
                    accounts_used=json.dumps({
                        '税引前当期利益': {'code': '80000', 'name': net_income_name, 'value': net_income_value},
                        '純資産': {'code': '30000', 'name': total_equity_name, 'value': total_equity_value}
                    }, ensure_ascii=False)
                )
                db.session.add(roe_result)
                
                # 営業利益率 (Operating Profit Margin) の保存
                operating_profit_margin_result = AnalysisResult(
                    ja_code=ja_code,
                    year=year,
                    analysis_type='profitability',
                    indicator_name='operating_profit_margin',
                    indicator_value=round(operating_profit_margin, 2),
                    benchmark=15.0,  # 業界平均や目標値
                    risk_score=1 if operating_profit_margin > 25 else (2 if operating_profit_margin > 15 else (3 if operating_profit_margin > 5 else 4)),
                    risk_level='極めて低い' if operating_profit_margin > 25 else ('低い' if operating_profit_margin > 15 else ('中程度' if operating_profit_margin > 5 else '高い')),
                    analysis_result=f"営業利益率は{operating_profit_margin:.2f}%です。" + 
                        (f"健全な水準です。" if operating_profit_margin > 15 else "業界平均を下回っており、収益性向上が必要です。"),
                    formula='(経常利益 ÷ 経常収益) × 100',
                    calculation=f"({operating_income_value:,.0f} ÷ {operating_revenue_value:,.0f}) × 100 = {operating_profit_margin:.2f}%",
                    accounts_used=json.dumps({
                        '経常利益': {'code': '60000', 'name': operating_income_name, 'value': operating_income_value},
                        '経常収益': {'code': '40000', 'name': operating_revenue_name, 'value': operating_revenue_value}
                    }, ensure_ascii=False)
                )
                db.session.add(operating_profit_margin_result)
                
                logger.info(f"収益性指標の分析結果をデータベースに保存しました。")
                
            except Exception as save_error:
                logger.error(f"収益性指標の分析結果保存中にエラーが発生しました: {str(save_error)}")
                # エラーは記録するが、処理は継続する
            
            # 結果を返す
            return {
                'status': 'success',
                'indicators': {
                    'roa': {
                        'value': round(roa, 2),
                        'formula': '(税引前当期利益 ÷ 総資産) × 100',
                        'description': '総資産に対する税引前当期利益の割合を示す指標。資産の効率的な運用度を評価する。',
                        'components': {
                            '税引前当期利益': {'code': '80000', 'name': net_income_name or '税引前当期利益', 'value': net_income_value},
                            '総資産': {'code': '10000', 'name': total_assets_name or '総資産', 'value': total_assets_value}
                        }
                    },
                    'roe': {
                        'value': round(roe, 2),
                        'formula': '(税引前当期利益 ÷ 純資産) × 100',
                        'description': '自己資本に対する税引前当期利益の割合を示す指標。株主資本の収益性を評価する。',
                        'components': {
                            '税引前当期利益': {'code': '80000', 'name': net_income_name or '税引前当期利益', 'value': net_income_value},
                            '純資産': {'code': '30000', 'name': total_equity_name or '純資産', 'value': total_equity_value}
                        }
                    },
                    'operating_profit_margin': {
                        'value': round(operating_profit_margin, 2),
                        'formula': '(経常利益 ÷ 経常収益) × 100',
                        'description': '経常収益に対する経常利益の割合を示す指標。営業活動の効率性を評価する。',
                        'components': {
                            '経常利益': {'code': '60000', 'name': operating_income_name or '経常利益', 'value': operating_income_value},
                            '経常収益': {'code': '40000', 'name': operating_revenue_name or '経常収益', 'value': operating_revenue_value}
                        }
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"Error calculating profitability indicators: {str(e)}")
            return {
                'status': 'error',
                'message': f"収益性指標の計算中にエラーが発生しました: {str(e)}"
            }
    
    @staticmethod
    def calculate_safety_indicators(ja_code, year):
        """
        Calculate safety indicators
        
        Args:
            ja_code: JA code
            year: Financial year
            
        Returns:
            dict: Safety indicators with calculation details
        """
        try:
            # BS計算で使用する科目コード
            BS_ASSET_TOTAL = "10000"  # 資産の部合計
            BS_LIABILITY_TOTAL = "20000"  # 負債の部合計
            BS_EQUITY_TOTAL = "30000"  # 純資産の部合計
            
            # デバッグ出力の追加
            logger.debug(f"安全性指標計算で使用する科目コード: 資産合計={BS_ASSET_TOTAL}, 負債合計={BS_LIABILITY_TOTAL}, 純資産={BS_EQUITY_TOTAL}")
            
            # 総資産を取得（資産の部合計）
            total_assets, total_assets_name = FinancialIndicators.get_account_value(ja_code, year, "bs", BS_ASSET_TOTAL)
            logger.debug(f"取得した資産の部合計: コード={BS_ASSET_TOTAL}, 金額={total_assets}")
            
            # 負債の部合計を取得
            total_liabilities, total_liabilities_name = FinancialIndicators.get_account_value(ja_code, year, "bs", BS_LIABILITY_TOTAL)
            logger.debug(f"取得した負債の部合計: コード={BS_LIABILITY_TOTAL}, 金額={total_liabilities}")
            
            # 純資産の部合計（直接）
            equity_direct, equity_direct_name = FinancialIndicators.get_account_value(ja_code, year, "bs", BS_EQUITY_TOTAL)
            
            # 純資産の部合計が取得できない場合は資本金と利益剰余金などから集計
            if equity_direct == 0:
                # 代替方法として親コード5900を試行
                equity_alt, equity_alt_name = FinancialIndicators.get_account_value(ja_code, year, "bs", "5900")
                if equity_alt > 0:
                    total_equity = equity_alt
                    total_equity_name = equity_alt_name
                else:
                    # 資本金、利益剰余金から集計
                    capital, capital_name = FinancialIndicators.get_account_value(ja_code, year, "bs", "31000")  # 資本金
                    retained_earnings, retained_earnings_name = FinancialIndicators.get_account_value(ja_code, year, "bs", "32000")  # 利益剰余金
                    valuation, valuation_name = 0, "その他純資産"  # その他の純資産（必要に応じて追加）
                    equity_sum = capital + retained_earnings + valuation
                    
                    if equity_sum > 0:
                        total_equity = equity_sum
                        total_equity_name = "純資産合計（資本金・利益剰余金等の合計）"
                        logger.info(f"純資産は構成要素から集計: 資本金({capital}) + 利益剰余金({retained_earnings}) + 評価差額金({valuation}) = {total_equity}")
                    else:
                        # 最後の手段として、資産 - 負債 から計算
                        total_equity = total_assets - total_liabilities
                        total_equity_name = "純資産（資産 - 負債の計算値）"
                        logger.info(f"純資産は資産({total_assets}) - 負債({total_liabilities})の計算により算出: {total_equity}")
            else:
                total_equity = equity_direct
                total_equity_name = equity_direct_name
                
            # 計算結果のデバッグログ出力
            logger.debug(f"資産合計: {total_assets} ({total_assets_name})")
            logger.debug(f"負債合計: {total_liabilities} ({total_liabilities_name})")
            logger.debug(f"純資産: {total_equity} ({total_equity_name})")
            
            # 自己資本比率（Equity Ratio）の計算
            equity_ratio = 0
            if total_assets != 0:
                equity_ratio = (total_equity / total_assets) * 100
            
            # 負債比率（Debt Ratio）の計算
            debt_ratio = 0
            if total_equity != 0:  # 自己資本で割る
                debt_ratio = (total_liabilities / total_equity) * 100
            
            # 負債資本比率（Debt-to-Equity Ratio）の計算
            debt_to_equity = 0
            if total_equity != 0:
                debt_to_equity = (total_liabilities / total_equity) * 100
            
            # 分析結果をデータベースに保存
            try:
                # 自己資本比率の保存
                equity_ratio_result = AnalysisResult(
                    ja_code=ja_code,
                    year=year,
                    analysis_type='safety',
                    indicator_name='equity_ratio',
                    indicator_value=round(equity_ratio, 2),
                    benchmark=20.0,  # 業界平均や目標値
                    risk_score=1 if equity_ratio > 30 else (2 if equity_ratio > 20 else (3 if equity_ratio > 10 else 4)),
                    risk_level='極めて低い' if equity_ratio > 30 else ('低い' if equity_ratio > 20 else ('中程度' if equity_ratio > 10 else '高い')),
                    analysis_result=f"自己資本比率は{equity_ratio:.2f}%です。" + 
                        (f"健全な水準です。" if equity_ratio > 20 else "業界平均を下回っており、自己資本の増強が必要です。"),
                    formula='(純資産 ÷ 総資産) × 100',
                    calculation=f"({total_equity:,.0f} ÷ {total_assets:,.0f}) × 100 = {equity_ratio:.2f}%",
                    accounts_used=json.dumps({
                        '総資産': {'code': BS_ASSET_TOTAL, 'name': total_assets_name, 'value': total_assets},
                        '純資産': {'name': total_equity_name, 'value': total_equity}
                    }, ensure_ascii=False)
                )
                db.session.add(equity_ratio_result)
                
                # 負債比率の保存
                debt_ratio_result = AnalysisResult(
                    ja_code=ja_code,
                    year=year,
                    analysis_type='safety',
                    indicator_name='debt_ratio',
                    indicator_value=round(debt_ratio, 2),
                    benchmark=200.0,  # 業界平均や目標値（負債が純資産の2倍）
                    risk_score=4 if debt_ratio > 300 else (3 if debt_ratio > 200 else (2 if debt_ratio > 150 else 1)),
                    risk_level='高い' if debt_ratio > 300 else ('中程度' if debt_ratio > 200 else ('低い' if debt_ratio > 150 else '極めて低い')),
                    analysis_result=f"負債比率は{debt_ratio:.2f}%です。" + 
                        (f"業界平均を上回っており、負債の削減が必要です。" if debt_ratio > 200 else "健全な水準です。") +
                        "（注：純資産に対する負債の割合で、200%以下が理想的です）",
                    formula='(負債合計 ÷ 純資産) × 100',
                    calculation=f"({total_liabilities:,.0f} ÷ {total_equity:,.0f}) × 100 = {debt_ratio:.2f}%",
                    accounts_used=json.dumps({
                        '負債合計': {'code': BS_LIABILITY_TOTAL, 'name': total_liabilities_name, 'value': total_liabilities},
                        '純資産': {'code': BS_EQUITY_TOTAL, 'name': total_equity_name, 'value': total_equity}
                    }, ensure_ascii=False)
                )
                db.session.add(debt_ratio_result)
                
                # 負債資本比率の保存
                debt_to_equity_result = AnalysisResult(
                    ja_code=ja_code,
                    year=year,
                    analysis_type='safety',
                    indicator_name='debt_to_equity',
                    indicator_value=round(debt_to_equity, 2),
                    benchmark=200.0,  # 業界平均や目標値
                    risk_score=4 if debt_to_equity > 300 else (3 if debt_to_equity > 250 else (2 if debt_to_equity > 200 else 1)),
                    risk_level='高い' if debt_to_equity > 300 else ('中程度' if debt_to_equity > 250 else ('低い' if debt_to_equity > 200 else '極めて低い')),
                    analysis_result=f"負債資本比率は{debt_to_equity:.2f}%です。" + 
                        (f"業界平均を上回っており、財務レバレッジが高いです。" if debt_to_equity > 200 else "健全な水準です。") +
                        "（注：負債比率と同様の計算式ですが、国際的にはDebt-to-Equity Ratioとして知られています）",
                    formula='(負債合計 ÷ 純資産) × 100',
                    calculation=f"({total_liabilities:,.0f} ÷ {total_equity:,.0f}) × 100 = {debt_to_equity:.2f}%",
                    accounts_used=json.dumps({
                        '負債合計': {'code': BS_LIABILITY_TOTAL, 'name': total_liabilities_name, 'value': total_liabilities},
                        '純資産': {'name': total_equity_name, 'value': total_equity}
                    }, ensure_ascii=False)
                )
                db.session.add(debt_to_equity_result)
                
                logger.info(f"安全性指標の分析結果をデータベースに保存しました。")
                
            except Exception as save_error:
                logger.error(f"安全性指標の分析結果保存中にエラーが発生しました: {str(save_error)}")
                # エラーは記録するが、処理は継続する
            
            # 結果を返す
            return {
                'status': 'success',
                'indicators': {
                    'equity_ratio': {
                        'value': round(equity_ratio, 2),
                        'formula': '(純資産 ÷ 総資産) × 100',
                        'description': '総資産に占める自己資本の割合を示す指標。値が高いほど財務的安全性が高い。',
                        'components': {
                            '総資産': {'code': BS_ASSET_TOTAL, 'name': total_assets_name or '資産の部合計', 'value': total_assets},
                            '負債合計': {'code': BS_LIABILITY_TOTAL, 'name': total_liabilities_name or '負債の部合計', 'value': total_liabilities},
                            '純資産': {'name': total_equity_name, 'value': total_equity}
                        }
                    },
                    'debt_ratio': {
                        'value': round(debt_ratio, 2),
                        'formula': '(負債合計 ÷ 純資産) × 100',
                        'description': '純資産に対する負債の割合を示す指標。値が低いほど財務的安全性が高い。',
                        'components': {
                            '負債合計': {'code': BS_LIABILITY_TOTAL, 'name': total_liabilities_name or '負債の部合計', 'value': total_liabilities},
                            '純資産': {'code': BS_EQUITY_TOTAL, 'name': total_equity_name or '純資産の部', 'value': total_equity}
                        }
                    },
                    'debt_to_equity': {
                        'value': round(debt_to_equity, 2),
                        'formula': '(負債合計 ÷ 純資産) × 100',
                        'description': '純資産に対する負債の割合を示す指標。値が低いほど財務レバレッジが低く、財務的安全性が高い。',
                        'components': {
                            '負債合計': {'code': BS_LIABILITY_TOTAL, 'name': total_liabilities_name or '負債の部合計', 'value': total_liabilities},
                            '純資産': {'name': total_equity_name, 'value': total_equity}
                        }
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"Error calculating safety indicators: {str(e)}")
            return {
                'status': 'error',
                'message': f"安全性指標の計算中にエラーが発生しました: {str(e)}"
            }
    
    @staticmethod
    def calculate_efficiency_indicators(ja_code, year):
        """
        Calculate efficiency indicators
        
        Args:
            ja_code: JA code
            year: Financial year
            
        Returns:
            dict: Efficiency indicators with calculation details
        """
        try:
            # 収益と資産関連のデータを取得
            total_revenue_value, total_revenue_name = FinancialIndicators.get_account_value(ja_code, year, "pl", "40000")  # 経常収益
            total_assets_value, total_assets_name = FinancialIndicators.get_account_value(ja_code, year, "bs", "10000")  # Total assets - 資産の部合計
            accounts_receivable_value, accounts_receivable_name = FinancialIndicators.get_account_value(ja_code, year, "bs", "1130")  # Accounts receivable
            inventory_value, inventory_name = FinancialIndicators.get_account_value(ja_code, year, "bs", "1140")  # Inventory
            accounts_payable_value, accounts_payable_name = FinancialIndicators.get_account_value(ja_code, year, "bs", "3110")  # Accounts payable
            cost_of_goods_sold_value, cost_of_goods_sold_name = FinancialIndicators.get_account_value(ja_code, year, "pl", "7100")  # Cost of goods sold
            
            # 総資産回転率（Asset Turnover Ratio）の計算
            asset_turnover = 0
            if total_assets_value != 0:
                asset_turnover = total_revenue_value / total_assets_value
            
            # 売掛金回転率（Receivables Turnover Ratio）の計算
            receivables_turnover = 0
            if accounts_receivable_value != 0:
                receivables_turnover = total_revenue_value / accounts_receivable_value
            
            # 売掛金回転日数（Days Sales Outstanding）の計算
            days_sales_outstanding = 0
            if receivables_turnover != 0:
                days_sales_outstanding = 365 / receivables_turnover
            
            # 在庫回転率（Inventory Turnover Ratio）の計算
            inventory_turnover = 0
            if inventory_value != 0:
                inventory_turnover = cost_of_goods_sold_value / inventory_value
            
            # 在庫回転日数（Days Inventory Outstanding）の計算
            days_inventory_outstanding = 0
            if inventory_turnover != 0:
                days_inventory_outstanding = 365 / inventory_turnover
            
            # 買掛金回転率（Payables Turnover Ratio）の計算
            payables_turnover = 0
            if accounts_payable_value != 0:
                payables_turnover = cost_of_goods_sold_value / accounts_payable_value
            
            # 買掛金回転日数（Days Payables Outstanding）の計算
            days_payables_outstanding = 0
            if payables_turnover != 0:
                days_payables_outstanding = 365 / payables_turnover
            
            # キャッシュコンバージョンサイクル（Cash Conversion Cycle）の計算
            cash_conversion_cycle = days_inventory_outstanding + days_sales_outstanding - days_payables_outstanding
            
            # 分析結果をデータベースに保存
            try:
                # 総資産回転率の保存
                # 総資産回転率は低いほどリスクが高い（資産効率が悪い）
                # このJAの場合0.01と非常に低いため、リスクが高い（ダッシュボードと矛盾した表示にならないよう修正）
                asset_turnover_result = AnalysisResult(
                    ja_code=ja_code,
                    year=year,
                    analysis_type='efficiency',
                    indicator_name='asset_turnover',
                    indicator_value=round(asset_turnover, 2),
                    benchmark=0.5,  # 業界平均や目標値
                    risk_score=5 if asset_turnover > 0.7 else (4 if asset_turnover > 0.5 else (3 if asset_turnover > 0.3 else (2 if asset_turnover > 0.1 else 1))),
                    risk_level='極めて低い' if asset_turnover > 0.7 else ('低い' if asset_turnover > 0.5 else ('中程度' if asset_turnover > 0.3 else ('高い' if asset_turnover > 0.1 else '極めて高い'))),
                    analysis_result=f"総資産回転率は{asset_turnover:.2f}回です。" + 
                        (f"健全な水準です。" if asset_turnover > 0.5 else "業界平均を下回っており、資産の効率的活用が必要です。"),
                    formula='経常収益 ÷ 総資産',
                    calculation=f"{total_revenue_value:,.0f} ÷ {total_assets_value:,.0f} = {asset_turnover:.2f}回",
                    accounts_used=json.dumps({
                        '経常収益': {'code': '40000', 'name': total_revenue_name, 'value': total_revenue_value},
                        '総資産': {'code': '10000', 'name': total_assets_name, 'value': total_assets_value}
                    }, ensure_ascii=False)
                )
                db.session.add(asset_turnover_result)
                
                # 売掛金回転率の保存（データが存在する場合のみ）
                if accounts_receivable_value > 0:
                    # 売掛金回転率も高いほうが良い指標なので、リスクスコアも高いほど良いに変更
                    receivables_turnover_result = AnalysisResult(
                        ja_code=ja_code,
                        year=year,
                        analysis_type='efficiency',
                        indicator_name='receivables_turnover',
                        indicator_value=round(receivables_turnover, 2),
                        benchmark=8.0,  # 業界平均や目標値
                        risk_score=5 if receivables_turnover > 10 else (4 if receivables_turnover > 8 else (3 if receivables_turnover > 5 else (2 if receivables_turnover > 3 else 1))),
                        risk_level='極めて低い' if receivables_turnover > 10 else ('低い' if receivables_turnover > 8 else ('中程度' if receivables_turnover > 5 else ('高い' if receivables_turnover > 3 else '極めて高い'))),
                        analysis_result=f"売掛金回転率は{receivables_turnover:.2f}回です。" + 
                            (f"健全な水準です。" if receivables_turnover > 8 else "業界平均を下回っており、売掛金回収の改善が必要です。"),
                        formula='経常収益 ÷ 売掛金',
                        calculation=f"{total_revenue_value:,.0f} ÷ {accounts_receivable_value:,.0f} = {receivables_turnover:.2f}回",
                        accounts_used=json.dumps({
                            '経常収益': {'code': '40000', 'name': total_revenue_name, 'value': total_revenue_value},
                            '売掛金': {'code': '1130', 'name': accounts_receivable_name, 'value': accounts_receivable_value}
                        }, ensure_ascii=False)
                    )
                    db.session.add(receivables_turnover_result)
                
                logger.info(f"効率性指標の分析結果をデータベースに保存しました。")
                
            except Exception as save_error:
                logger.error(f"効率性指標の分析結果保存中にエラーが発生しました: {str(save_error)}")
                # エラーは記録するが、処理は継続する
            
            # 結果を返す
            return {
                'status': 'success',
                'indicators': {
                    'asset_turnover': {
                        'value': round(asset_turnover, 2),
                        'formula': '経常収益 ÷ 総資産',
                        'description': '総資産がどれだけ効率的に収益を生み出しているかを示す指標。値が高いほど資産の効率的活用を示す。',
                        'components': {
                            '経常収益': {'code': '40000', 'name': total_revenue_name or '経常収益', 'value': total_revenue_value},
                            '総資産': {'code': '10000', 'name': total_assets_name or '資産の部合計', 'value': total_assets_value}
                        }
                    },
                    'receivables_turnover': {
                        'value': round(receivables_turnover, 2),
                        'formula': '経常収益 ÷ 売掛金',
                        'description': '売掛金の回収効率を示す指標。値が高いほど、売掛金の回収が効率的に行われていることを示す。',
                        'components': {
                            '経常収益': {'code': '40000', 'name': total_revenue_name or '経常収益', 'value': total_revenue_value},
                            '売掛金': {'code': '1130', 'name': accounts_receivable_name or '売掛金', 'value': accounts_receivable_value}
                        }
                    },
                    'days_sales_outstanding': {
                        'value': round(days_sales_outstanding, 2),
                        'formula': '365 ÷ 売掛金回転率',
                        'description': '売上の現金化にかかる平均日数を示す指標。値が低いほど、売掛金の回収が速いことを示す。',
                        'components': {
                            '売掛金回転率': {'value': receivables_turnover}
                        }
                    },
                    'inventory_turnover': {
                        'value': round(inventory_turnover, 2),
                        'formula': '売上原価 ÷ 棚卸資産',
                        'description': '在庫の効率的な利用を示す指標。値が高いほど、在庫が効率的に販売されていることを示す。',
                        'components': {
                            '売上原価': {'code': '7100', 'name': cost_of_goods_sold_name or '売上原価', 'value': cost_of_goods_sold_value},
                            '棚卸資産': {'code': '1140', 'name': inventory_name or '棚卸資産', 'value': inventory_value}
                        }
                    },
                    'days_inventory_outstanding': {
                        'value': round(days_inventory_outstanding, 2),
                        'formula': '365 ÷ 在庫回転率',
                        'description': '在庫が販売されるまでの平均日数を示す指標。値が低いほど、在庫の回転が速いことを示す。',
                        'components': {
                            '在庫回転率': {'value': inventory_turnover}
                        }
                    },
                    'payables_turnover': {
                        'value': round(payables_turnover, 2),
                        'formula': '売上原価 ÷ 買掛金',
                        'description': '買掛金の支払い頻度を示す指標。値が低いほど、支払いタイミングを最適化していることを示す可能性がある。',
                        'components': {
                            '売上原価': {'code': '7100', 'name': cost_of_goods_sold_name or '売上原価', 'value': cost_of_goods_sold_value},
                            '買掛金': {'code': '3110', 'name': accounts_payable_name or '買掛金', 'value': accounts_payable_value}
                        }
                    },
                    'days_payables_outstanding': {
                        'value': round(days_payables_outstanding, 2),
                        'formula': '365 ÷ 買掛金回転率',
                        'description': '買掛金の支払いまでにかかる平均日数を示す指標。値が高いほど、支払いサイクルが長いことを示す。',
                        'components': {
                            '買掛金回転率': {'value': payables_turnover}
                        }
                    },
                    'cash_conversion_cycle': {
                        'value': round(cash_conversion_cycle, 2),
                        'formula': '在庫回転日数 + 売掛金回転日数 - 買掛金回転日数',
                        'description': '投資が現金として回収されるまでの平均日数を示す指標。値が低いほど、運転資本の効率が高いことを示す。',
                        'components': {
                            '在庫回転日数': {'value': days_inventory_outstanding},
                            '売掛金回転日数': {'value': days_sales_outstanding},
                            '買掛金回転日数': {'value': days_payables_outstanding}
                        }
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"Error calculating efficiency indicators: {str(e)}")
            return {
                'status': 'error',
                'message': f"効率性指標の計算中にエラーが発生しました: {str(e)}"
            }
    
    @staticmethod
    def calculate_cash_flow_indicators(ja_code, year):
        """
        Calculate cash flow indicators
        
        Args:
            ja_code: JA code
            year: Financial year
            
        Returns:
            dict: Cash flow indicators with calculation details
        """
        try:
            # キャッシュフロー関連のデータを取得
            operating_cash_flow_value, operating_cash_flow_name = FinancialIndicators.get_account_value(ja_code, year, "cf", "110000")  # 営業活動によるキャッシュ・フロー
            investing_cash_flow_value, investing_cash_flow_name = FinancialIndicators.get_account_value(ja_code, year, "cf", "12000")  # 投資活動によるキャッシュ・フロー
            total_debt_value, total_debt_name = FinancialIndicators.get_account_value(ja_code, year, "bs", "4900")  # 負債の部合計
            total_revenue_value, total_revenue_name = FinancialIndicators.get_account_value(ja_code, year, "pl", "6000")  # 経常収益
            net_income_value, net_income_name = FinancialIndicators.get_account_value(ja_code, year, "pl", "9900")  # 当期純利益
            
            # フリーキャッシュフロー（Free Cash Flow）の計算
            # 営業キャッシュフロー - 投資活動によるキャッシュ・フロー
            # 注：投資活動によるキャッシュ・フローは通常マイナス値なので、引き算ではなく足し算する場合があります
            # ただし、この実装では、投資活動CFがプラスかマイナスかに関わらず一貫した処理を行うため、一律で減算します
            free_cash_flow = operating_cash_flow_value - abs(investing_cash_flow_value)
            
            # 営業キャッシュフロー比率（Operating Cash Flow Ratio）の計算
            ocf_ratio = 0
            if total_debt_value != 0:
                ocf_ratio = operating_cash_flow_value / total_debt_value
            
            # キャッシュフローマージン（Cash Flow Margin）の計算
            cash_flow_margin = 0
            if total_revenue_value != 0:
                cash_flow_margin = (operating_cash_flow_value / total_revenue_value) * 100
            
            # キャッシュフロー収益比率（Cash Flow to Income Ratio）の計算
            cf_to_income = 0
            if net_income_value != 0:
                cf_to_income = operating_cash_flow_value / net_income_value
            
            # 分析結果をデータベースに保存
            try:
                # フリーキャッシュフローの保存
                free_cash_flow_result = AnalysisResult(
                    ja_code=ja_code,
                    year=year,
                    analysis_type='cash_flow',
                    indicator_name='free_cash_flow',
                    indicator_value=round(free_cash_flow, 2),
                    benchmark=50000.0,  # 業界平均や目標値
                    risk_score=1 if free_cash_flow > 100000 else (2 if free_cash_flow > 50000 else (3 if free_cash_flow > 0 else 4)),
                    risk_level='極めて低い' if free_cash_flow > 100000 else ('低い' if free_cash_flow > 50000 else ('中程度' if free_cash_flow > 0 else '高い')),
                    analysis_result=f"フリーキャッシュフローは{free_cash_flow:,.0f}円です。" + 
                        (f"健全な水準です。" if free_cash_flow > 50000 else "業界平均を下回っており、キャッシュフロー改善が必要です。"),
                    formula='営業キャッシュフロー - 投資活動によるキャッシュフロー',
                    calculation=f"{operating_cash_flow_value:,.0f} - {abs(investing_cash_flow_value):,.0f} = {free_cash_flow:,.0f}",
                    accounts_used=json.dumps({
                        '営業キャッシュフロー': {'code': '110000', 'name': operating_cash_flow_name, 'value': operating_cash_flow_value},
                        '投資活動によるキャッシュフロー': {'code': '12000', 'name': investing_cash_flow_name, 'value': investing_cash_flow_value}
                    }, ensure_ascii=False)
                )
                db.session.add(free_cash_flow_result)
                
                # 営業キャッシュフロー比率の保存
                ocf_ratio_result = AnalysisResult(
                    ja_code=ja_code,
                    year=year,
                    analysis_type='cash_flow',
                    indicator_name='ocf_ratio',
                    indicator_value=round(ocf_ratio, 2),
                    benchmark=0.2,  # 業界平均や目標値
                    risk_score=1 if ocf_ratio > 0.3 else (2 if ocf_ratio > 0.2 else (3 if ocf_ratio > 0.1 else 4)),
                    risk_level='極めて低い' if ocf_ratio > 0.3 else ('低い' if ocf_ratio > 0.2 else ('中程度' if ocf_ratio > 0.1 else '高い')),
                    analysis_result=f"営業キャッシュフロー比率は{ocf_ratio:.2f}です。" + 
                        (f"健全な水準です。" if ocf_ratio > 0.2 else "業界平均を下回っており、負債に対するキャッシュフロー創出力の改善が必要です。"),
                    formula='営業キャッシュフロー ÷ 総負債',
                    calculation=f"{operating_cash_flow_value:,.0f} ÷ {total_debt_value:,.0f} = {ocf_ratio:.2f}",
                    accounts_used=json.dumps({
                        '営業キャッシュフロー': {'code': '110000', 'name': operating_cash_flow_name, 'value': operating_cash_flow_value},
                        '総負債': {'code': '4900', 'name': total_debt_name, 'value': total_debt_value}
                    }, ensure_ascii=False)
                )
                db.session.add(ocf_ratio_result)
                
                logger.info(f"キャッシュフロー指標の分析結果をデータベースに保存しました。")
                
            except Exception as save_error:
                logger.error(f"キャッシュフロー指標の分析結果保存中にエラーが発生しました: {str(save_error)}")
                # エラーは記録するが、処理は継続する
            
            # 結果を返す
            return {
                'status': 'success',
                'indicators': {
                    'free_cash_flow': {
                        'value': round(free_cash_flow, 2),
                        'formula': '営業キャッシュフロー - 投資活動によるキャッシュフロー',
                        'description': '企業が事業運営後に自由に使える現金を示す指標。値が高いほど、柔軟な資金活用が可能。',
                        'components': {
                            '営業キャッシュフロー': {'code': '110000', 'name': operating_cash_flow_name or '営業活動によるキャッシュ・フロー', 'value': operating_cash_flow_value},
                            '投資活動によるキャッシュフロー': {'code': '12000', 'name': investing_cash_flow_name or '投資活動によるキャッシュ・フロー', 'value': investing_cash_flow_value}
                        }
                    },
                    'ocf_ratio': {
                        'value': round(ocf_ratio, 2),
                        'formula': '営業キャッシュフロー ÷ 負債合計',
                        'description': '負債に対する営業キャッシュフローの比率を示す指標。値が高いほど、負債返済能力が高い。',
                        'components': {
                            '営業キャッシュフロー': {'code': '110000', 'name': operating_cash_flow_name or '営業活動によるキャッシュ・フロー', 'value': operating_cash_flow_value},
                            '負債合計': {'code': '4900', 'name': total_debt_name or '負債の部合計', 'value': total_debt_value}
                        }
                    },
                    'cash_flow_margin': {
                        'value': round(cash_flow_margin, 2),
                        'formula': '(営業キャッシュフロー ÷ 経常収益) × 100',
                        'description': '収益に対する営業キャッシュフローの割合を示す指標。値が高いほど、収益の現金化率が高い。',
                        'components': {
                            '営業キャッシュフロー': {'code': '110000', 'name': operating_cash_flow_name or '営業活動によるキャッシュ・フロー', 'value': operating_cash_flow_value},
                            '経常収益': {'code': '40000', 'name': total_revenue_name or '経常収益', 'value': total_revenue_value}
                        }
                    },
                    'cf_to_income': {
                        'value': round(cf_to_income, 2),
                        'formula': '営業キャッシュフロー ÷ 当期純利益',
                        'description': '純利益に対する営業キャッシュフローの比率を示す指標。値が高いほど、利益の質が高い。',
                        'components': {
                            '営業キャッシュフロー': {'code': '110000', 'name': operating_cash_flow_name or '営業活動によるキャッシュ・フロー', 'value': operating_cash_flow_value},
                            '当期純利益': {'code': '80000', 'name': net_income_name or '税引前当期利益', 'value': net_income_value}
                        }
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"Error calculating cash flow indicators: {str(e)}")
            return {
                'status': 'error',
                'message': f"キャッシュフロー指標の計算中にエラーが発生しました: {str(e)}"
            }