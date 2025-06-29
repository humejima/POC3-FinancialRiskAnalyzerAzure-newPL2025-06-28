"""
追加ルート定義 - このファイルにはアプリケーションに追加する新しいルートが含まれています
"""
import os
import logging
from flask import render_template, redirect, url_for, flash, request, jsonify
from app import db
from models import StandardAccount, StandardAccountBalance, CSVData, AccountMapping
from import_standard_accounts import import_standard_accounts
from import_cf_standard_accounts import import_cf_standard_accounts
from create_account_balances import create_standard_account_balances
from recreate_all_balances import recreate_all_balances
from recreate_deposit_balances import recreate_deposit_balances
from financial_indicators import FinancialIndicators
from recalculate_indicators import recalculate_indicators

# ロガーの設定
logger = logging.getLogger(__name__)

def register_additional_routes(app):
    """追加ルートを登録する"""
    
    # API エンドポイントはmain.pyで登録されています
    # 重複登録を避けるためコメントアウト
    # from api_endpoints import register_api_endpoints
    # register_api_endpoints(app)
    
    # 標準勘定科目一覧ページ用の新しいルート
    @app.route('/standard_accounts_new')
    def standard_accounts_new():
        """タブ切り替え形式の標準勘定科目一覧ページ"""
        bs_accounts = StandardAccount.query.filter_by(financial_statement='bs').order_by(StandardAccount.display_order).all()
        pl_accounts = StandardAccount.query.filter_by(financial_statement='pl').order_by(StandardAccount.display_order).all()
        cf_accounts = StandardAccount.query.filter_by(financial_statement='cf').order_by(StandardAccount.display_order).all()
        
        return render_template('standard_accounts.html', 
                            bs_accounts=bs_accounts,
                            pl_accounts=pl_accounts,
                            cf_accounts=cf_accounts)
    
    # 全標準勘定科目一括インポート用のルート
    @app.route('/import_all_standard_accounts', methods=['GET', 'POST'])
    def import_all_standard_accounts_route():
        """全標準勘定科目一括インポート"""
        try:
            logger.info("標準勘定科目の一括インポートを開始します...")
            
            # 1. BS/PL標準勘定科目のインポート
            logger.info("貸借対照表（BS）および損益計算書（PL）標準勘定科目をインポートします...")
            bs_pl_count = import_standard_accounts("attached_assets/標準勘定科目6.csv")
            logger.info(f"{bs_pl_count}件のBS/PL勘定科目をインポートしました")
            
            # 2. CF標準勘定科目のインポート
            logger.info("キャッシュフロー計算書（CF）標準勘定科目をインポートします...")
            cf_count = import_cf_standard_accounts("attached_assets/キャッシュフロー計算書標準科目テーブル.csv")
            logger.info(f"{cf_count}件のCF勘定科目をインポートしました")
            
            # 合計
            total_count = bs_pl_count + cf_count
            flash(f'標準勘定科目の一括インポートが完了しました。合計: {total_count}件（BS/PL: {bs_pl_count}件、CF: {cf_count}件）', 'success')
            
        except Exception as e:
            logger.error(f"標準勘定科目の一括インポートに失敗しました: {str(e)}")
            flash(f'標準勘定科目の一括インポートに失敗しました: {str(e)}', 'danger')
        
        return redirect(url_for('standard_accounts'))
        
    # 勘定科目残高再計算APIルート
    @app.route('/api/recalculate_balances', methods=['POST'])
    def api_recalculate_balances():
        """勘定科目残高を再計算するAPIエンドポイント"""
        try:
            ja_code = request.form.get('ja_code')
            year = request.form.get('year', 2025)
            file_type = request.form.get('file_type', None)  # None の場合、すべての財務諸表タイプが再計算される
            
            if not ja_code:
                return jsonify({'status': 'error', 'message': 'JAコードが必要です'}), 400
                
            # 文字列型の年度を整数型に変換
            try:
                year = int(year)
            except (ValueError, TypeError):
                return jsonify({'status': 'error', 'message': '年度は数値でなければなりません'}), 400
            
            # recreate_all_balances関数を使用して残高を再計算
            logger.info(f"残高再計算を開始: JA={ja_code}, 年度={year}, タイプ={file_type or 'すべて'}")
            result = recreate_all_balances(ja_code, year, file_type)
            
            return jsonify({
                'status': 'success',
                'message': f"残高を再計算しました: JA={ja_code}, 年度={year}, タイプ={file_type or 'すべて'}",
                'details': result
            })
            
        except Exception as e:
            logger.error(f"残高再計算エラー: {str(e)}")
            return jsonify({'status': 'error', 'message': f"残高再計算に失敗しました: {str(e)}"}), 500
            
    # 財務指標再計算APIルートは routes.py に移動したため、こちらのコードは削除
    # 重複定義による衝突を避けるためにコードを削除
    # 新しい実装は routes.py の api_recalculate_indicators 関数を参照
            
    # 預金残高の特別再計算APIルート
    @app.route('/api/fix_deposit_balances', methods=['POST'])
    def api_fix_deposit_balances():
        """預金関連の残高を特別に再計算するAPIエンドポイント"""
        try:
            ja_code = request.form.get('ja_code')
            year = request.form.get('year', 2025)
            
            if not ja_code:
                return jsonify({'status': 'error', 'message': 'JAコードが必要です'}), 400
                
            # 文字列型の年度を整数型に変換
            try:
                year = int(year)
            except (ValueError, TypeError):
                return jsonify({'status': 'error', 'message': '年度は数値でなければなりません'}), 400
            
            # recreate_deposit_balances関数を使用して預金残高を再計算
            logger.info(f"預金残高の特別再計算を開始: JA={ja_code}, 年度={year}")
            result = recreate_deposit_balances(ja_code, year)
            
            return jsonify({
                'status': 'success',
                'message': f"預金残高を再計算しました: JA={ja_code}, 年度={year}",
                'details': result
            })
            
        except Exception as e:
            logger.error(f"預金残高再計算エラー: {str(e)}")
            return jsonify({'status': 'error', 'message': f"預金残高の再計算に失敗しました: {str(e)}"}), 500
    
    # 勘定科目残高再計算ページルート
    @app.route('/recalculate_balances', methods=['GET', 'POST'])
    def recalculate_balances_page():
        """勘定科目残高を再計算するページ"""
        if request.method == 'POST':
            try:
                ja_code = request.form.get('ja_code')
                year = request.form.get('year', 2025)
                file_type = request.form.get('file_type')
                
                if not ja_code:
                    flash('JAコードが必要です', 'danger')
                    return redirect(url_for('recalculate_balances_page'))
                
                # 文字列型の年度を整数型に変換
                try:
                    year = int(year)
                except (ValueError, TypeError):
                    flash('年度は数値でなければなりません', 'danger')
                    return redirect(url_for('recalculate_balances_page'))
                
                # recreate_all_balances関数を使用して残高を再計算
                logger.info(f"残高再計算を開始: JA={ja_code}, 年度={year}, タイプ={file_type or 'すべて'}")
                result = recreate_all_balances(ja_code, year, file_type)
                
                # 結果メッセージを構築
                success_messages = []
                error_messages = []
                
                for ft, res in result.items():
                    if res['status'] == 'success':
                        success_messages.append(f"{ft}: 削除={res['deleted']}件, 作成={res.get('created', 0)}件")
                    else:
                        error_messages.append(f"{ft}: エラー - {res.get('error', '不明なエラー')}")
                
                if success_messages:
                    flash(f"残高再計算が完了しました:<br>{'<br>'.join(success_messages)}", 'success')
                
                if error_messages:
                    flash(f"一部の残高再計算に失敗しました:<br>{'<br>'.join(error_messages)}", 'danger')
                
                # セッションにJAコードと年度を保存
                from flask import session
                session['selected_ja_code'] = ja_code
                session['selected_year'] = year
                
                return redirect(url_for('account_balances', ja_code=ja_code, year=year, financial_statement=file_type or 'bs'))
                
            except Exception as e:
                logger.error(f"残高再計算エラー: {str(e)}")
                flash(f"残高再計算に失敗しました: {str(e)}", 'danger')
                return redirect(url_for('recalculate_balances_page'))
        
        # GETリクエストの場合はフォームを表示
        from models import JA
        jas = JA.query.all()
        
        # セッションから選択されたJAと年度を取得
        from flask import session
        selected_ja_code = request.args.get('ja_code') or session.get('selected_ja_code')
        selected_year = request.args.get('year') or session.get('selected_year')
        
        return render_template('recalculate_balances.html', jas=jas, selected_ja_code=selected_ja_code, selected_year=selected_year)
        
    # 財務指標再計算API - 最小化バージョン
    # routes.pyに同等機能を実装したため削除
    # @app.route('/api/recalculate_indicators', methods=['POST'])
    # def recalculate_indicators_api():
    # この関数は routes.py の api_recalculate_indicators に置き換えられました