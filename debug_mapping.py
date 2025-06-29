import unicodedata
import re
import logging
from app import app, db
from models import StandardAccount, CSVData, AccountMapping

# ロギングの設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def normalize_account_name(name):
    """勘定科目名を正規化する（空白、全角/半角、カッコなどを処理）"""
    if not name:
        return ""
        
    # 全角を半角に変換
    name = unicodedata.normalize('NFKC', name)
    
    # 空白、括弧、記号を削除
    name = re.sub(r'[\s\(\)\[\]\{\}\.,。、・･：:「」『』【】"\']+', '', name)
    
    # 数字を削除
    name = re.sub(r'\d+', '', name)
    
    # 小文字に変換
    name = name.lower()
    
    return name

def debug_mapping():
    """データベース内のデータを調査してマッピングの問題を特定する"""
    with app.app_context():
        # 標準勘定科目の取得
        bs_accounts = StandardAccount.query.filter_by(financial_statement='bs').all()
        logger.info(f"標準BS勘定科目数: {len(bs_accounts)}")
        
        # 標準勘定科目の一部を表示
        for account in bs_accounts[:5]:
            logger.info(f"標準科目: {account.code} - {account.name}")
            logger.info(f"  正規化後: {normalize_account_name(account.name)}")
        
        # 実際のCSVデータの取得
        csv_data = CSVData.query.filter_by(file_type='bs', is_mapped=False).all()
        logger.info(f"未マッピングBSデータ数: {len(csv_data)}")
        
        # CSVデータの一部を表示
        for data in csv_data[:5]:
            logger.info(f"CSVデータ: [JA: {data.ja_code}] [Row: {data.row_number}] {data.account_name}")
            logger.info(f"  正規化後: {normalize_account_name(data.account_name)}")
        
        # 標準勘定科目の名前と正規化された名前のキーワードリスト作成
        # "土地"や"建物"のような単純なキーワードを検索
        keyword_dict = {}
        for account in bs_accounts:
            if len(account.name) <= 10:  # 短めの名前のみをキーワードとして扱う
                keyword = normalize_account_name(account.name)
                keyword_dict[keyword] = account.code
        
        logger.info(f"キーワード数: {len(keyword_dict)}")
        logger.info(f"キーワード例: {list(keyword_dict.items())[:10]}")
        
        # 正規化後のマッピングを作成
        standard_name_to_code = {}
        standard_normalized_to_code = {}
        
        for account in bs_accounts:
            standard_name_to_code[account.name] = account.code
            normalized = normalize_account_name(account.name)
            standard_normalized_to_code[normalized] = account.code
        
        # CSVデータと標準勘定科目の一致をチェック
        exact_match_count = 0
        normalized_match_count = 0
        keyword_match_count = 0
        no_match_count = 0
        
        for data in csv_data:
            if data.account_name in standard_name_to_code:
                logger.info(f"完全一致: {data.account_name}")
                exact_match_count += 1
            else:
                normalized = normalize_account_name(data.account_name)
                if normalized in standard_normalized_to_code:
                    std_code = standard_normalized_to_code[normalized]
                    std_account = StandardAccount.query.filter_by(code=std_code).first()
                    logger.info(f"正規化後一致: {data.account_name} -> {std_account.name}")
                    normalized_match_count += 1
                else:
                    # キーワード検索
                    keyword_match = False
                    for keyword, code in keyword_dict.items():
                        if keyword in normalized:
                            std_account = StandardAccount.query.filter_by(code=code).first()
                            logger.info(f"キーワード一致: {data.account_name} -> {std_account.name} (キーワード: {keyword})")
                            keyword_match = True
                            keyword_match_count += 1
                            break
                            
                    if not keyword_match:
                        logger.info(f"一致なし: {data.account_name}")
                        no_match_count += 1
        
        logger.info(f"完全一致: {exact_match_count}, 正規化後一致: {normalized_match_count}, キーワード一致: {keyword_match_count}, 一致なし: {no_match_count}")

if __name__ == "__main__":
    debug_mapping()