"""
バッチ処理によるマッピング実装。
このモジュールは直接Flaskルートから呼び出して使用します。
デフォルトでは40件ずつ処理しますが、必要に応じてバッチサイズを調整できます。
"""
import logging
import traceback
from sqlalchemy.exc import SQLAlchemyError
from app import db
from models import CSVData, StandardAccount, AccountMapping

logger = logging.getLogger(__name__)

def batch_map_accounts(ja_code, year, file_type, batch_size=40):
    """
    一度に複数の勘定科目をマッピングします。
    バッチ処理でメモリ使用量を抑えつつ、処理速度を向上させます。
    AI支援マッピングを自動的に使用し、失敗した場合のみ従来の完全一致マッピングにフォールバックします。
    
    Args:
        ja_code: JA code
        year: Financial year (int)
        file_type: Type of financial statement (bs, pl, cf)
        batch_size: 一度に処理する件数（デフォルト: 40件）
        
    Returns:
        dict: Operation result
    """
    try:
        # AI支援マッピングを試行
        try:
            logger.info(f"AI支援マッピングを開始します（JA={ja_code}, 年度={year}, タイプ={file_type}）")
            from ai_account_mapper import auto_map_accounts
            
            # AI支援マッピングを実行
            ai_result = auto_map_accounts(
                ja_code=ja_code,
                year=year,
                file_type=file_type,
                requested_tasks=["exact_match", "ai_mapping", "string_similarity"],
                batch_size=batch_size
            )
            
            if isinstance(ai_result, dict) and ai_result.get("status") == "success":
                mapped_count = ai_result.get("mapped_count", 0)
                logger.info(f"AI支援マッピング成功: {mapped_count}件のマッピングを作成しました")
                
                # 残りの未マッピング件数を取得
                remaining_count = db.session.query(CSVData).filter(
                    CSVData.ja_code == ja_code,
                    CSVData.year == year,
                    CSVData.file_type == file_type,
                    CSVData.is_mapped == False
                ).count()
                
                # 型チェックとキャスト
                mapped_count = int(mapped_count) if mapped_count is not None else 0
                remaining_count = int(remaining_count) if remaining_count is not None else 0
                
                return {
                    "status": "success",
                    "message": f"AIマッピング完了: {mapped_count}件のマッピングを作成しました（未処理: {remaining_count}件）",
                    "mapped": mapped_count,
                    "total": mapped_count + remaining_count,
                    "unmapped": remaining_count
                }
            
            logger.warning(f"AI支援マッピングが失敗または未実行: {ai_result}")
            logger.warning("従来の完全一致マッピングにフォールバックします")
        except Exception as e:
            logger.error(f"AI支援マッピングエラー: {str(e)}")
            logger.error(traceback.format_exc())
            logger.warning("従来の完全一致マッピングを実行します")
        
        # ここから従来の完全一致マッピングを実行（AIマッピングが失敗した場合）
        # 対象となる未マッピングCSVデータのIDを取得（最大batch_size件まで）
        query = db.session.query(CSVData.id, CSVData.account_name).filter(
            CSVData.ja_code == ja_code,
            CSVData.year == year,
            CSVData.file_type == file_type,
            CSVData.is_mapped == False
        ).limit(batch_size)
        
        target_csv_data = query.all()
        
        if not target_csv_data:
            return {
                "status": "no_data",
                "message": "マッピング対象の勘定科目がありません。"
            }
        
        logger.info(f"従来の完全一致マッピング対象件数: {len(target_csv_data)}件")
        
        # 標準勘定科目名を取得してメモリに保持（パフォーマンス向上）
        std_accounts = db.session.query(StandardAccount).filter(
            StandardAccount.financial_statement == file_type
        ).all()
        
        # 名前から標準勘定科目を素早く検索できるよう辞書化
        std_account_dict = {acct.name: acct for acct in std_accounts}
        
        # 各CSVデータに対するマッピング結果を記録
        results = {
            "total": len(target_csv_data),
            "mapped": 0,
            "no_match": 0,
            "details": []
        }
        
        # トランザクション開始
        for csv_id, account_name in target_csv_data:
            try:
                # 対応する標準勘定科目を検索
                std_account = std_account_dict.get(account_name)
                
                if not std_account:
                    # 一致する標準勘定科目がない場合
                    results["no_match"] += 1
                    results["details"].append({
                        "id": csv_id,
                        "name": account_name,
                        "status": "no_match"
                    })
                    continue
                
                # CSVデータレコードを取得
                csv_data = db.session.query(CSVData).filter(CSVData.id == csv_id).first()
                
                # CSVデータが見つからない場合はスキップ
                if not csv_data:
                    logger.warning(f"CSV データが見つかりません: ID {csv_id}")
                    continue
                
                # 既存のマッピングをチェック
                existing = db.session.query(AccountMapping).filter(
                    AccountMapping.ja_code == ja_code,
                    AccountMapping.original_account_name == account_name,
                    AccountMapping.financial_statement == file_type
                ).first()
                
                if existing:
                    # 既存のマッピングがある場合はCSVデータのフラグだけを更新
                    csv_data.is_mapped = True
                    csv_data.standard_account_code = existing.standard_account_code
                    results["mapped"] += 1
                    results["details"].append({
                        "id": csv_id,
                        "name": account_name,
                        "status": "updated",
                        "standard_code": existing.standard_account_code,
                        "standard_name": existing.standard_account_name
                    })
                else:
                    # 新しいマッピングを作成（属性ごとに設定）
                    new_mapping = AccountMapping()
                    new_mapping.ja_code = ja_code
                    new_mapping.year = year  # 年度も設定（重要）
                    new_mapping.original_account_name = account_name
                    new_mapping.standard_account_code = std_account.code
                    new_mapping.standard_account_name = std_account.name
                    new_mapping.financial_statement = file_type
                    new_mapping.confidence = 1.0
                    new_mapping.rationale = "完全一致: 名称が標準勘定科目と一致しました"
                    new_mapping.mapping_source = "exact_match"
                    
                    db.session.add(new_mapping)
                    csv_data.is_mapped = True
                    csv_data.standard_account_code = std_account.code
                    results["mapped"] += 1
                    results["details"].append({
                        "id": csv_id,
                        "name": account_name,
                        "status": "new_mapping",
                        "standard_code": std_account.code,
                        "standard_name": std_account.name
                    })
            
            except Exception as e:
                logger.error(f"CSV ID: {csv_id}, 勘定科目名: {account_name} の処理中にエラー: {str(e)}")
                results["details"].append({
                    "id": csv_id,
                    "name": account_name,
                    "status": "error",
                    "error": str(e)
                })
        
        # 一括コミット
        db.session.commit()
        
        # マッピング後に標準勘定科目残高を自動的に作成
        if results["mapped"] > 0:
            try:
                from create_account_balances import create_standard_account_balances
                balance_count = create_standard_account_balances(ja_code, year, file_type)
                logger.info(f"マッピング後に{balance_count}件の標準勘定科目残高を作成しました")
                
                # 成功メッセージ（残高作成成功）
                message = f'{results["mapped"]}件のマッピングを作成し、{balance_count}件の残高データを更新しました。{results["no_match"]}件は一致する標準勘定科目が見つかりませんでした。'
            except Exception as balance_err:
                logger.error(f"残高作成中にエラー: {str(balance_err)}")
                # 成功メッセージ（残高作成失敗）
                message = f'{results["mapped"]}件のマッピングを作成しましたが、残高データの更新中にエラーが発生しました: {str(balance_err)}。{results["no_match"]}件は一致する標準勘定科目が見つかりませんでした。'
        else:
            # 成功メッセージ（マッピングなし）
            message = f'新たなマッピングはありませんでした。{results["no_match"]}件は一致する標準勘定科目が見つかりませんでした。'
        
        return {
            "status": "success",
            "message": message,
            "mapped": results["mapped"],
            "no_match": results["no_match"],
            "total": results["total"],
            "details": results["details"]
        }
        
    except SQLAlchemyError as db_err:
        db.session.rollback()
        logger.error(f"データベースエラー: {str(db_err)}")
        logger.error(traceback.format_exc())
        return {
            "status": "db_error",
            "message": f"データベースエラー: {str(db_err)}"
        }
    except Exception as e:
        db.session.rollback()
        logger.error(f"マッピング中にエラーが発生しました: {str(e)}")
        logger.error(traceback.format_exc())
        return {
            "status": "error",
            "message": f"エラー: {str(e)}"
        }