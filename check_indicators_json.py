"""
計算結果のJSON構造を確認するスクリプト
"""
from app import app
from financial_indicators import FinancialIndicators
import json

def check_safety_indicators(ja_code='JA001', year=2021):
    """
    安全性指標の計算結果のJSON構造を確認する
    """
    with app.app_context():
        result = FinancialIndicators.calculate_safety_indicators(ja_code, year)
        
        print('安全性指標計算結果:')
        
        # JSON形式で整形して出力
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
        # debt_ratio部分だけ抜き出して詳細表示
        if 'indicators' in result and 'debt_ratio' in result['indicators']:
            debt_ratio = result['indicators']['debt_ratio']
            print('\n負債比率の詳細:')
            print(f'- 値: {debt_ratio.get("value")}')
            print(f'- 計算式: {debt_ratio.get("formula")}')
            print(f'- 説明: {debt_ratio.get("description")}')
            print('- 使用科目:')
            for key, value in debt_ratio.get('components', {}).items():
                print(f'  * {key}: コード={value.get("code", "なし")}, 名前={value.get("name", "不明")}, 値={value.get("value", 0):,.0f}')
        
if __name__ == "__main__":
    check_safety_indicators()