"""
直接SQLマッピング機能のデバッグスクリプト
問題の原因を特定するために、データベース内のデータを直接調査します
"""
import os
import sys
import psycopg2
from psycopg2.extras import DictCursor

def test_direct_mapping():
    # DATABASE_URLからの接続
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if not DATABASE_URL:
        print('DATABASE_URL environment variable is not set')
        sys.exit(1)
        
    print(f'Connecting to {DATABASE_URL[:20]}...')
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor(cursor_factory=DictCursor)
        
        # テスト対象データの確認
        ja_code = 'JA002'
        year = 2025
        file_type = 'bs'
        
        print(f'Checking data for JA: {ja_code}, Year: {year}, Type: {file_type}')
        
        # 未マッピングデータの確認
        cursor.execute("""
            SELECT COUNT(*) 
            FROM csv_data 
            WHERE ja_code = %s 
            AND year = %s 
            AND file_type = %s 
            AND is_mapped = false
        """, (ja_code, year, file_type))
        
        result = cursor.fetchone()
        unmapped_count = result[0] if result else 0
        
        print(f'Unmapped count: {unmapped_count}')
        
        # 実際に最初の5件の未マッピングデータを表示
        cursor.execute("""
            SELECT id, account_name, current_value, is_mapped 
            FROM csv_data 
            WHERE ja_code = %s 
            AND year = %s 
            AND file_type = %s 
            AND is_mapped = false
            LIMIT 5
        """, (ja_code, year, file_type))
        
        print('Sample unmapped data:')
        sample_rows = cursor.fetchall()
        if not sample_rows:
            print('  No unmapped data found!')
        else:
            for row in sample_rows:
                print(f'  ID: {row["id"]}, Name: {row["account_name"]}, Value: {row["account_value"]}, Mapped: {row["is_mapped"]}')
        
        # テスト用にis_mappedフラグを更新してみる（検証用）
        if sample_rows:
            test_id = sample_rows[0]["id"]
            cursor.execute("""
                UPDATE csv_data
                SET is_mapped = true
                WHERE id = %s
                RETURNING id, account_name, is_mapped
            """, (test_id,))
            
            updated_row = cursor.fetchone()
            if updated_row:
                print(f'Updated test record: ID={updated_row["id"]}, Name={updated_row["account_name"]}, Mapped={updated_row["is_mapped"]}')
                conn.commit()
                print('Committed test update')
            else:
                print('Failed to update test record')
                conn.rollback()
        
        # 標準勘定科目の最初の5件を表示
        cursor.execute("""
            SELECT code, name, statement_type
            FROM standard_account
            WHERE statement_type = %s
            LIMIT 5
        """, (file_type,))
        
        print('Sample standard accounts:')
        for row in cursor.fetchall():
            print(f'  Code: {row["code"]}, Name: {row["name"]}, Type: {row["statement_type"]}')
        
        # 再度未マッピングデータの確認
        cursor.execute("""
            SELECT COUNT(*) 
            FROM csv_data 
            WHERE ja_code = %s 
            AND year = %s 
            AND file_type = %s 
            AND is_mapped = false
        """, (ja_code, year, file_type))
        
        result = cursor.fetchone()
        updated_unmapped_count = result[0] if result else 0
        
        print(f'Updated unmapped count: {updated_unmapped_count}')
        print(f'Difference: {unmapped_count - updated_unmapped_count}')
        
        cursor.close()
        conn.close()
        print('Diagnostic complete')
        
    except Exception as e:
        print(f'Error: {e}')
        sys.exit(1)

if __name__ == '__main__':
    test_direct_mapping()