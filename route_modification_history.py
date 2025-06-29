"""
修正履歴管理用のFlaskルート
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from modification_history import modification_manager, check_similar_issues, log_modification
import logging

logger = logging.getLogger(__name__)

modification_bp = Blueprint('modification_history', __name__)

@modification_bp.route('/modification_history')
def view_history():
    """修正履歴の一覧表示"""
    try:
        stats = modification_manager.get_modification_stats()
        return render_template('modification_history.html', 
                             history=modification_manager.history,
                             stats=stats)
    except Exception as e:
        logger.error(f"修正履歴表示エラー: {e}")
        flash(f"修正履歴の表示中にエラーが発生しました: {e}", 'error')
        return redirect(url_for('index'))

@modification_bp.route('/check_similar_issue', methods=['POST'])
def check_similar_issue():
    """類似問題のチェック"""
    try:
        data = request.get_json()
        description = data.get('description', '')
        error_messages = data.get('error_messages', [])

        result = check_similar_issues(description, error_messages)
        return jsonify(result)
    except Exception as e:
        logger.error(f"類似問題チェックエラー: {e}")
        return jsonify({'error': str(e)}), 500

@modification_bp.route('/record_modification', methods=['POST'])
def record_modification():
    """修正の手動記録"""
    try:
        data = request.get_json()

        record_id = log_modification(
            issue_type=data.get('issue_type', ''),
            description=data.get('description', ''),
            file_paths=data.get('file_paths', []),
            code_changes=data.get('code_changes', {}),
            solution_steps=data.get('solution_steps', []),
            error_messages=data.get('error_messages', []),
            tags=data.get('tags', []),
            related_functions=data.get('related_functions', []),
            impact_level=data.get('impact_level', 'medium')
        )

        return jsonify({'success': True, 'record_id': record_id})
    except Exception as e:
        logger.error(f"修正記録エラー: {e}")
        return jsonify({'error': str(e)}), 500

@modification_bp.route('/api/modification_recommendations/<path:issue>')
def get_recommendations(issue):
    """問題に対する推奨事項を取得"""
    try:
        recommendations = modification_manager.generate_recommendations(issue)
        return jsonify({'recommendations': recommendations})
    except Exception as e:
        logger.error(f"推奨事項取得エラー: {e}")
        return jsonify({'error': str(e)}), 500

def register_modification_routes(app):
    """修正履歴ルートを登録"""
    app.register_blueprint(modification_bp)
    logger.info("修正履歴ルートが登録されました")