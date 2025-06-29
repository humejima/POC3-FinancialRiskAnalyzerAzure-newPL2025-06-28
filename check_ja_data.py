"""
データベース内のJAデータとCSVデータの状態を確認するスクリプト
"""

from app import app, db
from models import JA, CSVData

def check_ja_data():
    """JAデータとCSVデータの状態を確認"""
    with app.app_context():
        print('利用可能なJA:')
        for ja in JA.query.all():
            print(f'{ja.ja_code}: {ja.name}')
        
        print('\nCSVデータ件数:')
        for ja in JA.query.all():
            bs_count = CSVData.query.filter_by(ja_code=ja.ja_code, file_type='bs').count()
            pl_count = CSVData.query.filter_by(ja_code=ja.ja_code, file_type='pl').count()
            cf_count = CSVData.query.filter_by(ja_code=ja.ja_code, file_type='cf').count()
            print(f'{ja.ja_code}: BS={bs_count}, PL={pl_count}, CF={cf_count}')
        
        print('\n未マッピングデータ件数:')
        for ja in JA.query.all():
            bs_count = CSVData.query.filter_by(ja_code=ja.ja_code, file_type='bs', is_mapped=False).count()
            pl_count = CSVData.query.filter_by(ja_code=ja.ja_code, file_type='pl', is_mapped=False).count()
            cf_count = CSVData.query.filter_by(ja_code=ja.ja_code, file_type='cf', is_mapped=False).count()
            if bs_count > 0 or pl_count > 0 or cf_count > 0:
                print(f'{ja.ja_code}: BS={bs_count}, PL={pl_count}, CF={cf_count}')

if __name__ == "__main__":
    check_ja_data()