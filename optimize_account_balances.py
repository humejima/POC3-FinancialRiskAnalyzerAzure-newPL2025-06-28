"""
標準勘定科目残高画面の処理速度最適化スクリプト
"""
import time
import logging
from flask import request, flash, redirect, url_for, session, render_template
from app import db
from models import JA, CSVData, StandardAccount, StandardAccountBalance
from create_account_balances import create_standard_account_balances

# ロガー設定
logger = logging.getLogger(__name__)

def optimized_account_balances():
    """最適化された標準勘定科目残高一覧表示の処理"""
    start_time = time.time()
    logger.info("標準勘定科目残高一覧処理開始")
    
    try:
        # JA、年度、財務諸表タイプを取得
        ja_code = request.args.get('ja_code')
        year = request.args.get('year')
        financial_statement = request.args.get('financial_statement', 'bs')
        
        # 更新フラグを確認
        refresh = request.args.get('refresh', 'false').lower() == 'true'
        # 合計計算フラグを確認
        calculate_totals = request.args.get('calculate_totals', 'false').lower() == 'true'
        # 残高再作成フラグを確認
        recreate_balances = request.args.get('recreate_balances', 'false').lower() == 'true'
        
        if refresh:
            db.session.expire_all()
            
        # 年度が文字列ならば整数に変換
        year_int = None
        if year:
            try:
                year_int = int(year)
            except (ValueError, TypeError):
                flash('年度の形式が正しくありません。整数を指定してください。', 'warning')
                year_int = 2021  # デフォルト値
                logger.warning(f"年度の変換に失敗しました: {year} -> デフォルト値 2021 を使用")
            year = year_int
        
        # セッションに保存
        session['selected_ja_code'] = ja_code
        session['selected_year'] = year
        
        if not ja_code or not year:
            return redirect(url_for('select_ja'))
        
        # デバッグ: 選択されたJA、年度と、使用されるパラメータを表示
        logger.info(f"選択されたJA={ja_code}, 年度={year_int}, タイプ={financial_statement}, 残高再作成={recreate_balances}")
            
        # 残高データを再作成するか
        if recreate_balances and ja_code and year_int:
            logger.info(f"残高データ再作成処理開始: JA={ja_code}, 年度={year_int}, タイプ={financial_statement}")
            try:
                # 直接クエリで残高データを削除
                deleted = StandardAccountBalance.query.filter_by(
                    ja_code=ja_code, 
                    year=year_int,
                    statement_type=financial_statement
                ).delete()
                
                logger.info(f"削除した残高データ: {deleted}件")
                db.session.commit()
                
                # 残高データを作成
                created_count = create_standard_account_balances(ja_code, year_int, financial_statement)
                logger.info(f"作成した残高データ: {created_count}件")
                
                flash(f'標準勘定科目残高を再作成しました（{created_count}件）', 'success')
            except Exception as e:
                db.session.rollback()
                logger.error(f"残高データ再作成中にエラー: {str(e)}")
                flash(f'残高データの再作成中にエラーが発生しました: {str(e)}', 'danger')
                
        # 勘定科目の合計を計算（要求された場合のみ）
        if calculate_totals and ja_code and year_int:
            try:
                from account_calculator import AccountCalculator
                processed_count = AccountCalculator.calculate_account_totals(ja_code, year_int, financial_statement)
                if processed_count > 0:
                    flash(f'{processed_count}個の勘定科目合計を計算しました', 'success')
            except Exception as e:
                logger.error(f"勘定科目合計の計算中にエラー: {str(e)}")
                flash(f'勘定科目合計の計算中にエラーが発生しました: {str(e)}', 'danger')

        # 選択されたJAと年度で標準勘定科目残高を取得
        balances = []
        if ja_code and year_int:
            # パフォーマンス測定
            query_start_time = time.time()
            
            # 標準勘定科目マスタを一度に取得（JOIN最適化）
            all_standard_accounts = StandardAccount.query.filter_by(
                financial_statement=financial_statement
            ).order_by(StandardAccount.code.cast(db.Integer)).all()
            
            # 標準残高をすべて一度に取得
            all_balances = StandardAccountBalance.query.filter_by(
                ja_code=ja_code,
                year=year_int,
                statement_type=financial_statement
            ).all()
            
            # 残高をディクショナリ化（高速アクセス用）
            balance_dict = {balance.standard_account_code: balance for balance in all_balances}
            
            # もし残高データが0件なら、自動作成を試みる
            if len(all_balances) == 0:
                try:
                    logger.info(f"残高データが存在しないため自動作成を試みます: JA={ja_code}, 年度={year_int}, タイプ={financial_statement}")
                    created_count = create_standard_account_balances(ja_code, year_int, financial_statement)
                    logger.info(f"残高データを自動作成: {created_count}件")
                    flash(f'標準勘定科目残高を自動作成しました（{created_count}件）', 'info')
                    
                    # 作成後に再度残高データを取得
                    all_balances = StandardAccountBalance.query.filter_by(
                        ja_code=ja_code,
                        year=year_int,
                        statement_type=financial_statement
                    ).all()
                    
                    # 残高ディクショナリを更新
                    balance_dict = {balance.standard_account_code: balance for balance in all_balances}
                    logger.info(f"再取得した残高データ件数: {len(all_balances)}")
                except Exception as e:
                    logger.error(f"残高データの自動作成中にエラー: {str(e)}")
                    flash(f'残高データの自動作成中にエラーが発生しました: {str(e)}', 'danger')
            
            # 親子関係マッピングを事前に構築（パフォーマンス最適化）
            parent_children_map = {}
            all_parent_codes = set()
            
            # 親コードを収集
            for account in all_standard_accounts:
                if account.parent_code:
                    all_parent_codes.add(account.parent_code)
                    if account.parent_code not in parent_children_map:
                        parent_children_map[account.parent_code] = []
                    parent_children_map[account.parent_code].append(account)
                    
            # 財務諸表タイプに応じて重要な親科目コードのリストを取得
            if financial_statement == 'bs':
                # BS（貸借対照表）の重要な親科目コード
                important_parent_codes = ['1000', '1600', '1700', '1800', '1900', '2000', '2100', '3000', '3600', '3900', '5200', 
                                          # 合計科目も追加
                                          '2900', '4900', '5900', '5950', '5951']
            elif financial_statement == 'pl':
                # PL（損益計算書）の重要な親科目コード
                important_parent_codes = ['40000', '41000', '50000', '51000', '60000', '70000', '80000', '81000', '82000', 
                                          '83000', '90000', '91000', '92000', '99000']
            elif financial_statement == 'cf':
                # CF（キャッシュフロー計算書）の重要な親科目コード
                important_parent_codes = ['6000', '6100', '6200', '6300', '6400', '6500', '6600', '6700', '6800', '6900', 
                                          '7000', '7100', '7200', '7300', '7400', '7500', '7600', '7700', '7800', '7900', '9900']
            else:
                # デフォルト（すべてのタイプの科目を表示）
                important_parent_codes = []
            
            logger.info(f"データ取得完了: 標準科目={len(all_standard_accounts)}件, 残高データ={len(all_balances)}件, 重要親科目={len(important_parent_codes)}件")
            logger.info(f"クエリと前処理時間: {time.time() - query_start_time:.3f}秒")
            
            # 処理結果格納用
            items_dict = {}
            
            # データ整形処理開始
            processing_start_time = time.time()
            
            # 全標準勘定科目についてデータを整形（マスタに存在するが残高にないものも含む）
            for std_account in all_standard_accounts:
                code = std_account.code
                
                # 重要でない親科目でかつ子科目を持たない場合はスキップ
                if code not in important_parent_codes and code not in parent_children_map:
                    # 残高テーブルにある場合は処理する
                    if code in balance_dict:
                        pass  # 残高テーブルにある場合は通常通り処理
                    else:
                        # 子科目を持たない親科目でかつ残高テーブルにない場合はスキップ
                        continue
                
                # 基本情報の設定（残高テーブルに存在する場合はそれを使用、ない場合は標準勘定科目マスタから）
                if code in balance_dict:
                    balance_item = balance_dict[code]
                    balance = {
                        'standard_account_code': balance_item.standard_account_code,
                        'standard_account_name': balance_item.standard_account_name,
                        'statement_subtype': balance_item.statement_subtype,
                        'current_value': balance_item.current_value,
                        'previous_value': balance_item.previous_value,
                        'parent_code': std_account.parent_code,
                        'display_order': std_account.display_order,
                        'is_child': std_account.parent_code is not None
                    }
                else:
                    # 残高テーブルにない場合は0で初期化
                    balance = {
                        'standard_account_code': std_account.code,
                        'standard_account_name': std_account.name,
                        'statement_subtype': std_account.account_type,
                        'current_value': 0,
                        'previous_value': 0,
                        'parent_code': std_account.parent_code,
                        'display_order': std_account.display_order,
                        'is_child': std_account.parent_code is not None
                    }
                
                # バランスリストに追加
                balances.append(balance)
                # コード→バランスのディクショナリにも登録（後で別の箇所から参照できるように）
                items_dict[code] = balance
                
            logger.info(f"残高データ整形時間: {time.time() - processing_start_time:.3f}秒")
            
        # 利用可能なJAと年度のリストを取得
        jas = JA.query.all()
        years = db.session.query(CSVData.year).distinct().order_by(CSVData.year.desc()).all()
        years = [y[0] for y in years]
        
        # 選択されたJAの情報を取得
        selected_ja = JA.query.filter_by(code=ja_code).first()
        
        # 表示に使用するデータを準備
        data = {
            'balances': balances,
            'jas': jas,
            'years': years,
            'selected_ja': selected_ja,
            'selected_ja_code': ja_code,
            'selected_year': year,
            'selected_financial_statement': financial_statement
        }
        
        logger.info(f"総処理時間: {time.time() - start_time:.3f}秒")
        return render_template('account_balances.html', **data)
        
    except Exception as e:
        logger.error(f"標準勘定科目残高画面でエラー: {str(e)}")
        flash(f'エラーが発生しました: {str(e)}', 'danger')
        return redirect(url_for('index'))

if __name__ == "__main__":
    print("このスクリプトは直接実行せず、routes.pyからインポートして使用してください。")