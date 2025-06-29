"""
既存の分析結果レコードを更新するスクリプト
AnalysisResultテーブルの古いレコードを削除し、正しい値に更新します
"""
from app import app, db
from models import AnalysisResult
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_analysis_records(ja_code='JA001', year=2021):
    """古い分析結果レコードを削除し、更新する"""
    with app.app_context():
        try:
            # 古い流動性指標レコードを削除
            old_records = AnalysisResult.query.filter_by(
                ja_code=ja_code,
                year=year,
                analysis_type='liquidity'
            ).filter(
                AnalysisResult.indicator_value == 0
            ).all()
            
            for record in old_records:
                logger.info(f"レコードを削除: {record.indicator_name} (ID: {record.id})")
                db.session.delete(record)
            
            db.session.commit()
            logger.info(f"{len(old_records)}件の古いレコードを削除しました")
            
            # 既存のレコードの分析結果テキストを更新
            current_ratio = AnalysisResult.query.filter_by(
                ja_code=ja_code,
                year=year,
                analysis_type='liquidity',
                indicator_name='current_ratio'
            ).first()
            
            if current_ratio:
                current_ratio.analysis_result = f"流動比率は{current_ratio.indicator_value:.2f}%です。この値は業界平均を" + \
                                                ("上回っており、良好な短期支払能力を示しています。" if current_ratio.indicator_value >= 100 else 
                                                "下回っており、短期債務支払能力の向上が必要です。")
                logger.info(f"流動比率の分析結果を更新しました: {current_ratio.indicator_value:.2f}%")
                
            quick_ratio = AnalysisResult.query.filter_by(
                ja_code=ja_code,
                year=year,
                analysis_type='liquidity',
                indicator_name='quick_ratio'
            ).first()
            
            if quick_ratio:
                quick_ratio.analysis_result = f"当座比率は{quick_ratio.indicator_value:.2f}%です。この値は業界平均を" + \
                                             ("上回っており、良好な即時支払能力を示しています。" if quick_ratio.indicator_value >= 80 else 
                                            "下回っており、即時支払能力の向上が必要です。")
                logger.info(f"当座比率の分析結果を更新しました: {quick_ratio.indicator_value:.2f}%")
                
            cash_ratio = AnalysisResult.query.filter_by(
                ja_code=ja_code,
                year=year,
                analysis_type='liquidity',
                indicator_name='cash_ratio'
            ).first()
            
            if cash_ratio:
                cash_ratio.analysis_result = f"現金比率は{cash_ratio.indicator_value:.2f}%です。この値は業界平均を" + \
                                            ("上回っており、良好な現金支払能力を示しています。" if cash_ratio.indicator_value >= 20 else 
                                            "下回っており、現金支払能力の向上が必要です。")
                logger.info(f"現金比率の分析結果を更新しました: {cash_ratio.indicator_value:.2f}%")
                
            working_capital = AnalysisResult.query.filter_by(
                ja_code=ja_code,
                year=year,
                analysis_type='liquidity',
                indicator_name='working_capital'
            ).first()
            
            if working_capital:
                working_capital.analysis_result = f"運転資本は{working_capital.indicator_value:,.0f}円です。この値は" + \
                                                ("プラスで、良好な運転資金状況を示しています。" if working_capital.indicator_value > 0 else 
                                                "マイナスで、運転資金の改善が必要です。")
                logger.info(f"運転資本の分析結果を更新しました: {working_capital.indicator_value:,.0f}円")
            
            db.session.commit()
            logger.info("分析結果レコードの更新が完了しました")
            return True
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"分析結果の更新中にエラーが発生しました: {str(e)}")
            return False

if __name__ == "__main__":
    update_analysis_records()