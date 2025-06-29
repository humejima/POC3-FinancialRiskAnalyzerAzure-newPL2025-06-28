"""
AIマッピング機能のエンドポイントを直接修正するためのスクリプト。
このファイルを実行すると、routes.pyのai_mapエンドポイントが修正されます。
"""
import os
import logging
import sys

# 詳細なログ出力を有効化
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                   stream=sys.stdout)
logger = logging.getLogger(__name__)

def create_routes_patch():
    """routes.pyのai_mapエンドポイントにパッチを適用する"""
    patch_content = """
@app.route('/ai_map', methods=['GET', 'POST'])
def ai_map():
    """AIマッピングを実行（文字列類似度のみ使用）"""
    try:
        # POSTとGETのどちらからでもパラメータを取得できるようにする
        ja_code = request.form.get('ja_code') or request.args.get('ja_code') or session.get('selected_ja_code')
        year_str = request.form.get('year') or request.args.get('year') or str(session.get('selected_year'))
        file_type = request.form.get('file_type') or request.args.get('file_type', 'cf')
        
        logger.info(f"AI mapping received parameters: ja_code={ja_code}, year={year_str}, file_type={file_type}")
        
        if not ja_code or not year_str or not file_type:
            flash('必須項目が不足しています。JAコード、年度、ファイルタイプが必要です。', 'danger')
            return redirect(url_for('mapping', file_type=file_type or 'cf'))
        
        try:
            year = int(year_str)
        except (ValueError, TypeError) as e:
            logger.error(f"Parameter conversion error: {str(e)}")
            flash('年度は整数で指定してください。', 'danger')
            return redirect(url_for('mapping', file_type=file_type))
        
        logger.info(f"AI mapping started for JA: {ja_code}, year: {year}, file_type: {file_type}")
        
        # 利用可能な標準勘定科目の数をチェック
        standard_accounts_count = StandardAccount.query.filter_by(financial_statement=file_type).count()
        logger.info(f"Standard accounts for {file_type}: {standard_accounts_count}")
        
        if standard_accounts_count == 0:
            flash(f'{file_type.upper()}タイプの標準勘定科目が登録されていません。先に標準勘定科目を登録してください。', 'danger')
            return redirect(url_for('mapping', file_type=file_type))
        
        # 未マッピングの勘定科目数をチェック
        unmapped_count = CSVData.query.filter_by(
            ja_code=ja_code, 
            year=year, 
            file_type=file_type, 
            is_mapped=False
        ).count()
        
        logger.info(f"Unmapped account count before proceeding: {unmapped_count}")
        
        if unmapped_count == 0:
            flash(f'すべての勘定科目がすでにマッピングされています。AI処理は不要です。', 'success')
            return redirect(url_for('mapping', file_type=file_type))
            
        # バッチ処理を実行（direct_sql_mappingモジュールを使用）
        from direct_sql_mapping import execute_direct_mapping
        result = execute_direct_mapping(ja_code, year, file_type, max_items=20)
        
        if result['status'] == 'success':
            flash(f"バッチマッピングを実行しました。{result['mapped_count']}件の勘定科目をマッピングしました。", 'success')
        else:
            flash(f"マッピング処理中にエラーが発生しました: {result['message']}", 'danger')
        
        return redirect(url_for('mapping', file_type=file_type))
        
    except Exception as e:
        logger.error(f"Error in ai_map: {str(e)}")
        logger.error(traceback.format_exc())
        flash(f'エラーが発生しました: {str(e)}', 'danger')
        return redirect(url_for('mapping', file_type=file_type or 'bs'))
"""
    
    with open('ai_map_endpoint.py', 'w') as f:
        f.write(patch_content)
    
    logger.info("AIマッピングエンドポイントのパッチを作成しました: ai_map_endpoint.py")
    logger.info("このファイルを適切に編集してroutes.pyに適用してください。")

if __name__ == "__main__":
    create_routes_patch()
    logger.info("This is a patch creation script. It doesn't modify any files directly.")