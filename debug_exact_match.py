import os
import sys
import logging
import traceback
import json
from datetime import datetime

from app import db
from models import StandardAccount, CSVData, AccountMapping

# ログの設定
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def debug_exact_match(ja_code, year, file_type):
    """
    完全一致マッピングプロセスを最小限のコンポーネントでデバッグ
    
    Args:
        ja_code: JA code
        year: Financial year
        file_type: Type of financial statement (bs, pl, cf)
    """
    try:
        logger.info("=" * 50)
        logger.info(f"デバッグ開始: ja_code={ja_code}, year={year}, file_type={file_type}")
        
        # ステップ1: 対象の未マッピングCSVデータ数をカウント
        csv_count = db.session.query(CSVData).filter(
            CSVData.ja_code == ja_code,
            CSVData.year == year, 
            CSVData.file_type == file_type,
            CSVData.is_mapped == False
        ).count()
        logger.info(f"未マッピングデータ数: {csv_count}")
        
        # ステップ2: 標準勘定科目の数をカウント
        std_count = db.session.query(StandardAccount).filter(
            StandardAccount.financial_statement == file_type
        ).count()
        logger.info(f"標準勘定科目数: {std_count}")
        
        # ステップ3: 文字列の長さをチェック - 特に長い名前がないか
        long_names = db.session.query(CSVData.account_name, db.func.length(CSVData.account_name).label('name_length')).filter(
            CSVData.ja_code == ja_code,
            CSVData.year == year,
            CSVData.file_type == file_type,
            CSVData.is_mapped == False,
            db.func.length(CSVData.account_name) > 50
        ).all()
        if long_names:
            logger.info(f"異常に長い名前が見つかりました: {long_names}")
        
        # ステップ4: 既存のマッピングの数をカウント
        mapping_count = db.session.query(AccountMapping).filter(
            AccountMapping.ja_code == ja_code,
            AccountMapping.financial_statement == file_type
        ).count()
        logger.info(f"既存のマッピング数: {mapping_count}")
        
        # ステップ5: 完全一致する可能性のあるレコードをカウント（ただし、実行はまだしない）
        match_query = """
        SELECT COUNT(*) 
        FROM csv_data c
        JOIN standard_account s ON c.account_name = s.name
        WHERE c.ja_code = :ja_code
        AND c.year = :year
        AND c.file_type = :file_type
        AND c.is_mapped = false
        AND s.financial_statement = :file_type
        """
        potential_matches = db.session.execute(
            match_query, 
            {"ja_code": ja_code, "year": year, "file_type": file_type}
        ).scalar()
        logger.info(f"潜在的な完全一致の数: {potential_matches}")
        
        # 完全一致するレコードの詳細を確認
        if potential_matches > 0:
            detail_query = """
            SELECT c.account_name, s.name, s.code 
            FROM csv_data c
            JOIN standard_account s ON c.account_name = s.name
            WHERE c.ja_code = :ja_code
            AND c.year = :year
            AND c.file_type = :file_type
            AND c.is_mapped = false
            AND s.financial_statement = :file_type
            LIMIT 10
            """
            matches = db.session.execute(
                detail_query, 
                {"ja_code": ja_code, "year": year, "file_type": file_type}
            ).fetchall()
            logger.info(f"最初の10件の完全一致: {matches}")
        
        # ステップ6: マッピングの追加（実行はここで）
        if potential_matches > 0:
            # テスト用に最初の1件のみマッピング
            try:
                insert_query = """
                INSERT INTO account_mapping (ja_code, original_account_name, standard_account_code, 
                                         standard_account_name, financial_statement, confidence, rationale, created_at)
                SELECT 
                    c.ja_code, 
                    c.account_name, 
                    s.code, 
                    s.name, 
                    c.file_type, 
                    1.0, 
                    '完全一致: 名称が標準勘定科目と一致しました', 
                    CURRENT_TIMESTAMP
                FROM 
                    csv_data c
                JOIN 
                    standard_account s ON c.account_name = s.name
                WHERE 
                    c.ja_code = :ja_code
                    AND c.year = :year
                    AND c.file_type = :file_type
                    AND c.is_mapped = false
                    AND s.financial_statement = :file_type
                    AND NOT EXISTS (
                        SELECT 1 FROM account_mapping m 
                        WHERE m.ja_code = c.ja_code 
                        AND m.original_account_name = c.account_name
                        AND m.financial_statement = c.file_type
                    )
                LIMIT 1
                """
                db.session.execute(
                    insert_query, 
                    {"ja_code": ja_code, "year": year, "file_type": file_type}
                )
                
                # CSVデータの更新（1件のみ）
                update_query = """
                UPDATE csv_data c
                SET is_mapped = true
                WHERE 
                    c.ja_code = :ja_code
                    AND c.year = :year
                    AND c.file_type = :file_type
                    AND c.is_mapped = false
                    AND EXISTS (
                        SELECT 1 FROM account_mapping m 
                        WHERE m.ja_code = c.ja_code 
                        AND m.original_account_name = c.account_name
                        AND m.financial_statement = c.file_type
                    )
                LIMIT 1
                """
                db.session.execute(
                    update_query, 
                    {"ja_code": ja_code, "year": year, "file_type": file_type}
                )
                
                # コミット
                db.session.commit()
                logger.info("テスト用マッピングが正常に追加されました")
            except Exception as e:
                db.session.rollback()
                logger.error(f"テスト用マッピング追加中にエラー: {str(e)}")
                logger.error(traceback.format_exc())
        
        logger.info("デバッグ処理完了")
        logger.info("=" * 50)
        
        return {"status": "success", "csv_count": csv_count, "std_count": std_count, "potential_matches": potential_matches}
    
    except Exception as e:
        logger.error(f"デバッグ中に予期しないエラー: {str(e)}")
        logger.error(traceback.format_exc())
        return {"status": "error", "message": str(e)}

# コマンドラインから実行する場合
if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python debug_exact_match.py JA_CODE YEAR FILE_TYPE")
        sys.exit(1)
    
    ja_code = sys.argv[1]
    year = int(sys.argv[2])
    file_type = sys.argv[3]
    
    result = debug_exact_match(ja_code, year, file_type)
    print(json.dumps(result, indent=2))