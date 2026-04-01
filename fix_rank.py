import codecs

filepath = "app/routes/routes_b.py"
with open(filepath, "r", encoding="utf-8") as f:
    text = f.read()

# 修复算法：确保已配置真实唯一照片的前20个名胜古迹必须排在最热门前列
text = text.replace(
    'return (item.id * 13) % 100',
    'return 200 - item.id if item.id <= 20 else (item.id * 13) % 100'
)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(text)

print("Rank fixed")
