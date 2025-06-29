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

def simple_exact_match(ja_code, year, file_type, batch_size=10):
    """
    最もシンプルな完全一致マッピング実装。
    一度に処理するレコード数を制限して、メモリ使用量とトランザクション時間を最小化。
    
    Args:
        ja_code: JA code
        year: Financial year
        file_type: Type of financial statement (bs, pl, cf)
        batch_size: 一度に処理するレコード数
        
    Returns:
        dict: Mapping result statistics
    """
    total_mapped = 0
    
    try:
        logger.info(f"シンプル完全一致マッピング開始: ja_code={ja_code}, year={year}, file_type={file_type}")
        
        # Step 1: 未マッピングデータのIDだけを取得
        unmapped_ids_query = """
        SELECT c.id
        FROM csv_data c
        JOIN standard_account s ON c.account_name = s.name
        WHERE 
            c.ja_code = :ja_code
            AND c.year = :year
            AND c.file_type = :file_type
            AND c.is_mapped = false
            AND s.financial_statement = :file_type
        """
        
        all_unmapped_ids = [
            row[0] for row in db.session.execute(
                unmapped_ids_query,
                {"ja_code": ja_code, "year": year, "file_type": file_type}
            ).fetchall()
        ]
        
        total_to_map = len(all_unmapped_ids)
        logger.info(f"マッピング対象のレコード数: {total_to_map}")
        
        if total_to_map == 0:
            return {
                "status": "success",
                "mapped": 0,
                "message": "マッピング対象のレコードはありません"
            }
        
        # Step 2: バッチで処理
        for i in range(0, total_to_map, batch_size):
            batch_ids = all_unmapped_ids[i:i+batch_size]
            
            try:
                # 各レコードを個別に処理
                for csv_id in batch_ids:
                    try:
                        # 1. CSVデータを取得
                        csv_record = db.session.query(CSVData).filter(CSVData.id == csv_id).first()
                        if not csv_record or csv_record.is_mapped:
                            continue
                        
                        # 2. 対応する標準勘定科目を取得
                        std_account = db.session.query(StandardAccount).filter(
                            StandardAccount.name == csv_record.account_name,
                            StandardAccount.financial_statement == file_type
                        ).first()
                        
                        if not std_account:
                            continue
                        
                        # 3. 既存のマッピングをチェック
                        existing = db.session.query(AccountMapping).filter(
                            AccountMapping.ja_code == ja_code,
                            AccountMapping.original_account_name == csv_record.account_name,
                            AccountMapping.financial_statement == file_type
                        ).first()
                        
                        if existing:
                            # 既存マッピングがあれば、CSVデータだけを更新
                            csv_record.is_mapped = True
                        else:
                            # 新しいマッピングを作成
                            new_mapping = AccountMapping(
                                ja_code=ja_code,
                                original_account_name=csv_record.account_name,
                                standard_account_code=std_account.code,
                                standard_account_name=std_account.name,
                                financial_statement=file_type,
                                confidence=1.0,
                                rationale="完全一致: 名称が標準勘定科目と一致しました"
                            )
                            db.session.add(new_mapping)
                            
                            # CSVデータを更新
                            csv_record.is_mapped = True
                        
                        total_mapped += 1
                        
                    except Exception as record_error:
                        logger.error(f"レコードID {csv_id} の処理中にエラー: {str(record_error)}")
                        # 個別のレコードエラーは無視して続行
                        continue
                
                # バッチごとにコミット
                db.session.commit()
                logger.info(f"バッチ処理完了: {len(batch_ids)}件処理, 累計 {total_mapped}件マッピング完了")
                
            except Exception as batch_error:
                db.session.rollback()
                logger.error(f"バッチ処理中にエラー: {str(batch_error)}")
                logger.error(traceback.format_exc())
                # バッチ処理のエラーがあっても、次のバッチは処理する
        
        return {
            "status": "success",
            "total": total_to_map,
            "mapped": total_mapped,
            "message": f"完全一致マッピングが完了しました: {total_mapped}件マッピング完了"
        }
        
    except Exception as e:
        logger.error(f"シンプル完全一致マッピング中にエラー: {str(e)}")
        logger.error(traceback.format_exc())
        return {
            "status": "error",
            "message": f"エラーが発生しました: {str(e)}"
        }

# コマンドラインから実行する場合
if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python simple_exact_match.py JA_CODE YEAR FILE_TYPE [BATCH_SIZE]")
        sys.exit(1)
    
    ja_code = sys.argv[1]
    year = int(sys.argv[2])
    file_type = sys.argv[3]
    batch_size = int(sys.argv[4]) if len(sys.argv) > 4 else 10
    
    result = simple_exact_match(ja_code, year, file_type, batch_size)
    print(json.dumps(result, indent=2))