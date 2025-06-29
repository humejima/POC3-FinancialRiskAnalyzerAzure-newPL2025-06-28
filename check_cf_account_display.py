from app import app, db
from models import StandardAccountBalance
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_cf_accounts():
    """CFの残高表示を確認する（特に営業活動によるキャッシュ・フロー）"""
    with app.app_context():
        # 営業活動によるキャッシュ・フローの残高を確認
        operating_cf = StandardAccountBalance.query.filter_by(
            ja_code='JA001',
            year=2021,
            statement_type='cf',
            standard_account_code='110000'
        ).first()
        
        if operating_cf:
            logger.info(f"営業活動CF: コード={operating_cf.standard_account_code}, "
                       f"名前={operating_cf.standard_account_name}, "
                       f"当期={operating_cf.current_value}, 前期={operating_cf.previous_value}")
        else:
            logger.error("営業活動CFの残高が見つかりませんでした")
        
        # JA001、2021年度のCF残高をすべて表示
        balances = StandardAccountBalance.query.filter_by(
            ja_code='JA001',
            year=2021,
            statement_type='cf'
        ).all()
        
        logger.info(f"CF残高データ件数: {len(balances)}")
        
        for balance in balances:
            logger.info(f"科目={balance.standard_account_code} {balance.standard_account_name}, "
                       f"値={balance.current_value}")

if __name__ == "__main__":
    check_cf_accounts()