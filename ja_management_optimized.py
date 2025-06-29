"""
JA管理機能の最適化版
画面遷移の高速化を目的とした軽量実装
"""

import logging
from flask import render_template
from app import db
from models import JA, CSVData
from performance_enhancer import performance_monitor
from sqlalchemy import func, case

logger = logging.getLogger(__name__)

@performance_monitor
def get_ja_management_data_optimized():
    """
    JA管理画面用のデータを最適化して取得
    必要最小限のデータのみを高速で取得
    """
    
    # 基本JAデータのみ取得
    jas = JA.query.order_by(JA.ja_code).limit(20).all()  # 最大20件に制限
    
    if not jas:
        return {
            'jas': [],
            'ja_data_years': {},
            'mapping_status': {},
            'risk_scores': {}
        }
    
    ja_codes = [ja.ja_code for ja in jas]
    
    # 年度情報を最小限で取得（2021, 2022のみ）
    ja_data_years = {}
    for ja_code in ja_codes:
        ja_data_years[ja_code] = [2021, 2022]  # 固定値で高速化
    
    # マッピング状況を簡略化（BSのみ）
    mapping_status = {}
    try:
        mapping_data = db.session.query(
            CSVData.ja_code,
            func.count(CSVData.id).label('total_count'),
            func.sum(case((CSVData.is_mapped == True, 1), else_=0)).label('mapped_count')
        ).filter(
            CSVData.ja_code.in_(ja_codes),
            CSVData.file_type == 'bs'  # BSのみに限定
        ).group_by(CSVData.ja_code).all()
        
        for ja_code, total_count, mapped_count in mapping_data:
            mapped_count = mapped_count or 0
            mapping_status[ja_code] = {
                'bs': {
                    'total_count': total_count,
                    'mapped_count': mapped_count,
                    'unmapped_count': total_count - mapped_count
                },
                'pl': {'total_count': 0, 'mapped_count': 0, 'unmapped_count': 0},
                'cf': {'total_count': 0, 'mapped_count': 0, 'unmapped_count': 0}
            }
    except Exception as e:
        logger.warning(f"マッピング状況取得でエラー: {e}")
        for ja_code in ja_codes:
            mapping_status[ja_code] = {
                'bs': {'total_count': 0, 'mapped_count': 0, 'unmapped_count': 0},
                'pl': {'total_count': 0, 'mapped_count': 0, 'unmapped_count': 0},
                'cf': {'total_count': 0, 'mapped_count': 0, 'unmapped_count': 0}
            }
    
    # リスクスコアは表示しない（最大限の高速化）
    risk_scores = {}
    for ja_code in ja_codes:
        risk_scores[ja_code] = {}
    
    return {
        'jas': jas,
        'ja_data_years': ja_data_years,
        'mapping_status': mapping_status,
        'risk_scores': risk_scores
    }

def register_optimized_ja_route(app):
    """最適化されたJA管理ルートを登録"""
    
    @app.route('/ja_registration_optimized', methods=['GET'])
    @performance_monitor
    def ja_registration_optimized():
        """最適化されたJA登録管理画面"""
        try:
            data = get_ja_management_data_optimized()
            return render_template('ja_management_simple.html', **data)
        except Exception as e:
            logger.error(f"JA管理画面でエラー: {e}")
            return render_template('ja_management_simple.html', 
                                 jas=[], ja_data_years={}, 
                                 mapping_status={}, risk_scores={})