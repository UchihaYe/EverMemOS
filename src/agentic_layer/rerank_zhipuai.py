"""
Zhipu AI Rerank Service Implementation

Commercial API implementation for Zhipu AI (GLM) rerank service
"""

import asyncio
import aiohttp
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from agentic_layer.rerank_interface import RerankServiceInterface, RerankError
from api_specs.memory_models import MemoryType

logger = logging.getLogger(__name__)


@dataclass
class ZhipuRerankConfig:
    """Zhipu AI Rerank configuration"""

    api_key: str = ""
    base_url: str = "https://open.bigmodel.cn/api/paas/v4/"
    model: str = "rerank-1.5"
    timeout: int = 30
    max_retries: int = 3
    batch_size: int = 10
    max_concurrent_requests: int = 5


class ZhipuRerankService(RerankServiceInterface):
    """
    Zhipu AI rerank service implementation
    Uses Zhipu AI's commercial API for document reranking
    """

    def __init__(self, config: Optional[ZhipuRerankConfig] = None):
        if config is None:
            config = ZhipuRerankConfig()

        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
        self._semaphore = asyncio.Semaphore(config.max_concurrent_requests)
        logger.info(
            f"Initialized ZhipuRerankService | url={config.base_url} | model={config.model}"
        )

    async def _ensure_session(self):
        """Ensure HTTP session is created"""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            headers = {"Content-Type": "application/json"}
            if self.config.api_key and self.config.api_key != "EMPTY":
                headers["Authorization"] = f"Bearer {self.config.api_key}"
            self.session = aiohttp.ClientSession(timeout=timeout, headers=headers)

    async def close(self):
        """Close HTTP session"""
        if self.session and not self.session.closed:
            await self.session.close()

    async def rerank_memories(
        self,
        query: str,
        hits: List[Dict[str, Any]],
        top_k: Optional[int] = None,
        instruction: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Rerank memories based on query using Zhipu AI API
        """
        await self._ensure_session()

        # Extract document texts from hits
        documents = [hit.get("episode", hit.get("subject", "")) for hit in hits]

        # Use Zhipu AI rerank API endpoint
        url = f"{self.config.base_url}rerank"

        # Format request data for Zhipu AI
        request_data = {
            "model": self.config.model,
            "query": query,
            "documents": documents,
        }

        async with self._semaphore:
            for attempt in range(self.config.max_retries):
                try:
                    async with self.session.post(url, json=request_data) as response:
                        if response.status == 200:
                            result = await response.json()
                            # Process rerank results
                            reranked_results = []
                            if "results" in result:
                                for i, rerank_item in enumerate(result["results"]):
                                    if i < len(hits):
                                        hit = hits[i].copy()
                                        hit["rerank_score"] = rerank_item.get("relevance_score", 0)
                                        reranked_results.append(hit)
                            return reranked_results[:top_k] if top_k else reranked_results
                        else:
                            error_text = await response.text()
                            logger.warning(
                                f"Zhipu AI rerank API error (status {response.status}, attempt {attempt + 1}/{self.config.max_retries}): {error_text}"
                            )
                            if attempt < self.config.max_retries - 1:
                                await asyncio.sleep(2**attempt)
                                continue
                            else:
                                raise RerankError(
                                    f"Rerank request failed after {self.config.max_retries} attempts: {error_text}"
                                )
                except asyncio.TimeoutError:
                    logger.warning(
                        f"Zhipu AI rerank timeout (attempt {attempt + 1}/{self.config.max_retries})"
                    )
                    if attempt < self.config.max_retries - 1:
                        await asyncio.sleep(2**attempt)
                        continue
                    else:
                        raise RerankError(
                            f"Rerank request timed out after {self.config.max_retries} attempts"
                        )
                except aiohttp.ClientError as e:
                    logger.warning(
                        f"Zhipu AI rerank client error (attempt {attempt + 1}/{self.config.max_retries}): {e}"
                    )
                    if attempt < self.config.max_retries - 1:
                        await asyncio.sleep(2**attempt)
                        continue
                    else:
                        raise RerankError(
                            f"Rerank request failed after {self.config.max_retries} attempts: {e}"
                        )
                except Exception as e:
                    logger.error(f"Unexpected error in Zhipu AI rerank request: {e}")
                    raise RerankError(f"Unexpected rerank error: {e}")

    async def rerank_documents(
        self, query: str, documents: List[str], instruction: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Rerank raw documents (low-level API)

        Args:
            query: Query text
            documents: List of document strings to rerank
            instruction: Optional reranking instruction

        Returns:
            Dict with 'results' key containing list of {index, score, rank}
        """
        await self._ensure_session()

        if not documents:
            return {"results": []}

        url = f"{self.config.base_url}rerank"

        request_data = {
            "model": self.config.model,
            "query": query,
            "documents": documents,
        }

        async with self._semaphore:
            for attempt in range(self.config.max_retries):
                try:
                    async with self.session.post(url, json=request_data) as response:
                        if response.status == 200:
                            result = await response.json()
                            
                            # Zhipu AI returns {"results": [{"index": ..., "relevance_score": ...}, ...]}
                            results = result.get("results", [])
                            
                            # Convert to standard format
                            indexed_scores = [(r.get("index", i), r.get("relevance_score", 0.0)) 
                                            for i, r in enumerate(results)]
                            indexed_scores.sort(key=lambda x: x[1], reverse=True)
                            
                            formatted_results = []
                            for rank, (original_index, score) in enumerate(indexed_scores):
                                formatted_results.append({
                                    "index": original_index,
                                    "score": score,
                                    "rank": rank
                                })
                            
                            return {"results": formatted_results}
                        else:
                            error_text = await response.text()
                            logger.warning(
                                f"Zhipu AI rerank API error (status {response.status}, attempt {attempt + 1}/{self.config.max_retries}): {error_text}"
                            )
                            if attempt < self.config.max_retries - 1:
                                await asyncio.sleep(2**attempt)
                                continue
                            else:
                                raise RerankError(
                                    f"Rerank request failed after {self.config.max_retries} attempts: {error_text}"
                                )
                except asyncio.TimeoutError:
                    logger.warning(
                        f"Zhipu AI rerank timeout (attempt {attempt + 1}/{self.config.max_retries})"
                    )
                    if attempt < self.config.max_retries - 1:
                        await asyncio.sleep(2**attempt)
                        continue
                    else:
                        raise RerankError(
                            f"Rerank request timed out after {self.config.max_retries} attempts"
                        )
                except aiohttp.ClientError as e:
                    logger.warning(
                        f"Zhipu AI rerank client error (attempt {attempt + 1}/{self.config.max_retries}): {e}"
                    )
                    if attempt < self.config.max_retries - 1:
                        await asyncio.sleep(2**attempt)
                        continue
                    else:
                        raise RerankError(
                            f"Rerank request failed after {self.config.max_retries} attempts: {e}"
                        )
                except Exception as e:
                    logger.error(f"Unexpected error in Zhipu AI rerank request: {e}")
                    raise RerankError(f"Unexpected rerank error: {e}")