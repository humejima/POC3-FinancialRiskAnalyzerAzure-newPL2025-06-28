"""
安全性指標（負債比率）を確認するスクリプト
"""
from app import app, db
from models import AnalysisResult

def check_debt_ratio(ja_code='JA001', year=2021):
    """
    負債比率の分析結果を確認する
    """
    with app.app_context():
        result = db.session.query(AnalysisResult).filter_by(
            ja_code=ja_code,
            year=year,
            analysis_type='safety',
            indicator_name='debt_ratio'
        ).first()
        
        if result:
            print(f'負債比率の分析結果:')
            print(f'- 値: {result.indicator_value}')
            print(f'- 計算式: {result.formula}')
            print(f'- 計算詳細: {result.calculation}')
            print(f'- 分析: {result.analysis_result}')
        else:
            print(f'負債比率の分析結果が見つかりません（JA: {ja_code}, 年度: {year}）')
        
        # 参考として自己資本比率も確認
        equity_result = db.session.query(AnalysisResult).filter_by(
            ja_code=ja_code,
            year=year,
            analysis_type='safety',
            indicator_name='equity_ratio'
        ).first()
        
        if equity_result:
            print(f'\n自己資本比率の分析結果:')
            print(f'- 値: {equity_result.indicator_value}')
            print(f'- 計算式: {equity_result.formula}')
            print(f'- 計算詳細: {equity_result.calculation}')
            print(f'- 分析: {equity_result.analysis_result}')
        
if __name__ == "__main__":
    check_debt_ratio()