"""
全ての残高データを再作成するスクリプト
既存の残高データを一度クリアし、CSVデータからマッピング情報を使って再構築する
"""
import sys
import logging
from app import app, db
from models import JA, CSVData, AccountMapping, StandardAccountBalance
from create_account_balances import create_standard_account_balances

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def recreate_all_balances(ja_code, year, file_type=None):
    """
    指定したJA、年度、財務諸表タイプの標準勘定科目残高を再作成する
    既存の残高データをクリアしてから作成し直すため、様々なエラーに対応できる
    
    Args:
        ja_code: JA code
        year: Financial year
        file_type: Type of financial statement (bs, pl, cf). None to process all types.
    
    Returns:
        dict: 処理結果
    """
    file_types = [file_type] if file_type else ['bs', 'pl', 'cf']
    result = {}
    
    for ft in file_types:
        logger.info(f"Processing {ja_code}, {year}, {ft}")
        
        # 既存の残高データを削除
        deleted = StandardAccountBalance.query.filter_by(
            ja_code=ja_code,
            year=int(year),
            statement_type=ft
        ).delete()
        
        logger.info(f"Deleted {deleted} existing balance records for {ja_code}, {year}, {ft}")
        
        # コミット
        db.session.commit()
        
        # 残高データを再作成
        try:
            # create_standard_account_balancesにはapp_contextが含まれている
            created = create_standard_account_balances(ja_code, year, ft)
            logger.info(f"Created {created} balance records for {ja_code}, {year}, {ft}")
            result[ft] = {
                "deleted": deleted,
                "created": created,
                "status": "success"
            }
        except Exception as e:
            logger.error(f"Error creating balance records for {ja_code}, {year}, {ft}: {str(e)}")
            result[ft] = {
                "deleted": deleted,
                "created": 0,
                "status": "error",
                "error": str(e)
            }
    
    # 処理結果を返す
    return result

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("使用方法: python recreate_all_balances.py <ja_code> <year> [file_type]")
        sys.exit(1)
    
    ja_code = sys.argv[1]
    year = int(sys.argv[2])
    file_type = sys.argv[3] if len(sys.argv) > 3 else None
    
    result = recreate_all_balances(ja_code, year, file_type)
    
    print("処理結果:")
    for ft, res in result.items():
        print(f"- {ft}: 削除={res['deleted']}件, 作成={res.get('created', 0)}件, 状態={res['status']}")