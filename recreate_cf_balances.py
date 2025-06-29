from app import app, db
from models import StandardAccountBalance
from create_account_balances import create_standard_account_balances
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def recreate_cf_balances(ja_code='JA001', year=2025):
    """CFデータの標準勘定科目残高を再作成する"""
    with app.app_context():
        # 既存のCFデータを削除
        deleted = StandardAccountBalance.query.filter_by(
            ja_code=ja_code,
            year=year,
            statement_type='cf'
        ).delete()
        
        logger.info(f"{deleted}件のCF残高データを削除しました。")
        db.session.commit()
        
        # 標準勘定科目残高を作成
        count = create_standard_account_balances(ja_code, year, 'cf')
        logger.info(f"{count}件のCF残高データを作成しました。")
        
        return deleted, count

if __name__ == '__main__':
    deleted, created = recreate_cf_balances()
    print(f"{deleted}件のCF残高データを削除し、{created}件の新しいデータを作成しました。")
