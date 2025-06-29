"""
安全性指標データの状態確認スクリプト
"""
from app import app
from models import AnalysisResult
import json

with app.app_context():
    results = AnalysisResult.query.filter_by(analysis_type='safety').all()
    print(f'安全性指標データ数: {len(results)}')
    
    if results:
        for i, r in enumerate(results[:3]):
            print(f'[{i+1}] JA={r.ja_code}, year={r.year}, indicator={r.indicator_name}, value={r.indicator_value}')
            
            # accounts_usedのJSONを解析して確認
            if r.accounts_used:
                try:
                    accounts = json.loads(r.accounts_used)
                    for k, v in accounts.items():
                        code = v.get('code', 'N/A')
                        name = v.get('name', 'N/A')
                        print(f'  → {k}: コード={code}, 名前={name}')
                except:
                    print(f'  → accounts_used解析エラー: {r.accounts_used[:100]}...')
            else:
                print('  → account_usedデータなし')