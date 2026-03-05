"""
BGE Reranker API Server
使用 FlagEmbedding 创建简单的 rerank API 服务
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
from FlagEmbedding import FlagReranker
import torch

app = FastAPI(title="BGE Reranker API")


class RerankRequest(BaseModel):
    query: str
    documents: List[str]
    top_k: Optional[int] = None


class RerankResponse(BaseModel):
    results: List[dict]


# 初始化 reranker
reranker = None

@app.on_event("startup")
async def startup_event():
    global reranker
    print("Loading BGE Reranker model...")
    
    # 使用 CPU 或 GPU
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")
    
    # 加载模型（使用 base 版本以节省显存）
    reranker = FlagReranker('BAAI/bge-reranker-base', use_fp16=True)
    print("BGE Reranker model loaded successfully!")


@app.post("/rerank")
async def rerank(request: RerankRequest) -> RerankResponse:
    """
    Rerank documents based on query
    
    Args:
        query: Query text
        documents: List of documents to rerank
        top_k: Return top K results (optional)
    
    Returns:
        Reranked documents with scores
    """
    if reranker is None:
        raise HTTPException(status_code=503, detail="Model not loaded yet")
    
    try:
        # 准备查询-文档对
        pairs = [[request.query, doc] for doc in request.documents]
        
        # 计算分数
        scores = reranker.compute_score(pairs)
        
        # 排序
        indexed_scores = list(enumerate(scores))
        indexed_scores.sort(key=lambda x: x[1], reverse=True)
        
        # 格式化结果
        results = []
        for rank, (idx, score) in enumerate(indexed_scores):
            results.append({
                "index": idx,
                "document": request.documents[idx],
                "score": float(score),
                "rank": rank
            })
        
        # 应用 top_k
        if request.top_k and len(results) > request.top_k:
            results = results[:request.top_k]
        
        return RerankResponse(results=results)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rerank error: {str(e)}")


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "ok", "model_loaded": reranker is not None}


if __name__ == "__main__":
    print("Starting BGE Reranker API Server...")
    uvicorn.run(app, host="0.0.0.0", port=12000)
