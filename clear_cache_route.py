"""
キャッシュバイパスのための特殊ルート
"""
import time
from datetime import datetime
from flask import request, session, redirect, url_for

def register_cache_clear_routes(app):
    """
    キャッシュをクリアするためのルートを登録
    """
    @app.route('/ja_registration/clear_cache')
    def ja_registration_clear_cache():
        """JAユーザー登録画面のキャッシュをクリア"""
        timestamp = int(time.time())
        return redirect(url_for('ja_registration', clear_cache=timestamp))