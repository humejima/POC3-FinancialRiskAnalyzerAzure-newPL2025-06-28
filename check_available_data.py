from app import app, db
from models import StandardAccount, StandardAccountBalance, JA

with app.app_context():
    # 利用可能なJAとデータタイプを確認
    jas = JA.query.all()
    print("利用可能なJA:")
    for ja in jas:
        print(f"{ja.ja_code}: {ja.name}, 年度: {ja.year}, データ: {ja.available_data}")

