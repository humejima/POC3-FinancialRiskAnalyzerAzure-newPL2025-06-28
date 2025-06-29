"""
JA管理用の機能を実装するモジュール
JAの登録、編集、削除などの機能を提供
"""

import logging
from flask import flash, redirect, render_template, request, url_for
from app import db
from models import JA
from performance_enhancer import performance_monitor

# ロガー設定
logger = logging.getLogger(__name__)

def register_ja_routes(app):
    """JA管理用のルートを登録する"""
    
    @app.route('/ja_registration', methods=['GET'])
    @app.route('/ja_management', methods=['GET'])
    @performance_monitor
    def ja_registration():
        """JA登録管理画面を表示（登録済みJA一覧のみ）"""
        from models import CSVData
        from sqlalchemy import distinct, func
        
        # 実際のデータに基づいた取得（パフォーマンス最適化済み）
        try:
            # ステップ1: JAの基本情報を取得
            jas = JA.query.order_by(JA.ja_code).all()
            
            if not jas:
                ja_data_years = {}
                mapping_status = {}
                risk_scores = {}
            else:
                ja_codes = [ja.ja_code for ja in jas]
                
                # ステップ2: 実際に取り込まれた年度のみを取得（2021, 2022に限定）
                ja_data_years = {}
                years_data = db.session.query(CSVData.ja_code, CSVData.year)\
                    .filter(CSVData.ja_code.in_(ja_codes))\
                    .filter(CSVData.year.in_([2021, 2022]))\
                    .distinct()\
                    .order_by(CSVData.ja_code, CSVData.year.desc())\
                    .all()
                
                for ja_code, year in years_data:
                    if ja_code not in ja_data_years:
                        ja_data_years[ja_code] = []
                    ja_data_years[ja_code].append(year)
                
                # ステップ3: 実際のマッピング状況を取得（BS、PLのみで高速化）
                mapping_status = {}
                from sqlalchemy import case
                mapping_data = db.session.query(
                    CSVData.ja_code,
                    CSVData.file_type,
                    func.count(CSVData.id).label('total_count'),
                    func.sum(case((CSVData.is_mapped == True, 1), else_=0)).label('mapped_count')
                ).filter(CSVData.ja_code.in_(ja_codes))\
                 .filter(CSVData.file_type.in_(['bs', 'pl', 'cf']))\
                 .filter(CSVData.year.in_([2021, 2022]))\
                 .group_by(CSVData.ja_code, CSVData.file_type)\
                 .all()
                
                # 初期化
                for ja_code in ja_codes:
                    mapping_status[ja_code] = {
                        'bs': {'total_count': 0, 'mapped_count': 0, 'unmapped_count': 0},
                        'pl': {'total_count': 0, 'mapped_count': 0, 'unmapped_count': 0},
                        'cf': {'total_count': 0, 'mapped_count': 0, 'unmapped_count': 0}
                    }
                
                # 実データを反映
                for ja_code, file_type, total_count, mapped_count in mapping_data:
                    mapped_count = mapped_count or 0
                    mapping_status[ja_code][file_type] = {
                        'total_count': total_count,
                        'mapped_count': mapped_count,
                        'unmapped_count': total_count - mapped_count
                    }
                
                # ステップ4: リスクスコアを効率的に取得
                risk_scores = {}
                from models import AnalysisResult
                
                # 各JAの最新年度を特定
                latest_years = {}
                for ja_code, years in ja_data_years.items():
                    if years:
                        latest_years[ja_code] = max(years)
                
                if latest_years:
                    # 代表的な指標でリスクスコアを一括取得
                    indicators = {
                        'profitability': 'roa',  # 収益性
                        'liquidity': 'current_ratio',  # 流動性  
                        'efficiency': 'asset_turnover_ratio',  # 効率性
                        'safety': 'debt_ratio',  # 安全性
                        'cash_flow': 'operating_cash_flow_ratio'  # キャッシュフロー
                    }
                    
                    # 年度とJAコードでフィルタして効率的に取得
                    risk_conditions = []
                    for ja_code, year in latest_years.items():
                        risk_conditions.append((AnalysisResult.ja_code == ja_code) & (AnalysisResult.year == year))
                    
                    if risk_conditions:
                        from sqlalchemy import or_
                        risk_data = db.session.query(
                            AnalysisResult.ja_code,
                            AnalysisResult.analysis_type,
                            AnalysisResult.risk_score
                        ).filter(
                            or_(*risk_conditions),
                            AnalysisResult.indicator_name.in_(indicators.values())
                        ).all()
                        
                        for ja_code, analysis_type, risk_score in risk_data:
                            if ja_code not in risk_scores:
                                risk_scores[ja_code] = {}
                            risk_scores[ja_code][analysis_type] = risk_score
                
                # 初期化（データがないJAのため）
                for ja_code in ja_codes:
                    if ja_code not in risk_scores:
                        risk_scores[ja_code] = {}
        
        except Exception as e:
            logger.error(f"JA管理データ取得でエラー: {e}")
            jas = []
            ja_data_years = {}
            mapping_status = {}
            risk_scores = {}
            
        return render_template('ja_management.html', 
                             jas=jas, 
                             ja_data_years=ja_data_years,
                             mapping_status=mapping_status,
                             risk_scores=risk_scores)
    
    @app.route('/new_ja_registration', methods=['GET'])
    def new_ja_registration():
        """新規JA登録画面を表示"""
        return render_template('new_ja_registration.html')
    
    @app.route('/register_ja', methods=['POST'])
    def register_ja():
        """新規JAを登録"""
        try:
            ja_code = request.form.get('ja_code')
            ja_name = request.form.get('ja_name')
            prefecture = request.form.get('prefecture')
            scale = request.form.get('scale')
            
            # 入力チェック
            if not ja_code or not ja_name or not prefecture:
                flash('必須項目が入力されていません', 'danger')
                return redirect(url_for('new_ja_registration'))
            
            # JAコード重複チェック
            existing_ja = JA.query.filter_by(ja_code=ja_code).first()
            if existing_ja:
                flash(f'JAコード "{ja_code}" は既に登録されています', 'warning')
                return redirect(url_for('new_ja_registration'))
            
            # 新規JA作成（デフォルト年度は2021）
            new_ja = JA(
                ja_code=ja_code,
                name=ja_name,
                prefecture=prefecture,
                scale=scale,
                year=2021,
                available_data=''
            )
            
            db.session.add(new_ja)
            db.session.commit()
            
            flash(f'新規JA "{ja_name}" が正常に登録されました', 'success')
            return redirect(url_for('ja_registration'))
            
        except Exception as e:
            logger.error(f'JA登録中にエラーが発生しました: {str(e)}')
            db.session.rollback()
            flash(f'JA登録に失敗しました: {str(e)}', 'danger')
            return redirect(url_for('ja_registration'))
    
    @app.route('/update_ja', methods=['POST'])
    def update_ja():
        """JA情報を更新"""
        try:
            ja_code = request.form.get('ja_code')
            ja_name = request.form.get('ja_name')
            prefecture = request.form.get('prefecture')
            scale = request.form.get('scale')
            
            if not ja_code or not ja_name or not prefecture:
                flash('必須項目が入力されていません', 'danger')
                return redirect(url_for('ja_registration'))
            
            # 対象JAの取得
            ja = JA.query.filter_by(ja_code=ja_code).first()
            if not ja:
                flash(f'更新対象のJA "{ja_code}" が見つかりません', 'danger')
                return redirect(url_for('ja_registration'))
            
            # 情報更新
            ja.name = ja_name
            ja.prefecture = prefecture
            ja.scale = scale
            
            db.session.commit()
            
            flash(f'JA "{ja_name}" の情報が正常に更新されました', 'success')
            return redirect(url_for('ja_registration'))
            
        except Exception as e:
            logger.error(f'JA更新中にエラーが発生しました: {str(e)}')
            db.session.rollback()
            flash(f'JA情報の更新に失敗しました: {str(e)}', 'danger')
            return redirect(url_for('ja_registration'))
    
    @app.route('/delete_ja/<ja_code>', methods=['GET'])
    def delete_ja(ja_code):
        """JAを削除（関連データも含めて完全削除）"""
        try:
            # 対象JAの取得
            ja = JA.query.filter_by(ja_code=ja_code).first()
            if not ja:
                flash(f'削除対象のJA "{ja_code}" が見つかりません', 'danger')
                return redirect(url_for('ja_registration'))
            
            ja_name = ja.name
            
            # SQLを使って直接削除（外部キー制約を考慮した順序）
            logger.info(f'JA "{ja_code}" の関連データ削除を開始します')
            
            # 1. 分析結果データの削除
            result1 = db.session.execute(
                db.text("DELETE FROM analysis_result WHERE ja_code = :ja_code"),
                {"ja_code": ja_code}
            )
            logger.info(f'分析結果データ {result1.rowcount}件を削除')
            
            # 2. 標準勘定科目残高データの削除
            result2 = db.session.execute(
                db.text("DELETE FROM standard_account_balance WHERE ja_code = :ja_code"),
                {"ja_code": ja_code}
            )
            logger.info(f'標準勘定科目残高データ {result2.rowcount}件を削除')
            
            # 3. アカウントマッピングデータの削除
            result3 = db.session.execute(
                db.text("DELETE FROM account_mapping WHERE ja_code = :ja_code"),
                {"ja_code": ja_code}
            )
            logger.info(f'アカウントマッピングデータ {result3.rowcount}件を削除')
            
            # 4. CSVデータの削除
            result4 = db.session.execute(
                db.text("DELETE FROM csv_data WHERE ja_code = :ja_code"),
                {"ja_code": ja_code}
            )
            logger.info(f'CSVデータ {result4.rowcount}件を削除')
            
            # 5. JAレコードの削除
            result5 = db.session.execute(
                db.text("DELETE FROM ja WHERE ja_code = :ja_code"),
                {"ja_code": ja_code}
            )
            logger.info(f'JAレコード "{ja_name}" を削除')
            
            # 全ての変更をコミット
            db.session.commit()
            
            flash(f'JA "{ja_name}" とその関連データが正常に削除されました', 'success')
            return redirect(url_for('ja_registration'))
            
        except Exception as e:
            logger.error(f'JA削除中にエラーが発生しました: {str(e)}')
            db.session.rollback()
            flash(f'JAの削除に失敗しました: {str(e)}', 'danger')
            return redirect(url_for('ja_registration'))