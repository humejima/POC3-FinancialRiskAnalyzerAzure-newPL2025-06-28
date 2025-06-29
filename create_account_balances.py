from app import app, db
from models import CSVData, AccountMapping, StandardAccountBalance
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_standard_account_balances(ja_code, year, file_type):
    """指定したJA、年度、勘定科目タイプの標準勘定科目残高を作成する"""
    with app.app_context():
        # マッピング前にCSVデータがない場合は早期リターン
        csv_count = CSVData.query.filter_by(
            ja_code=ja_code,
            year=int(year),
            file_type=file_type
        ).count()
        
        if csv_count == 0:
            logger.warning(f"No CSV data found for {ja_code}, {year}, {file_type}")
            return 0
        
        # Get all mapped CSV data
        mapped_data = CSVData.query.filter_by(
            ja_code=ja_code,
            year=int(year),
            file_type=file_type,
            is_mapped=True
        ).all()
        
        logger.info(f"Found {len(mapped_data)} mapped records for {ja_code}, {year}, {file_type}")
        
        # マッピングされたデータがない場合、マッピングを実行
        if len(mapped_data) == 0:
            logger.warning(f"No mapped data found. Try to run mapping first for {ja_code}, {year}, {file_type}")
            # マッピングされたデータがない場合はゼロを返す
            return 0
        
        # Get account mappings
        mappings = {}
        for mapping in AccountMapping.query.filter_by(
            ja_code=ja_code,
            financial_statement=file_type
        ).all():
            mappings[mapping.original_account_name] = mapping
        
        logger.info(f"Found {len(mappings)} account mappings")
        
        # Process each mapped account
        processed_count = 0
        
        for data in mapped_data:
            mapping = mappings.get(data.account_name)
            if not mapping:
                logger.warning(f"No mapping found for {data.account_name}")
                continue
            
            # Determine statement subtype based on file type and category
            statement_subtype = "その他"
            if file_type == "bs":
                category = data.category or ""  # Noneの場合は空文字列を使用
                if "資産" in category:
                    statement_subtype = "BS資産"
                elif "負債" in category:
                    statement_subtype = "BS負債"
                elif "純資産" in category:
                    statement_subtype = "BS純資産"
            elif file_type == "pl":
                category = data.category or ""
                if "収益" in category:
                    statement_subtype = "PL収益"
                elif "費用" in category:
                    statement_subtype = "PL費用"
            elif file_type == "cf":
                category = data.category or ""
                if "営業活動" in category:
                    statement_subtype = "CF営業活動"
                elif "投資活動" in category:
                    statement_subtype = "CF投資活動"
                elif "財務活動" in category:
                    statement_subtype = "CF財務活動"
                elif "現金" in category or "現金同等物" in category:
                    statement_subtype = "CF現金同等物"
                else:
                    # カテゴリーがわからない場合はCFのままとする
                    statement_subtype = "CF"
                    
                # デバッグ出力を追加
                logger.info(f"CF区分の処理: 元のカテゴリー='{category}' → サブタイプ='{statement_subtype}'")
            
            # statement_subtypeの最終チェック
            if statement_subtype == "その他" and file_type == "cf":
                statement_subtype = "CF"
            
            # Check if standard account balance record already exists
            balance = StandardAccountBalance.query.filter_by(
                ja_code=ja_code,
                year=int(year),
                statement_type=file_type,
                standard_account_code=mapping.standard_account_code
            ).first()
            
            logger.info(f"Processing {data.account_name} -> {mapping.standard_account_code} ({mapping.standard_account_name})")
            logger.info(f"  Current value: {data.current_value}, Previous value: {data.previous_value}")
            
            # 特に重要な科目（当期純利益など）をデバッグ
            if mapping.standard_account_code == '9900':
                logger.warning(f"!!!注目!!! 当期純利益データの処理: {data.account_name} -> {mapping.standard_account_code}, ja_code={ja_code}, values={data.current_value},{data.previous_value}")
                
            # 預金関連科目のデバッグ
            if mapping.standard_account_code.startswith('30'):
                logger.warning(f"!!!預金科目処理!!! {data.account_name} -> {mapping.standard_account_code} ({mapping.standard_account_name}), category={data.category}, values={data.current_value},{data.previous_value}")
            
            # 数値を確実に変換して格納する
            try:
                current_value = float(data.current_value) if data.current_value is not None else 0
            except (ValueError, TypeError):
                logger.warning(f"Invalid current_value: {data.current_value}, using 0")
                current_value = 0
                
            try:
                previous_value = float(data.previous_value) if data.previous_value is not None else 0
            except (ValueError, TypeError):
                logger.warning(f"Invalid previous_value: {data.previous_value}, using 0")
                previous_value = 0
                
            if balance:
                # Update existing record
                balance.current_value = current_value
                balance.previous_value = previous_value
                logger.info(f"  Updating existing balance record with values: current={current_value}, previous={previous_value}")
            else:
                
                # Create new record
                new_balance = StandardAccountBalance()
                new_balance.ja_code = ja_code
                new_balance.year = int(year)
                new_balance.statement_type = file_type
                new_balance.statement_subtype = statement_subtype
                new_balance.standard_account_code = mapping.standard_account_code
                new_balance.standard_account_name = mapping.standard_account_name
                new_balance.current_value = current_value
                new_balance.previous_value = previous_value
                db.session.add(new_balance)
                logger.info(f"  Created new balance record")
            
            processed_count += 1
        
        db.session.commit()
        logger.info(f"Processed {processed_count} records")
        return processed_count

if __name__ == '__main__':
    ja_code = 'JA001'
    year = 2025
    file_type = 'bs'
    count = create_standard_account_balances(ja_code, year, file_type)
    print(f"Created or updated {count} standard account balances")
