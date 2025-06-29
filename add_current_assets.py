import os
import logging
from app import app, db
from models import StandardAccount

# ロギングの設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def add_current_assets_account():
    """流動資産科目を追加して、1000, 1600, 1700, 1800, 1900の親科目として設定する"""
    with app.app_context():
        # 流動資産科目のコード
        current_assets_code = '1'
        
        # 流動資産科目を追加（既に存在する場合は更新）
        current_assets = StandardAccount.query.filter_by(code=current_assets_code).first()
        
        if current_assets:
            logger.info(f"流動資産科目がすでに存在します: {current_assets.code} - {current_assets.name}")
            # 既存の科目を更新
            current_assets.name = '流動資産'
            current_assets.category = 'BS資産'
            current_assets.financial_statement = 'bs'
            current_assets.account_type = 'BS資産'
            current_assets.display_order = 1
            current_assets.parent_code = None
            current_assets.description = '現金預け金、有価証券、貸出金、外国為替、その他資産の合計'
        else:
            # 新規に科目を作成
            current_assets = StandardAccount(
                code=current_assets_code,
                name='流動資産',
                category='BS資産',
                financial_statement='bs',
                account_type='BS資産',
                display_order=1,
                parent_code=None,
                description='現金預け金、有価証券、貸出金、外国為替、その他資産の合計'
            )
            db.session.add(current_assets)
            logger.info(f"流動資産科目を追加しました: {current_assets_code}")
        
        # 流動資産の子科目を設定
        child_codes = ['1000', '1600', '1700', '1800', '1900']
        updated_children = 0
        
        for child_code in child_codes:
            child = StandardAccount.query.filter_by(code=child_code).first()
            if child:
                old_parent = child.parent_code
                child.parent_code = current_assets_code
                updated_children += 1
                logger.info(f"科目 {child_code} ({child.name}) の親科目を変更: {old_parent} -> {current_assets_code}")
        
        # 変更をコミット
        db.session.commit()
        logger.info(f"流動資産科目の設定が完了しました。{updated_children}件の子科目を更新しました。")
        
        # 関連する子科目も再帰的に親子関係を更新
        child_parents = {
            # コールローン、買現先勘定などを現金預け金の子科目に
            '1100': '1000',  # コールローン -> 現金預け金
            '1200': '1000',  # 買現先勘定 -> 現金預け金
            '1300': '1000',  # 債券貸借取引支払保証金 -> 現金預け金
            '1400': '1000',  # 買入手形 -> 現金預け金
            '1500': '1000',  # 買入金銭債権 -> 現金預け金
        }
        
        updated_subchildren = 0
        for code, parent_code in child_parents.items():
            account = StandardAccount.query.filter_by(code=code).first()
            if account:
                old_parent = account.parent_code
                account.parent_code = parent_code
                updated_subchildren += 1
                logger.info(f"子科目更新: {code} ({account.name}): {old_parent} -> {parent_code}")
        
        # 変更をコミット
        db.session.commit()
        logger.info(f"子科目の親子関係も更新しました。{updated_subchildren}件の科目を更新。")

if __name__ == "__main__":
    add_current_assets_account()