"""
標準勘定科目を初期化するスクリプト
BS（貸借対照表）、PL（損益計算書）、CF（キャッシュフロー計算書）の標準勘定科目をDBに登録します
"""

import logging
from app import db
from models import StandardAccount

# ロガーの設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def initialize_bs_accounts():
    """BS（貸借対照表）の標準勘定科目を登録"""
    try:
        # BSの標準勘定科目定義
        bs_accounts = [
            # 資産の部
            {"code": "1", "name": "流動資産", "parent_code": None, "account_type": "asset", "display_order": 1, "statement_subtype": "asset"},
            {"code": "1000", "name": "現金・預金", "parent_code": "1", "account_type": "asset", "display_order": 101, "statement_subtype": "asset"},
            {"code": "1100", "name": "系統預け金", "parent_code": "1000", "account_type": "asset", "display_order": 102, "statement_subtype": "asset"},
            {"code": "1200", "name": "系統外預け金", "parent_code": "1000", "account_type": "asset", "display_order": 103, "statement_subtype": "asset"},
            {"code": "1300", "name": "有価証券", "parent_code": "1", "account_type": "asset", "display_order": 110, "statement_subtype": "asset"},
            {"code": "1400", "name": "貸出金", "parent_code": "1", "account_type": "asset", "display_order": 120, "statement_subtype": "asset"},
            {"code": "1500", "name": "その他資産", "parent_code": "1", "account_type": "asset", "display_order": 130, "statement_subtype": "asset"},
            
            # 固定資産
            {"code": "2000", "name": "固定資産", "parent_code": None, "account_type": "asset", "display_order": 200, "statement_subtype": "asset"},
            {"code": "2100", "name": "有形固定資産", "parent_code": "2000", "account_type": "asset", "display_order": 210, "statement_subtype": "asset"},
            {"code": "2200", "name": "無形固定資産", "parent_code": "2000", "account_type": "asset", "display_order": 220, "statement_subtype": "asset"},
            
            # 負債の部
            {"code": "3000", "name": "流動負債", "parent_code": None, "account_type": "liability", "display_order": 300, "statement_subtype": "liability"},
            {"code": "3100", "name": "預金", "parent_code": "3000", "account_type": "liability", "display_order": 310, "statement_subtype": "liability"},
            {"code": "3200", "name": "借入金", "parent_code": "3000", "account_type": "liability", "display_order": 320, "statement_subtype": "liability"},
            {"code": "3300", "name": "その他負債", "parent_code": "3000", "account_type": "liability", "display_order": 330, "statement_subtype": "liability"},
            
            # 固定負債
            {"code": "4000", "name": "固定負債", "parent_code": None, "account_type": "liability", "display_order": 400, "statement_subtype": "liability"},
            {"code": "4100", "name": "長期借入金", "parent_code": "4000", "account_type": "liability", "display_order": 410, "statement_subtype": "liability"},
            {"code": "4200", "name": "引当金", "parent_code": "4000", "account_type": "liability", "display_order": 420, "statement_subtype": "liability"},
            
            # 純資産の部
            {"code": "5000", "name": "純資産", "parent_code": None, "account_type": "equity", "display_order": 500, "statement_subtype": "equity"},
            {"code": "5100", "name": "出資金", "parent_code": "5000", "account_type": "equity", "display_order": 510, "statement_subtype": "equity"},
            {"code": "5200", "name": "利益剰余金", "parent_code": "5000", "account_type": "equity", "display_order": 520, "statement_subtype": "equity"},
            
            # 合計
            {"code": "2900", "name": "資産の部合計", "parent_code": None, "account_type": "total", "display_order": 290, "statement_subtype": "asset"},
            {"code": "4900", "name": "負債の部合計", "parent_code": None, "account_type": "total", "display_order": 490, "statement_subtype": "liability"},
            {"code": "5900", "name": "純資産の部合計", "parent_code": None, "account_type": "total", "display_order": 590, "statement_subtype": "equity"},
            {"code": "5950", "name": "負債及び純資産の部合計", "parent_code": None, "account_type": "total", "display_order": 599, "statement_subtype": "liability_equity"},
        ]
        
        # BS勘定科目の登録
        for account in bs_accounts:
            std_account = StandardAccount(
                code=account["code"],
                name=account["name"],
                financial_statement="bs",
                account_type=account["account_type"],
                display_order=account["display_order"],
                parent_code=account["parent_code"],
                statement_subtype=account["statement_subtype"]
            )
            db.session.add(std_account)
        
        # 変更をコミット
        db.session.commit()
        logger.info(f"{len(bs_accounts)}件のBS標準勘定科目を登録しました")
        return True, f"{len(bs_accounts)}件のBS標準勘定科目を登録しました"
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"BS標準勘定科目の登録中にエラーが発生しました: {str(e)}")
        return False, f"エラー: {str(e)}"

def initialize_pl_accounts():
    """PL（損益計算書）の標準勘定科目を登録"""
    try:
        # PLの標準勘定科目定義
        pl_accounts = [
            # 経常収益
            {"code": "6000", "name": "経常収益", "parent_code": None, "account_type": "revenue", "display_order": 600, "statement_subtype": "revenue"},
            {"code": "6100", "name": "資金運用収益", "parent_code": "6000", "account_type": "revenue", "display_order": 610, "statement_subtype": "revenue"},
            {"code": "6200", "name": "役務取引等収益", "parent_code": "6000", "account_type": "revenue", "display_order": 620, "statement_subtype": "revenue"},
            {"code": "6300", "name": "その他経常収益", "parent_code": "6000", "account_type": "revenue", "display_order": 630, "statement_subtype": "revenue"},
            
            # 経常費用
            {"code": "7000", "name": "経常費用", "parent_code": None, "account_type": "expense", "display_order": 700, "statement_subtype": "expense"},
            {"code": "7100", "name": "資金調達費用", "parent_code": "7000", "account_type": "expense", "display_order": 710, "statement_subtype": "expense"},
            {"code": "7200", "name": "人件費", "parent_code": "7000", "account_type": "expense", "display_order": 720, "statement_subtype": "expense"},
            {"code": "7300", "name": "物件費", "parent_code": "7000", "account_type": "expense", "display_order": 730, "statement_subtype": "expense"},
            {"code": "7400", "name": "税金", "parent_code": "7000", "account_type": "expense", "display_order": 740, "statement_subtype": "expense"},
            
            # 利益
            {"code": "8000", "name": "経常利益", "parent_code": None, "account_type": "profit", "display_order": 800, "statement_subtype": "profit"},
            {"code": "8100", "name": "特別利益", "parent_code": None, "account_type": "profit", "display_order": 810, "statement_subtype": "profit"},
            {"code": "8200", "name": "特別損失", "parent_code": None, "account_type": "profit", "display_order": 820, "statement_subtype": "loss"},
            {"code": "8300", "name": "税引前当期利益", "parent_code": None, "account_type": "profit", "display_order": 830, "statement_subtype": "profit"},
            {"code": "8400", "name": "法人税等", "parent_code": None, "account_type": "expense", "display_order": 840, "statement_subtype": "expense"},
            {"code": "8500", "name": "当期剰余金", "parent_code": None, "account_type": "profit", "display_order": 850, "statement_subtype": "profit"},
        ]
        
        # PL勘定科目の登録
        for account in pl_accounts:
            std_account = StandardAccount(
                code=account["code"],
                name=account["name"],
                financial_statement="pl",
                account_type=account["account_type"],
                display_order=account["display_order"],
                parent_code=account["parent_code"],
                statement_subtype=account["statement_subtype"]
            )
            db.session.add(std_account)
        
        # 変更をコミット
        db.session.commit()
        logger.info(f"{len(pl_accounts)}件のPL標準勘定科目を登録しました")
        return True, f"{len(pl_accounts)}件のPL標準勘定科目を登録しました"
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"PL標準勘定科目の登録中にエラーが発生しました: {str(e)}")
        return False, f"エラー: {str(e)}"

def initialize_cf_accounts():
    """CF（キャッシュフロー計算書）の標準勘定科目を登録"""
    try:
        # CFの標準勘定科目定義
        cf_accounts = [
            # 営業活動によるキャッシュフロー
            {"code": "9000", "name": "営業活動によるキャッシュフロー", "parent_code": None, "account_type": "operating", "display_order": 900, "statement_subtype": "operating"},
            {"code": "9100", "name": "税引前当期利益", "parent_code": "9000", "account_type": "operating", "display_order": 910, "statement_subtype": "operating"},
            {"code": "9200", "name": "減価償却費", "parent_code": "9000", "account_type": "operating", "display_order": 920, "statement_subtype": "operating"},
            {"code": "9300", "name": "引当金の増減額", "parent_code": "9000", "account_type": "operating", "display_order": 930, "statement_subtype": "operating"},
            
            # 投資活動によるキャッシュフロー
            {"code": "9500", "name": "投資活動によるキャッシュフロー", "parent_code": None, "account_type": "investing", "display_order": 950, "statement_subtype": "investing"},
            {"code": "9510", "name": "有形固定資産の取得による支出", "parent_code": "9500", "account_type": "investing", "display_order": 951, "statement_subtype": "investing"},
            {"code": "9520", "name": "有価証券の取得による支出", "parent_code": "9500", "account_type": "investing", "display_order": 952, "statement_subtype": "investing"},
            
            # 財務活動によるキャッシュフロー
            {"code": "9700", "name": "財務活動によるキャッシュフロー", "parent_code": None, "account_type": "financing", "display_order": 970, "statement_subtype": "financing"},
            {"code": "9710", "name": "出資金の増減額", "parent_code": "9700", "account_type": "financing", "display_order": 971, "statement_subtype": "financing"},
            {"code": "9720", "name": "借入金の増減額", "parent_code": "9700", "account_type": "financing", "display_order": 972, "statement_subtype": "financing"},
            
            # 合計
            {"code": "9900", "name": "現金及び現金同等物の増減額", "parent_code": None, "account_type": "total", "display_order": 990, "statement_subtype": "total"},
            {"code": "9910", "name": "現金及び現金同等物の期首残高", "parent_code": None, "account_type": "total", "display_order": 991, "statement_subtype": "total"},
            {"code": "9920", "name": "現金及び現金同等物の期末残高", "parent_code": None, "account_type": "total", "display_order": 992, "statement_subtype": "total"},
        ]
        
        # CF勘定科目の登録
        for account in cf_accounts:
            std_account = StandardAccount(
                code=account["code"],
                name=account["name"],
                financial_statement="cf",
                account_type=account["account_type"],
                display_order=account["display_order"],
                parent_code=account["parent_code"],
                statement_subtype=account["statement_subtype"]
            )
            db.session.add(std_account)
        
        # 変更をコミット
        db.session.commit()
        logger.info(f"{len(cf_accounts)}件のCF標準勘定科目を登録しました")
        return True, f"{len(cf_accounts)}件のCF標準勘定科目を登録しました"
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"CF標準勘定科目の登録中にエラーが発生しました: {str(e)}")
        return False, f"エラー: {str(e)}"

def initialize_all_standard_accounts():
    """すべての標準勘定科目を初期化"""
    results = []
    
    # BS勘定科目
    bs_success, bs_message = initialize_bs_accounts()
    results.append(bs_message)
    
    # PL勘定科目
    pl_success, pl_message = initialize_pl_accounts()
    results.append(pl_message)
    
    # CF勘定科目
    cf_success, cf_message = initialize_cf_accounts()
    results.append(cf_message)
    
    return bs_success and pl_success and cf_success, results

if __name__ == "__main__":
    success, messages = initialize_all_standard_accounts()
    for message in messages:
        print(message)