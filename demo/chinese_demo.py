"""MemSys 中文演示 - 简单易用！

演示如何使用记忆系统：
1. 存储对话
2. 检索记忆

前置条件：
    先启动 API 服务器（在另一个终端）：
    uv run python src/run.py

运行演示：
    uv run python src/bootstrap.py demo/chinese_demo.py
"""

import asyncio
from demo.utils import SimpleMemoryManager


async def main():
    """超简单的使用示例 - 只需要 3 步！"""
    
    # 创建记忆管理器
    memory = SimpleMemoryManager()
    
    memory.print_separator("🧠  MemSys 中文演示")
    
    # ========== 第 1 步：存储对话 ==========
    print("\n📝 第 1 步：存储对话")
    memory.print_separator()
    
    await memory.store("我喜欢踢足球，周末经常去球场踢球")
    await asyncio.sleep(2)
    
    await memory.store("足球是一项很棒的运动！你喜欢哪个球队？", sender="Assistant")
    await asyncio.sleep(2)
    
    await memory.store("我最喜欢巴塞罗那，梅西是我的偶像")
    await asyncio.sleep(2)
    
    await memory.store("我也喜欢看篮球，NBA 是我最爱看的")
    await asyncio.sleep(2)
    
    await memory.store("我要去睡觉了")
    await asyncio.sleep(2)
    
    await memory.store("今天天气真好")
    await asyncio.sleep(2)
    
    await memory.store("宇宙正在膨胀")
    await asyncio.sleep(2)
    
    # ========== 第 2 步：等待索引建立 ==========
    print("\n⏳ 第 2 步：等待索引建立")
    memory.print_separator()
    await memory.wait_for_index(seconds=10)
    
    # ========== 第 3 步：检索记忆 ==========
    print("\n🔍 第 3 步：检索记忆")
    memory.print_separator()
    
    print("\n💬 查询 1：用户喜欢什么运动？")
    await memory.search("用户喜欢什么运动？")
    
    print("\n💬 查询 2：用户最喜欢的球队是哪个？")
    await memory.search("用户最喜欢的球队是哪个？")
    
    print("\n💬 查询 3：用户的运动爱好是什么？")
    await memory.search("用户的运动爱好是什么？")
    
    print("\n💬 查询 4：用户今天感觉怎么样？")
    await memory.search("用户今天感觉怎么样？")
    
    print("\n💬 查询 5：用户对宇宙有什么看法？")
    await memory.search("用户对宇宙有什么看法？")
    
    # ========== 完成 ==========
    memory.print_summary()


if __name__ == "__main__":
    asyncio.run(main())
