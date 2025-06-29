"""
PL（損益計算書）のマッピングを修正するスクリプト
"""
import logging
from app import app, db
from models import AccountMapping, CSVData, StandardAccount

# ロガーの設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_pl_mappings(ja_code, year):
    """
    PLデータのマッピングを作成する
    
    Args:
        ja_code: JAコード
        year: 年度
    """
    with app.app_context():
        # CSVデータの確認
        csv_data = CSVData.query.filter_by(
            ja_code=ja_code, 
            year=year, 
            file_type='pl'
        ).all()
        
        if not csv_data:
            logger.warning(f"PLデータが見つかりません: JA={ja_code}, 年度={year}")
            return False
            
        logger.info(f"PLデータ件数: {len(csv_data)}")
        
        # 現在のマッピングの確認
        existing_mappings = AccountMapping.query.filter_by(
            ja_code=ja_code,
            financial_statement='pl'
        ).all()
        
        logger.info(f"現在のマッピング件数: {len(existing_mappings)}")
        
        # 標準勘定科目の取得
        standard_accounts = StandardAccount.query.filter_by(
            financial_statement='pl'
        ).all()
        
        standard_account_dict = {account.name: account for account in standard_accounts}
        logger.info(f"標準勘定科目数: {len(standard_account_dict)}")
        
        # マッピングの追加
        mappings_to_add = []
        mappings_added = 0
        
        # 主要なPL科目のマッピング定義
        pl_mappings = {
            '経常収益': '40000',  # 経常収益
            '資金運用収益': '41000',  # 資金運用収益
            '貸出金利息': '41100',  # 貸出金利息
            '預け金利息': '41200',  # 預け金利息
            '有価証券利息配当金': '41300',  # 有価証券利息配当金
            'その他の資金運用収益': '41400',  # その他の資金運用収益
            '役務取引等収益': '41500',  # 役務取引等収益
            '受入手数料': '41510',  # 受入手数料
            'その他の役務取引等収益': '41520',  # その他の役務取引等収益
            'その他経常収益': '41700',  # その他経常収益
            '経常費用': '50000',  # 経常費用
            '資金調達費用': '51000',  # 資金調達費用
            '預金利息': '51100',  # 預金利息
            '譲渡性預金利息': '51120',  # 譲渡性預金利息
            '借用金利息': '51130',  # 借用金利息
            '役務取引等費用': '51500',  # 役務取引等費用
            '支払手数料': '51510',  # 支払手数料
            'その他の役務取引等費用': '51520',  # その他の役務取引等費用
            'その他経常費用': '51900',  # その他経常費用
            '経常利益': '60000',  # 経常利益
            '特別利益': '70000',  # 特別利益
            '特別損失': '75000',  # 特別損失
            '税引前当期利益': '80000',  # 税引前当期利益
            '法人税等': '85000',  # 法人税、住民税及び事業税
            '法人税等調整額': '86000',  # 法人税等調整額
            '当期純利益': '90000',  # 当期純利益
            '当期首繰越利益剰余金': '91000',  # 当期首繰越剰余金
            '当期未処分剰余金': '93000'   # 当期未処分剰余金
        }
        
        # 現在のマッピングを辞書化
        existing_mapping_dict = {}
        for mapping in existing_mappings:
            existing_mapping_dict[mapping.original_account_name] = mapping
        
        # CSVデータを処理
        for data in csv_data:
            account_name = data.account_name
            
            # すでにマッピングが存在する場合はスキップ
            if account_name in existing_mapping_dict:
                logger.info(f"すでにマッピングが存在します: {account_name}")
                continue
                
            # マッピングの作成
            if account_name in pl_mappings:
                standard_code = pl_mappings[account_name]
                
                # 標準勘定科目の名前を取得
                standard_name = None
                for std_account in standard_accounts:
                    if std_account.code == standard_code:
                        standard_name = std_account.name
                        break
                
                if not standard_name:
                    logger.warning(f"標準勘定科目名が見つかりません: {standard_code}")
                    standard_name = account_name
                
                # 新しいマッピングを作成
                new_mapping = AccountMapping(
                    ja_code=ja_code,
                    original_account_name=account_name,
                    standard_account_code=standard_code,
                    standard_account_name=standard_name,
                    financial_statement='pl',
                    confidence=1.0,
                    rationale=f"自動マッピング（{account_name} → {standard_code}）"
                )
                
                mappings_to_add.append(new_mapping)
                logger.info(f"マッピングを追加: {account_name} → {standard_code} ({standard_name})")
                
                # CSVデータをマッピング済みにマーク
                data.is_mapped = True
                
        # データベースに保存
        if mappings_to_add:
            db.session.add_all(mappings_to_add)
            db.session.commit()
            mappings_added = len(mappings_to_add)
            logger.info(f"{mappings_added}件のマッピングを追加しました")
        else:
            logger.info("追加するマッピングはありませんでした")
            
        return mappings_added

def fix_pl_balances(ja_code, year):
    """
    PLの残高を修正する
    
    Args:
        ja_code: JAコード
        year: 年度
    """
    with app.app_context():
        # 残高の再作成をトリガー
        from create_account_balances import create_standard_account_balances
        count = create_standard_account_balances(ja_code, year, 'pl')
        logger.info(f"{count}件の残高を作成または更新しました")
        
        return count

if __name__ == "__main__":
    ja_code = "JA001"
    year = 2021
    
    logger.info(f"PLのマッピング修正を開始: JA={ja_code}, 年度={year}")
    
    # マッピングの作成
    mappings_added = create_pl_mappings(ja_code, year)
    logger.info(f"マッピング追加結果: {mappings_added}件")
    
    # 残高の修正
    if mappings_added > 0:
        balance_count = fix_pl_balances(ja_code, year)
        logger.info(f"残高修正結果: {balance_count}件")
    else:
        logger.info("マッピングが追加されなかったため、残高の修正はスキップします")