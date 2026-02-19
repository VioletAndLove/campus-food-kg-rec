#=============================================================================
# 功能：将人工标注的 Excel 菜单数据转换为结构化 JSON 格式
# 归属：week3-4 数据层任务（采集→清洗→构图）
# 上游：docs/菜单标注模板.xlsx（人工录入/爬取后的原始数据）
# 下游：data/menu.json（供 json2neo4j.py 导入 Neo4j）
# =============================================================================

import pandas as pd, json, os


EXCEL = 'docs/菜单标注模板.xlsx'
JSON  = 'data/menu.json'  # 输出文件位置和名字
os.makedirs('data', exist_ok=True) # 创建 data 目录,已有就不创建了

df = pd.read_excel(EXCEL, dtype=str).fillna('') #读取excel,且所有列强制为str类型，fillna是空值填充空字符串
menu = []  #初始化空列表，用于存储所有的菜品字典
for _, row in df.iterrows():   #遍历dataFrame的每一行，_表示忽略行索引
    menu.append({
        "file":   row['照片文件名'],
        "dish":   row['菜品名'],
        "price":  int(row['价格(元)']),
        "tags":   [t.strip() for t in row['口味标签'].split(';') if t],#口味标签，按分号";"分割,去空白，过滤空字符串
        "ingredients": [i.strip() for i in row['食材'].split('、') if i],#按顿号“、”分割，去空白，过滤空字符串
        "note":   row['备注']
    })

with open(JSON, 'w', encoding='utf-8') as f:   #以utf-8编码打开文件写入json
    json.dump(menu, f, ensure_ascii=False, indent=2)   #menu就是字典，也就是要序列化的对象，f是文件句柄，ensure_ascii=False是允许允许输出中文字符，不转义为 \uXXXX，indent=2是格式化缩进，便于人工查看和调试

print(f"✅ 已转换 {len(menu)} 条菜品 → {JSON}")
