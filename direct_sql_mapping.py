"""
最も基本的なSQL直接実行によるマッピング実装。
他のすべての方法が失敗した場合の緊急対応策。
"""
import logging
import os
import psycopg2
from psycopg2.extras import DictCursor

logger = logging.getLogger(__name__)

def execute_direct_mapping(ja_code, year, file_type, max_items=20):
    """
    SQLコマンドを直接実行してマッピングを実行する最後の手段。
    すべてのORM抽象化をバイパスすることで、一般的なORM関連の問題を回避します。
    
    完全一致だけでなく、部分一致や類似した文字列も検出して処理することができます。
    
    Args:
        ja_code: JA code
        year: Financial year (int)
        file_type: Type of financial statement (bs, pl, cf)
        max_items: 一度に処理する最大件数 (デフォルト: 20件)
        
    Returns:
        dict: 処理結果
    """
    # パラメータのログ出力とパラメータの検証
    logger.info(f"⭐ 直接SQLマッピング開始: JA={ja_code}, 年度={year}, ファイルタイプ={file_type}, 最大処理数={max_items}")
    
    # 結果を格納する辞書を初期化
    response_data = {
        "status": "success",
        "message": "",
        "ja_code": ja_code,
        "year": year,
        "file_type": file_type,
        "max_items": max_items,
        "total_processed": 0,
        "mapped_count": 0,
        "unmapped_count": 0,
        "total_exact_match": 0
    }
    
    # パラメータの検証
    if not ja_code or not year or not file_type:
        error_msg = f"必須パラメータが不足しています: JA={ja_code}, 年度={year}, ファイルタイプ={file_type}"
        logger.error(f"❌ {error_msg}")
        response_data["status"] = "error"
        response_data["message"] = error_msg
        return response_data
    
    if not isinstance(max_items, int) or max_items <= 0:
        max_items = 20  # デフォルト値を設定
        logger.info(f"最大処理数が無効なため、デフォルト値を使用: {max_items}")
        
    # 完全一致マッピングの場合、バッチサイズを大きく設定する
    # 部分一致またはAI処理を使用する場合のみ必要に応じて制限する
    using_partial_match = False
    is_using_openai = False
    is_exact_match_mode = True  # デフォルトは完全一致モード
    
    # 完全一致の場合は常に大きなバッチサイズを使用（最大40件）
    # この関数は主に完全一致マッピングに使用されるため、デフォルトで40件に設定
    if max_items < 40:
        max_items = 40
        logger.info(f"バッチサイズを40件に設定します")
    
    # OpenAI APIは部分一致モードでのみ使用される可能性があるので、
    # ここではOpenAI APIの有無をチェックするだけで、バッチサイズには影響させない
    try:
        # OpenAI APIは使用しない（安全策）
        is_using_openai = False
        logger.info("OpenAI APIは使用しません（安定性向上のため）")
    except:
        logger.info("OpenAI APIは利用できません")
    conn = None
    try:
        # 直接データベース接続を確立
        db_url = os.environ.get("DATABASE_URL")
        if not db_url:
            return {
                "status": "error",
                "message": "DATABASE_URL environment variable is not set"
            }
            
        conn = psycopg2.connect(db_url)
        conn.autocommit = True  # オートコミットに設定（トランザクションを使わない）
        logger.info(f"データベース接続確立: autocommit={conn.autocommit}")
        
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            # 1. 完全一致する勘定科目をカウント
            logger.info(f"🔍 完全一致勘定科目の検索開始: JA={ja_code}, 年度={year}, ファイルタイプ={file_type}")
            
            count_exact_query = """
                SELECT COUNT(*) 
                FROM csv_data c
                JOIN standard_account s ON c.account_name = s.name
                WHERE c.ja_code = %s
                AND c.year = %s
                AND c.file_type = %s
                AND c.is_mapped = false
                AND s.financial_statement = %s
            """
            logger.info(f"💾 完全一致クエリ: {count_exact_query}")
            
            try:
                cursor.execute(count_exact_query, (ja_code, year, file_type, file_type))
                logger.info("✅ 完全一致カウントクエリ実行完了")
            except Exception as e:
                logger.error(f"❌ 完全一致カウントクエリ実行エラー: {str(e)}")
                raise
            
            # 結果取得
            try:
                fetch_result = cursor.fetchone()
                match_count = fetch_result[0] if fetch_result else 0
                logger.info(f"💯 完全一致する勘定科目数: {match_count}")
            except Exception as e:
                logger.error(f"❌ 完全一致カウント結果取得エラー: {str(e)}")
                match_count = 0
                
            # 結果格納
            response_data["total_exact_match"] = match_count
            
            # 完全一致がない場合は、部分一致を試みる
            if match_count == 0:
                logger.info("完全一致がないため、部分一致の検索を開始します")
                # 部分一致ではOpenAI APIを使う可能性があるため、バッチサイズを調整
                if is_using_openai and max_items > 5:
                    max_items = 5
                    logger.info(f"部分一致でOpenAI APIを使用するため、バッチサイズを5件に制限します")

                # 未マッピングのCSVデータを取得
                cursor.execute("""
                    SELECT COUNT(*)
                    FROM csv_data
                    WHERE ja_code = %s
                    AND year = %s
                    AND file_type = %s
                    AND is_mapped = false
                """, (ja_code, year, file_type))
                
                result = cursor.fetchone()
                unmapped_count = result[0] if result else 0
                
                if unmapped_count == 0:
                    return {
                        "status": "no_data",
                        "message": "未マッピングの勘定科目がありません。"
                    }
                    
                logger.info(f"未マッピングの勘定科目数: {unmapped_count}")
                
                # 未マッピングのデータを取得して一つずつ処理
                # 処理対象の件数をログに出力
                logger.info(f"部分一致マッピングを実行します（バッチサイズ: {max_items}件）")
                
                cursor.execute("""
                    SELECT id, account_name
                    FROM csv_data
                    WHERE ja_code = %s
                    AND year = %s
                    AND file_type = %s
                    AND is_mapped = false
                    LIMIT %s
                """, (ja_code, year, file_type, max_items))
                
                # 取得した件数をログに出力
                unmapped_accounts = cursor.fetchall()
                logger.info(f"処理対象件数: {len(unmapped_accounts)}件")
                
                # 標準勘定科目を一度に取得（効率化のため）
                cursor.execute("""
                    SELECT code, name
                    FROM standard_account
                    WHERE financial_statement = %s
                """, (file_type,))
                
                std_accounts = cursor.fetchall()
                
                # 部分一致処理の結果
                partial_results = []
                partial_mapped_count = 0
                
                for account in unmapped_accounts:
                    csv_id = account['id']
                    account_name = account['account_name']
                    
                    # 勘定科目名の変換パターンを追加
                    test_names = [account_name]
                    # 貯金⇒預金の変換
                    if "貯金" in account_name:
                        test_names.append(account_name.replace("貯金", "預金"))
                    if "貯" in account_name:
                        test_names.append(account_name.replace("貯", "預"))
                    # その他の一般的な変換パターン
                    if "使用料" in account_name:
                        test_names.append(account_name.replace("使用料", "利用料"))
                    if "未収金" in account_name:
                        test_names.append(account_name.replace("未収金", "未収入金"))
                    if "前受金" in account_name:
                        test_names.append(account_name.replace("前受金", "前受収益"))
                        
                    # 特定のキーワードによる部分一致マッピング
                    important_keywords = {
                        "現金": "1010",  # 現金
                        "預金": "1020",  # 預け金
                        "貯金": "1020",  # 預け金（貯金は預金と同等）
                        "出資": "1962",  # 外部出資（系統出資なども含む）
                        "有価証券": "1600",  # 有価証券
                        "貸付金": "1700",  # 貸出金
                        "土地": "2030",  # 土地
                        "建物": "2010",  # 建物
                        "機械": "2040",  # 機械及び装置
                    }
                    
                    # 最も良いマッチを探す
                    best_match = None
                    best_score = 0
                    
                    # 重要キーワードによる直接マッピング
                    for keyword, code in important_keywords.items():
                        if keyword in account_name:
                            for std in std_accounts:
                                if std['code'] == code:
                                    logger.info(f"キーワード「{keyword}」による直接マッピング: {account_name} -> {std['name']} (コード: {code})")
                                    best_match = std
                                    best_score = 0.8  # キーワードマッチは高い信頼度を与える
                                    break
                            
                    # 完全一致と部分一致をチェック
                    for std in std_accounts:
                        std_code = std['code']
                        std_name = std['name']
                        
                        # 完全一致チェック（最優先）
                        for test_name in test_names:
                            if test_name == std_name:
                                best_match = std
                                best_score = 1.0
                                break
                        
                        if best_score == 1.0:
                            break
                            
                        # 部分一致チェック（完全一致がなければこちらを使用）
                        for test_name in test_names:
                            # 双方向の部分一致チェック
                            if std_name in test_name or test_name in std_name:
                                base_score = min(len(std_name), len(test_name)) / max(len(std_name), len(test_name))
                                
                                # キーワードボーナス（キーワードが複数一致するとより高いスコアに）
                                words1 = set(test_name.split())
                                words2 = set(std_name.split())
                                common_words = words1.intersection(words2)
                                keyword_bonus = len(common_words) * 0.1
                                
                                # 最終スコア = 基本スコア + キーワードボーナス（最大1.0）
                                score = min(1.0, base_score + keyword_bonus)
                                
                                if score > best_score:
                                    best_match = std
                                    best_score = score
                                    
                        # 特定パターンのボーナス
                        if std_name in account_name and len(std_name) > 2:  # 短すぎる文字列は除外
                            score = 0.7  # 標準科目名がアカウント名に含まれる場合は高いスコア
                            if score > best_score:
                                best_match = std
                                best_score = score
                    
                    # 十分な類似度があれば処理（しきい値を下げて0.4以上で許可）
                    if best_match and best_score >= 0.4:  # 40%以上の類似度
                        std_code = best_match['code']
                        std_name = best_match['name']
                        
                        # 既存のマッピングを確認
                        cursor.execute("""
                            SELECT id FROM account_mapping 
                            WHERE ja_code = %s
                            AND original_account_name = %s
                            AND financial_statement = %s
                        """, (ja_code, account_name, file_type))
                        
                        existing = cursor.fetchone()
                        
                        if not existing:
                            # 新しいマッピングを挿入
                            cursor.execute("""
                                INSERT INTO account_mapping 
                                (ja_code, original_account_name, standard_account_code, 
                                 standard_account_name, financial_statement, confidence, rationale)
                                VALUES (%s, %s, %s, %s, %s, %s, %s)
                            """, (
                                ja_code, account_name, std_code, std_name, 
                                file_type, best_score, f"類似度マッピング: 類似度 {best_score:.2f}"
                            ))
                            
                            # CSVデータのフラグを更新
                            cursor.execute("""
                                UPDATE csv_data SET is_mapped = true
                                WHERE id = %s
                            """, (csv_id,))
                            
                            partial_results.append({
                                "id": csv_id,
                                "name": account_name,
                                "std_name": std_name,
                                "confidence": best_score,
                                "action": "inserted"
                            })
                            
                            partial_mapped_count += 1
                            
                if partial_mapped_count > 0:
                    # 変更を確定
                    conn.commit()
                    logger.info(f"部分一致によるマッピング完了: {partial_mapped_count}件")
                    
                    return {
                        "status": "success",
                        "mapped": partial_mapped_count,
                        "total": unmapped_count,
                        "message": f"類似度マッピング: {partial_mapped_count}件のマッピングを作成しました（残り{unmapped_count - partial_mapped_count}件）",
                        "details": partial_results
                    }
                else:
                    # 処理したものの、マッピングができなかった場合は具体的な情報を提供
                    return {
                        "status": "no_match",
                        "message": "類似した勘定科目が見つかりませんでした。",
                        "total": unmapped_count,
                        "remaining": unmapped_count,
                        "mapped": 0
                    }
            
            # 2. 完全一致する勘定科目の総数を確認
            cursor.execute("""
                SELECT COUNT(*)
                FROM csv_data c
                JOIN standard_account s ON c.account_name = s.name
                WHERE c.ja_code = %s
                AND c.year = %s
                AND c.file_type = %s
                AND c.is_mapped = false
                AND s.financial_statement = %s
            """, (ja_code, year, file_type, file_type))
            
            result = cursor.fetchone()
            total_exact_match_count = result[0] if result else 0
            logger.info(f"完全一致するマッピング対象の総数: {total_exact_match_count}件")
            
            # 3. 完全一致する勘定科目を指定した最大件数まで取得
            logger.info(f"バッチサイズ: {max_items}件まで取得します")
            cursor.execute("""
                SELECT c.id, c.account_name, s.code, s.name
                FROM csv_data c
                JOIN standard_account s ON c.account_name = s.name
                WHERE c.ja_code = %s
                AND c.year = %s
                AND c.file_type = %s
                AND c.is_mapped = false
                AND s.financial_statement = %s
                LIMIT %s
            """, (ja_code, year, file_type, file_type, max_items))
            
            matches = cursor.fetchall()
            
            # 処理結果を記録
            results = []
            mapped_count = 0
            
            # 未マッピングの総数を取得（この時点で再度確認）
            cursor.execute("""
                SELECT COUNT(*)
                FROM csv_data
                WHERE ja_code = %s
                AND year = %s
                AND file_type = %s
                AND is_mapped = false
            """, (ja_code, year, file_type))
            
            result = cursor.fetchone()
            unmapped_count = result[0] if result else 0
            logger.info(f"未マッピングの勘定科目総数: {unmapped_count}件")
            
            for match in matches:
                csv_id = match['id']
                account_name = match['account_name']
                std_code = match['code']
                std_name = match['name']
                
                logger.info(f"処理: CSV ID={csv_id}, 勘定科目名={account_name}, 標準コード={std_code}")
                
                # 3. 既存のマッピングを確認
                cursor.execute("""
                    SELECT id FROM account_mapping 
                    WHERE ja_code = %s
                    AND original_account_name = %s
                    AND financial_statement = %s
                """, (ja_code, account_name, file_type))
                
                existing = cursor.fetchone()
                
                if existing:
                    # 既存マッピングがある場合はCSVデータのフラグのみ更新
                    cursor.execute("""
                        UPDATE csv_data SET is_mapped = true
                        WHERE id = %s
                    """, (csv_id,))
                    
                    results.append({
                        "id": csv_id,
                        "name": account_name,
                        "action": "updated"
                    })
                else:
                    # 新しいマッピングを挿入
                    cursor.execute("""
                        INSERT INTO account_mapping 
                        (ja_code, original_account_name, standard_account_code, 
                         standard_account_name, financial_statement, confidence, rationale)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (
                        ja_code, account_name, std_code, std_name, 
                        file_type, 1.0, "完全一致: 名称が標準勘定科目と一致しました"
                    ))
                    
                    # CSVデータのフラグを更新
                    cursor.execute("""
                        UPDATE csv_data SET is_mapped = true
                        WHERE id = %s
                    """, (csv_id,))
                    
                    results.append({
                        "id": csv_id,
                        "name": account_name,
                        "action": "inserted",
                        "standard_code": std_code
                    })
                
                mapped_count += 1
            
            # 変更を確定
            conn.commit()
            logger.info(f"直接SQL実行によるマッピング完了: {mapped_count}件")
            
            # マッピング後に標準勘定科目残高を自動的に作成
            balance_count = 0
            if mapped_count > 0:
                try:
                    # importに失敗した場合のエラーを検知するため遅延インポート
                    from create_account_balances import create_standard_account_balances
                    balance_count = create_standard_account_balances(ja_code, year, file_type)
                    logger.info(f"マッピング後に{balance_count}件の標準勘定科目残高を作成しました")
                    
                    # マッピングと残高作成両方成功
                    # 残り件数を計算（未処理件数 = 元のマッチ数 - 処理した件数）
                    # 再度未マッピング件数を確認（正確なカウントのため）
                    cursor.execute("""
                        SELECT COUNT(*)
                        FROM csv_data
                        WHERE ja_code = %s
                        AND year = %s
                        AND file_type = %s
                        AND is_mapped = false
                    """, (ja_code, year, file_type))
                    
                    result = cursor.fetchone()
                    remaining_count = result[0] if result else 0
                    
                    # 処理結果の統合
                    response_data.update({
                        "status": "success",
                        "mapped": mapped_count,
                        "mapped_count": mapped_count,
                        "unmapped_count": remaining_count,
                        "balances": balance_count,
                        "total": unmapped_count,
                        "remaining": remaining_count,
                        "message": f"{mapped_count}件のマッピングを作成し、{balance_count}件の残高データを更新しました（残り: {remaining_count}件、バッチサイズ: {max_items}件）",
                        "details": results
                    })
                    
                    # 詳細なログ出力
                    logger.info(f"✅ 処理完了: 合計={match_count}, マッピング成功={mapped_count}, 残高データ更新={balance_count}")
                    
                    return response_data
                except Exception as balance_err:
                    logger.error(f"残高作成中にエラー: {str(balance_err)}")
                    # マッピング成功、残高作成失敗
                    # 再度未マッピング件数を確認（正確なカウントのため）
                    cursor.execute("""
                        SELECT COUNT(*)
                        FROM csv_data
                        WHERE ja_code = %s
                        AND year = %s
                        AND file_type = %s
                        AND is_mapped = false
                    """, (ja_code, year, file_type))
                    
                    result = cursor.fetchone()
                    remaining_count = result[0] if result else 0
                    
                    # 処理結果の統合
                    response_data.update({
                        "status": "partial_success",
                        "mapped": mapped_count,
                        "mapped_count": mapped_count,
                        "unmapped_count": remaining_count,
                        "total": unmapped_count,
                        "remaining": remaining_count,
                        "message": f"{mapped_count}件のマッピングを作成しましたが、残高データの更新中にエラーが発生しました: {str(balance_err)}（残り: {remaining_count}件、バッチサイズ: {max_items}件）",
                        "details": results
                    })
                    
                    # 詳細なログ出力
                    logger.info(f"⚠️ 処理部分完了: 合計={match_count}, マッピング成功={mapped_count}, 残高データ更新=失敗")
                    
                    return response_data
            else:
                # マッピングなし
                # 処理結果の統合
                response_data.update({
                    "status": "success",
                    "mapped": 0,
                    "total": match_count,
                    "message": f"新たなマッピングはありませんでした（残り{match_count}件）",
                    "details": results
                })
                
                # 詳細なログ出力
                logger.info(f"⭐ 処理完了: 合計={match_count}, マッピング成功=0, マッピングなし={match_count}")
                
                return response_data
            
    except Exception as e:
        logger.error(f"直接SQL実行中にエラー: {str(e)}")
        if conn:
            try:
                conn.rollback()
            except:
                pass
        # エラー情報を詳細に記録
        error_msg = f"エラー: {str(e)}"
        logger.error(f"❌ {error_msg}")
        
        # エラー応答を構築
        response_data.update({
            "status": "error",
            "message": error_msg,
            "error_type": type(e).__name__,
            "ja_code": ja_code,
            "year": year,
            "file_type": file_type
        })
        
        return response_data
    finally:
        if conn:
            try:
                conn.close()
                logger.info("データベース接続を閉じました")
            except:
                pass