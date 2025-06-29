"""
JAテーブルにJAデータが存在することを確認するスクリプト
CSVデータをインポートする前に、該当のJAコードが存在していないと外部キー制約違反となる
"""
import logging
from app import app, db
from models import JA

# ロギング設定
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def ensure_ja_exists(ja_code="JA001", ja_name="テスト農協", current_year=2021):
    """
    指定したJAコードがJAテーブルに存在することを確認し、
    存在しない場合は新規に作成する
    
    Args:
        ja_code: JAコード (デフォルト: JA001)
        ja_name: JA名称 (デフォルト: テスト農協)
        current_year: 年度 (デフォルト: 2021)
    """
    with app.app_context():
        # 既存のJAをチェック
        existing_ja = JA.query.filter_by(ja_code=ja_code).first()
        
        if existing_ja:
            logger.info(f"JAコード {ja_code} は既に存在します: {existing_ja.name}")
            return existing_ja
        
        # 存在しない場合は新規作成
        try:
            new_ja = JA(
                ja_code=ja_code, 
                name=ja_name,
                prefecture="テスト",
                year=current_year,
                available_data="bs,pl,cf"
            )
            db.session.add(new_ja)
            db.session.commit()
            logger.info(f"JAコード {ja_code} を新規作成しました: {ja_name}")
            return new_ja
        except Exception as e:
            import traceback
            logger.error(f"JAの作成中にエラーが発生しました: {str(e)}")
            logger.error(traceback.format_exc())
            db.session.rollback()
            return None

def list_all_jas():
    """登録済みのJAをすべて表示"""
    with app.app_context():
        jas = JA.query.all()
        logger.info(f"登録済みJA: {len(jas)}件")
        for ja in jas:
            logger.info(f"  {ja.ja_code}: {ja.name}")

if __name__ == "__main__":
    # JA001を作成（すでに存在している場合は何もしない）
    ensure_ja_exists("JA001", "テスト農協1号", 2021)
    # JA007を作成（マッピング用のテストJA）
    ensure_ja_exists("JA007", "テスト農協7号", 2021)
    # 登録済みJAを表示
    list_all_jas()