"""
デモ用にテストデータを作成するスクリプト
このスクリプトを実行して特定のJAに未マッピングデータを作成します
"""
import os
import sys
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# ロギング設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_demo_data():
    """JA002用のデモデータを作成"""
    try:
        # DATABASE_URLからの接続
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            logger.error('DATABASE_URL environment variable is not set')
            sys.exit(1)
            
        logger.info(f'データベースに接続しています...')
        
        # SQLAlchemy経由で接続
        engine = create_engine(database_url)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # JA002とBS用のデモデータを追加（未マッピング状態）
        ja_code = 'JA002'
        year = 2025
        file_type = 'bs'
        
        # 処理前の未マッピングデータを確認
        result = session.execute(
            text("""
                SELECT COUNT(*) 
                FROM csv_data 
                WHERE ja_code = :ja_code 
                AND year = :year 
                AND file_type = :file_type 
                AND is_mapped = false
            """), 
            {'ja_code': ja_code, 'year': year, 'file_type': file_type}
        )
        count_before = result.scalar()
        logger.info(f'現在の未マッピングデータ数: {count_before}件')
        
        # すでに十分なデータがある場合は処理をスキップ
        if count_before >= 5:
            logger.info('十分な未マッピングデータが既に存在するため、新規作成をスキップします')
            sys.exit(0)
        
        # まだマッピングされていないデモデータを追加
        demo_accounts = [
            {'name': '現金', 'value': 1000000},
            {'name': '定期預金', 'value': 5000000},
            {'name': '貸出金', 'value': 10000000},
            {'name': '有価証券', 'value': 3000000},
            {'name': '固定資産', 'value': 8000000},
            {'name': '出資金', 'value': 2000000},
            {'name': '積立金', 'value': 4000000},
            {'name': '借入金', 'value': 7000000},
            {'name': '資本金', 'value': 9000000},
            {'name': '預かり金', 'value': 6000000}
        ]
        
        # データを作成
        for i, account in enumerate(demo_accounts):
            session.execute(
                text("""
                    INSERT INTO csv_data (
                        ja_code, year, file_type, row_number, account_name, 
                        current_value, previous_value, is_mapped, created_at
                    ) VALUES (
                        :ja_code, :year, :file_type, :row_number, :account_name,
                        :current_value, :previous_value, false, :created_at
                    ) ON CONFLICT DO NOTHING
                """),
                {
                    'ja_code': ja_code,
                    'year': year,
                    'file_type': file_type,
                    'row_number': i + 1,
                    'account_name': account['name'],
                    'current_value': account['value'],
                    'previous_value': account['value'] * 0.9,  # 前年は現在の90%とする
                    'created_at': datetime.now()
                }
            )
        
        # 変更をコミット
        session.commit()
        logger.info('デモデータの作成が完了しました')
        
        # 処理後の未マッピングデータを確認
        result = session.execute(
            text("""
                SELECT COUNT(*) 
                FROM csv_data 
                WHERE ja_code = :ja_code 
                AND year = :year 
                AND file_type = :file_type 
                AND is_mapped = false
            """), 
            {'ja_code': ja_code, 'year': year, 'file_type': file_type}
        )
        count_after = result.scalar()
        logger.info(f'作成後の未マッピングデータ数: {count_after}件（{count_after - count_before}件追加）')
        
        session.close()
        
    except Exception as e:
        logger.error(f'エラー: {str(e)}')
        sys.exit(1)

if __name__ == '__main__':
    create_demo_data()