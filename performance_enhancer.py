"""
パフォーマンス最適化モジュール
画面遷移とデータベースクエリの性能を改善する
"""

import time
import logging
from functools import wraps
from flask import g

logger = logging.getLogger(__name__)

def performance_monitor(func):
    """
    関数の実行時間を測定するデコレータ
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        
        logger.info(f"関数 {func.__name__} の実行時間: {execution_time:.3f}秒")
        return result
    return wrapper

# Alias for backward compatibility
timed_function = performance_monitor

def cache_query_result(cache_key=None, cache_duration=300, timeout=None):
    """
    クエリ結果をキャッシュするデコレータ
    """
    # Handle both timeout and cache_duration parameters for backward compatibility
    if timeout is not None:
        cache_duration = timeout
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 簡単なメモリキャッシュの実装
            if not hasattr(g, 'query_cache'):
                g.query_cache = {}
            
            key = f"{cache_key}_{hash(str(args) + str(kwargs))}"
            current_time = time.time()
            
            # キャッシュされた結果が有効かチェック
            if key in g.query_cache:
                cached_data, cached_time = g.query_cache[key]
                if current_time - cached_time < cache_duration:
                    logger.debug(f"キャッシュからデータを取得: {key}")
                    return cached_data
            
            # キャッシュにない場合は関数を実行
            result = func(*args, **kwargs)
            g.query_cache[key] = (result, current_time)
            logger.debug(f"データをキャッシュに保存: {key}")
            
            return result
        return wrapper
    return decorator

# Alias for backward compatibility
cached_query = cache_query_result

class QueryOptimizer:
    """
    データベースクエリの最適化を行うクラス
    """
    
    @staticmethod
    def batch_ja_data_query(ja_codes):
        """
        複数のJAの基本データを一括で取得
        """
        from models import JA, CSVData, AnalysisResult
        from app import db
        from sqlalchemy import func, distinct
        
        start_time = time.time()
        
        # 基本的なJA情報
        jas = JA.query.filter(JA.ja_code.in_(ja_codes)).order_by(JA.ja_code).all()
        
        # 年度情報を一括取得
        years_data = db.session.query(CSVData.ja_code, CSVData.year)\
            .filter(CSVData.ja_code.in_(ja_codes))\
            .distinct()\
            .all()
        
        ja_data_years = {}
        for ja_code, year in years_data:
            if ja_code not in ja_data_years:
                ja_data_years[ja_code] = []
            ja_data_years[ja_code].append(year)
        
        # マッピング状況を一括取得
        mapping_data = db.session.query(
            CSVData.ja_code,
            CSVData.file_type,
            func.count(CSVData.id).label('total_count'),
            func.sum(func.case([(CSVData.is_mapped == True, 1)], else_=0)).label('mapped_count')
        ).filter(CSVData.ja_code.in_(ja_codes))\
         .group_by(CSVData.ja_code, CSVData.file_type)\
         .all()
        
        mapping_status = {}
        for ja_code, file_type, total_count, mapped_count in mapping_data:
            if ja_code not in mapping_status:
                mapping_status[ja_code] = {}
            
            mapped_count = mapped_count or 0
            mapping_status[ja_code][file_type] = {
                'total_count': total_count,
                'mapped_count': mapped_count,
                'unmapped_count': total_count - mapped_count
            }
        
        end_time = time.time()
        logger.info(f"バッチクエリ実行時間: {end_time - start_time:.3f}秒")
        
        return {
            'jas': jas,
            'ja_data_years': ja_data_years,
            'mapping_status': mapping_status
        }

def optimize_template_rendering():
    """
    テンプレートレンダリングの最適化設定
    """
    return {
        'cache_size': 400,
        'auto_reload': False,
        'optimized': True
    }