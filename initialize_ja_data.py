"""
JAマスタデータを初期化するスクリプト
このスクリプトはデータベースにJAの基本情報を登録します
"""

import logging
from datetime import datetime
from app import db
from models import JA

# ロガーの設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def initialize_ja_data():
    """
    JAマスタデータを初期化する
    基本的なJAコードと名前を登録する
    """
    try:
        # JA一覧
        ja_list = [
            {"ja_code": "JA001", "name": "JA北海道", "prefecture": "北海道", "year": 2025, "available_data": "bs,pl,cf"},
            {"ja_code": "JA002", "name": "JA東北", "prefecture": "宮城県", "year": 2025, "available_data": "bs,pl,cf"},
            {"ja_code": "JA003", "name": "JA関東", "prefecture": "東京都", "year": 2025, "available_data": "bs,pl,cf"},
            {"ja_code": "JA004", "name": "JA中部", "prefecture": "愛知県", "year": 2025, "available_data": "bs,pl,cf"},
            {"ja_code": "JA005", "name": "JA関西", "prefecture": "大阪府", "year": 2025, "available_data": "bs,pl,cf"},
            {"ja_code": "JA006", "name": "JA九州", "prefecture": "福岡県", "year": 2025, "available_data": "bs,pl,cf"},
        ]
        
        # JA情報を登録
        for ja_data in ja_list:
            ja = JA(
                ja_code=ja_data["ja_code"],
                name=ja_data["name"],
                prefecture=ja_data["prefecture"],
                year=ja_data["year"],
                available_data=ja_data["available_data"],
                last_updated=datetime.utcnow()
            )
            db.session.add(ja)
        
        # 変更をコミット
        db.session.commit()
        logger.info(f"{len(ja_list)}件のJAデータを正常に登録しました")
        
        return True, f"{len(ja_list)}件のJAデータを登録しました"
    except Exception as e:
        db.session.rollback()
        logger.error(f"JAデータの初期化中にエラーが発生しました: {str(e)}")
        return False, f"エラー: {str(e)}"

if __name__ == "__main__":
    success, message = initialize_ja_data()
    print(message)