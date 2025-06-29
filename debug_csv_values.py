"""
CSVデータの値をデバッグ出力するツール
残高データの生成に問題があるか確認
"""
import sys
import logging
from app import db
from models import CSVData, AccountMapping

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_csv_values(ja_code, year, file_type):
    """
    CSVデータの残高値をデバッグ出力
    型情報も含めて詳細に表示
    """
    # CSVデータを取得
    csv_data = CSVData.query.filter_by(
        ja_code=ja_code,
        year=int(year),
        file_type=file_type
    ).order_by(CSVData.id).limit(20).all()
    
    logger.info(f"CSV残高値のデバッグ（最大20件）")
    
    for i, data in enumerate(csv_data):
        logger.info(f"データ{i+1}: 科目={data.account_name}")
        logger.info(f"  当期値={data.current_value} (型: {type(data.current_value).__name__})")
        logger.info(f"  前期値={data.previous_value} (型: {type(data.previous_value).__name__})")
        
        # 文字列か数値か確認
        if isinstance(data.current_value, str):
            logger.info(f"  当期値は文字列です。数値に変換可能か試みます。")
            try:
                float_val = float(data.current_value)
                logger.info(f"  変換成功: {float_val}")
            except ValueError:
                logger.info(f"  変換失敗: 数値に変換できません。")
        
        # マッピング情報も確認
        mapping = AccountMapping.query.filter_by(
            ja_code=ja_code,
            original_account_name=data.account_name,
            financial_statement=file_type
        ).first()
        
        if mapping:
            logger.info(f"  マッピング: 標準科目コード={mapping.standard_account_code}, 標準科目名={mapping.standard_account_name}")
        else:
            logger.info(f"  マッピングなし")
    
    # 文字列形式の残高値の有無を確認
    string_values = db.session.query(CSVData).filter(
        CSVData.ja_code == ja_code,
        CSVData.year == int(year),
        CSVData.file_type == file_type,
        db.func.trim(CSVData.current_value) != '',
        db.cast(CSVData.current_value, db.Float).is_(None)
    ).all()
    
    if string_values:
        logger.info(f"数値に変換できない当期値を持つレコード: {len(string_values)}件")
        for data in string_values[:5]:  # 最初の5件だけ表示
            logger.info(f"  科目={data.account_name}, 当期値={data.current_value}")
    else:
        logger.info("数値に変換できない当期値を持つレコードはありません。")
    
    return len(csv_data)

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("使用方法: python debug_csv_values.py <ja_code> <year> <file_type>")
        sys.exit(1)
    
    ja_code = sys.argv[1]
    year = int(sys.argv[2])
    file_type = sys.argv[3]
    
    count = debug_csv_values(ja_code, year, file_type)
    print(f"CSV残高値のデバッグ完了: {count}件のデータを確認しました。")