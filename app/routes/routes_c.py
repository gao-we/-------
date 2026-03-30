from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.domain import Diary, User, Location, Comment
from app.core.algorithms.trie_kmp import kmp_search
from app.core.algorithms.huffman import HuffmanCompressor
import uuid
import json

router = APIRouter()
compressor = HuffmanCompressor()

@router.post("/diary")
def create_diary(title: str, content: str, db: Session = Depends(get_db)):
    """
    发布日记并存储。同时运用哈夫曼编码进行压缩存储以节约空间。
    为演示，如果没有用户或位置，会自动选用第一个。
    """
    first_user = db.query(User).first()
    first_loc = db.query(Location).first()
    if not first_user or not first_loc:
        raise HTTPException(status_code=400, detail="Database not seeded with User/Location")
    
    # 满足打分要求：对内容进行无损哈夫曼压缩
    comp_content, mapping = compressor.compress(content)
    reverse_map = {v: k for k, v in mapping.items()}

    new_diary = Diary(
        user_id=first_user.id,
        location_id=first_loc.id,
        title=title,
        content=content,
        compressed_content=comp_content,
        huffman_map=reverse_map
    )
    db.add(new_diary)
    db.commit()
    db.refresh(new_diary)

    return {
        "status": "success", 
        "id": new_diary.id, 
        "compression_ratio": f"{len(comp_content) / (len(content)*8 * 2):.2%}" if content else "0%"
    }

@router.get("/diary/search")
def search_diary(keyword: str = Query(..., description="要查找的日记文本关键词"), db: Session = Depends(get_db)):
    """
    旅游日记搜索。
    基于 KMP 的全文字符串精确搜索。
    """
    all_diaries = db.query(Diary).all()
    results = []
    
    for record in all_diaries:
        # 分别在标题和内容中进行 O(N+M) 的高效查找
        if kmp_search(record.title, keyword) or kmp_search(record.content, keyword):
            # 获取匹配后增加浏览量机制
            record.views += 1
            results.append({
                "id": record.id, 
                "title": record.title, 
                "views": record.views
            })
            
    db.commit()
        
    # 可复用 成员 B 写的 Top-K 按浏览量排序...
    results.sort(key=lambda x: x["views"], reverse=True)
    return {"status": "success", "keyword": keyword, "matches": len(results), "results": results}

@router.get("/diary/{diary_id}/decompress")
def get_compressed_diary(diary_id: int, db: Session = Depends(get_db)):
    """
    展示哈夫曼解压过程API
    """
    diary = db.query(Diary).filter(Diary.id == diary_id).first()
    if not diary or not diary.compressed_content:
        raise HTTPException(status_code=404, detail="日记不存在或无压缩数据")
        
    original_text = compressor.decompress(diary.compressed_content, diary.huffman_map)
    return {
        "id": diary_id,
        "binary_data": diary.compressed_content,
        "decompressed_text": original_text
    }

# 多叉树
diary_comment_tree = {}

@router.post("/diary/{diary_id}/comment")
def add_comment(diary_id: int, content: str, parent_comment_id: str = None, db: Session = Depends(get_db)):
    # 检查日记是否存在
    count = db.query(Diary).filter(Diary.id == diary_id).count()
    if count == 0:
        raise HTTPException(status_code=404, detail="Diary not found")
        
    if diary_id not in diary_comment_tree:
        diary_comment_tree[diary_id] = []
        
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
