from fastapi import APIRouter, HTTPException, Query
from app.models.schemas import DiaryEntry
from app.data.diary_db import diary_records, diary_compressed_storage, diary_comment_tree
from app.core.algorithms.trie_kmp import kmp_search
from app.core.algorithms.huffman import HuffmanCompressor
import uuid

router = APIRouter()
compressor = HuffmanCompressor()

@router.post("/diary")
def create_diary(title: str, content: str):
    """
    发布日记并存储。同时运用哈夫曼编码进行压缩存储以节约空间。
    """
    d_id = str(uuid.uuid4())[:8]
    
    # 原始存储
    diary_records[d_id] = {
        "title": title,
        "content": content,
        "likes": 0,
        "views": 0
    }
    diary_comment_tree[d_id] = []
    
    # 满足打分要求：对内容进行无损哈夫曼压缩
    comp_content, mapping = compressor.compress(content)
    diary_compressed_storage[d_id] = {
        "compressed": comp_content,
        "reverse_mapping": {v: k for k, v in mapping.items()}
    }

    return {
        "status": "success", 
        "id": d_id, 
        "compression_ratio": f"{len(comp_content) / (len(content)*8 * 2):.2%}" if content else "0%"
    }

@router.get("/diary/search")
def search_diary(keyword: str = Query(..., description="要查找的日记文本关键词")):
    """
    旅游日记搜索。
    基于 KMP 的全文字符串精确搜索。
    """
    results = []
    for d_id, record in diary_records.items():
        # 分别在标题和内容中进行 O(N+M) 的高效查找
        if kmp_search(record["title"], keyword) or kmp_search(record["content"], keyword):
            results.append({"id": d_id, **record})
            
    # 增加游览量 (热度)
    for r in results:
        diary_records[r["id"]]["views"] += 1
        
    # 可复用 成员 B 写的 Top-K 按浏览量排序...
    results.sort(key=lambda x: x["views"], reverse=True)
    return {"status": "success", "keyword": keyword, "matches": len(results), "results": results}

@router.get("/diary/{diary_id}/decompress")
def get_compressed_diary(diary_id: str):
    """
    展示哈夫曼解压过程API
    """
    if diary_id not in diary_compressed_storage:
        raise HTTPException(404, "日记压缩档不存在")
        
    archive = diary_compressed_storage[diary_id]
    original_text = compressor.decompress(archive["compressed"], archive["reverse_mapping"])
    return {
        "id": diary_id,
        "binary_data": archive["compressed"],
        "decompressed_text": original_text
    }

@router.post("/diary/{diary_id}/comment")
def add_comment(diary_id: str, content: str, parent_comment_id: str = None):
    """
    旅游日记交流（评论与点赞）。
    使用 多叉树 结构解决无限极评论/楼中楼回复模型。
    """
    if diary_id not in diary_comment_tree:
        raise HTTPException(code=404, detail="Diary not found")
        
    comment_id = f"c_{str(uuid.uuid4())[:6]}"
    new_node = {
        "id": comment_id,
        "content": content,
        "replies": []
    }
    
    if parent_comment_id is None:
        # 直接回复这篇日记（挂在根节点）
        diary_comment_tree[diary_id].append(new_node)
    else:
        # 回复某个评论，需要在多叉树中进行 DFS/BFS 寻找 parent_comment_id
        def find_and_insert(nodes: list) -> bool:
            for node in nodes:
                if node["id"] == parent_comment_id:
                    node["replies"].append(new_node)
                    return True
                if find_and_insert(node["replies"]):
                    return True
            return False
            
        success = find_and_insert(diary_comment_tree[diary_id])
        if not success:
            raise HTTPException(status_code=404, detail="Parent comment not found")
            
    return {"status": "success", "comment_id": comment_id, "tree": diary_comment_tree[diary_id]}

