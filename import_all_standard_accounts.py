"""
すべての標準勘定科目（BS、PL、CF）を一度に効率的にインポートするスクリプト
このスクリプトを実行することで、標準勘定科目データを削除して再作成します
"""

import os
import csv
import psycopg2
import logging
from io import StringIO

# ロガーの設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def import_bs_accounts():
    """
    BS標準勘定科目をCSVからインポート
    """
    try:
        # CSVファイルのパス
        csv_path = 'uploads/standard_bs_accounts.csv'
        
        # データベースに接続
        conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
        cursor = conn.cursor()
        
        # 既存のBS勘定科目を削除
        cursor.execute("DELETE FROM standard_account WHERE financial_statement = 'bs'")
        deleted_count = cursor.rowcount
        conn.commit()
        logger.info(f"{deleted_count}件のBS標準勘定科目を削除しました")
        
        # CSVからデータを読み込む
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            count = 0
            
            # 一括インポート用のバッファを準備
            buffer = StringIO()
            
            for row in reader:
                code = str(row['code'])
                name = str(row['name'])
                category = str(row['category'])
                financial_statement = 'bs'
                account_type = str(row['account_type'])
                display_order = int(row['display_order'])
                
                # parent_codeの処理
                parent_code = "NULL"
                if row.get('parent_code') and row['parent_code'].strip():
                    parent_code = "'" + row['parent_code'] + "'"
                
                # descriptionの処理
                description = "NULL"
                if row.get('description') and row['description'].strip():
                    description = "'" + row['description'].replace("'", "''") + "'"
                
                # COPYコマンド用の行を作成
                name_escaped = name.replace('\\', '\\\\').replace('\t', '\\t').replace('\n', '\\n')
                buffer.write(f"{code}\t{name_escaped}\t{category}\t{financial_statement}\t{account_type}\t{display_order}\t{parent_code if parent_code != 'NULL' else ''}\t{description if description != 'NULL' else ''}\n")
                count += 1
            
            # バッファを先頭に巻き戻し
            buffer.seek(0)
            
            # COPY FROM コマンドを実行
            cursor.copy_from(
                buffer, 
                'standard_account', 
                columns=('code', 'name', 'category', 'financial_statement', 'account_type', 'display_order', 'parent_code', 'description'),
                null=''
            )
            
            # コミット
            conn.commit()
            logger.info(f"{count}件のBS標準勘定科目を登録しました")
        
        cursor.close()
        conn.close()
        return True
    
    except Exception as e:
        if 'conn' in locals() and conn:
            conn.rollback()
            conn.close()
        logger.exception(f"BS標準勘定科目のインポートに失敗しました: {str(e)}")
        return False

def import_pl_accounts():
    """
    PL標準勘定科目をCSVからインポート
    """
    try:
        # CSVファイルのパス
        csv_path = 'uploads/standard_pl_updated.csv'
        
        # データベースに接続
        conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
        cursor = conn.cursor()
        
        # 既存のPL勘定科目を削除
        cursor.execute("DELETE FROM standard_account WHERE financial_statement = 'pl'")
        deleted_count = cursor.rowcount
        conn.commit()
        logger.info(f"{deleted_count}件のPL標準勘定科目を削除しました")
        
        # CSVからデータを読み込む
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            count = 0
            
            # 一括インポート用のバッファを準備
            buffer = StringIO()
            
            for row in reader:
                code = str(row['code'])
                name = str(row['name'])
                category = str(row['category'])
                financial_statement = 'pl'
                account_type = str(row['account_type'])
                display_order = int(row['display_order'])
                
                # parent_codeの処理
                parent_code = "NULL"
                if row.get('parent_code') and row['parent_code'].strip():
                    parent_code = "'" + row['parent_code'] + "'"
                
                # descriptionの処理
                description = "NULL"
                if row.get('description') and row['description'].strip():
                    description = "'" + row['description'].replace("'", "''") + "'"
                
                # COPYコマンド用の行を作成
                name_escaped = name.replace('\\', '\\\\').replace('\t', '\\t').replace('\n', '\\n')
                buffer.write(f"{code}\t{name_escaped}\t{category}\t{financial_statement}\t{account_type}\t{display_order}\t{parent_code if parent_code != 'NULL' else ''}\t{description if description != 'NULL' else ''}\n")
                count += 1
            
            # バッファを先頭に巻き戻し
            buffer.seek(0)
            
            # COPY FROM コマンドを実行
            cursor.copy_from(
                buffer, 
                'standard_account', 
                columns=('code', 'name', 'category', 'financial_statement', 'account_type', 'display_order', 'parent_code', 'description'),
                null=''
            )
            
            # コミット
            conn.commit()
            logger.info(f"{count}件のPL標準勘定科目を登録しました")
        
        cursor.close()
        conn.close()
        return True
    
    except Exception as e:
        if 'conn' in locals() and conn:
            conn.rollback()
            conn.close()
        logger.exception(f"PL標準勘定科目のインポートに失敗しました: {str(e)}")
        return False

def import_cf_accounts():
    """
    CF標準勘定科目をCSVからインポート
    """
    try:
        # CSVファイルのパス
        csv_path = 'uploads/standard_cf_updated.csv'
        
        # データベースに接続
        conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
        cursor = conn.cursor()
        
        # 既存のCF勘定科目を削除
        cursor.execute("DELETE FROM standard_account WHERE financial_statement = 'cf'")
        deleted_count = cursor.rowcount
        conn.commit()
        logger.info(f"{deleted_count}件のCF標準勘定科目を削除しました")
        
        # CSVからデータを読み込む
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            count = 0
            
            # 一括インポート用のバッファを準備
            buffer = StringIO()
            
            for row in reader:
                code = str(row['code'])
                name = str(row['name'])
                category = str(row['category'])
                financial_statement = 'cf'
                account_type = str(row['account_type'])
                display_order = int(row['display_order'])
                
                # parent_codeの処理
                parent_code = "NULL"
                if row.get('parent_code') and row['parent_code'].strip():
                    parent_code = "'" + row['parent_code'] + "'"
                
                # descriptionの処理
                description = "NULL"
                if row.get('description') and row['description'].strip():
                    description = "'" + row['description'].replace("'", "''") + "'"
                
                # COPYコマンド用の行を作成
                name_escaped = name.replace('\\', '\\\\').replace('\t', '\\t').replace('\n', '\\n')
                buffer.write(f"{code}\t{name_escaped}\t{category}\t{financial_statement}\t{account_type}\t{display_order}\t{parent_code if parent_code != 'NULL' else ''}\t{description if description != 'NULL' else ''}\n")
                count += 1
            
            # バッファを先頭に巻き戻し
            buffer.seek(0)
            
            # COPY FROM コマンドを実行
            cursor.copy_from(
                buffer, 
                'standard_account', 
                columns=('code', 'name', 'category', 'financial_statement', 'account_type', 'display_order', 'parent_code', 'description'),
                null=''
            )
            
            # コミット
            conn.commit()
            logger.info(f"{count}件のCF標準勘定科目を登録しました")
        
        cursor.close()
        conn.close()
        return True
    
    except Exception as e:
        if 'conn' in locals() and conn:
            conn.rollback()
            conn.close()
        logger.exception(f"CF標準勘定科目のインポートに失敗しました: {str(e)}")
        return False

def import_all_standard_accounts():
    """
    すべての標準勘定科目（BS、PL、CF）をインポート
    """
    # BSのインポート
    bs_success = import_bs_accounts()
    if bs_success:
        print("BS標準勘定科目のインポートに成功しました")
    else:
        print("BS標準勘定科目のインポートに失敗しました")
        return False
    
    # PLのインポート
    pl_success = import_pl_accounts()
    if pl_success:
        print("PL標準勘定科目のインポートに成功しました")
    else:
        print("PL標準勘定科目のインポートに失敗しました")
        return False
    
    # CFのインポート
    cf_success = import_cf_accounts()
    if cf_success:
        print("CF標準勘定科目のインポートに成功しました")
    else:
        print("CF標準勘定科目のインポートに失敗しました")
        return False
    
    return True

if __name__ == "__main__":
    success = import_all_standard_accounts()
    if success:
        print("すべての標準勘定科目のインポートに成功しました")
    else:
        print("標準勘定科目のインポートに失敗しました")