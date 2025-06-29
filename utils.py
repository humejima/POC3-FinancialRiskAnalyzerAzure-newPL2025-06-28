import unicodedata
import logging
import re

logger = logging.getLogger(__name__)

def normalize_string(text, for_db=True):
    """
    文字列を正規化して、データベース操作のためのエラーを防止する。
    
    Args:
        text: 正規化する文字列
        for_db: データベース用かどうか（Trueなら厳密にサニタイズする）
        
    Returns:
        str: 正規化された文字列
    """
    if text is None:
        return None
        
    # 文字列型でなければ変換
    if not isinstance(text, str):
        text = str(text)
    
    try:
        # Unicodeの正規化（NFKC）
        normalized = unicodedata.normalize('NFKC', text)
        
        if for_db:
            # データベース用にさらに特殊文字を除去
            # Control characters and non-printable characters
            normalized = re.sub(r'[\x00-\x1F\x7F-\x9F]', '', normalized)
            
            # エンコードしてからデコードして問題ないか確認
            try:
                normalized.encode('utf-8', errors='strict')
            except UnicodeEncodeError:
                logger.warning(f"文字列エンコードエラーを修正: {text}")
                normalized = normalized.encode('utf-8', errors='ignore').decode('utf-8', errors='ignore')
                
        return normalized
    except Exception as e:
        logger.error(f"文字列正規化中にエラー発生: {str(e)}, 元の文字列: {text}")
        # 非常に問題のある文字列の場合は、安全なASCII文字列に置き換え
        if for_db:
            return text.encode('ascii', errors='ignore').decode('ascii', errors='ignore')
        return text