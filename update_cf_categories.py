from app import app, db
from models import CSVData

def update_cf_categories():
    """CFデータのカテゴリを更新する"""
    
    with app.app_context():
        # CF CSV データを取得
        csv_data = CSVData.query.filter_by(file_type='cf', ja_code='JA001', year=2025).all()
        
        # カテゴリ区分のリセット
        for data in csv_data:
            data.category = None
        
        # カテゴリマッピング - まずカテゴリ自体を認識
        category_rows = {}
        for data in csv_data:
            if "事業活動によるキャッシュ・フロー" in data.account_name and data.row_number < 24:
                data.category = "営業活動"
                category_rows["営業活動"] = data.row_number
            elif "事業活動によるキャッシュ・フロー" in data.account_name and data.row_number >= 24:
                data.category = "営業活動"
                # これは小計行
            elif "投資活動によるキャッシュ・フロー" in data.account_name and data.row_number < 33:
                data.category = "投資活動"
                category_rows["投資活動"] = data.row_number
            elif "投資活動によるキャッシュ・フロー" in data.account_name and data.row_number >= 33:
                data.category = "投資活動"
                # これは小計行
            elif "財務活動によるキャッシュ・フロー" in data.account_name and data.row_number < 36:
                data.category = "財務活動"
                category_rows["財務活動"] = data.row_number
            elif "財務活動によるキャッシュ・フロー" in data.account_name and data.row_number >= 36:
                data.category = "財務活動"
                # これは小計行
            elif "現金及び現金同等物" in data.account_name:
                data.category = "現金及び現金同等物"
                
        # 次に、各行のカテゴリを、それが属するセクションに基づいて設定
        current_category = None
        for data in sorted(csv_data, key=lambda x: x.row_number):
            if data.category:
                current_category = data.category
            elif data.account_name and data.account_name.strip() and not data.account_name.startswith("0"):
                if current_category:
                    data.category = current_category
                # 特定のケース - 行番号36以降は現金及び現金同等物として扱う
                if data.row_number > 35 and "現金及び現金同等物" in data.account_name:
                    data.category = "現金及び現金同等物"
                # 特定のケース - 出資配当金はカテゴリがあっても財務活動に設定
                if "出資配当金" in data.account_name:
                    data.category = "財務活動"
        
        # 変更を保存
        db.session.commit()
        
        # 更新された件数をカウント
        updated_count = sum(1 for d in csv_data if d.category is not None)
        print(f"{updated_count}件のCFデータカテゴリを更新しました。")

if __name__ == "__main__":
    update_cf_categories()