import pandas as pd
import logging
import csv
import io
from app import app, db
from models import StandardAccount

# ロガーの設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def import_standard_accounts(csv_file):
    """
    Import standard accounts from CSV file
    
    Args:
        csv_file: Path to CSV file
    
    Returns:
        int: Number of accounts imported
    """
    with app.app_context():
        try:
            # 現在の標準勘定科目をすべて削除
            logger.info("既存の標準勘定科目を削除中...")
            db.session.query(StandardAccount).delete()
            db.session.commit()
            
            # CSVファイルの読み込み
            logger.info(f"CSVファイル '{csv_file}' を読み込み中...")
            
            # CSVファイルをテキストとして開き、最初の2行を読み飛ばす
            with open(csv_file, 'r', encoding='utf-8-sig') as file:
                # ヘッダーを読み飛ばす
                next(file)  # 「標準科目DBのレコード定義は以下」という行をスキップ
                next(file)  # ヘッダー行をスキップ
                
                # 残りの行を読み込む
                reader = csv.reader(file)
                rows = list(reader)
            
            # 財務諸表区分のマッピング
            statement_type_map = {
                'BS': 'bs',
                'PL': 'pl',
                'CF': 'cf'
            }
            
            # 区分のマッピング
            category_map = {
                '資産': 'Assets',
                '負債': 'Liabilities',
                '純資産': 'Equity',
                '収益': 'Income',
                '費用': 'Expense'
            }
            
            # アカウント追加
            count = 0
            for row in rows:
                try:
                    # 空行や不完全な行はスキップ
                    if len(row) < 6 or not row[0]:
                        continue
                    
                    # コードを取得
                    code = row[0].strip()
                    
                    # 名前を取得
                    name = row[1].strip() if len(row) > 1 and row[1] else ""
                    if not name:
                        continue
                    
                    # 勘定科目区分を取得
                    account_type = row[2].strip() if len(row) > 2 and row[2] else ""
                    
                    # 表示順を取得
                    try:
                        display_order = int(row[3]) if len(row) > 3 and row[3] else 999
                    except ValueError:
                        display_order = 999
                    
                    # 上位科目コードを取得
                    parent_code = row[4].strip() if len(row) > 4 and row[4] else None
                    
                    # 財務諸表区分を取得
                    financial_statement_raw = row[5].strip() if len(row) > 5 and row[5] else "BS"
                    financial_statement = statement_type_map.get(financial_statement_raw, 'bs')
                    
                    # 勘定科目の区分をマッピング
                    category = category_map.get(account_type, 'Other')
                    
                    # 勘定科目の説明を取得
                    description = row[6].strip() if len(row) > 6 and row[6] else ''
                    
                    # 標準勘定科目の作成
                    account = StandardAccount(
                        code=code,
                        name=name,
                        category=category,
                        financial_statement=financial_statement,
                        account_type=account_type,
                        display_order=display_order,
                        parent_code=parent_code,
                        description=description
                    )
                    
                    db.session.add(account)
                    count += 1
                    
                    if count % 20 == 0:
                        logger.info(f"{count}件の勘定科目をインポートしました...")
                    
                except Exception as e:
                    logger.error(f"行のインポートエラー: {row}\nエラー: {str(e)}")
                    continue
            
            db.session.commit()
            logger.info(f"合計 {count} 件の標準勘定科目をインポートしました。")
            
            # 勘定科目区分別にカウント
            bs_count = db.session.query(StandardAccount).filter_by(financial_statement='bs').count()
            pl_count = db.session.query(StandardAccount).filter_by(financial_statement='pl').count()
            cf_count = db.session.query(StandardAccount).filter_by(financial_statement='cf').count()
            
            logger.info(f"BS科目: {bs_count}件, PL科目: {pl_count}件, CF科目: {cf_count}件")
            return count
            
        except Exception as e:
            logger.error(f"インポート処理中にエラーが発生しました: {str(e)}")
            db.session.rollback()
            raise

if __name__ == "__main__":
    import_standard_accounts("attached_assets/標準勘定科目6.csv")