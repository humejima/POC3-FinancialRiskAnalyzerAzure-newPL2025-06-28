import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# OpenAIモジュールが正しくインポートできるか確認
try:
    from openai import OpenAI
    has_openai = True
    logger.info("OpenAI module imported successfully")
except ImportError as e:
    has_openai = False
    logger.error(f"Failed to import OpenAI: {e}")

# APIキー確認
openai_api_key = os.environ.get("OPENAI_API_KEY")
if openai_api_key:
    logger.info("OPENAI_API_KEY found in environment")
else:
    logger.error("OPENAI_API_KEY not found in environment")

# クライアント初期化
if has_openai and openai_api_key:
    try:
        client = OpenAI(api_key=openai_api_key)
        logger.info("OpenAI client initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize OpenAI client: {e}")