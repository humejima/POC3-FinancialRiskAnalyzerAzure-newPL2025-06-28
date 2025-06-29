from flask import render_template, redirect, url_for, flash, request, jsonify
from app import app, db
from models import StandardAccount
from import_all_standard_accounts import import_standard_accounts, import_cf_standard_accounts
import logging
import os

# ロガーの設定
logger = logging.getLogger(__name__)

@app.route('/standard_accounts')
def standard_accounts():
    """標準勘定科目一覧ページ"""
    bs_accounts = StandardAccount.query.filter_by(financial_statement='bs').order_by(StandardAccount.display_order).all()
    pl_accounts = StandardAccount.query.filter_by(financial_statement='pl').order_by(StandardAccount.display_order).all()
    cf_accounts = StandardAccount.query.filter_by(financial_statement='cf').order_by(StandardAccount.display_order).all()
    
    return render_template('standard_accounts.html', 
                        bs_accounts=bs_accounts,
                        pl_accounts=pl_accounts,
                        cf_accounts=cf_accounts)

@app.route('/import_all_standard_accounts')
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

if __name__ == "__main__":
    # テスト用
    with app.app_context():
        standard_accounts()