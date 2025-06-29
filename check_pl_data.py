"""
PLデータの確認スクリプト
"""
from app import app, db
from models import StandardAccountBalance

def check_pl_data():
    with app.app_context():
        try:
            # PLデータを取得
            pl_data = StandardAccountBalance.query.filter_by(
                ja_code='JA001',
                year=2025,
                statement_type='pl'
            ).all()
            
            print(f"PLデータ数: {len(pl_data)}")
            
            # 最初の10件を表示
            for i, record in enumerate(pl_data[:10]):
                print(f"{i+1}. {record.standard_account_code}: {record.standard_account_name} = {record.current_value}")
            
        except Exception as e:
            print(f"エラー: {str(e)}")

if __name__ == "__main__":
    check_pl_data()