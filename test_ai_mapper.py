import logging
import sys
from openai import OpenAI

# 詳細なログ出力を有効化
logging.basicConfig(level=logging.DEBUG, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                   stream=sys.stdout)
logger = logging.getLogger(__name__)

# サンプルを実行するための最小限の実装
def test_ai_mapping():
    try:
        # AIAccountMapperクラスをインポート
        from ai_account_mapper import AIAccountMapper
        
        # インスタンス化
        mapper = AIAccountMapper()
        
        # クライアント初期化状態の確認
        if mapper.client:
            logger.info("OpenAI client initialized successfully")
        else:
            logger.warning("OpenAI client not initialized, using fallback")
        
        # 任意の勘定科目でマッピングをテスト
        account_name = "現金及び預金"
        file_type = "bs"
        
        # 文字列類似度マッピングをテスト
        logger.info(f"Testing string similarity mapping for '{account_name}'")
        result = mapper.string_similarity_mapping(account_name, file_type)
        logger.info(f"String similarity result: {result}")
        
        # AI通信をスキップしたテスト（問題の切り分け）
        return result
    
    except Exception as e:
        logger.error(f"Error in test_ai_mapping: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None

if __name__ == "__main__":
    # テスト実行
    result = test_ai_mapping()
    print(f"\nFinal result: {result}")