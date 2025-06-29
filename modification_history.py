"""
修正履歴管理システム
過去の修正を記録し、類似の問題を検出して同じ修正を繰り返さないようにする
"""

import os
import json
import hashlib
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from difflib import SequenceMatcher
import re

logger = logging.getLogger(__name__)

# AGENTメッセージの日本語化辞書
AGENT_MESSAGE_TRANSLATIONS = {
    "Error": "エラー",
    "Warning": "警告",
    "Info": "情報",
    "Debug": "デバッグ",
    "Success": "成功",
    "Failed": "失敗",
    "Processing": "処理中",
    "Completed": "完了",
    "Starting": "開始",
    "Finished": "終了",
    "Database connection": "データベース接続",
    "File not found": "ファイルが見つかりません",
    "Permission denied": "アクセス権限がありません",
    "Invalid input": "無効な入力です",
    "Connection timeout": "接続がタイムアウトしました",
    "Internal server error": "内部サーバーエラー",
    "Bad request": "不正なリクエスト",
    "Unauthorized": "認証されていません",
    "Forbidden": "アクセスが禁止されています",
    "Not found": "見つかりません",
    "Method not allowed": "メソッドが許可されていません",
    "Conflict": "競合が発生しました",
    "Validation error": "検証エラー",
    "Import successful": "インポートが成功しました",
    "Export completed": "エクスポートが完了しました",
    "Data backup created": "データバックアップが作成されました",
    "Configuration updated": "設定が更新されました",
    "User authentication": "ユーザー認証",
    "Session expired": "セッションが期限切れです",
    "Request processed": "リクエストが処理されました",
    "System maintenance": "システムメンテナンス"
}

def translate_agent_message(message: str) -> str:
    """
    AGENTメッセージを日本語に翻訳する

    Args:
        message: 英語のメッセージ

    Returns:
        str: 日本語に翻訳されたメッセージ
    """
    if not message:
        return message

    # 完全一致での翻訳を試行
    if message in AGENT_MESSAGE_TRANSLATIONS:
        return AGENT_MESSAGE_TRANSLATIONS[message]

    # 部分一致での翻訳を試行
    translated_message = message
    for english_term, japanese_term in AGENT_MESSAGE_TRANSLATIONS.items():
        # 大文字小文字を無視して置換
        pattern = re.compile(re.escape(english_term), re.IGNORECASE)
        translated_message = pattern.sub(japanese_term, translated_message)

    return translated_message

@dataclass
class ModificationRecord:
    """修正記録のデータクラス"""
    id: str
    timestamp: str
    issue_type: str
    description: str
    file_paths: List[str]
    code_changes: Dict[str, str]  # ファイルパス -> 変更内容
    solution_steps: List[str]
    error_messages: List[str]
    success: bool
    tags: List[str]
    related_functions: List[str]
    impact_level: str  # low, medium, high

    def translate_messages(self):
        """レコード内のメッセージを日本語化する"""
        self.description = translate_agent_message(self.description)
        self.solution_steps = [translate_agent_message(step) for step in self.solution_steps]
        self.error_messages = [translate_agent_message(msg) for msg in self.error_messages]

class ModificationHistoryManager:
    """修正履歴管理クラス"""

    def __init__(self, history_file='modification_history.json'):
        self.history_file = history_file
        self.history = self._load_history()

    def _load_history(self) -> List[Dict]:
        """履歴ファイルを読み込む"""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"履歴ファイル読み込みエラー: {e}")
                return []
        return []

    def _save_history(self):
        """履歴をファイルに保存"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"履歴ファイル保存エラー: {e}")

    def generate_issue_hash(self, issue_description: str, error_messages: List[str]) -> str:
        """問題の特徴からハッシュを生成"""
        content = f"{issue_description}{''.join(error_messages)}"
        return hashlib.md5(content.encode('utf-8')).hexdigest()[:12]

    def record_modification(self, 
                          issue_type: str,
                          description: str,
                          file_paths: List[str],
                          code_changes: Dict[str, str],
                          solution_steps: List[str],
                          error_messages: List[str] = None,
                          tags: List[str] = None,
                          related_functions: List[str] = None,
                          impact_level: str = "medium",
                          auto_translate: bool = True) -> str:
        """修正を記録"""

        error_messages = error_messages or []
        tags = tags or []
        related_functions = related_functions or []

        record_id = self.generate_issue_hash(description, error_messages)

        record = ModificationRecord(
            id=record_id,
            timestamp=datetime.now().isoformat(),
            issue_type=issue_type,
            description=description,
            file_paths=file_paths,
            code_changes=code_changes,
            solution_steps=solution_steps,
            error_messages=error_messages,
            success=True,
            tags=tags,
            related_functions=related_functions,
            impact_level=impact_level
        )

        if auto_translate:
            record.translate_messages()

        # 既存の記録をチェック
        existing = self.find_similar_modifications(description, error_messages)
        if existing:
            logger.warning(f"類似の修正が過去に実行されています: {existing[0]['id']}")
            self._update_existing_record(record_id, record)
        else:
            self.history.append(asdict(record))

        self._save_history()
        logger.info(f"修正記録を保存しました: {record_id}")
        return record_id

    def _update_existing_record(self, record_id: str, new_record: ModificationRecord):
        """既存の記録を更新"""
        for i, record in enumerate(self.history):
            if record['id'] == record_id:
                record['timestamp'] = new_record.timestamp
                record['solution_steps'].extend(new_record.solution_steps)
                break
        else:
            self.history.append(asdict(new_record))

    def find_similar_modifications(self, 
                                 description: str, 
                                 error_messages: List[str] = None,
                                 similarity_threshold: float = 0.7) -> List[Dict]:
        """類似の修正を検索"""
        error_messages = error_messages or []
        similar_records = []

        for record in self.history:
            # 説明文の類似度チェック
            desc_similarity = SequenceMatcher(None, description.lower(), record['description'].lower()).ratio()

            # エラーメッセージの類似度チェック
            error_similarity = 0
            if error_messages and record['error_messages']:
                for err1 in error_messages:
                    for err2 in record['error_messages']:
                        sim = SequenceMatcher(None, err1.lower(), err2.lower()).ratio()
                        error_similarity = max(error_similarity, sim)

            # 総合的な類似度
            overall_similarity = max(desc_similarity, error_similarity)

            if overall_similarity >= similarity_threshold:
                record_copy = record.copy()
                record_copy['similarity_score'] = overall_similarity
                similar_records.append(record_copy)

        return sorted(similar_records, key=lambda x: x['similarity_score'], reverse=True)

    def check_before_modification(self, issue_description: str, error_messages: List[str] = None) -> Dict:
        """修正前にチェックして類似の問題があるか確認"""
        similar = self.find_similar_modifications(issue_description, error_messages)

        result = {
            'should_proceed': True,
            'similar_modifications': similar,
            'recommendations': []
        }

        if similar:
            result['should_proceed'] = False
            result['recommendations'] = [
                f"類似の修正が過去に実行されています（{len(similar)}件）",
                "以下の解決方法を参考にしてください："
            ]

            for mod in similar[:3]:  # 上位3件を表示
                result['recommendations'].append(f"- {mod['description']}")
                result['recommendations'].extend([f"  手順: {step}" for step in mod['solution_steps'][:2]])

        return result

    def get_modification_stats(self) -> Dict:
        """修正統計を取得"""
        if not self.history:
            return {'total': 0, 'by_type': {}, 'recent': []}

        stats = {
            'total': len(self.history),
            'by_type': {},
            'by_impact': {},
            'recent': []
        }

        # タイプ別統計
        for record in self.history:
            issue_type = record['issue_type']
            stats['by_type'][issue_type] = stats['by_type'].get(issue_type, 0) + 1

            impact = record['impact_level']
            stats['by_impact'][impact] = stats['by_impact'].get(impact, 0) + 1

        # 最新5件
        sorted_history = sorted(self.history, key=lambda x: x['timestamp'], reverse=True)
        stats['recent'] = sorted_history[:5]

        return stats

    def generate_recommendations(self, current_issue: str) -> List[str]:
        """現在の問題に対する推奨事項を生成"""
        similar = self.find_similar_modifications(current_issue)
        recommendations = []

        if similar:
            recommendations.append("⚠️  類似の問題が過去に発生しています")
            for mod in similar[:2]:
                recommendations.append(f"📋 過去の解決方法: {mod['description']}")
                recommendations.extend([f"   • {step}" for step in mod['solution_steps'][:3]])
        else:
            recommendations.append("✅ 新しい問題です。解決後は履歴に記録されます")

        return recommendations

# グローバルインスタンス
modification_manager = ModificationHistoryManager()

def log_modification(issue_type: str, description: str, **kwargs) -> str:
    """修正をログに記録するヘルパー関数"""
    return modification_manager.record_modification(issue_type, description, **kwargs)

def check_similar_issues(description: str, error_messages: List[str] = None) -> Dict:
    """類似問題をチェックするヘルパー関数"""
    return modification_manager.check_before_modification(description, error_messages)

if __name__ == "__main__":
    # テスト実行
    manager = ModificationHistoryManager()

    # サンプル修正を記録
    manager.record_modification(
        issue_type="データベースエラー",
        description="flask db コマンドが見つからないエラー",
        file_paths=["main.py", "app.py"],
        code_changes={
            "main.py": "Flask-Migrateの初期化を追加"
        },
        solution_steps=[
            "Flask-Migrateをインストール",
            "app.pyにMigrateを追加",
            "flask db initを実行"
        ],
        error_messages=["Error: No such command 'db'"],
        tags=["flask", "migrate", "database"],
        related_functions=["init_db"],
        impact_level="medium"
    )

    # 統計を表示
    stats = manager.get_modification_stats()
    print("=== 修正履歴統計 ===")
    print(f"総修正数: {stats['total']}")
    print(f"タイプ別: {stats['by_type']}")