"""
JA財務分析システム データバックアップ機能
標準勘定科目残高データとマッピングデータの保護
"""

import os
import json
import sqlite3
from datetime import datetime
from app import app, db
from models import StandardAccountBalance, AccountMapping, CSVData
from sqlalchemy import text

class DataBackupSystem:
    """データバックアップシステム"""
    
    def __init__(self):
        self.backup_dir = 'data_backups'
        os.makedirs(self.backup_dir, exist_ok=True)
    
    def create_mapping_backup(self, ja_code, year, description="auto"):
        """
        マッピングデータのバックアップを作成
        
        Args:
            ja_code: JA code
            year: Financial year
            description: バックアップの説明
            
        Returns:
            str: バックアップファイルのパス
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"mapping_backup_{ja_code}_{year}_{timestamp}_{description}.json"
        filepath = os.path.join(self.backup_dir, filename)
        
        with app.app_context():
            # マッピングデータを取得
            mappings = AccountMapping.query.filter_by(ja_code=ja_code).all()
            csv_data = CSVData.query.filter_by(ja_code=ja_code, year=year).all()
            
            backup_data = {
                'backup_info': {
                    'timestamp': timestamp,
                    'ja_code': ja_code,
                    'year': year,
                    'description': description,
                    'total_mappings': len(mappings),
                    'total_csv_records': len(csv_data)
                },
                'mappings': [
                    {
                        'id': m.id,
                        'original_account_name': m.original_account_name,
                        'standard_account_code': m.standard_account_code,
                        'standard_account_name': m.standard_account_name,
                        'confidence': m.confidence,
                        'financial_statement': m.financial_statement,
                        'rationale': m.rationale
                    } for m in mappings
                ],
                'csv_data': [
                    {
                        'id': c.id,
                        'account_name': c.account_name,
                        'current_value': float(c.current_value) if c.current_value else 0,
                        'previous_value': float(c.previous_value) if c.previous_value else 0,
                        'file_type': c.file_type,
                        'is_mapped': c.is_mapped,
                        'row_number': c.row_number,
                        'category': c.category
                    } for c in csv_data
                ]
            }
            
            # JSONファイルに保存
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, ensure_ascii=False, indent=2)
        
        print(f"✓ マッピングバックアップ作成完了: {filename}")
        return filepath
    
    def create_balance_backup(self, ja_code, year, financial_statement="bs", description="auto"):
        """
        残高データのバックアップを作成
        
        Args:
            ja_code: JA code
            year: Financial year
            financial_statement: bs, pl, cf
            description: バックアップの説明
            
        Returns:
            str: バックアップファイルのパス
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"balance_backup_{ja_code}_{year}_{financial_statement}_{timestamp}_{description}.json"
        filepath = os.path.join(self.backup_dir, filename)
        
        with app.app_context():
            # 残高データを取得（正しいフィールド名を使用）
            balances = StandardAccountBalance.query.filter_by(
                ja_code=ja_code, 
                year=year
            ).all()
            
            # 指定された財務諸表タイプでフィルタリング
            filtered_balances = []
            for balance in balances:
                # statement_typeで直接フィルタリング
                if balance.statement_type == financial_statement:
                    filtered_balances.append(balance)
            
            balances = filtered_balances
            
            backup_data = {
                'backup_info': {
                    'timestamp': timestamp,
                    'ja_code': ja_code,
                    'year': year,
                    'financial_statement': financial_statement,
                    'description': description,
                    'total_balances': len(balances)
                },
                'balances': [
                    {
                        'id': b.id,
                        'standard_account_code': b.standard_account_code,
                        'standard_account_name': b.standard_account_name,
                        'current_value': float(b.current_value) if b.current_value else 0,
                        'previous_value': float(b.previous_value) if b.previous_value else 0,
                        'statement_type': b.statement_type,
                        'statement_subtype': b.statement_subtype
                    } for b in balances
                ]
            }
            
            # JSONファイルに保存
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, ensure_ascii=False, indent=2)
        
        print(f"✓ 残高バックアップ作成完了: {filename}")
        return filepath
    
    def check_existing_data(self, ja_code, year):
        """
        既存データの状況を確認する
        
        Args:
            ja_code: JA code
            year: Financial year
            
        Returns:
            dict: 既存データの情報
        """
        with app.app_context():
            from models import AccountMapping, CSVData, StandardAccountBalance
            
            mapping_count = AccountMapping.query.filter_by(ja_code=ja_code).count()
            csv_count = CSVData.query.filter_by(ja_code=ja_code, year=year).count()
            balance_count = StandardAccountBalance.query.filter_by(ja_code=ja_code, year=year).count()
            
            return {
                'mapping_records': mapping_count,
                'csv_records': csv_count,
                'balance_records': balance_count,
                'has_existing_data': (mapping_count > 0 or csv_count > 0 or balance_count > 0)
            }

    def restore_mapping_data(self, backup_filepath, confirm_restore=False):
        """
        マッピングデータの復元
        
        Args:
            backup_filepath: バックアップファイルのパス
            confirm_restore: 復元実行の確認
            
        Returns:
            dict: 復元結果
        """
        if not os.path.exists(backup_filepath):
            return {'success': False, 'message': 'バックアップファイルが見つかりません'}
        
        try:
            with open(backup_filepath, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)
            
            ja_code = backup_data['backup_info']['ja_code']
            year = backup_data['backup_info']['year']
            
            # 既存データの確認
            existing_data = self.check_existing_data(ja_code, year)
            
            if not confirm_restore:
                return {
                    'success': False,
                    'message': '復元を実行するには confirm_restore=True を設定してください',
                    'backup_info': backup_data['backup_info'],
                    'existing_data': existing_data
                }
            
            with app.app_context():
                # 既存データを削除（注意：完全削除）
                deleted_mappings = AccountMapping.query.filter_by(ja_code=ja_code).delete()
                deleted_csv = CSVData.query.filter_by(ja_code=ja_code, year=year).delete()
                deleted_balances = StandardAccountBalance.query.filter_by(ja_code=ja_code, year=year).delete()
                
                # バックアップデータを復元
                for mapping_data in backup_data['mappings']:
                    mapping = AccountMapping()
                    mapping.ja_code = ja_code
                    mapping.original_account_name = mapping_data['original_account_name']
                    mapping.standard_account_code = mapping_data['standard_account_code']
                    mapping.standard_account_name = mapping_data['standard_account_name']
                    mapping.confidence = mapping_data['confidence']
                    mapping.financial_statement = mapping_data.get('financial_statement', 'bs')
                    mapping.rationale = mapping_data.get('rationale', 'バックアップから復元')
                    db.session.add(mapping)
                
                for csv_data in backup_data['csv_data']:
                    csv_record = CSVData()
                    csv_record.ja_code = ja_code
                    csv_record.year = year
                    csv_record.account_name = csv_data['account_name']
                    csv_record.current_value = csv_data.get('balance', 0)
                    csv_record.file_type = csv_data['file_type']
                    csv_record.is_mapped = csv_data['is_mapped']
                    csv_record.row_number = csv_data['row_number']
                    db.session.add(csv_record)
                
                db.session.commit()
                
                return {
                    'success': True,
                    'message': f'データ復元が完了しました',
                    'details': {
                        'deleted_records': {
                            'mappings': deleted_mappings,
                            'csv_data': deleted_csv,
                            'balances': deleted_balances
                        },
                        'restored_records': {
                            'mappings': len(backup_data["mappings"]),
                            'csv_data': len(backup_data["csv_data"])
                        },
                        'backup_timestamp': backup_data['backup_info']['timestamp']
                    }
                }
                
        except Exception as e:
            return {'success': False, 'message': f'復元エラー: {str(e)}'}
    
    def list_backups(self):
        """利用可能なバックアップファイルをリスト表示"""
        backups = []
        for filename in os.listdir(self.backup_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(self.backup_dir, filename)
                stats = os.stat(filepath)
                backups.append({
                    'filename': filename,
                    'size': stats.st_size,
                    'created': datetime.fromtimestamp(stats.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                })
        
        backups.sort(key=lambda x: x['created'], reverse=True)
        return backups


def create_automatic_backup(ja_code, year, description="before_operation"):
    """
    処理前の自動バックアップ作成
    
    Args:
        ja_code: JA code
        year: Financial year
        description: バックアップの説明
        
    Returns:
        dict: バックアップ結果
    """
    backup_system = DataBackupSystem()
    
    try:
        # マッピングデータのバックアップ
        mapping_backup = backup_system.create_mapping_backup(ja_code, year, description)
        
        # 各財務諸表の残高データバックアップ
        balance_backups = []
        for fs in ['bs', 'pl', 'cf']:
            balance_backup = backup_system.create_balance_backup(ja_code, year, fs, description)
            balance_backups.append(balance_backup)
        
        return {
            'success': True,
            'mapping_backup': mapping_backup,
            'balance_backups': balance_backups,
            'message': 'データバックアップが正常に作成されました'
        }
        
    except Exception as e:
        return {
            'success': False,
            'message': f'バックアップ作成エラー: {str(e)}'
        }


if __name__ == "__main__":
    # テスト実行
    print("=== データバックアップシステム テスト ===")
    
    # JA001のバックアップを作成
    result = create_automatic_backup('JA001', 2021, 'test_backup')
    print(f"バックアップ結果: {result}")
    
    # バックアップリストを表示
    backup_system = DataBackupSystem()
    backups = backup_system.list_backups()
    print("\n利用可能なバックアップ:")
    for backup in backups:
        print(f"  {backup['filename']} ({backup['size']} bytes, {backup['created']})")