"""
残高データの状態を確認するスクリプト
"""
import sys
import logging
from app import db
from models import StandardAccountBalance, StandardAccount, AccountMapping, CSVData

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_balance_data(ja_code, year, file_type):
    """
    特定のJA、年度、財務諸表タイプの残高データをチェックする
    """
    # 残高データの件数を確認
    balance_count = StandardAccountBalance.query.filter_by(
        ja_code=ja_code,
        year=year,
        statement_type=file_type
    ).count()
    
    logger.info(f"残高データ件数: {balance_count}")
    
    # マッピング件数を確認
    mapping_count = AccountMapping.query.filter_by(
        ja_code=ja_code,
        financial_statement=file_type
    ).count()
    
    logger.info(f"マッピング件数: {mapping_count}")
    
    # CSVデータ件数を確認
    csv_count = CSVData.query.filter_by(
        ja_code=ja_code,
        year=year,
        file_type=file_type
    ).count()
    
    logger.info(f"CSVデータ件数: {csv_count}")
    
    # マッピング済みのCSVデータ件数を確認
    mapped_csv_count = CSVData.query.filter_by(
        ja_code=ja_code,
        year=year,
        file_type=file_type,
        is_mapped=True
    ).count()
    
    logger.info(f"マッピング済みCSVデータ件数: {mapped_csv_count}")
    
    # いくつかの残高データの詳細を表示
    balances = StandardAccountBalance.query.filter_by(
        ja_code=ja_code,
        year=year,
        statement_type=file_type
    ).limit(10).all()
    
    for i, balance in enumerate(balances):
        logger.info(f"残高データ {i+1}: コード={balance.standard_account_code}, "
                  f"名前={balance.standard_account_name}, "
                  f"当期値={balance.current_value}, "
                  f"前期値={balance.previous_value}")
    
    # 標準勘定科目と残高を結合して表示
    logger.info("標準勘定科目と残高の結合結果:")
    results = db.session.query(
        StandardAccount.code,
        StandardAccount.name,
        StandardAccountBalance.current_value,
        StandardAccountBalance.previous_value
    ).outerjoin(
        StandardAccountBalance,
        (StandardAccount.code == StandardAccountBalance.standard_account_code) &
        (StandardAccountBalance.ja_code == ja_code) &
        (StandardAccountBalance.year == year) &
        (StandardAccountBalance.statement_type == file_type)
    ).filter(
        StandardAccount.financial_statement == file_type
    ).order_by(StandardAccount.display_order).limit(10).all()
    
    for i, result in enumerate(results):
        logger.info(f"結合結果 {i+1}: コード={result.code}, "
                  f"名前={result.name}, "
                  f"当期値={result.current_value}, "
                  f"前期値={result.previous_value}")
    
    # マッピング例を確認
    mappings = AccountMapping.query.filter_by(
        ja_code=ja_code,
        financial_statement=file_type
    ).limit(5).all()
    
    logger.info("マッピング例:")
    for i, mapping in enumerate(mappings):
        logger.info(f"マッピング {i+1}: 元科目={mapping.original_account_name}, "
                  f"標準科目コード={mapping.standard_account_code}, "
                  f"標準科目名={mapping.standard_account_name}")
    
    # データの連続性を確認（マッピング→残高の流れを検証）
    logger.info("マッピングから残高への連続性確認:")
    for mapping in mappings:
        # マッピングに対応するCSVデータを検索
        csv_data = CSVData.query.filter_by(
            ja_code=ja_code,
            year=year,
            file_type=file_type,
            account_name=mapping.original_account_name
        ).first()
        
        if csv_data:
            logger.info(f"CSV: {csv_data.account_name}, 当期値={csv_data.current_value}")
            
            # CSVデータに対応する残高を検索
            balance = StandardAccountBalance.query.filter_by(
                ja_code=ja_code,
                year=year,
                statement_type=file_type,
                standard_account_code=mapping.standard_account_code
            ).first()
            
            if balance:
                logger.info(f"残高: コード={balance.standard_account_code}, 当期値={balance.current_value}")
            else:
                logger.info(f"残高データなし: コード={mapping.standard_account_code}")
        else:
            logger.info(f"CSVデータなし: {mapping.original_account_name}")

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("使用方法: python check_balance_data.py <ja_code> <year> <file_type>")
        sys.exit(1)
    
    ja_code = sys.argv[1]
    year = int(sys.argv[2])
    file_type = sys.argv[3]
    
    check_balance_data(ja_code, year, file_type)