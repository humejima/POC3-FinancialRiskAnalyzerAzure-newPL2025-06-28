import os
import pandas as pd
import numpy as np
import logging
import traceback
from datetime import datetime
from app import db
from models import JA, CSVData, StandardAccount

logger = logging.getLogger(__name__)

class DataProcessor:
    """
    Handles processing of CSV/Excel financial data files
    """
    
    @staticmethod
    def validate_file(file):
        """
        Validates the uploaded file format and basic structure
        
        Args:
            file: The uploaded file object
            
        Returns:
            tuple: (is_valid, error_message)
        """
        if not file:
            return False, "No file provided"
        
        filename = file.filename
        if not filename:
            return False, "Invalid filename"
            
        # Check file extension
        _, ext = os.path.splitext(filename.lower())
        if ext not in ['.csv', '.xlsx', '.xls']:
            return False, "File must be CSV or Excel format"
            
        return True, ""
    
    @staticmethod
    def detect_file_type(filename):
        """
        Detect financial statement type from filename
        
        Args:
            filename: The name of the uploaded file
            
        Returns:
            str: Detected file type (bs, pl, cf)
        """
        filename = filename.lower()
        if "bs" in filename or "balance" in filename:
            return "bs"
        elif "pl" in filename or "profit" in filename or "loss" in filename:
            return "pl"
        elif "cf" in filename or "cash" in filename or "flow" in filename:
            return "cf"
        else:
            return None
    
    @staticmethod
    def process_csv(file, ja_code, year, file_type=None):
        """
        Process a CSV file and store data in the database
        
        Args:
            file: The uploaded file object
            ja_code: JA code
            year: Financial year
            file_type: Type of financial statement (bs, pl, cf)
            
        Returns:
            tuple: (success, message, row_count)
        """
        try:
            # Detect file type if not provided
            if file_type is None:
                file_type = DataProcessor.detect_file_type(file.filename)
                if file_type is None:
                    return False, "Could not determine financial statement type", 0
            
            # Read the file based on its extension
            _, ext = os.path.splitext(file.filename.lower())
            if ext == '.csv':
                # 複数のエンコーディングを順番に試行
                encodings = ['utf-8-sig', 'utf-8', 'shift-jis', 'cp932', 'euc-jp', 'iso-2022-jp']
                for encoding in encodings:
                    try:
                        logger.info(f"Trying to read CSV with encoding: {encoding}")
                        df = pd.read_csv(file, encoding=encoding)
                        logger.info(f"Successfully read CSV with encoding: {encoding}")
                        break
                    except Exception as e:
                        logger.warning(f"Failed to read CSV with encoding {encoding}: {str(e)}")
                        file.seek(0)  # ファイルポインタをリセット
                        continue
                else:
                    # すべてのエンコーディングが失敗した場合
                    return False, f"Could not read CSV file with any supported encoding. Please ensure the file is properly encoded.", 0
            else:  # Excel files
                df = pd.read_excel(file)
            
            # Basic data cleaning
            df = df.replace([np.inf, -np.inf], np.nan)
            df = df.fillna(0)
            
            # Identify potential account name column
            account_col = None
            category_col = None
            
            # First, identify category column if it exists
            for col in df.columns:
                if "区分" in col or "category" in col.lower():
                    category_col = col
                    break
            
            # Then identify account name column, avoiding category column
            for col in df.columns:
                if col == category_col:
                    continue  # Skip category column
                if "科目名" in col or "account_name" in col.lower() or "勘定科目" in col:
                    account_col = col
                    break
                elif "科目" in col or "account" in col.lower() or "item" in col.lower():
                    account_col = col
                    break
            
            if account_col is None and len(df.columns) > 0:
                # If no specific account column found, use first non-category column
                for col in df.columns:
                    if col != category_col:
                        account_col = col
                        break
            
            if account_col is None:
                return False, "Could not identify account name column", 0
            
            # Identify value columns
            current_col = None
            previous_col = None
            
            for col in df.columns:
                if "当年" in col or "current" in col.lower() or "this" in col.lower() or "令和5年度" in col:
                    current_col = col
                elif "前年" in col or "previous" in col.lower() or "last" in col.lower() or "令和4年度" in col:
                    previous_col = col
            
            # If specific columns weren't found, try to use position
            if current_col is None:
                if len(df.columns) > 3:  # 4列以上ある場合（BS・PLデータタイプ）
                    current_col = df.columns[3]  # 北海道BSのフォーマットに合わせて修正（4列目）
                elif len(df.columns) > 1:  # 2列以上ある場合（CFデータタイプ）
                    current_col = df.columns[1]  # CFフォーマットでは2列目が当期の値
            
            if previous_col is None:
                if len(df.columns) > 2:  # 3列以上ある場合
                    previous_col = df.columns[2]  # 北海道BSのフォーマットに合わせて修正（3列目）
                elif len(df.columns) > 1:  # 2列以上ある場合
                    # CFでは前期データがない場合もあるため、とりあえず同じ列を使用
                    previous_col = current_col
                
            logger.info(f"Selected columns - Account: {account_col}, Current: {current_col}, Previous: {previous_col}")
            
            # CSVデータをインポートする前に、同一JAコード・年度・ファイルタイプの既存データを削除
            logger.info(f"Deleting existing data for JA: {ja_code}, Year: {year}, File type: {file_type}")
            existing_records = CSVData.query.filter_by(
                ja_code=ja_code,
                year=year,
                file_type=file_type
            ).delete()
            logger.info(f"Deleted {existing_records} existing records")
            
            # Process each row
            row_count = 0
            for index, row in df.iterrows():
                account_name = str(row[account_col]).strip()
                
                # Skip empty account names or rows that appear to be headers/totals
                if not account_name or account_name.lower() in ["合計", "total", "小計", "subtotal"]:
                    continue
                
                # 区分（カテゴリー）を取得
                category = None
                # 北海道BSのフォーマットでは区分が別の列にある場合がある
                if "区分" in df.columns:
                    category_col = "区分"
                    category_value = str(row[category_col]).strip()
                    if category_value and category_value not in ['nan', 'NaN', '']:
                        if "資産" in category_value:
                            category = "資産の部"
                        elif "負債" in category_value:
                            category = "負債の部"
                        elif "純資産" in category_value or "資本" in category_value:
                            category = "純資産の部"
                        elif "収益" in category_value or "収入" in category_value:
                            category = "収益の部"
                        elif "費用" in category_value or "支出" in category_value:
                            category = "費用の部"
                
                # 区分列から検出できなかった場合は勘定科目名から推測
                if category is None:
                    if "資産" in account_name:
                        category = "資産の部"
                    elif "負債" in account_name:
                        category = "負債の部"
                    elif "純資産" in account_name or "資本" in account_name:
                        category = "純資産の部"
                    elif "収益" in account_name or "収入" in account_name:
                        category = "収益の部"
                    elif "費用" in account_name or "支出" in account_name:
                        category = "費用の部"
                    # CF用の区分を追加
                    elif "営業活動" in account_name or "営業キャッシュ" in account_name:
                        category = "営業活動CF"
                    elif "投資活動" in account_name:
                        category = "投資活動CF"
                    elif "財務活動" in account_name:
                        category = "財務活動CF"
                
                # file_typeがcfの場合、デフォルトでCF区分を設定
                if file_type == "cf" and not category:
                    if "営業" in account_name:
                        category = "営業活動CF"
                    elif "投資" in account_name:
                        category = "投資活動CF"
                    elif "財務" in account_name:
                        category = "財務活動CF"
                    else:
                        category = "営業活動CF"  # デフォルト値
                
                # Get values
                current_value = 0
                previous_value = 0
                
                if current_col is not None:
                    try:
                        current_value_raw = row[current_col]
                        # 数値に変換する前に適切な処理を行う
                        if current_value_raw is None or str(current_value_raw).strip() == '':
                            current_value = 0
                        elif isinstance(current_value_raw, (int, float)):
                            current_value = float(current_value_raw)
                        else:
                            # カンマや空白を削除して数値に変換
                            current_value_str = str(current_value_raw).replace(',', '').strip()
                            # △記号をマイナス記号に変換
                            if '△' in current_value_str:
                                current_value_str = current_value_str.replace('△', '-')
                            if current_value_str and current_value_str != '0':
                                current_value = float(current_value_str)
                        logger.info(f"Row {index}, Account: {account_name}, Current Value: {current_value}")
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Error converting current value for {account_name}: {str(e)}, value: {row[current_col]}")
                        current_value = 0
                
                if previous_col is not None:
                    try:
                        previous_value_raw = row[previous_col]
                        # 数値に変換する前に適切な処理を行う
                        if previous_value_raw is None or str(previous_value_raw).strip() == '' or str(previous_value_raw) == 'nan':
                            previous_value = 0
                        elif isinstance(previous_value_raw, (int, float)):
                            previous_value = float(previous_value_raw)
                        else:
                            # カンマや空白を削除して数値に変換
                            previous_value_str = str(previous_value_raw).replace(',', '').strip()
                            # △記号をマイナス記号に変換
                            if '△' in previous_value_str:
                                previous_value_str = previous_value_str.replace('△', '-')
                            if previous_value_str and previous_value_str != '0':
                                previous_value = float(previous_value_str)
                        logger.info(f"Row {index}, Account: {account_name}, Previous Value: {previous_value}")
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Error converting previous value for {account_name}: {str(e)}, value: {row[previous_col]}")
                        previous_value = 0
                
                # Create database record
                csv_data = CSVData(
                    ja_code=ja_code,
                    year=year,
                    file_type=file_type,
                    row_number=index,
                    account_name=account_name,
                    category=category,
                    current_value=current_value,
                    previous_value=previous_value,
                    is_mapped=False,
                    created_at=datetime.utcnow()
                )
                
                db.session.add(csv_data)
                row_count += 1
            
            # Update JA record with available data
            ja = JA.query.filter_by(ja_code=ja_code).first()
            if ja:
                available_data = ja.available_data.split(',') if ja.available_data else []
                if file_type not in available_data:
                    available_data.append(file_type)
                    ja.available_data = ','.join(available_data)
                ja.last_updated = datetime.utcnow()
            else:
                # Create new JA record if it doesn't exist
                new_ja = JA(
                    ja_code=ja_code,
                    name=f"JA {ja_code}",  # Default name
                    prefecture="未設定",  # Default prefecture
                    year=year,
                    available_data=file_type,
                    last_updated=datetime.utcnow()
                )
                db.session.add(new_ja)
            
            db.session.commit()
            return True, f"Successfully processed {row_count} rows of data", row_count
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error processing file: {str(e)}")
            return False, f"Error processing file: {str(e)}", 0
    
    @staticmethod
    def validate_data(ja_code, year, file_type):
        """
        Validate the imported data for consistency and completeness
        
        Args:
            ja_code: JA code
            year: Financial year
            file_type: Type of financial statement (bs, pl, cf)
            
        Returns:
            tuple: (is_valid, validation_messages)
        """
        try:
            validation_messages = []
            
            # Get all CSV data for this JA, year, and file type
            data = CSVData.query.filter_by(
                ja_code=ja_code, 
                year=year, 
                file_type=file_type
            ).all()
            
            if not data:
                return False, ["No data found"]
            
            # Perform specific validations based on file type
            if file_type == "bs":
                # For Balance Sheet - validate assets = liabilities + equity
                total_assets = sum([d.current_value for d in data if d.category == "資産の部"])
                total_liabilities = sum([d.current_value for d in data if d.category == "負債の部"])
                total_equity = sum([d.current_value for d in data if d.category == "純資産の部"])
                
                assets_diff = abs(total_assets - (total_liabilities + total_equity))
                if assets_diff > 1:  # Allow small rounding difference
                    validation_messages.append(
                        f"Balance sheet equation doesn't balance: Assets ({total_assets}) ≠ "
                        f"Liabilities ({total_liabilities}) + Equity ({total_equity})"
                    )
            
            elif file_type == "pl":
                # For Profit & Loss - validate that revenues and expenses exist
                revenues = [d for d in data if d.category == "収益の部"]
                expenses = [d for d in data if d.category == "費用の部"]
                
                if not revenues:
                    validation_messages.append("No revenue items found in P&L statement")
                if not expenses:
                    validation_messages.append("No expense items found in P&L statement")
            
            elif file_type == "cf":
                # For Cash Flow - basic validation that there are operational CF items
                cf_categories = set(d.category for d in data if d.category)
                
                # 必須のCF区分があるか確認
                required_cf_categories = ["営業活動CF", "投資活動CF", "財務活動CF"]
                missing_categories = [cat for cat in required_cf_categories if cat not in cf_categories]
                
                if missing_categories:
                    validation_messages.append(
                        f"キャッシュフロー計算書に必要な区分がありません: {', '.join(missing_categories)}"
                    )
                
                # 営業活動CFのデータがあるか確認
                if not any(d.category == "営業活動CF" for d in data):
                    validation_messages.append("営業活動キャッシュフローの項目が見つかりません")
            
            # Check for duplicated account names
            account_names = [d.account_name for d in data]
            duplicates = {name for name in account_names if account_names.count(name) > 1}
            if duplicates:
                validation_messages.append(f"Duplicate account names found: {', '.join(duplicates)}")
            
            # Return validation results
            is_valid = len(validation_messages) == 0
            return is_valid, validation_messages
            
        except Exception as e:
            logger.error(f"Error validating data: {str(e)}")
            return False, [f"Error validating data: {str(e)}"]
    
    @staticmethod
    def get_unmapped_accounts(ja_code, year, file_type):
        """
        Get accounts that haven't been mapped to standard accounts
        重複を排除するため、勘定科目名でグループ化して最小のrow_numberのみを取得
        
        Args:
            ja_code: JA code
            year: Financial year
            file_type: Type of financial statement (bs, pl, cf)
            
        Returns:
            list: Unmapped accounts without duplicates
        """
        try:
            # SQLAlchemyでサブクエリを使用して勘定科目名ごとに最小のrow_numberを持つレコードのIDを取得
            from sqlalchemy import func
            
            # 未マッピングかつ同じJA、年度、ファイルタイプのレコードを取得
            # account_nameごとにグループ化して、各グループの最小row_numberを持つレコードのみを取得
            subquery = db.session.query(
                CSVData.account_name,
                func.min(CSVData.row_number).label('min_row')
            ).filter(
                CSVData.ja_code == ja_code,
                CSVData.year == year,
                CSVData.file_type == file_type,
                CSVData.is_mapped == False
            ).group_by(CSVData.account_name).subquery()
            
            # サブクエリを使用して元のレコードを取得
            unmapped = db.session.query(CSVData).join(
                subquery,
                db.and_(
                    CSVData.account_name == subquery.c.account_name,
                    CSVData.row_number == subquery.c.min_row
                )
            ).filter(
                CSVData.ja_code == ja_code,
                CSVData.year == year,
                CSVData.file_type == file_type,
                CSVData.is_mapped == False
            ).order_by(CSVData.row_number).all()
            
            return unmapped
        except Exception as e:
            logger.error(f"Error getting unmapped accounts: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return []
