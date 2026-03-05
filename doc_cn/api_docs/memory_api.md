# Memory API 文档

[主页](../../README.md) > [文档](../README.md) > [API 文档](.) > Memory API

## 概述

Memory API 提供用于存储、检索、搜索和管理对话记忆的 RESTful 端点。

**基础 URL：** `http://localhost:1995/api/v1/memories`

## API 端点

| 方法 | 端点 | 描述 |
|--------|----------|-------------|
| POST | `/memories` | 存储单条消息 |
| GET | `/memories` | 按类型获取记忆 |
| GET | `/memories/search` | 搜索记忆 |
| GET | `/memories/conversation-meta` | 获取对话元数据 |
| POST | `/memories/conversation-meta` | 保存对话元数据 |
| PATCH | `/memories/conversation-meta` | 部分更新元数据 |
| DELETE | `/memories` | 软删除记忆 |

---

## POST `/memories` - 存储消息

将单条消息存储到记忆中。

### 请求

```json
{
  "message_id": "msg_001",
  "create_time": "2025-01-15T10:00:00+00:00",
  "sender": "user_001",
  "content": "Let's discuss the technical solution for the new feature today",
  "group_id": "group_123",
  "group_name": "Project Discussion Group",
  "sender_name": "John",
  "role": "user",
  "refer_list": ["msg_000"]
}
```

### 请求字段

| 字段 | 类型 | 必需 | 描述 |
|-------|------|----------|-------------|
| `message_id` | string | 是 | 唯一消息标识符 |
| `create_time` | string | 是 | 带时区的 ISO 8601 时间戳 |
| `sender` | string | 是 | 发送者用户 ID |
| `content` | string | 是 | 消息内容 |
| `group_id` | string | 否 | 群组标识符 |
| `group_name` | string | 否 | 群组显示名称 |
| `sender_name` | string | 否 | 发送者显示名称（默认为 `sender`） |
| `role` | string | 否 | `user`（人类）或 `assistant`（AI） |
| `refer_list` | array | 否 | 引用的消息 ID 列表 |

### 群组 ID 行为

当未提供 `group_id` 和 `group_name`（为 null）时，API 会根据 `sender` 字段自动创建默认群组。这使简单用例能够使用，而无需多个发送者之间的相关记忆。

**何时省略 `group_id`：**
- **知识库摄取** - 单源内容，不需要发送者关联
- **角色/画像构建** - 为单个用户构建记忆，无需多方上下文
- **简单聊天机器人交互** - 1:1 对话，不需要分组

**何时提供 `group_id`：**
- **多用户对话** - 多参与者互动的群聊
- **用户 + AI 助手** - 用户和 AI 之间的对话，上下文关联很重要
- **基于项目/主题的组织** - 当你想按逻辑分组查询记忆时

提供 `group_id` 能够通过为系统提供关于多个发送者之间相关消息的上下文来更好地提取片段记忆。有关详细指导，请参阅[群聊指南](../advanced/GROUP_CHAT_GUIDE.md)。

### 示例

```bash
curl -X POST "http://localhost:1995/api/v1/memories" \
  -H "Content-Type: application/json" \
  -d '{
    "message_id": "msg_001",
    "create_time": "2025-01-15T10:00:00+00:00",
    "sender": "user_001",
    "sender_name": "John",
    "role": "user",
    "content": "Let us discuss technical solution for new feature today",
    "group_id": "group_123",
    "group_name": "Project Discussion Group",
    "refer_list": []
  }'
```

### 响应

**成功 (200)** - 已提取记忆（触发边界）：
```json
{
  "status": "ok",
  "message": "Extracted 1 memories",
  "result": {
    "saved_memories": [],
    "count": 1,
    "status_info": "extracted"
  }
}
```

**成功 (200)** - 消息已排队（未触发边界）：
```json
{
  "status": "ok",
  "message": "Message queued, awaiting boundary detection",
  "result": {
    "saved_memories": [],
    "count": 0,
    "status_info": "accumulated"
  }
}
```

---

## GET `/memories` - 获取记忆

按类型检索记忆，支持可选过滤器。

### 请求参数（查询字符串）

| 参数 | 类型 | 必需 | 默认值 | 描述 |
|-----------|------|----------|---------|-------------|
| `user_id` | string | 否* | - | 用户 ID |
| `group_id` | string | 否* | - | 群组 ID |
| `memory_type` | string | 否 | `episodic_memory` | 记忆类型 |
| `limit` | integer | 否 | 40 | 最大结果数（最大：500） |
| `offset` | integer | 否 | 0 | 分页偏移量 |
| `start_time` | string | 否 | - | 过滤开始时间（ISO 8601） |
| `end_time` | string | 否 | - | 过滤结束时间（ISO 8601） |
| `version_range` | array | 否 | - | 版本范围 `[start, end]` |

*必须提供 `user_id` 或 `group_id` 中的至少一个（不能同时为 `__all__`）。

### 记忆类型

| 类型 | 描述 |
|------|-------------|
| `profile` | 用户画像信息 |
| `episodic_memory` | 对话片段（默认） |
| `foresight` | 前瞻性记忆 |
| `event_log` | 原子事实 |

### 示例

```bash
curl "http://localhost:1995/api/v1/memories?user_id=user_123&memory_type=episodic_memory&limit=20"
```

### 响应

```json
{
  "status": "ok",
  "message": "Memory retrieval successful, retrieved 1 memories",
  "result": {
    "memories": [
      {
        "memory_type": "episodic_memory",
        "user_id": "user_123",
        "timestamp": "2024-01-15T10:30:00",
        "content": "User discussed coffee during the project sync",
        "summary": "Project sync coffee note"
      }
    ],
    "total_count": 100,
    "has_more": false,
    "metadata": {
      "source": "fetch_mem_service",
      "user_id": "user_123",
      "memory_type": "fetch"
    }
  }
}
```

---

## GET `/memories/search` - 搜索记忆

使用关键词、向量或混合检索方法搜索记忆。

### 请求体

```json
{
  "query": "coffee preference",
  "user_id": "user_123",
  "group_id": "group_456",
  "retrieve_method": "keyword",
  "memory_types": ["episodic_memory"],
  "top_k": 10,
  "start_time": "2024-01-01T00:00:00",
  "end_time": "2024-12-31T23:59:59",
  "radius": 0.6,
  "include_metadata": true
}
```

### 请求字段

| 字段 | 类型 | 必需 | 默认值 | 描述 |
|-------|------|----------|---------|-------------|
| `query` | string | 否 | - | 搜索查询文本 |
| `user_id` | string | 否* | - | 用户 ID |
| `group_id` | string | 否* | - | 群组 ID |
| `retrieve_method` | string | 否 | `keyword` | 检索方法 |
| `memory_types` | array | 否 | `[]`（默认为 `episodic_memory`） | 要搜索的记忆类型 |
| `top_k` | integer | 否 | 40 | 最大结果数（最大：100） |
| `start_time` | string | 否 | - | 过滤开始时间（ISO 8601） |
| `end_time` | string | 否 | - | 过滤结束时间（ISO 8601） |
| `radius` | float | 否 | - | 余弦相似度阈值（0.0-1.0，仅用于向量/混合） |
| `include_metadata` | boolean | 否 | true | 在响应中包含元数据 |
| `current_time` | string | 否 | - | 用于过滤前瞻性事件的当前时间 |

*必须提供 `user_id` 或 `group_id` 中的至少一个（不能同时为 `__all__`）。

**注意：** 搜索接口不支持 `profile` 记忆类型。

### 检索方法

| 方法 | 描述 |
|--------|-------------|
| `keyword` | BM25 关键词检索（默认） |
| `vector` | 向量语义检索 |
| `hybrid` | 关键词 + 向量 + 重排 |
| `rrf` | RRF 融合（关键词 + 向量 + RRF 排名） |
| `agentic` | LLM 引导的多轮智能检索 |

### 示例

```bash
curl -X GET "http://localhost:1995/api/v1/memories/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "coffee preference",
    "user_id": "user_123",
    "retrieve_method": "keyword",
    "top_k": 10
  }'
```

### 响应

```json
{
  "status": "ok",
  "message": "Memory search successful, retrieved 1 groups",
  "result": {
    "memories": [
      {
        "episodic_memory": [
          {
            "memory_type": "episodic_memory",
            "user_id": "user_123",
            "timestamp": "2024-01-15T10:30:00",
            "summary": "Discussed coffee choices",
            "group_id": "group_456"
          }
        ]
      }
    ],
    "scores": [{"episodic_memory": [0.95]}],
    "importance_scores": [0.85],
    "original_data": [],
    "total_count": 45,
    "has_more": false,
    "query_metadata": {
      "source": "episodic_memory_es_repository",
      "user_id": "user_123",
      "memory_type": "retrieve"
    },
    "metadata": {
      "source": "episodic_memory_es_repository",
      "user_id": "user_123",
      "memory_type": "retrieve"
    },
    "pending_messages": []
  }
}
```

### 响应字段

| 字段 | 描述 |
|-------|-------------|
| `memories` | 记忆组列表，按记忆类型组织 |
| `scores` | 每个记忆的相关性分数 |
| `importance_scores` | 用于排序的组重要性分数 |
| `original_data` | 与记忆关联的原始数据 |
| `total_count` | 找到的记忆总数 |
| `has_more` | 是否有更多结果可用 |
| `query_metadata` | 关于查询执行的元数据 |
| `metadata` | 额外的响应元数据 |
| `pending_messages` | 等待记忆提取的消息 |

---

## GET `/memories/conversation-meta` - 获取元数据

按 group_id 检索对话元数据，回退到默认配置。

### 请求参数

| 参数 | 类型 | 必需 | 描述 |
|-----------|------|----------|-------------|
| `group_id` | string | 否 | 群组 ID（省略以获取默认配置） |

### 示例

```bash
curl "http://localhost:1995/api/v1/memories/conversation-meta?group_id=group_123"
```

### 响应

```json
{
  "status": "ok",
  "message": "Conversation metadata retrieved successfully",
  "result": {
    "id": "...",
    "group_id": "group_123",
    "scene": "group_chat",
    "name": "Engineering Team",
    "user_details": {...},
    "is_default": false
  }
}
```

---

## POST `/memories/conversation-meta` - 保存元数据

保存或更新对话元数据（upsert 行为）。

### 请求体

```json
{
  "version": "1.0.0",
  "scene": "group_chat",
  "scene_desc": {
    "description": "Project discussion group chat",
    "type": "project_discussion"
  },
  "name": "Engineering Team",
  "description": "Backend team discussions",
  "group_id": "group_123",
  "created_at": "2025-01-15T10:00:00Z",
  "default_timezone": "America/New_York",
  "user_details": {
    "alice": {
      "full_name": "Alice Smith",
      "role": "user",
      "custom_role": "Tech Lead"
    }
  },
  "tags": ["engineering", "backend"]
}
```

### 请求字段

| 字段 | 类型 | 必需 | 描述 |
|-------|------|----------|-------------|
| `version` | string | 是 | 元数据版本 |
| `scene` | string | 是 | 场景标识符：`assistant` 或 `group_chat` |
| `scene_desc` | object | 是 | 场景描述对象 |
| `name` | string | 是 | 对话名称 |
| `description` | string | 否 | 对话描述 |
| `group_id` | string | 否 | 群组标识符（省略以获取默认配置） |
| `created_at` | string | 是 | 对话创建时间（ISO 8601 格式） |
| `default_timezone` | string | 否 | 默认时区（默认为系统时区） |
| `user_details` | object | 否 | 参与者详细信息，键为用户 ID |
| `tags` | array | 否 | 标签列表 |

### 用户详细信息字段

| 字段 | 类型 | 描述 |
|-------|------|-------------|
| `full_name` | string | 显示名称 |
| `role` | string | `user` 或 `assistant` |
| `custom_role` | string | 职位/职位名称 |
| `extra` | object | 额外的元数据 |

---

## PATCH `/memories/conversation-meta` - 更新元数据

部分更新对话元数据。

### 请求体

```json
{
  "group_id": "group_123",
  "name": "Updated Team Name",
  "tags": ["engineering", "python"]
}
```

### 可更新字段

| 字段 | 描述 |
|-------|-------------|
| `name` | 对话名称 |
| `description` | 对话描述 |
| `scene_desc` | 场景描述 |
| `tags` | 标签列表 |
| `user_details` | 用户详细信息（替换整个对象） |
| `default_timezone` | 默认时区 |

### 响应

```json
{
  "status": "ok",
  "message": "Conversation metadata updated successfully, 2 fields updated",
  "result": {
    "id": "...",
    "group_id": "group_123",
    "scene": "group_chat",
    "name": "Updated Team Name",
    "updated_fields": ["name", "tags"],
    "updated_at": "2025-01-15T12:00:00Z"
  }
}
```

---

## DELETE `/memories` - 删除记忆

基于过滤条件软删除记忆（AND 逻辑）。

### 请求体

```json
{
  "event_id": "evt_001",
  "user_id": "user_123",
  "group_id": "group_456"
}
```

### 请求字段

| 字段 | 类型 | 必需 | 默认值 | 描述 |
|-------|------|----------|---------|-------------|
| `event_id` | string | 否 | `__all__` | 按事件 ID 过滤 |
| `user_id` | string | 否 | `__all__` | 按用户 ID 过滤 |
| `group_id` | string | 否 | `__all__` | 按群组 ID 过滤 |

必须提供至少一个过滤器（不能全部为 `__all__`）。

### 示例

```bash
# 删除群组中用户的所有记忆
curl -X DELETE "http://localhost:1995/api/v1/memories" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user_123", "group_id": "group_456"}'
```

### 响应

```json
{
  "status": "ok",
  "message": "Successfully deleted 10 memories",
  "result": {
    "filters": ["user_id", "group_id"],
    "count": 10
  }
}
```

---

## 使用 run_memorize.py 进行批量处理

用于批量处理 GroupChatFormat JSON 文件：

```bash
# 处理群聊文件
uv run python src/bootstrap.py src/run_memorize.py \
  --input data/group_chat.json \
  --scene group_chat \
  --api-url http://localhost:1995/api/v1/memories

# 仅验证格式
uv run python src/bootstrap.py src/run_memorize.py \
  --input data/group_chat.json \
  --scene group_chat \
  --validate-only
```

### 参数

| 参数 | 必需 | 描述 |
|-----------|----------|-------------|
| `--input` | 是 | GroupChatFormat JSON 文件的路径 |
| `--scene` | 是 | `group_chat` 或 `assistant` |
| `--api-url` | 是* | Memory API 端点 |
| `--validate-only` | 否 | 仅验证格式，跳过处理 |

*除非使用 `--validate-only`，否则必需。

---

## 错误响应

所有错误响应遵循此格式：

```json
{
  "status": "failed",
  "code": "ERROR_CODE",
  "message": "Human-readable error message",
  "timestamp": "2025-01-15T10:30:00+00:00",
  "path": "/api/v1/memories"
}
```

### 错误代码

| 代码 | HTTP 状态 | 描述 |
|------|-------------|-------------|
| `INVALID_PARAMETER` | 400 | 无效或缺失的请求参数 |
| `RESOURCE_NOT_FOUND` | 404 | 请求的资源未找到 |
| `SYSTEM_ERROR` | 500 | 内部服务器错误 |

---

## 另请参阅

- [群聊指南](../advanced/GROUP_CHAT_GUIDE.md) - 多参与者对话
- [元数据控制指南](../advanced/METADATA_CONTROL.md) - 对话元数据管理
- [GroupChatFormat 规范](../../data_format/group_chat/group_chat_format.md) - 数据格式参考