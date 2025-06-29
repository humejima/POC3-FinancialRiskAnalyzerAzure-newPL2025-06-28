"""
預金関連の残高を再計算する
"""
import sys
import logging
from app import app, db
from models import StandardAccountBalance, CSVData, AccountMapping
from create_account_balances import create_standard_account_balances

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def recreate_deposit_balances(ja_code, year):
    """
    預金関連の残高データを再作成する
    """
    with app.app_context():
        logger.info(f"預金関連の残高再計算開始: {ja_code}, {year}")
        
        # 既存の預金残高を削除（コード30で始まるもの）
        deleted = StandardAccountBalance.query.filter(
            StandardAccountBalance.ja_code == ja_code,
            StandardAccountBalance.year == int(year),
            StandardAccountBalance.statement_type == 'bs',
            StandardAccountBalance.standard_account_code.like('30%')
        ).delete()
        
        logger.info(f"預金残高削除完了: {deleted}件")
        db.session.commit()
        
        # マッピングされた預金関連のCSVデータを直接取得
        deposit_data = db.session.query(CSVData).join(
            AccountMapping,
            (CSVData.account_name == AccountMapping.original_account_name) & 
            (CSVData.ja_code == AccountMapping.ja_code)
        ).filter(
            CSVData.ja_code == ja_code,
            CSVData.year == int(year),
            CSVData.file_type == 'bs',
            CSVData.is_mapped == True,
            AccountMapping.standard_account_code.like('30%')
        ).all()
        
        logger.info(f"預金関連データ: {len(deposit_data)}件")
        
        # 預金データを処理
        processed_count = 0
        
        for data in deposit_data:
            # マッピング情報を取得
            mapping = AccountMapping.query.filter_by(
                ja_code=ja_code,
                original_account_name=data.account_name,
                financial_statement='bs'
            ).first()
            
            if not mapping:
                logger.warning(f"マッピングが見つかりません: {data.account_name}")
                continue
            
            # サブタイプの決定
            statement_subtype = "BS負債"
            logger.info(f"処理中: {data.account_name} -> {mapping.standard_account_code} ({mapping.standard_account_name})")
            logger.info(f"  残高: 当年度={data.current_value}, 前年度={data.previous_value}")
            
            # 残高値の変換
            try:
                current_value = float(data.current_value) if data.current_value is not None else 0
            except (ValueError, TypeError):
                logger.warning(f"不正な当年度値: {data.current_value}, 0を使用")
                current_value = 0
                
            try:
                previous_value = float(data.previous_value) if data.previous_value is not None else 0
            except (ValueError, TypeError):
                logger.warning(f"不正な前年度値: {data.previous_value}, 0を使用")
                previous_value = 0
            
            # 新しい残高レコードを作成
            new_balance = StandardAccountBalance()
            new_balance.ja_code = ja_code
            new_balance.year = int(year)
            new_balance.statement_type = 'bs'
            new_balance.statement_subtype = statement_subtype
            new_balance.standard_account_code = mapping.standard_account_code
            new_balance.standard_account_name = mapping.standard_account_name
            new_balance.current_value = current_value
            new_balance.previous_value = previous_value
            
            db.session.add(new_balance)
            processed_count += 1
            logger.info(f"  残高レコード作成: {mapping.standard_account_code} = {current_value}")
        
        # コミット
        db.session.commit()
        logger.info(f"預金残高の再計算完了: {processed_count}件処理")
        
        return {
            "deleted": deleted,
            "created": processed_count,
            "status": "success" if processed_count > 0 else "warning"
        }

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("使用方法: python recreate_deposit_balances.py <ja_code> <year>")
        sys.exit(1)
    
    ja_code = sys.argv[1]
    year = int(sys.argv[2])
    
    result = recreate_deposit_balances(ja_code, year)
    print(f"預金残高の処理結果: 削除={result['deleted']}件, 作成={result['created']}件, 状態={result['status']}")