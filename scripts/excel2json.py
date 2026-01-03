import pandas as pd, json, os

EXCEL = 'docs/菜单标注模板.xlsx'
JSON  = 'data/menu.json'
os.makedirs('data', exist_ok=True)

df = pd.read_excel(EXCEL, dtype=str).fillna('')
menu = []
for _, row in df.iterrows():
    menu.append({
        "file":   row['照片文件名'],
        "dish":   row['菜品名'],
        "price":  int(row['价格(元)']),
        "tags":   [t.strip() for t in row['口味标签'].split(';') if t],
        "ingredients": [i.strip() for i in row['食材'].split('、') if i],
        "note":   row['备注']
    })

with open(JSON, 'w', encoding='utf-8') as f:
    json.dump(menu, f, ensure_ascii=False, indent=2)

print(f"✅ 已转换 {len(menu)} 条菜品 → {JSON}")
