import re

new_content = """import random

class TourismItem:
    def __init__(self, item_id: str, name: str, category: str, type_val: str, heat: int, evaluate_score: float, distance: float = 0.0, image_url: str = ""):
        self.item_id = item_id
        self.name = name
        self.category = category  
        self.type_val = type_val 
        self.heat = heat         
        self.evaluate_score = evaluate_score  
        self.distance = distance  
        self.image_url = image_url

    def to_dict(self):
        return {
            "id": self.item_id,
            "name": self.name,
            "category": self.category,
            "type": self.type_val,
            "heat": self.heat,
            "score": self.evaluate_score,
            "distance": self.distance,
            "image_url": self.image_url
        }

image_mapping = {
    # 景点 (Attractions)
    "故宫博物院": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/14/Forbidden_City_Beijing_China.jpg/1200px-Forbidden_City_Beijing_China.jpg",
    "万里长城": "https://images.unsplash.com/photo-1508804185872-d7bad45b0d0d?auto=format&fit=crop&q=80&w=1200",
    "杭州西湖": "https://upload.wikimedia.org/wikipedia/commons/a/ad/West_Lake_Standard.jpg",
    "东方明珠广播电视塔": "https://images.unsplash.com/photo-1474181487882-5abf3f0ba6c2?auto=format&fit=crop&q=80&w=1200",
    "秦始皇兵马俑": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6e/Terracotta_Army_Xian_China.jpg/1200px-Terracotta_Army_Xian_China.jpg",
    "上海外滩": "https://images.unsplash.com/photo-1548919973-5cfe5d4fc490?auto=format&fit=crop&q=80&w=1200",
    "布达拉宫": "https://upload.wikimedia.org/wikipedia/commons/c/cc/Potala_Palace_Lhasa_Tibet.jpg",
    "敦煌莫高窟": "https://upload.wikimedia.org/wikipedia/commons/d/d4/Mogao_Caves_Distant_View.jpg",
    "三亚亚龙湾": "https://images.unsplash.com/photo-1540202404-b9030fe1e55d?auto=format&fit=crop&q=80&w=1200",
    "安徽黄山": "https://images.unsplash.com/photo-1534008897995-27a23e859048?auto=format&fit=crop&q=80&w=1200",
    "张家界国家森林公园": "https://images.unsplash.com/photo-1505852903341-fc8d3dbf014e?auto=format&fit=crop&w=1200&q=80",
    "山东泰山": "https://images.unsplash.com/photo-1528644558235-97feecfec18e?auto=format&fit=crop&w=1200&q=80",
    "西安大雁塔": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ab/Giant_Wild_Goose_Pagoda.jpg/1200px-Giant_Wild_Goose_Pagoda.jpg",
    "北京颐和园": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e4/Summer_Palace.jpg/1200px-Summer_Palace.jpg",
    "云南丽江古城": "https://images.unsplash.com/photo-1522709117-91a0cc4a7a58?auto=format&fit=crop&w=1200&q=80",
    "苏州园林": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8c/Humble_Administrators_Garden_Suzhou_China.jpg/1200px-Humble_Administrators_Garden_Suzhou_China.jpg",
    "桂林山水": "https://images.unsplash.com/photo-1518684079-3c830dcef090?auto=format&fit=crop&w=1200&q=80",
    "鼓浪屿": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1b/Gulangyu_Island_View.jpg/1200px-Gulangyu_Island_View.jpg",
    "成都大熊猫繁育研究基地": "https://images.unsplash.com/photo-1564349683136-5efa1ca04df0?auto=format&fit=crop&w=1200&q=80",
    "九寨沟风景区": "https://images.unsplash.com/photo-1499856871958-5b9627545d1a?auto=format&fit=crop&w=1200&q=80",
    
    # 美食 (Foods)
    "北京烤鸭": "https://upload.wikimedia.org/wikipedia/commons/8/84/Peking_Duck_at_Quanjude.JPG",
    "重庆火锅": "https://images.unsplash.com/photo-1585937424108-6878b6680a6b?auto=format&fit=crop&q=80&w=1200",
    "兰州牛肉面": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c5/Lanzhou_beef_noodles_in_Tokyo_20170825.jpg/1200px-Lanzhou_beef_noodles_in_Tokyo_20170825.jpg",
    "广州早茶": "https://images.unsplash.com/photo-1583273131117-640be4430f8a?auto=format&fit=crop&q=80&w=1200",
    "西安肉夹馍": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/85/Rou_jia_mo.jpg/1200px-Rou_jia_mo.jpg",
    "武汉肠粉": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1a/Rice_noodle_rolls.jpg/1200px-Rice_noodle_rolls.jpg",
    "长沙热干面": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/30/Reganmian.jpg/1200px-Reganmian.jpg",
    "成都串串香": "https://images.unsplash.com/photo-1555126634-aba358189c45?auto=format&fit=crop&w=1200&q=80",
    "南京桂花鸭": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d4/Nanjing_Salted_Duck.jpg/1200px-Nanjing_Salted_Duck.jpg",
    "杭州龙井虾仁": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ae/Longjing_shrimp.jpg/1200px-Longjing_shrimp.jpg"
}

attraction_names = [
    "故宫博物院", "万里长城", "杭州西湖", "九寨沟风景区", "三亚亚龙湾", 
    "安徽黄山", "秦始皇兵马俑", "张家界国家森林公园", "山东泰山", "布达拉宫",
    "东方明珠广播电视塔", "西安大雁塔", "上海外滩", "北京颐和园", "云南丽江古城",
    "苏州园林", "桂林山水", "鼓浪屿", "敦煌莫高窟", "成都大熊猫繁育研究基地"
]

food_names = [
    "北京烤鸭", "重庆火锅", "广州早茶", "西安肉夹馍", "武汉肠粉", 
    "兰州牛肉面", "长沙热干面", "成都串串香", "南京桂花鸭", "杭州龙井虾仁"
]

fallback_attr = "https://images.unsplash.com/photo-1548678967-f1aca5e9ff0f?auto=format&fit=crop&w=500&q=60"
fallback_food = "https://images.unsplash.com/photo-1504674900247-0877df9cc836?auto=format&fit=crop&w=500&q=60"

categories_attr = ["自然风光", "历史古迹", "现代建筑", "游乐园", "人文展馆"]
attractions_data = []

# 固定前20个的顺序
for i in range(20):
    name = attraction_names[i]
    image = image_mapping.get(name, fallback_attr)
    attractions_data.append(
        TourismItem(
            item_id=f"A{i+1}",
            name=name,
            category=random.choice(categories_attr),
            type_val="attraction",
            heat=100000 - i * 1000,
            evaluate_score=round(random.uniform(4.5, 5.0), 1),
            distance=round(random.uniform(500, 20000), 1),
            image_url=image
        )
    )

for i in range(20, 300):
    name = f"精选风景区 {i+1}"
    image = fallback_attr
    attractions_data.append(
        TourismItem(
            item_id=f"A{i+1}",
            name=name,
            category=random.choice(categories_attr),
            type_val="attraction",
            heat=random.randint(100, 80000),
            evaluate_score=round(random.uniform(3.0, 4.5), 1),
            distance=round(random.uniform(500, 20000), 1),
            image_url=image
        )
    )

categories_food = ["川菜", "粤菜", "湘菜", "本地特色小吃", "快餐", "火锅"]
foods_data = []

for i in range(10):
    name = food_names[i]
    image = image_mapping.get(name, fallback_food)
    foods_data.append(
        TourismItem(
            item_id=f"F{i+1}",
            name=name,
            category=random.choice(categories_food),
            type_val="food",
            heat=50000 - i * 500,
            evaluate_score=round(random.uniform(4.2, 5.0), 1),
            distance=round(random.uniform(100, 10000), 1),
            image_url=image
        )
    )

for i in range(10, 200):
    name = f"特色美食 {i+1}"
    image = fallback_food
    foods_data.append(
        TourismItem(
            item_id=f"F{i+1}",
            name=name,
            category=random.choice(categories_food),
            type_val="food",
            heat=random.randint(50, 40000),
            evaluate_score=round(random.uniform(2.5, 4.0), 1),
            distance=round(random.uniform(100, 10000), 1),
            image_url=image
        )
    )

global_recommendation_db = {
    "attraction": attractions_data,
    "food": foods_data
}
"""

with open("app/data/recommendation_data.py", "w") as f:
    f.write(new_content)

