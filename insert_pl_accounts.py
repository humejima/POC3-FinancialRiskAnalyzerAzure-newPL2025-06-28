"""
PL標準勘定科目を直接挿入するスクリプト
"""

from app import app, db
from models import StandardAccount

# PL科目のリスト
pl_accounts = [
    {"code": "5000", "name": "事業総利益", "category": "Income", "account_type": "PL収益", "display_order": 1, "parent_code": None, "description": "事業総利益"},
    {"code": "5100", "name": "信用事業収益", "category": "Income", "account_type": "PL収益", "display_order": 2, "parent_code": "5000", "description": "信用事業収益"},
    {"code": "5110", "name": "資金運用収益", "category": "Income", "account_type": "PL収益", "display_order": 3, "parent_code": "5100", "description": "資金運用収益"},
    {"code": "5120", "name": "役務取引等収益", "category": "Income", "account_type": "PL収益", "display_order": 4, "parent_code": "5100", "description": "役務取引等収益"},
    {"code": "5130", "name": "その他信用事業収益", "category": "Income", "account_type": "PL収益", "display_order": 5, "parent_code": "5100", "description": "その他信用事業収益"},
    {"code": "5200", "name": "信用事業費用", "category": "Expense", "account_type": "PL費用", "display_order": 6, "parent_code": "5000", "description": "信用事業費用"},
    {"code": "5210", "name": "資金調達費用", "category": "Expense", "account_type": "PL費用", "display_order": 7, "parent_code": "5200", "description": "資金調達費用"},
    {"code": "5220", "name": "役務取引等費用", "category": "Expense", "account_type": "PL費用", "display_order": 8, "parent_code": "5200", "description": "役務取引等費用"},
    {"code": "5230", "name": "その他信用事業費用", "category": "Expense", "account_type": "PL費用", "display_order": 9, "parent_code": "5200", "description": "その他信用事業費用"},
    {"code": "5300", "name": "信用事業総利益", "category": "Income", "account_type": "PL収益", "display_order": 10, "parent_code": "5000", "description": "信用事業総利益"},
    {"code": "5400", "name": "共済事業収益", "category": "Income", "account_type": "PL収益", "display_order": 11, "parent_code": "5000", "description": "共済事業収益"},
    {"code": "5410", "name": "共済付加収入", "category": "Income", "account_type": "PL収益", "display_order": 12, "parent_code": "5400", "description": "共済付加収入"},
    {"code": "5420", "name": "共済貸付金利息", "category": "Income", "account_type": "PL収益", "display_order": 13, "parent_code": "5400", "description": "共済貸付金利息"},
    {"code": "5430", "name": "その他共済事業収益", "category": "Income", "account_type": "PL収益", "display_order": 14, "parent_code": "5400", "description": "その他共済事業収益"},
    {"code": "5500", "name": "共済事業費用", "category": "Expense", "account_type": "PL費用", "display_order": 15, "parent_code": "5000", "description": "共済事業費用"},
    {"code": "5510", "name": "共済推進費", "category": "Expense", "account_type": "PL費用", "display_order": 16, "parent_code": "5500", "description": "共済推進費"},
    {"code": "5520", "name": "共済保全費", "category": "Expense", "account_type": "PL費用", "display_order": 17, "parent_code": "5500", "description": "共済保全費"},
    {"code": "5530", "name": "その他共済事業費用", "category": "Expense", "account_type": "PL費用", "display_order": 18, "parent_code": "5500", "description": "その他共済事業費用"},
    {"code": "5600", "name": "共済事業総利益", "category": "Income", "account_type": "PL収益", "display_order": 19, "parent_code": "5000", "description": "共済事業総利益"},
    {"code": "5700", "name": "購買事業収益", "category": "Income", "account_type": "PL収益", "display_order": 20, "parent_code": "5000", "description": "購買事業収益"},
    {"code": "5710", "name": "購買品供給高", "category": "Income", "account_type": "PL収益", "display_order": 21, "parent_code": "5700", "description": "購買品供給高"},
    {"code": "5720", "name": "その他購買事業収益", "category": "Income", "account_type": "PL収益", "display_order": 22, "parent_code": "5700", "description": "その他購買事業収益"},
    {"code": "5800", "name": "購買事業費用", "category": "Expense", "account_type": "PL費用", "display_order": 23, "parent_code": "5000", "description": "購買事業費用"},
    {"code": "5810", "name": "購買品供給原価", "category": "Expense", "account_type": "PL費用", "display_order": 24, "parent_code": "5800", "description": "購買品供給原価"},
    {"code": "5820", "name": "購買品供給費", "category": "Expense", "account_type": "PL費用", "display_order": 25, "parent_code": "5800", "description": "購買品供給費"},
    {"code": "5830", "name": "その他購買事業費用", "category": "Expense", "account_type": "PL費用", "display_order": 26, "parent_code": "5800", "description": "その他購買事業費用"},
    {"code": "5900", "name": "購買事業総利益", "category": "Income", "account_type": "PL収益", "display_order": 27, "parent_code": "5000", "description": "購買事業総利益"},
    {"code": "6000", "name": "販売事業収益", "category": "Income", "account_type": "PL収益", "display_order": 28, "parent_code": "5000", "description": "販売事業収益"},
    {"code": "6010", "name": "販売品販売高", "category": "Income", "account_type": "PL収益", "display_order": 29, "parent_code": "6000", "description": "販売品販売高"},
    {"code": "6020", "name": "販売手数料", "category": "Income", "account_type": "PL収益", "display_order": 30, "parent_code": "6000", "description": "販売手数料"},
]

# CF科目のリスト
cf_accounts = [
    {"code": "9000", "name": "営業活動によるキャッシュ・フロー", "category": "CashFlow", "account_type": "CF営業", "display_order": 1, "parent_code": None, "description": "営業活動によるキャッシュ・フロー"},
    {"code": "9100", "name": "税引前当期純利益", "category": "CashFlow", "account_type": "CF営業", "display_order": 2, "parent_code": "9000", "description": "税引前当期純利益"},
    {"code": "9110", "name": "減価償却費", "category": "CashFlow", "account_type": "CF営業", "display_order": 3, "parent_code": "9000", "description": "減価償却費"},
    {"code": "9120", "name": "減損損失", "category": "CashFlow", "account_type": "CF営業", "display_order": 4, "parent_code": "9000", "description": "減損損失"},
    {"code": "9130", "name": "貸倒引当金の増減額", "category": "CashFlow", "account_type": "CF営業", "display_order": 5, "parent_code": "9000", "description": "貸倒引当金の増減額"},
    {"code": "9140", "name": "退職給付引当金の増減額", "category": "CashFlow", "account_type": "CF営業", "display_order": 6, "parent_code": "9000", "description": "退職給付引当金の増減額"},
    {"code": "9150", "name": "役員退職慰労引当金の増減額", "category": "CashFlow", "account_type": "CF営業", "display_order": 7, "parent_code": "9000", "description": "役員退職慰労引当金の増減額"},
    {"code": "9160", "name": "賞与引当金の増減額", "category": "CashFlow", "account_type": "CF営業", "display_order": 8, "parent_code": "9000", "description": "賞与引当金の増減額"},
    {"code": "9170", "name": "受取利息及び受取配当金", "category": "CashFlow", "account_type": "CF営業", "display_order": 9, "parent_code": "9000", "description": "受取利息及び受取配当金"},
    {"code": "9180", "name": "支払利息", "category": "CashFlow", "account_type": "CF営業", "display_order": 10, "parent_code": "9000", "description": "支払利息"},
    {"code": "9400", "name": "投資活動によるキャッシュ・フロー", "category": "CashFlow", "account_type": "CF投資", "display_order": 29, "parent_code": None, "description": "投資活動によるキャッシュ・フロー"},
    {"code": "9410", "name": "有価証券の取得による支出", "category": "CashFlow", "account_type": "CF投資", "display_order": 30, "parent_code": "9400", "description": "有価証券の取得による支出"},
    {"code": "9420", "name": "有価証券の売却による収入", "category": "CashFlow", "account_type": "CF投資", "display_order": 31, "parent_code": "9400", "description": "有価証券の売却による収入"},
    {"code": "9430", "name": "有価証券の償還による収入", "category": "CashFlow", "account_type": "CF投資", "display_order": 32, "parent_code": "9400", "description": "有価証券の償還による収入"},
    {"code": "9500", "name": "財務活動によるキャッシュ・フロー", "category": "CashFlow", "account_type": "CF財務", "display_order": 37, "parent_code": None, "description": "財務活動によるキャッシュ・フロー"},
]

def insert_pl_accounts():
    """PLの標準勘定科目を直接挿入する"""
    try:
        # 既存のPL勘定科目を削除
        deleted_count = StandardAccount.query.filter_by(financial_statement='pl').delete()
        print(f"{deleted_count}件のPL標準勘定科目を削除しました")
        db.session.commit()
        
        # 新しいPL勘定科目を登録
        count = 0
        for account_data in pl_accounts:
            account = StandardAccount()
            account.code = account_data["code"]
            account.name = account_data["name"]
            account.category = account_data["category"]
            account.financial_statement = "pl"
            account.account_type = account_data["account_type"]
            account.display_order = account_data["display_order"]
            account.parent_code = account_data["parent_code"]
            account.description = account_data["description"]
            
            db.session.add(account)
            count += 1
        
        # コミット
        db.session.commit()
        print(f"{count}件のPL標準勘定科目を登録しました")
        
        return True
    except Exception as e:
        db.session.rollback()
        print(f"PLインポート中にエラーが発生しました: {str(e)}")
        return False

def insert_cf_accounts():
    """CFの標準勘定科目を直接挿入する"""
    try:
        # 既存のCF勘定科目を削除
        deleted_count = StandardAccount.query.filter_by(financial_statement='cf').delete()
        print(f"{deleted_count}件のCF標準勘定科目を削除しました")
        db.session.commit()
        
        # 新しいCF勘定科目を登録
        count = 0
        for account_data in cf_accounts:
            account = StandardAccount()
            account.code = account_data["code"]
            account.name = account_data["name"]
            account.category = account_data["category"]
            account.financial_statement = "cf"
            account.account_type = account_data["account_type"]
            account.display_order = account_data["display_order"]
            account.parent_code = account_data["parent_code"]
            account.description = account_data["description"]
            
            db.session.add(account)
            count += 1
        
        # コミット
        db.session.commit()
        print(f"{count}件のCF標準勘定科目を登録しました")
        
        return True
    except Exception as e:
        db.session.rollback()
        print(f"CFインポート中にエラーが発生しました: {str(e)}")
        return False

if __name__ == "__main__":
    with app.app_context():
        # PLの標準勘定科目を登録
        insert_pl_accounts()
        
        # CFの標準勘定科目を登録
        insert_cf_accounts()