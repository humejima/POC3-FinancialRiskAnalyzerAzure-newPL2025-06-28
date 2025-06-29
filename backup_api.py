"""
バックアップ機能用APIエンドポイント
データ管理画面から呼び出されるバックアップとリストア機能
"""

from flask import request, jsonify, session
from app import app, db
import logging

logger = logging.getLogger(__name__)

def register_backup_api_endpoints(app):
    """バックアップAPI エンドポイントを登録する関数"""
    
    @app.route('/api/create_backup', methods=['POST'])
    def api_create_backup():
        """APIエンドポイント：データバックアップ作成"""
        try:
            data = request.get_json()
            ja_code = data.get('ja_code')
            year = data.get('year')
            description = data.get('description', 'manual_backup')
            
            if not ja_code or not year:
                return jsonify({'success': False, 'message': 'JA code and year are required'}), 400
            
            from backup_system import create_automatic_backup
            result = create_automatic_backup(ja_code, year, description)
            
            logger.info(f"バックアップ作成完了: JA={ja_code}, 年度={year}, 結果={result['success']}")
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"Backup creation error: {str(e)}")
            return jsonify({'success': False, 'message': f'バックアップ作成エラー: {str(e)}'}), 500

    @app.route('/api/list_backups')
    def api_list_backups():
        """APIエンドポイント：バックアップファイル一覧取得"""
        try:
            from backup_system import DataBackupSystem
            backup_system = DataBackupSystem()
            backups = backup_system.list_backups()
            
            logger.info(f"バックアップ一覧取得: {len(backups)}件")
            return jsonify({
                'success': True,
                'backups': backups
            })
            
        except Exception as e:
            logger.error(f"Backup list error: {str(e)}")
            return jsonify({'success': False, 'message': f'バックアップ一覧取得エラー: {str(e)}'}), 500

    @app.route('/api/restore_backup', methods=['POST'])
    def api_restore_backup():
        """APIエンドポイント：バックアップからデータ復元"""
        try:
            data = request.get_json()
            backup_filename = data.get('backup_filename')
            confirm_restore = data.get('confirm_restore', False)
            
            if not backup_filename:
                return jsonify({'success': False, 'message': 'Backup filename is required'}), 400
            
            from backup_system import DataBackupSystem
            backup_system = DataBackupSystem()
            
            # バックアップファイルのフルパスを構築
            backup_filepath = f"{backup_system.backup_dir}/{backup_filename}"
            
            result = backup_system.restore_mapping_data(backup_filepath, confirm_restore)
            
            if result['success']:
                logger.info(f"データ復元完了: {backup_filename}")
            else:
                logger.warning(f"データ復元失敗: {backup_filename}, 理由: {result['message']}")
                
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"Backup restore error: {str(e)}")
            return jsonify({'success': False, 'message': f'データ復元エラー: {str(e)}'}), 500