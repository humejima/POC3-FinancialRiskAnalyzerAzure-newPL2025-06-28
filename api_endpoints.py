"""
APIエンドポイント定義モジュール
"""
import logging
import json
from flask import jsonify, request, session
from models import AnalysisResult, StandardAccount, StandardAccountBalance, JA
from app import db
from performance_enhancer import timed_function, cached_query

logger = logging.getLogger(__name__)

def register_api_endpoints(app):
    """API エンドポイントを登録する関数"""
    
    @app.route('/api/risk_issues')
    @timed_function
    def api_risk_issues():
        """APIエンドポイント：主要リスク項目を取得"""
        # URLパラメータからJAコードと年度を取得（指定がなければセッションから）
        ja_code = request.args.get('ja_code') or session.get('selected_ja_code')
        year = request.args.get('year') or session.get('selected_year')
        
        logger.debug(f"Risk Issues API呼出: セッション ja_code={ja_code}, URLパラメータ ja_code={request.args.get('ja_code')}")
        logger.debug(f"Risk Issues API呼出: セッション year={year}, URLパラメータ year={request.args.get('year')}")
        
        # 分析結果の取得
        if ja_code and year:
            try:
                year_int = int(year)
                
                # RiskAnalyzerを使用して高リスク項目を取得
                from risk_analyzer import RiskAnalyzer
                risk_analyzer = RiskAnalyzer()
                risk_issues = risk_analyzer.get_risk_issues(ja_code, year_int)
                
                logger.debug(f"リスク項目数: {len(risk_issues)}")
                return jsonify(risk_issues)
            except Exception as e:
                logger.error(f"リスク項目取得中にエラー: {str(e)}")
        
        # 結果がなければ空のリストを返す
        logger.debug(f"リスク項目数: 0")
        return jsonify([])
    
    @app.route('/api/risk_data')
    @timed_function
    def api_risk_data():
        """APIエンドポイント：レーダーチャート用リスクデータを取得"""
        # URLパラメータからJAコードと年度を取得（指定がなければセッションから）
        ja_code = request.args.get('ja_code') or session.get('selected_ja_code')
        year = request.args.get('year') or session.get('selected_year')
        
        logger.debug(f"Risk API呼出: セッション ja_code={ja_code}, URLパラメータ ja_code={request.args.get('ja_code')}")
        logger.debug(f"Risk API呼出: セッション year={year}, URLパラメータ year={request.args.get('year')}")
        
        # デフォルトのリスクデータ
        default_risk = {"liquidity": 3, "safety": 3, "profitability": 3, "efficiency": 3, "cash_flow": 3}
        
        # レスポンスデータ構造を準備
        response_data = {
            "current_year": default_risk.copy(),
            "previous_year": None,
            "has_comparison": False
        }
        
        # リスク分析データを取得
        if ja_code and year:
            try:
                from risk_analyzer import RiskAnalyzer
                risk_analyzer = RiskAnalyzer()
                year_int = int(year)
                
                # 今年のリスクスコア
                current_risk_data = risk_analyzer.get_risk_scores(ja_code, year_int)
                response_data["current_year"] = current_risk_data
                
                # 前年のリスクスコア
                prev_year = year_int - 1
                try:
                    previous_risk_data = risk_analyzer.get_risk_scores(ja_code, prev_year)
                    response_data["previous_year"] = previous_risk_data
                    response_data["has_comparison"] = True
                except Exception as prev_e:
                    logger.warning(f"前年度データ取得エラー: {str(prev_e)}")
                    
                    # JA001の場合は、デモ用に擬似データを生成
                    if ja_code == 'JA001':
                        import random
                        # 現在のスコアをわずかに変動させた擬似データを生成
                        previous_risk_data = {}
                        for key, value in current_risk_data.items():
                            # ±10%のランダムな変動を加える
                            change_factor = random.uniform(0.9, 1.1)
                            previous_risk_data[key] = min(5, max(1, value * change_factor))
                        response_data["previous_year"] = previous_risk_data
                        response_data["has_comparison"] = True
                        logger.debug("デモ用に前年度擬似リスクデータを生成")
                
                logger.debug(f"リスク評価データ: {response_data}")
                return jsonify(response_data)
            except Exception as e:
                logger.error(f"リスク評価中にエラー: {str(e)}")
        
        # エラー時またはデータがない場合はデフォルト値を返す
        return jsonify(default_risk)
    
    @app.route('/api/account_data')
    @cached_query(timeout=300)  # 5分間キャッシュ
    def api_account_data():
        """APIエンドポイント：特定の財務諸表タイプの勘定科目データを取得"""
        ja_code = request.args.get('ja_code') or session.get('selected_ja_code')
        year = request.args.get('year') or session.get('selected_year')
        financial_statement = request.args.get('financial_statement', 'bs')
        
        if not ja_code or not year:
            return jsonify({"error": "JA code and year are required"}), 400
            
        try:
            year_int = int(year)
            
            # 財務諸表タイプに応じて重要な親科目コードのリストを取得
            if financial_statement == 'bs':
                # BS（貸借対照表）の重要な親科目コード
                important_parent_codes = ['1000', '1600', '1700', '1800', '1900', '2000', '2100', '3000', '3600', '3900', '5200', 
                                          # 合計科目も追加
                                          '2900', '4900', '5900', '5950', '5951']
            elif financial_statement == 'pl':
                # PL（損益計算書）の重要な親科目コード
                important_parent_codes = ['40000', '41000', '50000', '51000', '60000', '70000', '80000', '81000', '82000', 
                                          '83000', '90000', '91000', '92000', '99000']
            elif financial_statement == 'cf':
                # CF（キャッシュフロー計算書）の重要な親科目コード
                important_parent_codes = ['6000', '6100', '6200', '6300', '6400', '6500', '6600', '6700', '6800', '6900', 
                                          '7000', '7100', '7200', '7300', '7400', '7500', '7600', '7700', '7800', '7900', '9900']
            else:
                important_parent_codes = []
                
            # 標準勘定科目マスタを取得
            all_standard_accounts = StandardAccount.query.filter_by(
                financial_statement=financial_statement
            ).order_by(StandardAccount.code.cast(db.Integer)).all()
            
            # 標準残高を取得
            all_balances = StandardAccountBalance.query.filter_by(
                ja_code=ja_code,
                year=year_int,
                statement_type=financial_statement
            ).all()
            
            # 残高をディクショナリ化
            balance_dict = {balance.standard_account_code: balance for balance in all_balances}
            
            # 結果を整形
            result = []
            for account in all_standard_accounts:
                # 重要でない親科目でかつ値がない場合はスキップ
                if account.code not in important_parent_codes and account.code not in balance_dict:
                    continue
                    
                item = {
                    "code": account.code,
                    "name": account.name,
                    "parent_code": account.parent_code,
                    "is_important": account.code in important_parent_codes,
                    "display_order": account.display_order or 0
                }
                
                # 残高がある場合は値を追加
                if account.code in balance_dict:
                    balance = balance_dict[account.code]
                    item["current_value"] = balance.current_value
                    item["previous_value"] = balance.previous_value
                    item["statement_subtype"] = balance.statement_subtype
                else:
                    item["current_value"] = 0
                    item["previous_value"] = 0
                    item["statement_subtype"] = account.account_type
                    
                result.append(item)
                
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"勘定科目データ取得中にエラー: {str(e)}")
            return jsonify({"error": str(e)}), 500
    
    # キャッシュクリアエンドポイント（管理者用）
    @app.route('/api/clear_cache')
    def api_clear_cache():
        """APIエンドポイント：キャッシュをクリア"""
        from performance_enhancer import clear_cache
        clear_cache()
        return jsonify({"status": "success", "message": "Cache cleared successfully"})

    @app.route('/api/ja_comparison', methods=['POST'])
    def api_ja_comparison():
        """APIエンドポイント：JA比較分析データを取得"""
        try:
            data = request.get_json()
            ja1_code = data.get('ja1_code')
            ja1_year = data.get('ja1_year')
            ja2_code = data.get('ja2_code')
            ja2_year = data.get('ja2_year')
            
            logger.info(f"JA比較分析リクエスト: JA1={ja1_code}({ja1_year}) vs JA2={ja2_code}({ja2_year})")
            
            # パラメータ検証
            if not all([ja1_code, ja1_year, ja2_code, ja2_year]):
                return jsonify({
                    "status": "error",
                    "message": "必要なパラメータが不足しています"
                }), 400
            
            # JA情報を取得
            from models import JA
            ja1_info = JA.query.filter_by(ja_code=ja1_code).first()
            ja2_info = JA.query.filter_by(ja_code=ja2_code).first()
            
            if not ja1_info or not ja2_info:
                return jsonify({
                    "status": "error",
                    "message": "指定されたJAが見つかりません"
                }), 404
            
            # リスクスコアを取得
            from risk_analyzer import RiskAnalyzer
            
            ja1_scores = RiskAnalyzer.get_overall_risk_score(ja1_code, ja1_year)
            ja2_scores = RiskAnalyzer.get_overall_risk_score(ja2_code, ja2_year)
            
            # JA情報とスコアの整合性を確認
            if not ja1_scores or not ja2_scores:
                return jsonify({
                    "status": "error",
                    "message": "指定された年度のリスクデータが見つかりません"
                }), 404
            
            # レスポンスデータを構築
            response_data = {
                "status": "success",
                "ja1_info": {
                    "code": ja1_info.ja_code,
                    "name": ja1_info.name,
                    "year": ja1_year
                },
                "ja2_info": {
                    "code": ja2_info.ja_code,
                    "name": ja2_info.name,
                    "year": ja2_year
                },
                "ja1_scores": {
                    "profitability": ja1_scores.get('category_scores', {}).get('profitability', 3),
                    "efficiency": ja1_scores.get('category_scores', {}).get('efficiency', 3),
                    "safety": ja1_scores.get('category_scores', {}).get('safety', 3),
                    "cash_flow": ja1_scores.get('category_scores', {}).get('cash_flow', 3),
                    "liquidity": ja1_scores.get('category_scores', {}).get('liquidity', 3)
                },
                "ja2_scores": {
                    "profitability": ja2_scores.get('category_scores', {}).get('profitability', 3),
                    "efficiency": ja2_scores.get('category_scores', {}).get('efficiency', 3),
                    "safety": ja2_scores.get('category_scores', {}).get('safety', 3),
                    "cash_flow": ja2_scores.get('category_scores', {}).get('cash_flow', 3),
                    "liquidity": ja2_scores.get('category_scores', {}).get('liquidity', 3)
                }
            }
            
            logger.info(f"JA比較分析完了: {len(response_data)} 項目を返却")
            return jsonify(response_data)
            
        except Exception as e:
            logger.error(f"JA比較分析エラー: {e}")
            return jsonify({
                "status": "error",
                "message": f"比較分析中にエラーが発生しました: {str(e)}"
            }), 500