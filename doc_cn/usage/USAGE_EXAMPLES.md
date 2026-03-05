# 使用示例

[主页](../../README.md) > [文档](../README.md) > [使用](.) > 使用示例

本指南提供了在不同场景下如何使用 EverMemOS 的全面示例。

---

## 目录

1. [简单演示 - 快速开始](#1-简单演示---快速开始)
2. [完整演示 - 记忆提取和聊天](#2-完整演示---记忆提取和聊天)
3. [评估和性能测试](#3-评估和性能测试)
4. [直接 API 使用](#4-直接-api-使用)
5. [批量操作](#5-批量操作)
6. [高级集成](#6-高级集成)

---

## 前提条件

在使用这些示例之前，请确保您：

1. **已完成安装** - 请参阅[设置指南](../installation/SETUP.md)
2. **启动了 API 服务器**：
   ```bash
   uv run python src/run.py --port 1995
   ```
3. **配置了 .env** 文件，包含必需的 API 密钥

---

## 1. 简单演示 - 快速开始

体验 EverMemOS 的最快方式！只需 2 步即可看到记忆存储和检索的实际效果。

### 功能

- 存储 4 条关于运动爱好的对话消息
- 等待 10 秒进行索引
- 使用 3 个不同的查询搜索相关记忆
- 显示完整的工作流程，并附带友好的解释

### 使用方法

```bash
# 终端 1：启动 API 服务器
uv run python src/run.py --port 1995

# 终端 2：运行简单演示
uv run python src/bootstrap.py demo/simple_demo.py
```

### 预期输出

您将看到：
1. 消息正在存储
2. 索引进度
3. 查询结果，如"用户喜欢什么运动？"
4. 检索到的相关记忆及其分数

### 演示代码

查看完整代码：[`demo/simple_demo.py`](../../demo/simple_demo.py)

### 适用于

- 首次用户
- 快速测试
- 理解核心概念
- 验证安装

---

## 2. 完整演示 - 记忆提取和聊天

体验完整的 EverMemOS 工作流程：从对话中提取记忆，然后进行带有记忆检索的交互式聊天。

### 前提条件

**启动 API 服务器：**

```bash
# 终端 1：启动 API 服务器（必需）
uv run python src/run.py --port 1995
```

> 💡 **提示**：保持 API 服务器持续运行。所有后续操作应在另一个终端中执行。

---

### 步骤 1：提取记忆

运行记忆提取脚本以处理示例对话数据并构建记忆数据库：

```bash
# 终端 2：运行提取脚本
uv run python src/bootstrap.py demo/extract_memory.py
```

**此脚本的作用：**

1. 调用 `demo.tools.clear_all_data.clear_all_memories()`，以便演示从空的 MongoDB/Elasticsearch/Milvus/Redis 状态开始。在执行脚本之前确保通过 `docker-compose` 启动的依赖堆栈正在运行，否则清除步骤将失败。

2. 加载 `data/assistant_chat_zh.json`，将 `scene="assistant"` 附加到每条消息，并将每个条目流式传输到 `http://localhost:1995/api/v1/memories`。

3. 如果您在其他端点上托管 API 或想要摄取不同的场景，请更新 `demo/extract_memory.py` 中的 `base_url`、`data_file` 或 `profile_scene` 常量。

4. 仅通过 HTTP API 写入：MemCells、片段和画像在您的数据库中创建，而不是在 `demo/memcell_outputs/` 下。检查 MongoDB（以及 Milvus/Elasticsearch）以验证摄取或直接进入聊天演示。

> **💡 提示**：有关详细的配置说明和使用指南，请参阅[演示文档](../../demo/README.md)。

---

### 步骤 2：带记忆聊天

提取记忆后，启动交互式聊天演示：

```bash
# 终端 2：运行聊天程序（确保 API 服务器仍在运行）
uv run python src/bootstrap.py demo/chat_with_memory.py
```

**工作原理：**

此程序通过 `python-dotenv` 加载 `.env`，验证至少有一个 LLM 密钥（`LLM_API_KEY`、`OPENROUTER_API_KEY` 或 `OPENAI_API_KEY`）可用，并通过 `demo.utils.ensure_mongo_beanie_ready` 连接到 MongoDB 以枚举已包含 MemCells 的组。

每个用户查询都会调用 `api/v1/memories/search`，除非您明确选择智能体模式，在这种情况下，编排器会切换到智能体检索并警告额外的 LLM 延迟。

### 交互式工作流程

1. **选择语言**：选择 zh 或 en 终端 UI。
2. **选择场景模式**：助手（一对一）或群聊（多说话人分析）。
3. **选择对话组**：组通过 `query_all_groups_from_mongodb` 从 MongoDB 实时读取；首先运行提取步骤，以便列表非空。
4. **选择检索模式**：`rrf`、`vector`、`keyword` 或 LLM 引导的智能体检索。
5. **开始聊天**：提出问题，检查在每个响应之前显示的检索到的记忆，并使用 `help`、`clear`、`reload` 或 `exit` 来管理会话。

---

## 3. 评估和性能测试

评估框架提供了一种统一的、模块化的方式，可以在标准数据集（LoCoMo、LongMemEval、PersonaMem）上对记忆系统进行基准测试。

### 快速测试（冒烟测试）

使用有限的数据验证一切正常：

```bash
# 默认冒烟测试
# 第一次对话，前 10 条消息，前 3 个问题
uv run python -m evaluation.cli --dataset locomo --system evermemos --smoke

# 自定义冒烟测试：20 条消息，5 个问题
uv run python -m evaluation.cli --dataset locomo --system evermemos \
    --smoke --smoke-messages 20 --smoke-questions 5

# 测试不同的数据集
uv run python -m evaluation.cli --dataset longmemeval --system evermemos --smoke
uv run python -m evaluation.cli --dataset personamem --system evermemos --smoke

# 测试特定阶段（例如，仅搜索和回答）
uv run python -m evaluation.cli --dataset locomo --system evermemos \
    --smoke --stages search answer

# 快速查看冒烟测试结果
cat evaluation/results/locomo-evermemos-smoke/report.txt
```

### 完整评估

在整个数据集上运行完整评估：

```bash
# 在 LoCoMo 基准测试上评估 EvermemOS
uv run python -m evaluation.cli --dataset locomo --system evermemos

# 在其他数据集上评估
uv run python -m evaluation.cli --dataset longmemeval --system evermemos
uv run python -m evaluation.cli --dataset personamem --system evermemos

# 使用 --run-name 区分多次运行（对 A/B 测试有用）
uv run python -m evaluation.cli --dataset locomo --system evermemos --run-name baseline
uv run python -m evaluation.cli --dataset locomo --system evermemos --run-name experiment1

# 如果中断，从检查点恢复（自动）
# 只需重新运行相同的命令 - 它将检测并从检查点恢复
uv run python -m evaluation.cli --dataset locomo --system evermemos
```

### 查看结果

```bash
# 结果保存到 evaluation/results/{dataset}-{system}[-{run-name}]/
cat evaluation/results/locomo-evermemos/report.txt          # 摘要指标
cat evaluation/results/locomo-evermemos/eval_results.json   # 每个问题的详细结果
cat evaluation/results/locomo-evermemos/pipeline.log        # 执行日志
```

### 评估流程

评估流程由 4 个阶段组成，具有自动检查点和恢复支持：

1. **添加** - 将对话数据摄取到系统中
2. **搜索** - 为每个问题检索相关记忆
3. **回答** - 使用检索到的上下文生成答案
4. **评估** - 根据真实情况对答案进行评分

### 配置

> **⚙️ 评估配置**：
> - **数据准备**：将数据集放在 `evaluation/data/` 中（请参阅 `evaluation/README.md`）
> - **环境**：使用 LLM API 密钥配置 `.env`（请参阅 `env.template`）
> - **安装**：运行 `uv sync --group evaluation` 以安装依赖项
> - **自定义配置**：复制并修改 `evaluation/config/systems/` 或 `evaluation/config/datasets/` 中的 YAML 文件
> - **高级用法**：请参阅 `evaluation/README.md` 以了解检查点管理、特定阶段运行和系统比较

---

## 4. 直接 API 使用

使用 Memory API 将 EverMemOS 集成到您的应用程序中。

### 前提条件

**启动 API 服务器：**

```bash
uv run python src/run.py --port 1995
```

> 💡 **提示**：保持 API 服务器持续运行。所有后续 API 调用应在另一个终端中执行。

---

### 存储单条消息记忆

使用 `/api/v1/memories` 端点存储单个消息：

**最小示例（仅必需字段）：**

```bash
curl -X POST http://localhost:1995/api/v1/memories \
  -H "Content-Type: application/json" \
  -d '{
    "message_id": "msg_001",
    "create_time": "2025-02-01T10:00:00+00:00",
    "sender": "user_001",
    "content": "I love playing soccer on weekends"
  }'
```

**包含可选字段：**

```bash
curl -X POST http://localhost:1995/api/v1/memories \
  -H "Content-Type: application/json" \
  -d '{
    "message_id": "msg_001",
    "create_time": "2025-02-01T10:00:00+00:00",
    "sender": "user_103",
    "sender_name": "Chen",
    "content": "We need to complete product design this week",
    "group_id": "group_001",
    "group_name": "Project Discussion Group"
  }'
```

> ℹ️ **必需字段**：`message_id`、`create_time`、`sender`、`content`
> ℹ️ **可选字段**：`group_id`、`group_name`、`sender_name`、`role`、`refer_list`
> ℹ️ 默认情况下，提取并存储所有记忆类型

### API 端点

- **`POST /api/v1/memories`**：存储单条消息记忆
- **`GET /api/v1/memories/search`**：记忆检索（支持关键词/向量/混合搜索模式）

有关完整的 API 文档，请参阅[Memory API 文档](../api_docs/memory_api.md)。

---

### 检索记忆

EverMemOS 提供两种检索模式：**轻量级**（快速）和**智能体**（智能）。

#### 轻量级检索

适用于延迟敏感场景的快速检索。

**参数：**

| 参数 | 必需 | 描述 |
|-----------|----------|-------------|
| `query` | 是* | 自然语言查询（*对于画像类型可选） |
| `user_id` | 否* | 用户 ID |
| `group_id` | 否* | 群组 ID |
| `memory_types` | 否 | `["episodic_memory"]` / `["event_log"]` / `["foresight"]`（默认：`["episodic_memory"]`） |
| `retrieve_method` | 否 | `keyword` / `vector` / `hybrid` / `rrf`（推荐） / `agentic` |
| `current_time` | 否 | 过滤有效的前瞻性（格式：ISO 8601） |
| `top_k` | 否 | 结果数量（默认：40，最大：100） |

*必须提供 `user_id` 或 `group_id` 中的至少一个。

**示例 1：个人记忆**

```bash
curl -X GET http://localhost:1995/api/v1/memories/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What sports does the user like?",
    "user_id": "user_001",
    "memory_types": ["episodic_memory"],
    "retrieve_method": "rrf"
  }'
```

**示例 2：群组记忆**

```bash
curl -X GET http://localhost:1995/api/v1/memories/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Discuss project progress",
    "group_id": "project_team_001",
    "memory_types": ["episodic_memory"],
    "retrieve_method": "rrf"
  }'
```

> 📖 完整文档：[Memory API](../api_docs/memory_api.md) | 测试工具：`demo/tools/test_retrieval_comprehensive.py`

---

## 5. 批量操作

使用批量脚本高效处理多条消息。

有关完整信息，请参阅专门的[批量操作指南](BATCH_OPERATIONS.md)。

### 快速示例

```bash
# 批量存储群聊消息（中文数据）
uv run python src/bootstrap.py src/run_memorize.py \
  --input data/group_chat_zh.json \
  --api-url http://localhost:1995/api/v1/memories \
  --scene group_chat

# 或使用英文数据
uv run python src/bootstrap.py src/run_memorize.py \
  --input data/group_chat_en.json \
  --api-url http://localhost:1995/api/v1/memories \
  --scene group_chat

# 验证文件格式
uv run python src/bootstrap.py src/run_memorize.py \
  --input data/group_chat_en.json \
  --scene group_chat \
  --validate-only
```

> ℹ️ **场景参数说明**：`scene` 参数是必需的，并指定记忆提取策略：
> - 对于与 AI 助手的一对一对话，使用 `assistant`
> - 对于多人群组讨论，使用 `group_chat`

有关完整详细信息，请参阅：
- [批量操作指南](BATCH_OPERATIONS.md)
- [群聊格式规范](../../data_format/group_chat/group_chat_format.md)

---

## 6. 高级集成

### Python SDK 使用

在您的 Python 应用程序中使用 EverMemOS：

```python
import requests

class EverMemOSClient:
    def __init__(self, base_url="http://localhost:1995"):
        self.base_url = base_url

    def store_memory(self, message):
        """存储单条消息记忆。"""
        url = f"{self.base_url}/api/v1/memories"
        response = requests.post(url, json=message)
        response.raise_for_status()
        return response.json()

    def search_memories(self, query, user_id=None, **kwargs):
        """搜索相关记忆。"""
        url = f"{self.base_url}/api/v1/memories/search"
        params = {"query": query, **kwargs}
        if user_id:
            params["user_id"] = user_id

        response = requests.get(url, json=params)
        response.raise_for_status()
        return response.json()

# 使用
client = EverMemOSClient()

# 存储记忆
client.store_memory({
    "message_id": "msg_001",
    "create_time": "2025-02-01T10:00:00+00:00",
    "sender": "user_001",
    "content": "I love playing soccer on weekends"
})

# 搜索记忆
results = client.search_memories(
    query="What sports does the user like?",
    user_id="user_001",
    memory_types=["episodic_memory"],
    retrieve_method="rrf"
)

print(results)
```

### 自定义集成模式

对于高级集成场景：

1. **流式对话**：与聊天应用程序集成以持续存储消息
2. **自定义记忆类型**：扩展提取管道以获取特定领域的记忆
3. **多租户系统**：使用 `user_id` 和 `group_id` 进行隔离
4. **实时检索**：为频繁访问的记忆实现缓存策略

请参阅[API 使用指南](../dev_docs/api_usage_guide.md)以获取更多示例。

---

## 另请参阅

- [演示指南](DEMOS.md) - 详细的演示指南
- [批量操作指南](BATCH_OPERATIONS.md) - 批量处理详细信息
- [Memory API 文档](../api_docs/memory_api.md) - 完整 API 参考
- [API 使用指南](../dev_docs/api_usage_guide.md) - 高级 API 模式
- [评估指南](../../evaluation/README.md) - 基准测试文档