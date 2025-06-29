from app import app, db
from models import CSVData

with app.app_context():
    # CF CSV データのカテゴリを表示
    csv_data = CSVData.query.filter_by(file_type='cf').order_by(CSVData.row_number).all()
    
    print(f"CF CSV データのカテゴリ一覧 (全{len(csv_data)}件):")
    
    # 各データの行番号、勘定科目名、カテゴリを表示
    for data in csv_data:
        print(f"行{data.row_number}: {data.account_name} - カテゴリ: {data.category}")
