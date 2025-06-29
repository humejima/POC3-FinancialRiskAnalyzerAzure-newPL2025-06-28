import os
import csv
import logging
from app import app, db
from models import StandardAccount
from sqlalchemy import text

# ロギングの設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def add_parent_code_column():
    """標準勘定科目テーブルに上位科目コードカラムを追加する"""
    try:
        with app.app_context():
            # 上位科目コードカラムがすでに存在するか確認
            inspector = db.inspect(db.engine)
            columns = inspector.get_columns('standard_account')
            column_names = [column['name'] for column in columns]
            
            if 'parent_code' not in column_names:
                logger.info("上位科目コードカラムを追加しています...")
                sql = text("ALTER TABLE standard_account ADD COLUMN parent_code VARCHAR(10)")
                db.session.execute(sql)
                db.session.commit()
                logger.info("上位科目コードカラムが追加されました")
            else:
                logger.info("上位科目コードカラムはすでに存在します")
                
    except Exception as e:
        logger.error(f"カラム追加エラー: {str(e)}")
        db.session.rollback()
        raise

def update_parent_codes_bs_pl(csv_file):
    """標準勘定科目テーブルの上位科目コードを更新する（BS・PL用）"""
    try:
        with app.app_context():
            logger.info(f"CSVファイル {csv_file} から上位科目コードを読み込んでいます...")
            
            # CSVファイルを読み込む
            accounts_updated = 0
            with open(csv_file, 'r', encoding='utf-8-sig') as f:
                reader = csv.reader(f)
                next(reader)  # ヘッダー行をスキップ
                next(reader)  # 列定義行をスキップ
                
                for row in reader:
                    if len(row) >= 6:  # 必要な列数があることを確認
                        account_code = row[0].strip()
                        account_name = row[1].strip()
                        parent_code = row[4].strip() if row[4].strip() else None
                        
                        # 勘定科目コードが有効であることを確認
                        if account_code:
                            # 該当する標準勘定科目を検索して更新
                            account = StandardAccount.query.filter_by(code=account_code).first()
                            if account:
                                account.parent_code = parent_code
                                accounts_updated += 1
                                logger.debug(f"更新: {account_code} - {account_name}, 上位科目: {parent_code}")
                            else:
                                logger.warning(f"勘定科目コード {account_code} が見つかりません")
            
            db.session.commit()
            logger.info(f"BS・PL勘定科目の上位科目コードの更新が完了しました。{accounts_updated} 件の勘定科目が更新されました。")
            return accounts_updated
                
    except Exception as e:
        logger.error(f"上位科目コード更新エラー: {str(e)}")
        db.session.rollback()
        raise

def update_parent_codes_cf(csv_file):
    """標準勘定科目テーブルの上位科目コードを更新する（CF用）"""
    try:
        with app.app_context():
            logger.info(f"CSVファイル {csv_file} からCF勘定科目の上位科目コードを読み込んでいます...")
            
            # CSVファイルを読み込む
            accounts_updated = 0
            with open(csv_file, 'r', encoding='utf-8-sig') as f:
                reader = csv.reader(f)
                next(reader)  # ヘッダー行をスキップ
                
                for row in reader:
                    if len(row) >= 5:  # 必要な列数があることを確認
                        account_code = row[0].strip()
                        account_name = row[1].strip()
                        parent_code = row[3].strip() if row[3].strip() else None
                        
                        # 勘定科目コードが有効であることを確認
                        if account_code:
                            # 該当する標準勘定科目を検索して更新
                            account = StandardAccount.query.filter_by(code=account_code).first()
                            if account:
                                account.parent_code = parent_code
                                accounts_updated += 1
                                logger.debug(f"更新: {account_code} - {account_name}, 上位科目: {parent_code}")
                            else:
                                logger.warning(f"勘定科目コード {account_code} が見つかりません")
            
            db.session.commit()
            logger.info(f"CF勘定科目の上位科目コードの更新が完了しました。{accounts_updated} 件の勘定科目が更新されました。")
            return accounts_updated
                
    except Exception as e:
        logger.error(f"CF上位科目コード更新エラー: {str(e)}")
        db.session.rollback()
        raise

def update_and_improve_relation():
    """上位科目コードを利用して、財務指標計算のための関係を改善する"""
    try:
        with app.app_context():
            # 親子関係を持つ勘定科目のリストを作成
            parent_accounts = StandardAccount.query.filter(StandardAccount.parent_code != None).all()
            
            # 親科目ごとに子科目のリストを作成
            parent_child_map = {}
            for account in parent_accounts:
                parent_code = account.parent_code
                if parent_code not in parent_child_map:
                    parent_child_map[parent_code] = []
                parent_child_map[parent_code].append(account.code)
            
            # 親科目コードとその子科目コードのリストをログに出力
            logger.info("親科目コードとその子科目コード:")
            for parent_code, child_codes in parent_child_map.items():
                parent = StandardAccount.query.filter_by(code=parent_code).first()
                parent_name = parent.name if parent else "Unknown"
                logger.info(f"親科目 {parent_code} ({parent_name}): 子科目 {', '.join(child_codes)}")
            
            # 子科目を持つ親科目の数を返す
            return len(parent_child_map)
            
    except Exception as e:
        logger.error(f"関係改善エラー: {str(e)}")
        raise

def list_financial_statement_accounts(financial_statement):
    """指定された財務諸表区分の勘定科目をリストアップする"""
    try:
        with app.app_context():
            accounts = StandardAccount.query.filter_by(financial_statement=financial_statement).all()
            logger.info(f"{financial_statement}勘定科目の数: {len(accounts)}")
            
            for account in accounts:
                logger.debug(f"{account.code} - {account.name} - 親科目: {account.parent_code}")
                
    except Exception as e:
        logger.error(f"{financial_statement}勘定科目リストアップエラー: {str(e)}")
        raise

if __name__ == "__main__":
    bs_pl_csv_file = "attached_assets/標準勘定科目6.csv"
    cf_csv_file = "attached_assets/キャッシュフロー計算書標準科目テーブル.csv"
    
    if not os.path.exists(bs_pl_csv_file):
        logger.error(f"CSVファイル {bs_pl_csv_file} が見つかりません")
        exit(1)
        
    if not os.path.exists(cf_csv_file):
        logger.error(f"CSVファイル {cf_csv_file} が見つかりません")
        exit(1)
    
    try:
        # 上位科目コードカラムを追加
        add_parent_code_column()
        
        # BS・PL勘定科目の上位科目コードを更新
        bs_pl_updated_count = update_parent_codes_bs_pl(bs_pl_csv_file)
        logger.info(f"{bs_pl_updated_count} 件のBS・PL勘定科目が更新されました")
        
        # CF勘定科目の上位科目コードを更新
        cf_updated_count = update_parent_codes_cf(cf_csv_file)
        logger.info(f"{cf_updated_count} 件のCF勘定科目が更新されました")
        
        # 上位科目コードを利用して関係を改善
        parent_count = update_and_improve_relation()
        logger.info(f"{parent_count} 件の親科目が子科目を持っています")
        
        # 勘定科目の確認
        list_financial_statement_accounts("bs")
        list_financial_statement_accounts("pl")
        list_financial_statement_accounts("cf")
        
        logger.info("標準勘定科目の上位科目コード更新が完了しました")
        
    except Exception as e:
        logger.error(f"エラーが発生しました: {str(e)}")
        exit(1)