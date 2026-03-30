from typing import Dict, List

# 存储原始日记文本内容及附属信息
diary_records: Dict[str, dict] = {}

# 存储压缩后的信息（为了演示大作业的哈夫曼压缩功能，模拟数据库中的一个冷存储表）
diary_compressed_storage: Dict[str, dict] = {}

# 用于处理无限级评论的森林（多叉树的节点字典形式： { parent_id: [ child1, child2 ] } ）
# 在根级别，由于每个日记独立探讨，可把 diary_id 当作树的 root 标识
diary_comment_tree: Dict[str, List[dict]] = {}

def add_mock_diaries():
    """初始化一些伪造数据供测试"""
    mock_data = [
        {"id": "d1", "title": "五一爬山攻略", "content": "那是一座非常美丽的山，风景秀丽，路上买了一份烤肠简直是人间美味。就是上下山台阶很折磨人。"},
        {"id": "d2", "title": "校园美食探店日记", "content": "今天去了东校区二食堂，吃了一碗牛肉面，不愧是招牌，非常推荐校友去尝试！食堂环境也很不错。"},
        {"id": "d3", "title": "博物馆奇妙夜", "content": "博物馆里的展品太丰富了，尤其是三楼的历史文物区，仿佛穿越了时空，导览机给的讲解也很清晰。"}
    ]
    for d in mock_data:
        diary_records[d["id"]] = {
            "title": d["title"],
            "content": d["content"],
            "likes": 0,
            "views": 0
        }
        diary_comment_tree[d["id"]] = []

add_mock_diaries()
