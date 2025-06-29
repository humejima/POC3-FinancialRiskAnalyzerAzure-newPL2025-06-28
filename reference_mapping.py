"""
他のJAのマッピング済みデータを参照して新規JAのマッピングを効率化するモジュール

このモジュールは、既に他のJAでマッピングされている勘定科目を参照し、
新しくデータを取り込んだJAの未マッピング勘定科目に対して自動的にマッピングを行います。
マッピングの信頼度が高い（例：0.9以上）データのみを参照することで、精度の高いマッピングを実現します。
"""

import logging
import re
from difflib import SequenceMatcher
from sqlalchemy import func, desc, and_
from app import db
from models import JA, AccountMapping, CSVData, StandardAccount

# ロガー設定
logger = logging.getLogger(__name__)

def normalize_account_name(name, file_type='bs'):
    """
    勘定科目名を正規化する（空白、全角/半角、カッコなどを処理）
    
    Args:
        name: 勘定科目名
        file_type: ファイルタイプ (bs, pl, cf)
        
    Returns:
        str: 正規化された勘定科目名
    """
    if name is None:
        return ""
    
    # 「うち」で始まる括弧付き科目は特別処理（括弧内の内容を抽出）
    is_uchi_item = False
    uchi_content = ""
    if name.startswith('(うち') or name.startswith('（うち'):
        uchi_match = re.match(r'[\(（]うち(.*?)[\)）]', name)
        if uchi_match:
            uchi_content = uchi_match.group(1)
            is_uchi_item = True
    
    # 全角→半角変換（数字、アルファベット、スペース、記号）
    name = name.translate(str.maketrans({
        '０': '0', '１': '1', '２': '2', '３': '3', '４': '4',
        '５': '5', '６': '6', '７': '7', '８': '8', '９': '9',
        'ａ': 'a', 'ｂ': 'b', 'ｃ': 'c', 'ｄ': 'd', 'ｅ': 'e',
        'ｆ': 'f', 'ｇ': 'g', 'ｈ': 'h', 'ｉ': 'i', 'ｊ': 'j',
        'ｋ': 'k', 'ｌ': 'l', 'ｍ': 'm', 'ｎ': 'n', 'ｏ': 'o',
        'ｐ': 'p', 'ｑ': 'q', 'ｒ': 'r', 'ｓ': 's', 'ｔ': 't',
        'ｕ': 'u', 'ｖ': 'v', 'ｗ': 'w', 'ｘ': 'x', 'ｙ': 'y',
        'ｚ': 'z',
        'Ａ': 'A', 'Ｂ': 'B', 'Ｃ': 'C', 'Ｄ': 'D', 'Ｅ': 'E',
        'Ｆ': 'F', 'Ｇ': 'G', 'Ｈ': 'H', 'Ｉ': 'I', 'Ｊ': 'J',
        'Ｋ': 'K', 'Ｌ': 'L', 'Ｍ': 'M', 'Ｎ': 'N', 'Ｏ': 'O',
        'Ｐ': 'P', 'Ｑ': 'Q', 'Ｒ': 'R', 'Ｓ': 'S', 'Ｔ': 'T',
        'Ｕ': 'U', 'Ｖ': 'V', 'Ｗ': 'W', 'Ｘ': 'X', 'Ｙ': 'Y',
        'Ｚ': 'Z',
        '　': ' ', '（': '(', '）': ')', '＜': '<', '＞': '>',
        '【': '[', '】': ']', '％': '%', '＆': '&', '＊': '*',
        '＋': '+', '－': '-', '／': '/', '＝': '=', '：': ':',
        '；': ';', '，': ',', '．': '.', '＠': '@', '＿': '_',
        '｜': '|', '～': '~', '＄': '$', '＃': '#', '！': '!'
    }))
    
    # 空白文字の正規化（全ての種類の空白を半角スペースに変換し、連続する空白を1つにまとめる）
    name = re.sub(r'\s+', ' ', name)
    
    # 括弧付き「うち」項目の場合、括弧を削除せずに内容を使用
    if is_uchi_item and uchi_content:
        name = uchi_content
    else:
        # 括弧と括弧内の内容を削除
        name = re.sub(r'[\(（].*?[\)）]', '', name)
    
    # 先頭と末尾の空白を削除
    name = name.strip()
    
    # 財務諸表タイプ別の特殊処理
    if file_type == 'bs':
        # BSの場合「預金」→「貯金」変換
        name = name.replace('預金', '貯金')
        name = name.replace('普通預金', '普通貯金')
    elif file_type == 'pl':
        # PLの場合の特殊処理
        # 「収益」と「収入」の統一
        if '収入' in name and not '収益' in name:
            name = name.replace('収入', '収益')
        # 「費用」と「経費」の統一
        if '経費' in name and not '費用' in name:
            name = name.replace('経費', '費用')
        # 「当期首繰越利益剰余金」→「当期首繰越剰余金」に統一
        if '当期首繰越利益剰余金' in name:
            name = name.replace('当期首繰越利益剰余金', '当期首繰越剰余金')
    
    return name

def get_reference_ja_list():
    """
    マッピングが充実しているJAのリストを取得する（参照用）
    マッピング数でソートして上位5件を返す
    
    Returns:
        list: マッピング数が多いJAコードのリスト
    """
    try:
        # 各JAのマッピング数を集計してソート
        mapping_counts = db.session.query(
            AccountMapping.ja_code,
            func.count(AccountMapping.id).label('mapping_count')
        ).group_by(AccountMapping.ja_code).order_by(desc('mapping_count')).limit(5).all()
        
        # JAコードのリストを返す
        return [ja_code for ja_code, _ in mapping_counts]
        
    except Exception as e:
        logger.error(f"参照JA取得でエラー: {e}")
        return []

def apply_direct_pl_mapping(target_ja_code, target_year):
    """
    一般的なPL科目を直接マッピングする（参照マッピングの前処理）
    
    Args:
        target_ja_code: 対象のJAコード
        target_year: 対象の年度
        
    Returns:
        dict: 処理結果（マッピング件数、スキップ件数）
    """
    try:
        logger.info(f"PL直接マッピング開始: JA={target_ja_code}, 年度={target_year}")
        
        # 処理状況を記録する変数
        mapped_count = 0
        skipped_count = 0
        
        # 対象JAのPLデータで未マッピングの勘定科目を取得
        unmapped_accounts = db.session.query(CSVData).filter(
            CSVData.ja_code == target_ja_code,
            CSVData.year == target_year,
            CSVData.file_type == 'pl',
            CSVData.is_mapped == False
        ).all()
        
        if not unmapped_accounts:
            return {
                "mapped": 0,
                "skipped": 0
            }
        
        # 主要なPL科目のマッピングルール
        direct_mapping_rules = {
            'その他経常収益': '41700',
            'その他の経常収益': '41700',
            'その他収益': '41700',
            'その他の収益': '41700',
            '当期首繰越剰余金': '91000',
            '当期首繰越利益剰余金': '91000',
        }
        
        # 標準勘定科目情報のキャッシュを作成
        standard_accounts = {}
        for code in set(direct_mapping_rules.values()):
            account = StandardAccount.query.filter_by(code=code).first()
            if account:
                standard_accounts[code] = account
        
        # 未マッピング科目に対して直接マッピングを適用
        for csv_data in unmapped_accounts:
            account_name = csv_data.account_name
            normalized_name = normalize_account_name(account_name, 'pl')
            
            # 直接マッピングルールに一致する科目を処理
            for rule_name, standard_code in direct_mapping_rules.items():
                if rule_name in normalized_name or rule_name in account_name:
                    # 標準勘定科目の存在確認
                    if standard_code not in standard_accounts:
                        logger.warning(f"標準勘定科目が見つかりません: {standard_code}")
                        skipped_count += 1
                        continue
                    
                    standard_account = standard_accounts[standard_code]
                    
                    # マッピングを作成（属性ごとに設定）
                    new_mapping = AccountMapping()
                    new_mapping.ja_code = target_ja_code
                    new_mapping.year = target_year
                    new_mapping.original_account_name = account_name
                    new_mapping.standard_account_code = standard_code
                    new_mapping.standard_account_name = standard_account.name
                    new_mapping.financial_statement = 'pl'
                    new_mapping.confidence = 1.0  # 直接マッピングなので信頼度は1.0
                    new_mapping.rationale = f"直接マッピング（{rule_name} → {standard_code}）"
                    new_mapping.mapping_source = "direct_mapping"
                    
                    # CSVDataを更新
                    csv_data.is_mapped = True
                    
                    db.session.add(new_mapping)
                    mapped_count += 1
                    break
            else:
                skipped_count += 1
        
        # 変更をコミット
        db.session.commit()
        
        logger.info(f"PL直接マッピング完了: {mapped_count}件マッピング, {skipped_count}件スキップ")
        
        return {
            "mapped": mapped_count,
            "skipped": skipped_count
        }
        
    except Exception as e:
        logger.error(f"PL直接マッピングでエラー: {e}")
        db.session.rollback()
        return {
            "mapped": 0,
            "skipped": 0
        }

def apply_reference_mapping(target_ja_code, target_year, file_type, confidence_threshold=0.9, reference_ja_list=None):
    """
    他のJAのマッピング済みデータを参照して、新しいJAデータのマッピングを効率化する
    
    Args:
        target_ja_code: 対象のJAコード
        target_year: 対象の年度
        file_type: ファイルタイプ（bs, pl, cf）
        confidence_threshold: 信頼度しきい値（デフォルト：0.9）
        reference_ja_list: 参照するJAのリスト（Noneの場合はすべてのJAを参照）
        
    Returns:
        dict: 処理結果
    """
    try:
        logger.info(f"参照マッピング開始: JA={target_ja_code}, 年度={target_year}, タイプ={file_type}")
        
        # 処理状況を記録する変数
        mapped_count = 0
        skipped_count = 0
        
        # 対象JAの未マッピング勘定科目を取得
        unmapped_accounts = db.session.query(CSVData).filter(
            CSVData.ja_code == target_ja_code,
            CSVData.year == target_year,
            CSVData.file_type == file_type,
            CSVData.is_mapped == False  # 未マッピングのみ
        ).all()
        
        if not unmapped_accounts:
            return {
                "status": "success",
                "message": "未マッピング科目がありません",
                "mapped": 0,
                "skipped": 0
            }
        
        logger.info(f"未マッピング勘定科目: {len(unmapped_accounts)}件")
        
        # 参照するJAのマッピングデータを取得
        reference_mappings_query = db.session.query(
            AccountMapping.original_account_name,
            AccountMapping.standard_account_code,
            AccountMapping.confidence,
            AccountMapping.financial_statement
        )
        
        # 特定のJAのみ参照する場合はフィルタ追加
        if reference_ja_list:
            reference_mappings_query = reference_mappings_query.filter(
                AccountMapping.ja_code.in_(reference_ja_list)
            )
        
        # ファイルタイプとしきい値でフィルタ
        reference_mappings = reference_mappings_query.filter(
            AccountMapping.financial_statement == file_type,
            AccountMapping.confidence >= confidence_threshold
        ).all()
        
        logger.info(f"参照マッピングデータ: {len(reference_mappings)}件")
        
        # 参照マッピングデータの辞書を作成（高速検索用）
        reference_dict = {}
        for original_account_name, standard_code, confidence, ref_financial_statement in reference_mappings:
            norm_name = normalize_account_name(original_account_name, file_type)
            if norm_name and standard_code:
                # 同じ勘定科目名に複数のマッピングがある場合は信頼度が高い方を採用
                if norm_name not in reference_dict or confidence > reference_dict[norm_name][1]:
                    reference_dict[norm_name] = (standard_code, confidence)
        
        # 標準勘定科目コードとオブジェクトのマッピング辞書の作成
        standard_accounts = db.session.query(StandardAccount).filter(
            StandardAccount.financial_statement == file_type
        ).all()
        standard_dict = {account.code: account for account in standard_accounts}
        
        # 未マッピング科目に対して参照マッピングを適用
        for csv_data in unmapped_accounts:
            norm_name = normalize_account_name(csv_data.account_name, file_type)
            
            # 完全一致で参照
            if norm_name in reference_dict:
                standard_code, confidence = reference_dict[norm_name]
                
                # 標準勘定科目の存在確認
                if standard_code not in standard_dict:
                    logger.warning(f"標準勘定科目が見つかりません: {standard_code}")
                    skipped_count += 1
                    continue
                
                # 標準勘定科目の名前を取得
                standard_account = StandardAccount.query.filter_by(code=standard_code).first()
                if not standard_account:
                    logger.warning(f"標準勘定科目が見つかりません: {standard_code}")
                    skipped_count += 1
                    continue
                
                # マッピングを作成（属性ごとに設定）
                new_mapping = AccountMapping()
                new_mapping.ja_code = target_ja_code
                new_mapping.original_account_name = csv_data.account_name
                new_mapping.standard_account_code = standard_code
                new_mapping.standard_account_name = standard_account.name
                new_mapping.financial_statement = file_type
                new_mapping.confidence = confidence
                new_mapping.rationale = f"他JAの既存マッピングを参照（信頼度: {confidence}）"
                new_mapping.mapping_source = "reference_mapping"
                
                # CSVDataを更新
                csv_data.is_mapped = True
                
                db.session.add(new_mapping)
                mapped_count += 1
            else:
                # 完全一致しない場合は類似度で検索
                best_match = None
                best_similarity = 0.0
                
                for ref_name in reference_dict:
                    similarity = SequenceMatcher(None, norm_name, ref_name).ratio()
                    if similarity > best_similarity and similarity >= confidence_threshold:
                        best_similarity = similarity
                        best_match = ref_name
                
                if best_match:
                    standard_code, confidence = reference_dict[best_match]
                    
                    # 標準勘定科目の存在確認
                    if standard_code not in standard_dict:
                        logger.warning(f"標準勘定科目が見つかりません: {standard_code}")
                        skipped_count += 1
                        continue
                    
                    # マッピングを作成（信頼度は類似度とオリジナル信頼度の積）
                    adjusted_confidence = round(best_similarity * confidence, 2)
                    
                    # しきい値以上の信頼度がある場合のみマッピング
                    if adjusted_confidence >= confidence_threshold:
                        # 標準勘定科目の名前を取得（辞書から取得し、DBアクセスを最小限に）
                        if standard_code in standard_dict:
                            standard_account_name = standard_dict[standard_code].name
                        else:
                            # それでも見つからない場合はDBから直接検索
                            standard_account = StandardAccount.query.filter_by(code=standard_code, financial_statement=file_type).first()
                            if not standard_account:
                                logger.warning(f"標準勘定科目が見つかりません: {standard_code} (タイプ: {file_type})")
                                skipped_count += 1
                                continue
                            standard_account_name = standard_account.name
                        
                        # AccountMappingオブジェクトを作成（デフォルトコンストラクタ使用）
                        new_mapping = AccountMapping()
                        new_mapping.ja_code = target_ja_code
                        new_mapping.year = csv_data.year  # CSVデータの年度を使用
                        new_mapping.original_account_name = csv_data.account_name
                        new_mapping.standard_account_code = standard_code
                        new_mapping.standard_account_name = standard_account_name
                        new_mapping.financial_statement = file_type
                        new_mapping.confidence = adjusted_confidence
                        new_mapping.rationale = f"他JAの既存マッピングに類似（{best_match}, 類似度: {best_similarity:.2f}）"
                        new_mapping.mapping_source = "reference_mapping"
                        
                        # CSVDataを更新
                        csv_data.is_mapped = True
                        
                        db.session.add(new_mapping)
                        mapped_count += 1
                    else:
                        skipped_count += 1
                else:
                    skipped_count += 1
        
        # 変更をコミット
        db.session.commit()
        
        logger.info(f"参照マッピング完了: {mapped_count}件マッピング, {skipped_count}件スキップ")
        
        return {
            "status": "success",
            "message": "参照マッピングが完了しました",
            "mapped": mapped_count,
            "skipped": skipped_count
        }
        
    except Exception as e:
        logger.error(f"参照マッピングでエラー: {e}")
        # エラー時はロールバック
        db.session.rollback()
        
        return {
            "status": "error",
            "message": str(e),
            "mapped": 0,
            "skipped": 0
        }