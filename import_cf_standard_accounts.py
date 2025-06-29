import logging
import csv
from app import app, db
from models import StandardAccount

# ロガーの設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def import_cf_standard_accounts(csv_file):
    """
    CFの標準勘定科目をCSVファイルからインポート
    
    Args:
        csv_file: CSVファイルのパス
        
    Returns:
        int: インポートされた勘定科目の数
    """
    with app.app_context():
        try:
            # 既存のCF標準勘定科目を削除
            logger.info("既存のCF標準勘定科目を削除中...")
            db.session.query(StandardAccount).filter_by(financial_statement='cf').delete()
            db.session.commit()
            
            # CSVファイルの読み込み
            logger.info(f"CSVファイル '{csv_file}' を読み込み中...")
            
            # CSVファイルをテキストとして開き、ヘッダー行をスキップ
            with open(csv_file, 'r', encoding='utf-8-sig') as file:
                # ヘッダー行をスキップ
                next(file)
                
                # 残りの行を読み込む
                reader = csv.reader(file)
                rows = list(reader)
            
            # 区分のマッピング
            category_map = {
                '営業活動': 'Operating',
                '投資活動': 'Investing',
                '財務活動': 'Financing',
                '現金・現金同等物': 'Cash'
            }
            
            # アカウント追加
            count = 0
            for row in rows:
                try:
                    # 空行や不完全な行はスキップ
                    if len(row) < 4 or not row[0]:
                        continue
                    
                    # コードを取得
                    code = row[0].strip()
                    
                    # 名前を取得
                    name = row[1].strip() if len(row) > 1 and row[1] else ""
                    if not name:
                        continue
                    
                    # 勘定科目区分を取得
                    account_type = row[2].strip() if len(row) > 2 and row[2] else ""
                    
                    # 上位科目コードを取得
                    parent_code = row[3].strip() if len(row) > 3 and row[3] else None
                    
                    # 財務諸表区分を取得 - CFに固定
                    financial_statement = 'cf'
                    
                    # 勘定科目の区分をマッピング
                    category = category_map.get(account_type, 'Other')
                    
                    # 表示順は科目コードを数値に変換して使用
                    try:
                        display_order = int(code)
                    except ValueError:
                        display_order = 999
                    
                    # 標準勘定科目の作成
                    account = StandardAccount(
                        code=code,
                        name=name,
                        category=category,
                        financial_statement=financial_statement,
                        account_type=account_type,
                        display_order=display_order,
                        parent_code=parent_code,
                        description=account_type
                    )
                    
                    db.session.add(account)
                    count += 1
                    
                    if count % 10 == 0:
                        logger.info(f"{count}件のCF勘定科目をインポートしました...")
                    
                except Exception as e:
                    logger.error(f"行のインポートエラー: {row}\nエラー: {str(e)}")
                    continue
            
            db.session.commit()
            logger.info(f"合計 {count} 件のCF標準勘定科目をインポートしました。")
            
            # CF勘定科目のカウント
            cf_count = db.session.query(StandardAccount).filter_by(financial_statement='cf').count()
            logger.info(f"CF科目: {cf_count}件")
            
            return count
            
        except Exception as e:
            logger.error(f"インポート処理中にエラーが発生しました: {str(e)}")
            db.session.rollback()
            raise

if __name__ == "__main__":
    import_cf_standard_accounts("attached_assets/キャッシュフロー計算書標準科目テーブル.csv")