"""
JA006を作成するスクリプト
"""

from app import app, db
from models import JA

def ensure_ja006():
    """JA006を登録する"""
    with app.app_context():
        ja = JA.query.filter_by(code='JA006').first()
        if not ja:
            ja = JA(code='JA006', name='JA006', year=2021, available_data='bs,pl,cf')
            db.session.add(ja)
            db.session.commit()
            print('JA006を作成しました')
        else:
            print('JA006はすでに存在しています')

if __name__ == "__main__":
    ensure_ja006()