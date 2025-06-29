from models import AnalysisResult
from app import db

# JA002のリスク分析結果データを確認
results = AnalysisResult.query.filter_by(ja_code='JA002', year=2025).all()

print('分析結果テーブルの内容（JA002, 2025）:')
print('-----------------------------------------------------')

# カテゴリ別にグループ化
categories = {}
for r in results:
    if r.analysis_type not in categories:
        categories[r.analysis_type] = []
    categories[r.analysis_type].append(r)

# カテゴリごとの結果を表示
for category, items in categories.items():
    print(f"\nカテゴリ: {category} (項目数: {len(items)})")
    for item in items:
        print(f"  指標: {item.indicator_name}, スコア: {item.risk_score}")

print('\n重複カテゴリの確認:')
print('-----------------------------------------------------')
# 同じカテゴリの指標名の重複をチェック
for category, items in categories.items():
    indicator_names = [item.indicator_name for item in items]
    duplicates = set([name for name in indicator_names if indicator_names.count(name) > 1])
    if duplicates:
        print(f"カテゴリ {category} で重複している指標: {', '.join(duplicates)}")