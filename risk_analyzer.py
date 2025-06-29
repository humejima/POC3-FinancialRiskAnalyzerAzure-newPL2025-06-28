import logging
from app import db
from models import AnalysisResult

logger = logging.getLogger(__name__)

class RiskAnalyzer:
    """
    Analyze financial risk based on calculated indicators
    """
    
    @staticmethod
    def get_overall_risk_score(ja_code, year):
        """
        Calculate overall risk score across all categories
        
        Args:
            ja_code: JA code
            year: Financial year
            
        Returns:
            dict: Overall risk assessment
        """
        try:
            # 引数の型変換
            if isinstance(year, str):
                try:
                    year = int(year)
                except (ValueError, TypeError):
                    logger.warning(f"Year値の変換に失敗しました: {year}")
                    # エラー発生時でもデフォルト値で続行
                    year = 2025
            
            logger.debug(f"リスク評価を実行: JA={ja_code}, year={year}")
            
            # データベースから全ての分析結果を取得
            logger.debug(f"分析結果を検索中: JAコード={ja_code}, 年度={year}")
            
            # Get all analysis results for this JA and year
            results = AnalysisResult.query.filter_by(
                ja_code=ja_code,
                year=year
            ).all()
            
            # 詳細なデバッグ情報を追加
            if results:
                logger.debug(f"分析結果数: {len(results)}")
                analysis_types = set([r.analysis_type for r in results])
                logger.debug(f"分析タイプ一覧: {', '.join(analysis_types)}")
            else:
                logger.debug("分析結果が見つかりません")
            
            if not results:
                # 結果がない場合、デフォルト値を返す
                default_categories = ['liquidity', 'safety', 'profitability', 'efficiency', 'cash_flow']
                default_scores = {category: 3 for category in default_categories}
                
                logger.warning(f"JA {ja_code}, 年度 {year} の分析結果が見つかりません。デフォルト値を使用します。")
                
                return {
                    'status': 'success',
                    'message': 'Using default risk scores',
                    'overall_score': 3.0,
                    'category_scores': default_scores
                }
            
            # Group results by analysis type
            risk_by_category = {}
            for result in results:
                if result.analysis_type not in risk_by_category:
                    risk_by_category[result.analysis_type] = []
                
                if result.risk_score is not None:
                    risk_by_category[result.analysis_type].append(result.risk_score)
            
            # 全カテゴリが存在するか確認し、不足しているカテゴリの警告をログに出力
            expected_categories = ['liquidity', 'safety', 'profitability', 'efficiency', 'cash_flow']
            missing_categories = []
            for category in expected_categories:
                if category not in risk_by_category:
                    missing_categories.append(category)
                    # 不足しているカテゴリは空リストで初期化
                    risk_by_category[category] = []
            
            if missing_categories:
                logger.warning(f"JA {ja_code} の一部カテゴリが欠けています: {', '.join(missing_categories)}")
            
            # Calculate average risk score for each category
            category_scores = {}
            for category, scores in risk_by_category.items():
                if scores:
                    category_scores[category] = sum(scores) / len(scores)
                else:
                    # スコアがない場合はデフォルト値（中間リスク）を設定
                    logger.debug(f"カテゴリ {category} のリスクスコアがありません。デフォルト値を使用します。")
                    category_scores[category] = 3.0
            
            # Calculate overall risk score
            overall_score = None
            if category_scores:
                # Weighted average based on importance of categories
                weights = {
                    'liquidity': 0.25,
                    'safety': 0.25,
                    'profitability': 0.2,
                    'efficiency': 0.15,
                    'cash_flow': 0.15
                }
                
                weighted_sum = 0
                total_weight = 0
                
                for category, score in category_scores.items():
                    weight = weights.get(category, 0.1)  # Default weight for unknown categories
                    weighted_sum += score * weight
                    total_weight += weight
                
                if total_weight > 0:
                    overall_score = weighted_sum / total_weight
            
            # Determine overall risk level
            # リスクスコアとレーダーチャートの表示を整合させる
            # リスクスコアは直感的にリスク耐性を表す（高いほど良い）ように変更
            overall_risk_level = None
            if overall_score is not None:
                if overall_score <= 1.5:
                    overall_risk_level = "極めて高い" # リスク耐性が非常に低い = リスクが非常に高い
                elif overall_score <= 2.5:
                    overall_risk_level = "高い"     # リスク耐性が低い = リスクが高い
                elif overall_score <= 3.5:
                    overall_risk_level = "中程度"   # リスク耐性が普通 = リスクが中程度
                elif overall_score <= 4.5:
                    overall_risk_level = "低い"     # リスク耐性が高い = リスクが低い
                else:
                    overall_risk_level = "極めて低い" # リスク耐性が非常に高い = リスクが非常に低い
            
            return {
                'status': 'success',
                'overall_score': overall_score,
                'overall_risk_level': overall_risk_level,
                'category_scores': category_scores
            }
            
        except Exception as e:
            logger.error(f"Error calculating overall risk score: {str(e)}")
            return {
                'status': 'error',
                'message': f"Error calculating overall risk score: {str(e)}"
            }
    
    @staticmethod
    def get_risk_issues(ja_code, year, threshold=3.0):
        """
        主要リスク項目のリストを取得する
        スコアがthreshold以下の項目が高リスクとして表示される
        閾値を5.0に設定すると全カテゴリが表示される
        
        Args:
            ja_code: JA code
            year: Financial year
            threshold: リスクスコアの閾値（デフォルト: 3、1~5、値が低いほど高リスク）
            
        Returns:
            list: 主要リスク項目リスト
        """
        try:
            # Get analysis results with risk score below threshold (low score = high risk)
            # 低いスコア = 高いリスク（リスク耐性が低い）として解釈するよう変更
            high_risk_results = AnalysisResult.query.filter(
                AnalysisResult.ja_code == ja_code,
                AnalysisResult.year == year,
                AnalysisResult.risk_score <= threshold
            ).order_by(AnalysisResult.risk_score.asc()).all()
            
            issues = []
            for result in high_risk_results:
                # Format indicator name for display
                display_name = result.indicator_name
                if result.indicator_name == 'current_ratio':
                    display_name = '流動比率'
                elif result.indicator_name == 'quick_ratio':
                    display_name = '当座比率'
                elif result.indicator_name == 'cash_ratio':
                    display_name = '現金比率'
                elif result.indicator_name == 'working_capital':
                    display_name = '運転資本'
                elif result.indicator_name == 'roa':
                    display_name = '総資産利益率'
                elif result.indicator_name == 'roe':
                    display_name = '自己資本利益率'
                elif result.indicator_name == 'profit_margin':
                    display_name = '利益率'
                elif result.indicator_name == 'operating_margin':
                    display_name = '営業利益率'
                elif result.indicator_name == 'debt_ratio':
                    display_name = '負債比率'
                elif result.indicator_name == 'equity_ratio':
                    display_name = '自己資本比率'
                elif result.indicator_name == 'debt_to_equity':
                    display_name = '負債資本比率'
                elif result.indicator_name == 'interest_coverage':
                    display_name = 'インタレストカバレッジレシオ'
                elif result.indicator_name == 'asset_turnover':
                    display_name = '総資産回転率'
                elif result.indicator_name == 'receivables_turnover':
                    display_name = '売上債権回転率'
                elif result.indicator_name == 'inventory_turnover':
                    display_name = '棚卸資産回転率'
                elif result.indicator_name == 'days_sales_outstanding':
                    display_name = '売上債権回収期間'
                elif result.indicator_name == 'ocf_to_debt':
                    display_name = '営業CF対負債比率'
                elif result.indicator_name == 'cf_to_revenue':
                    display_name = 'CF対売上比率'
                elif result.indicator_name == 'cf_to_net_income':
                    display_name = 'CF対純利益比率'
                elif result.indicator_name == 'free_cash_flow':
                    display_name = 'フリーキャッシュフロー'
                
                # Format analysis type for display
                display_type = result.analysis_type
                if result.analysis_type == 'liquidity':
                    display_type = '流動性'
                elif result.analysis_type == 'profitability':
                    display_type = '収益性'
                elif result.analysis_type == 'safety':
                    display_type = '安全性'
                elif result.analysis_type == 'efficiency':
                    display_type = '効率性'
                elif result.analysis_type == 'cash_flow':
                    display_type = 'キャッシュフロー'
                
                # リスクレベルの表示を標準化・修正（リスクスコアとレーダーチャート表示を整合させる）
                risk_level_display = result.risk_level
                
                # リスクスコアとレーダーチャートの表示を整合させる
                # リスクスコアは直感的にリスク耐性を表す（高いほど良い）ように変更
                # 5.0に近いほどリスク耐性が高い（リスクが低い）
                if result.risk_score <= 1.5:
                    risk_level_display = '極めて高い' # リスク耐性が非常に低い = リスクが非常に高い
                elif result.risk_score <= 2.5:
                    risk_level_display = '高い'     # リスク耐性が低い = リスクが高い
                elif result.risk_score <= 3.5:
                    risk_level_display = '中程度'   # リスク耐性が普通 = リスクが中程度
                elif result.risk_score <= 4.5:
                    risk_level_display = '低い'     # リスク耐性が高い = リスクが低い
                else:
                    risk_level_display = '極めて低い' # リスク耐性が非常に高い = リスクが非常に低い
                    
                # 安全性と効率性のカテゴリは分析結果が「問題なし」や「良好」など、プラスの表現に変更
                if result.analysis_type == 'safety' and result.risk_score >= 4.0:
                    result.analysis_result = '安全性指標は良好で、経営の安定性が保たれています'
                elif result.analysis_type == 'efficiency' and result.risk_score >= 4.0:
                    result.analysis_result = '資産効率が高く、適切に資源が活用されています'
                
                # デバッグログで変換前後の値を表示
                logger.debug(f"リスクレベル変換: {result.risk_level} → {risk_level_display} (スコア={result.risk_score})")

                issues.append({
                    'type': display_type,
                    'name': display_name,
                    'value': result.indicator_value,
                    'benchmark': result.benchmark,
                    'risk_score': result.risk_score,
                    'risk_level': risk_level_display,
                    'analysis': result.analysis_result
                })
            
            return issues
            
        except Exception as e:
            logger.error(f"Error getting risk issues: {str(e)}")
            return []
    
    @staticmethod
    def get_risk_scores(ja_code, year):
        """
        Get risk scores for radar chart
        
        Args:
            ja_code: JA code
            year: Financial year
            
        Returns:
            dict: Risk scores by category
        """
        try:
            # Get risk scores from analysis results
            results = AnalysisResult.query.filter_by(
                ja_code=ja_code,
                year=year
            ).all()
            
            # リスクスコアを分析タイプごとに集計
            risk_by_category = {}
            for result in results:
                if result.analysis_type not in risk_by_category:
                    risk_by_category[result.analysis_type] = []
                
                if result.risk_score is not None:
                    risk_by_category[result.analysis_type].append(result.risk_score)
            
            # 各カテゴリの平均リスクスコアを計算
            risk_scores = {}
            expected_categories = ['liquidity', 'safety', 'profitability', 'efficiency', 'cash_flow']
            
            for category in expected_categories:
                if category in risk_by_category and risk_by_category[category]:
                    # リスクスコアが存在する場合は平均値を計算
                    risk_scores[category] = sum(risk_by_category[category]) / len(risk_by_category[category])
                else:
                    # スコアがない場合はデフォルト値（中間リスク）を設定
                    risk_scores[category] = 3.0
            
            return risk_scores
            
        except Exception as e:
            logger.error(f"Error getting risk scores: {str(e)}")
            # エラー時のデフォルト値
            return {"liquidity": 3, "safety": 3, "profitability": 3, "efficiency": 3, "cash_flow": 3}
    
    @staticmethod
    def generate_improvement_suggestions(ja_code, year):
        """
        Generate improvement suggestions based on risk analysis
        
        Args:
            ja_code: JA code
            year: Financial year
            
        Returns:
            dict: Improvement suggestions by category
        """
        try:
            # Get high-risk issues
            high_risk_issues = RiskAnalyzer.get_risk_issues(ja_code, year, threshold=3)
            
            if not high_risk_issues:
                return {
                    'status': 'info',
                    'message': '重大なリスク項目はありません。現在の財務状態は良好です。',
                    'suggestions': {}
                }
            
            # Group issues by type
            issues_by_type = {}
            for issue in high_risk_issues:
                if issue['type'] not in issues_by_type:
                    issues_by_type[issue['type']] = []
                issues_by_type[issue['type']].append(issue)
            
            # Generate suggestions for each type
            suggestions = {}
            
            for issue_type, issues in issues_by_type.items():
                type_suggestions = []
                
                if issue_type == '流動性':
                    if any(i['name'] == '流動比率' for i in issues):
                        type_suggestions.append('短期債務の見直しと返済計画の策定を検討してください。')
                        type_suggestions.append('不要な資産の現金化を検討し、流動資産を増やすことを検討してください。')
                    
                    if any(i['name'] == '当座比率' for i in issues):
                        type_suggestions.append('当座資産（現金、売掛金等）の増強を図り、即時支払能力を改善してください。')
                        type_suggestions.append('在庫水準の適正化を検討してください。')
                
                elif issue_type == '収益性':
                    if any(i['name'] == '総資産利益率' for i in issues) or any(i['name'] == '自己資本利益率' for i in issues):
                        type_suggestions.append('収益性向上のための事業構造改革を検討してください。')
                        type_suggestions.append('低収益事業の見直しと高収益事業への集中を検討してください。')
                    
                    if any(i['name'] == '利益率' for i in issues):
                        type_suggestions.append('コスト削減策の実施を検討してください。')
                        type_suggestions.append('価格戦略の見直しを検討してください。')
                
                elif issue_type == '安全性':
                    if any(i['name'] == '自己資本比率' for i in issues) or any(i['name'] == '負債資本比率' for i in issues):
                        type_suggestions.append('資本増強策の検討、例えば内部留保の積み増しを検討してください。')
                        type_suggestions.append('不要な負債の圧縮を検討してください。')
                    
                    if any(i['name'] == 'インタレストカバレッジレシオ' for i in issues):
                        type_suggestions.append('金利負担の軽減策の検討、例えば借り換えやリファイナンスを検討してください。')
                
                elif issue_type == '効率性':
                    if any(i['name'] == '総資産回転率' for i in issues):
                        type_suggestions.append('資産の効率的な活用方法の検討、例えば遊休資産の処分を検討してください。')
                    
                    if any(i['name'] == '売上債権回収期間' for i in issues):
                        type_suggestions.append('売掛金回収の迅速化策の導入を検討してください。')
                        type_suggestions.append('与信管理の強化を検討してください。')
                
                elif issue_type == 'キャッシュフロー':
                    if any(i['name'] == '営業CF対負債比率' for i in issues):
                        type_suggestions.append('営業キャッシュフローの改善策の検討、例えば在庫回転率の向上を検討してください。')
                    
                    if any(i['name'] == 'フリーキャッシュフロー' for i in issues):
                        type_suggestions.append('設備投資計画の見直しと優先順位付けを検討してください。')
                        type_suggestions.append('運転資本の管理強化を検討してください。')
                
                suggestions[issue_type] = type_suggestions
            
            return {
                'status': 'success',
                'message': '以下に財務改善のための提案を示します。',
                'suggestions': suggestions
            }
            
        except Exception as e:
            logger.error(f"Error generating improvement suggestions: {str(e)}")
            return {
                'status': 'error',
                'message': f"Error generating improvement suggestions: {str(e)}",
                'suggestions': {}
            }
