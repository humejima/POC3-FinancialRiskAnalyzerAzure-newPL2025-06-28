"""
Azure OpenAI APIの接続テスト
"""
import os
import json
from openai import AzureOpenAI, OpenAI

def test_azure_openai():
    """Azure OpenAI APIの接続をテストする"""
    print("Azure OpenAI接続テスト")
    
    # 環境変数の取得
    azure_api_key = os.environ.get("AZURE_OPENAI_KEY")
    azure_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
    azure_deployment = os.environ.get("AZURE_OPENAI_DEPLOYMENT")
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    
    # 環境変数チェック
    print(f"AZURE_OPENAI_KEY: {'設定済み' if azure_api_key else '未設定'}")
    print(f"AZURE_OPENAI_ENDPOINT: {'設定済み' if azure_endpoint else '未設定'}")
    print(f"AZURE_OPENAI_DEPLOYMENT: {'設定済み' if azure_deployment else '未設定'}")
    print(f"OPENAI_API_KEY: {'設定済み' if openai_api_key else '未設定'}")
    
    print(f"Azure Endpoint: {azure_endpoint}")
    print(f"Azure Deployment: {azure_deployment}")
    
    # Azure OpenAIをテスト
    if azure_api_key and azure_endpoint and azure_deployment:
        print("\nAzure OpenAIでテスト実行中...")
        try:
            # Azure OpenAIクライアント初期化
            client = AzureOpenAI(
                api_key=azure_api_key,
                api_version="2023-05-15",
                azure_endpoint=azure_endpoint
            )
            
            # API呼び出しパラメータ - 新しいOpenAIタイプ形式を使用
            messages = [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "こんにちは、Azureモデルと正常に接続できていますか？JSONフォーマットで応答してください。"}
            ]
            
            # メッセージ形式の変換（型エラー対策）
            from openai.types.chat import ChatCompletionSystemMessageParam, ChatCompletionUserMessageParam
            typed_messages = [
                ChatCompletionSystemMessageParam(role="system", content="You are a helpful assistant."),
                ChatCompletionUserMessageParam(role="user", content="こんにちは、Azureモデルと正常に接続できていますか？JSONフォーマットで応答してください。")
            ]
            
            # モデル名のデバッグ出力
            print(f"Using model name: {azure_deployment}")
            
            # 両方のパターンを試す
            try:
                print("Trying with model parameter...")
                # API呼び出し（model引数を使用）
                response = client.chat.completions.create(
                    model=azure_deployment,
                    messages=typed_messages,
                    response_format={"type": "json_object"}
                )
                print("model parameter worked!")
            except Exception as e:
                print(f"model parameter failed: {e}")
                print("Trying with deployment_id parameter...")
                # API呼び出し（deployment_id引数を使用）
                # メッセージが必要というエラーが出ているので修正
                response = client.chat.completions.create(
                    deployment_id=azure_deployment,
                    messages=typed_messages,
                    response_format={"type": "json_object"}
                )
                print("deployment_id parameter worked!")
            
            # 結果表示
            content = response.choices[0].message.content
            print(f"Azure OpenAI応答: {content}")
            
            # JSONとして解析
            try:
                if content:
                    json_data = json.loads(content)
                    print("JSON解析成功:")
                    print(json.dumps(json_data, indent=2, ensure_ascii=False))
                else:
                    print("応答が空です")
            except json.JSONDecodeError as e:
                print(f"JSON解析エラー: {e}")
            except Exception as e:
                print(f"その他のJSON処理エラー: {e}")
                
            return True
            
        except Exception as e:
            print(f"Azure OpenAIエラー: {e}")
    else:
        print("Azure OpenAIテストスキップ: 環境変数が不足しています")
    
    # 標準のOpenAIをテスト
    if openai_api_key:
        print("\n標準OpenAIでテスト実行中...")
        try:
            # OpenAIクライアント初期化
            client = OpenAI(api_key=openai_api_key)
            
            # API呼び出し - 型付きメッセージを使用
            from openai.types.chat import ChatCompletionSystemMessageParam, ChatCompletionUserMessageParam
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    ChatCompletionSystemMessageParam(role="system", content="You are a helpful assistant."),
                    ChatCompletionUserMessageParam(role="user", content="こんにちは、OpenAIモデルと正常に接続できていますか？JSONフォーマットで応答してください。")
                ],
                response_format={"type": "json_object"}
            )
            
            # 結果表示
            content = response.choices[0].message.content
            print(f"OpenAI応答: {content}")
            
            # JSONとして解析
            try:
                if content:
                    json_data = json.loads(content)
                    print("JSON解析成功:")
                    print(json.dumps(json_data, indent=2, ensure_ascii=False))
                else:
                    print("応答が空です")
            except json.JSONDecodeError as e:
                print(f"JSON解析エラー: {e}")
            except Exception as e:
                print(f"その他のJSON処理エラー: {e}")
                
            return True
            
        except Exception as e:
            print(f"OpenAIエラー: {e}")
    else:
        print("OpenAIテストスキップ: 環境変数が不足しています")
        
    return False

if __name__ == "__main__":
    test_azure_openai()