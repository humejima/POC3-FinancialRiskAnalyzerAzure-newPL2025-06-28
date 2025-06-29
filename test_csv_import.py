import pandas as pd
import numpy as np
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_csv_import(file_path):
    """CSVインポート処理をテストする"""
    try:
        # CSVファイルを読み込む
        logger.info(f"Reading CSV file: {file_path}")
        df = pd.read_csv(file_path, encoding='utf-8-sig')
        
        # 基本データクリーニング
        df = df.replace([np.inf, -np.inf], np.nan)
        
        # データフレームの最初の数行を出力
        logger.info("DataFrame head:")
        print(df.head())
        
        # 列情報を出力
        logger.info("DataFrame columns:")
        for col in df.columns:
            logger.info(f"Column: {col}, Type: {df[col].dtype}")
            
        # 勘定科目列を特定
        account_col = None
        for col in df.columns:
            if "科目" in col or "account" in col.lower() or "item" in col.lower():
                account_col = col
                logger.info(f"Found account column: {account_col}")
                break
        
        if account_col is None and len(df.columns) > 0:
            # 特定の科目列が見つからない場合は最初の列を使用
            account_col = df.columns[0]
            logger.info(f"Using first column as account column: {account_col}")
        
        # 値の列を特定
        current_col = None
        previous_col = None
        
        for col in df.columns:
            if "当年" in col or "current" in col.lower() or "this" in col.lower() or "令和5年度" in col:
                current_col = col
                logger.info(f"Found current value column: {current_col}")
            elif "前年" in col or "previous" in col.lower() or "last" in col.lower() or "令和4年度" in col:
                previous_col = col
                logger.info(f"Found previous value column: {previous_col}")
        
        # 特定の列が見つからない場合は位置で推測
        if current_col is None and len(df.columns) > 1:
            current_col = df.columns[2]  # 3列目（インデックス2）
            logger.info(f"Using column at index 2 as current value column: {current_col}")
        if previous_col is None and len(df.columns) > 2:
            previous_col = df.columns[1]  # 2列目（インデックス1）
            logger.info(f"Using column at index 1 as previous value column: {previous_col}")
        
        # 各行を処理
        sample_data = []
        for index, row in df.iterrows():
            if index > 10:  # 最初の10行だけをサンプルとして処理
                break
                
            account_name = str(row[account_col]).strip()
            
            # 空の勘定科目名または合計行をスキップ
            if not account_name or account_name.lower() in ["合計", "total", "小計", "subtotal"]:
                continue
            
            # カテゴリを抽出
            category = None
            if "資産" in account_name:
                category = "資産の部"
            elif "負債" in account_name:
                category = "負債の部"
            elif "純資産" in account_name or "資本" in account_name:
                category = "純資産の部"
            
            # 値を取得
            current_value = 0
            previous_value = 0
            
            if current_col:
                try:
                    current_value_raw = row[current_col]
                    logger.info(f"Current value raw: {current_value_raw}, Type: {type(current_value_raw)}")
                    if pd.isna(current_value_raw):
                        current_value = 0
                    else:
                        current_value = float(current_value_raw)
                    logger.info(f"Current value processed: {current_value}")
                except (ValueError, TypeError) as e:
                    logger.error(f"Error converting current value: {e}")
                    current_value = 0
            
            if previous_col:
                try:
                    previous_value_raw = row[previous_col]
                    logger.info(f"Previous value raw: {previous_value_raw}, Type: {type(previous_value_raw)}")
                    if pd.isna(previous_value_raw):
                        previous_value = 0
                    else:
                        previous_value = float(previous_value_raw)
                    logger.info(f"Previous value processed: {previous_value}")
                except (ValueError, TypeError) as e:
                    logger.error(f"Error converting previous value: {e}")
                    previous_value = 0
            
            sample_data.append({
                'account_name': account_name,
                'category': category,
                'current_value': current_value,
                'previous_value': previous_value
            })
        
        # サンプルデータを出力
        logger.info("Sample processed data:")
        for item in sample_data:
            print(f"Account: {item['account_name']}, Category: {item['category']}")
            print(f"  Current Value: {item['current_value']}, Previous Value: {item['previous_value']}")
        
        return True
    
    except Exception as e:
        logger.error(f"Error processing CSV: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    file_path = 'attached_assets/北海道BS_2025-04-21.csv'
    test_csv_import(file_path)
