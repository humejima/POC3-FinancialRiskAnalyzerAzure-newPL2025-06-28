from app import app, db
from models import StandardAccount
import logging

# ロガーの設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_bs_total_accounts():
    """
    BS（貸借対照表）合計科目を標準勘定科目マスタに追加する
    """
    # 合計科目のリスト [コード, 名前, カテゴリ, 表示順序, 親コード, 説明]
    total_accounts = [
        ["2900", "資産の部合計", "BS資産", 50, None, "資産の部の合計金額"],
        ["4900", "負債の部合計", "BS負債", 70, None, "負債の部の合計金額"],
        ["5900", "純資産の部合計", "BS純資産", 90, None, "純資産の部の合計金額"],
        ["5950", "負債及び純資産の部合計", "BS", 95, None, "負債及び純資産の部の合計金額"],
        ["5951", "バランスチェック（資産合計）", "BS", 96, None, "資産の部合計（チェック用）"]
    ]
    
    added_count = 0
    updated_count = 0
    
    for code, name, category, display_order, parent_code, description in total_accounts:
        # 既存のレコードを確認
        existing = StandardAccount.query.filter_by(
            code=code,
            financial_statement="bs"
        ).first()
        
        if existing:
            # 更新
            existing.name = name
            existing.category = category
            existing.display_order = display_order
            existing.parent_code = parent_code
            existing.description = description
            updated_count += 1
            logger.info(f"更新: コード={code}, 名前={name}")
        else:
            # 新規作成（属性ごとに設定）
            new_account = StandardAccount()
            new_account.code = code
            new_account.name = name
            new_account.category = category
            new_account.financial_statement = "bs"
            new_account.account_type = category
            new_account.display_order = display_order
            new_account.parent_code = parent_code
            new_account.description = description
            db.session.add(new_account)
            added_count += 1
            logger.info(f"追加: コード={code}, 名前={name}")
    
    db.session.commit()
    logger.info(f"合計 {added_count} 件追加、{updated_count} 件更新しました。")

if __name__ == "__main__":
    with app.app_context():
        try:
            add_bs_total_accounts()
            logger.info("標準勘定科目マスタへの合計科目の追加が完了しました。")
        except Exception as e:
            logger.error(f"エラーが発生しました: {str(e)}")