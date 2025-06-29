"""
AIによる勘定科目マッピングのためのルール定義
"""
import logging
from ai_account_mapper import AIAccountMapper

# ロガーの設定
logger = logging.getLogger(__name__)

def apply_ja_deposit_account_rules(mapper):
    """
    JAの預金科目マッピングルールをAIマッパーに適用する
    
    預金関連科目（当座預金、普通預金、定期預金、定期積金、譲渡性預金等）は
    JAでは預かり金として扱われるため、必ず負債科目にマッピングするルールを追加
    
    Args:
        mapper: AIAccountMapperインスタンス
    """
    if not isinstance(mapper, AIAccountMapper):
        logger.warning("AIAccountMapperインスタンスが渡されていません")
        return False
    
    # 追加のプロンプト指示
    deposit_rule = """
    特別なルール: JAの「預金」（当座預金、普通預金、定期預金、定期積金、譲渡性預金等）は、
    金融機関として預かり金であるため、必ず負債科目として分類します。
    これらの科目が資産科目として誤って分類されないよう注意してください。
    """
    
    # マッピングプロンプトに追加
    if hasattr(mapper, '_add_special_rule'):
        mapper._add_special_rule('deposit_accounts', deposit_rule)
        logger.info("JAの預金科目に関する特別ルールを追加しました")
        return True
    else:
        logger.warning("AIAccountMapperに特別ルール追加機能がありません")
        return False

def get_ja_deposit_account_rules():
    """
    JAの預金科目マッピングルールを文字列として取得
    
    Returns:
        str: マッピングルールの説明
    """
    rules_description = """
    # JAの預金科目マッピングルール
    
    JAの財務諸表において、「預金」関連科目（当座預金、普通預金、定期預金、定期積金、譲渡性預金等）は
    金融機関である農協（JA）が顧客から預かったお金であるため、
    負債科目として分類する必要があります。
    
    これらが誤って資産科目としてマッピングされないように、以下のルールを適用します：
    
    1. 科目名に「預金」「定期積金」「譲渡性預金」などの文字列を含む場合は、
       負債カテゴリの適切な科目にマッピングする
       
    2. AIマッピング時には、「JAの『預金』は負債科目として分類する」という
       特別なルールをプロンプトに含める
       
    3. マッピング修正時には、誤って資産科目にマッピングされた預金関連科目を
       適切な負債科目に修正する
    """
    
    return rules_description