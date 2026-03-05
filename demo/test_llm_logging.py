"""Test LLM logging functionality"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

async def main():
    """Test LLM logging"""
    
    from memory_layer.llm.llm_provider import LLMProvider
    from core.observation.logger import get_logger
    
    logger = get_logger(__name__)
    logger.info("Starting LLM logging test...")
    
    # Create LLM provider
    llm_provider = LLMProvider(
        provider_type="zhipuai",
        model="glm-4.7",
        api_key=os.getenv("LLM_API_KEY"),
        base_url=os.getenv("LLM_BASE_URL"),
        temperature=0.3
    )
    
    # Test prompt
    test_prompt = "请简单介绍一下你自己，用一句话回答。"
    
    logger.info(f"Sending test prompt to LLM: {test_prompt}")
    
    try:
        response = await llm_provider.generate(test_prompt)
        logger.info(f"LLM response received: {response}")
        print(f"\n✅ LLM 调用成功！")
        print(f"📝 输入: {test_prompt}")
        print(f"💬 输出: {response}")
        print(f"\n📋 请检查 llm_calls.log 文件查看详细的 LLM 调用日志")
    except Exception as e:
        logger.error(f"LLM 调用失败: {e}")
        print(f"❌ LLM 调用失败: {e}")

if __name__ == "__main__":
    asyncio.run(main())