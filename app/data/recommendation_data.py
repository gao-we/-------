import random

class TourismItem:
    def __init__(self, item_id: str, name: str, category: str, type_val: str, heat: int, evaluate_score: float, distance: float = 0.0):
        self.item_id = item_id
        self.name = name
        self.category = category  # 比如 自然风光，历史古迹，或者对于美食：川菜，小吃等
        self.type_val = type_val  # 'attraction' 或者是 'food'
        self.heat = heat          # 热度（如游览量、点赞数）
        self.evaluate_score = evaluate_score  # 评价得分 (0.0 - 5.0)
        self.distance = distance  # 动态距离，默认为0，后续可以更新它

    def to_dict(self):
        return {
            "id": self.item_id,
            "name": self.name,
            "category": self.category,
            "type": self.type_val,
            "heat": self.heat,
            "score": self.evaluate_score,
            "distance": self.distance
        }

# 伪造景区推荐基础数据
categories_attr = ["自然风光", "历史古迹", "现代建筑", "游乐园", "人文展馆"]
attractions_data = []
for i in range(1, 301):
    attractions_data.append(
        TourismItem(
            item_id=f"A{i}",
            name=f"风景点{i}",
            category=random.choice(categories_attr),
            type_val="attraction",
            heat=random.randint(100, 100000),      # 热度 100~10万
            evaluate_score=round(random.uniform(3.0, 5.0), 1), # 评分 3.0~5.0
            distance=round(random.uniform(500, 20000), 1)
        )
    )

# 伪造美食数据
categories_food = ["川菜", "粤菜", "湘菜", "本地特色小吃", "快餐", "火锅"]
foods_data = []
for i in range(1, 201):
    foods_data.append(
        TourismItem(
            item_id=f"F{i}",
            name=f"特色菜馆{i}",
            category=random.choice(categories_food),
            type_val="food",
            heat=random.randint(50, 50000),
            evaluate_score=round(random.uniform(2.5, 5.0), 1),
            distance=round(random.uniform(100, 10000), 1)
        )
    )

global_recommendation_db = {
    "attraction": attractions_data,
    "food": foods_data
}
