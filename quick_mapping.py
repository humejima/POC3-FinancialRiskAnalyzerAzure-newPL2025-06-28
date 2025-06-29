"""
最も単純な完全一致マッピング実装。
このモジュールは直接Flaskルートから呼び出して使用します。
"""
import logging
from sqlalchemy.exc import SQLAlchemyError
from app import db
from models import CSVData, StandardAccount, AccountMapping

logger = logging.getLogger(__name__)

def quick_map_one_account(ja_code, year, file_type):
    """
    一つの勘定科目だけをマッピングします。
    エラーのリスクを最小限に抑えます。
    
    Args:
        ja_code: JA code
        year: Financial year (int)
        file_type: Type of financial statement (bs, pl, cf)
        
    Returns:
        dict: Operation result
    """
    try:
        # 未マッピングのCSVデータを1件だけ取得
        csv_data = db.session.query(CSVData).filter(
            CSVData.ja_code == ja_code,
            CSVData.year == year,
            CSVData.file_type == file_type,
            CSVData.is_mapped == False
        ).first()
        
        if not csv_data:
            return {
                "status": "no_data",
                "message": "マッピング対象の勘定科目がありません。"
            }
        
        logger.info(f"マッピング対象: {csv_data.account_name}")
        
        # 一致する標準勘定科目を検索
        std_account = db.session.query(StandardAccount).filter(
            StandardAccount.name == csv_data.account_name,
            StandardAccount.financial_statement == file_type
        ).first()
        
        if not std_account:
            return {
                "status": "no_match",
                "message": f"勘定科目 '{csv_data.account_name}' に一致する標準勘定科目がありません。"
            }
        
        logger.info(f"標準勘定科目一致: {std_account.name} (コード: {std_account.code})")
        
        # 既存のマッピングがないか確認
        existing = db.session.query(AccountMapping).filter(
            AccountMapping.ja_code == ja_code,
            AccountMapping.original_account_name == csv_data.account_name,
            AccountMapping.financial_statement == file_type
        ).first()
        
        if existing:
            # 既存のマッピングがある場合はCSVデータのフラグだけを更新
            csv_data.is_mapped = True
            db.session.commit()
            return {
                "status": "updated",
                "message": f"勘定科目 '{csv_data.account_name}' のマッピングフラグを更新しました。"
            }
        
        # 新しいマッピングを作成
        new_mapping = AccountMapping(
            ja_code=ja_code,
            original_account_name=csv_data.account_name,
            standard_account_code=std_account.code,
            standard_account_name=std_account.name,
            financial_statement=file_type,
            confidence=1.0,
            rationale="完全一致: 名称が標準勘定科目と一致しました"
        )
        
        db.session.add(new_mapping)
        csv_data.is_mapped = True
        db.session.commit()
        
        return {
            "status": "success",
            "message": f"勘定科目 '{csv_data.account_name}' を標準勘定科目 '{std_account.name}' にマッピングしました。"
        }
        
    except SQLAlchemyError as db_err:
        db.session.rollback()
        logger.error(f"データベースエラー: {str(db_err)}")
        return {
            "status": "db_error",
            "message": f"データベースエラー: {str(db_err)}"
        }
    except Exception as e:
        db.session.rollback()
        logger.error(f"マッピング中にエラーが発生しました: {str(e)}")
        return {
            "status": "error",
            "message": f"エラー: {str(e)}"
        }