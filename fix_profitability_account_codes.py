"""
収益性指標の計算に使用する正しい科目コードに修正するスクリプト
以下のコードを修正：
- 当期純利益：9900 → 33000
- 資産の部合計：2900 → 10000
- 純資産：5000 → 30000
"""

from app import app, db
from models import AnalysisResult
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_profitability_account_codes():
    """収益性指標の計算に使用する科目コードを修正する"""
    with app.app_context():
        # ROA (総資産利益率)の修正
        try:
            # ROA分析結果を取得
            roa_results = AnalysisResult.query.filter_by(
                analysis_type='profitability',
                indicator_name='roa'
            ).all()
            
            logger.info(f"ROA（総資産利益率）の分析結果: {len(roa_results)}件")
            
            for result in roa_results:
                try:
                    # JSONを解析
                    accounts_used = json.loads(result.accounts_used)
                    
                    # 修正前の情報をログ
                    if '当期純利益' in accounts_used and '総資産' in accounts_used:
                        old_net_income_code = accounts_used['当期純利益'].get('code', 'なし')
                        old_assets_code = accounts_used['総資産'].get('code', 'なし')
                        logger.info(f"ROA修正前: JA={result.ja_code}, 当期純利益コード={old_net_income_code}, 総資産コード={old_assets_code}")
                    
                    # 当期純利益のコード修正
                    if '当期純利益' in accounts_used:
                        accounts_used['当期純利益']['code'] = '33000'
                    
                    # 総資産のコード修正
                    if '総資産' in accounts_used:
                        accounts_used['総資産']['code'] = '10000'
                    
                    # 計算式の更新
                    result.formula = '(当期純利益 ÷ 資産の部合計) × 100'
                    
                    # JSONを文字列に戻して保存
                    result.accounts_used = json.dumps(accounts_used, ensure_ascii=False)
                    
                    logger.info(f"ROA修正完了: JA={result.ja_code}, 年度={result.year}")
                except Exception as e:
                    logger.error(f"ROA修正エラー: JA={result.ja_code}, 年度={result.year}, エラー={str(e)}")
            
            # ROE (自己資本利益率)の修正
            roe_results = AnalysisResult.query.filter_by(
                analysis_type='profitability',
                indicator_name='roe'
            ).all()
            
            logger.info(f"ROE（自己資本利益率）の分析結果: {len(roe_results)}件")
            
            for result in roe_results:
                try:
                    # JSONを解析
                    accounts_used = json.loads(result.accounts_used)
                    
                    # 修正前の情報をログ
                    if '当期純利益' in accounts_used and '純資産' in accounts_used:
                        old_net_income_code = accounts_used['当期純利益'].get('code', 'なし')
                        old_equity_code = accounts_used['純資産'].get('code', 'なし')
                        logger.info(f"ROE修正前: JA={result.ja_code}, 当期純利益コード={old_net_income_code}, 純資産コード={old_equity_code}")
                    
                    # 当期純利益のコード修正
                    if '当期純利益' in accounts_used:
                        accounts_used['当期純利益']['code'] = '33000'
                    
                    # 純資産のコード修正
                    if '純資産' in accounts_used:
                        accounts_used['純資産']['code'] = '30000'
                    
                    # 計算式の更新
                    result.formula = '(当期純利益 ÷ 純資産) × 100'
                    
                    # JSONを文字列に戻して保存
                    result.accounts_used = json.dumps(accounts_used, ensure_ascii=False)
                    
                    logger.info(f"ROE修正完了: JA={result.ja_code}, 年度={result.year}")
                except Exception as e:
                    logger.error(f"ROE修正エラー: JA={result.ja_code}, 年度={result.year}, エラー={str(e)}")
            
            # 変更をコミット
            db.session.commit()
            logger.info("収益性指標の科目コード修正が完了しました")
            
            return True
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"収益性指標の科目コード修正中にエラーが発生しました: {str(e)}")
            return False

if __name__ == "__main__":
    fix_profitability_account_codes()