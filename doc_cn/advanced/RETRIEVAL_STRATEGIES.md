# 记忆检索策略

[主页](../../README.md) > [文档](../README.md) > [高级](.) > 检索策略

本指南解释了 EverMemOS 中可用的不同检索策略以及何时使用每种策略。

---

## 目录

- [概述](#overview)
- [轻量级检索](#lightweight-retrieval)
- [智能体检索](#agentic-retrieval)
- [选择策略](#choosing-a-strategy)
- [API 示例](#api-examples)
- [性能比较](#performance-comparison)
- [最佳实践](#best-practices)

---

## 概述

EverMemOS 提供两种主要的检索策略：

1. **轻量级检索** - 快速、高效的检索，适用于延迟敏感的场景
2. **智能体检索** - 智能、多轮检索，适用于复杂查询

两种策略都利用记忆感知层通过多轮推理和智能融合来回忆相关记忆，实现精确的上下文感知。

---

## 轻量级检索

跳过 LLM 调用的快速检索模式，以实现最低延迟。

### 检索模式

#### 1. 关键词搜索

使用 Elasticsearch BM25 的纯关键词搜索。

**特点：**
- 最快的检索模式
- 不需要嵌入
- 最适合精确关键词匹配
- 语义查询的准确率较低

**何时使用：**
- 精确短语或关键词搜索
- 延迟至关重要（< 100ms）
- 不需要语义理解

**示例：**
```python
{
    "query": "soccer weekend",
    "retrieve_method": "keyword"
}
```

#### 2. 向量（语义搜索）

使用 Milvus 的纯向量搜索。

**特点：**
- 语义理解
- 查找相似含义，而不仅仅是关键词
- 需要嵌入模型
- 中等延迟（~200-500ms）

**何时使用：**
- 语义相似性很重要
- 查询措辞与存储内容不同
- 需要概念匹配

**示例：**
```python
{
    "query": "What sports does user enjoy?",
    "retrieve_method": "vector"
}
```

#### 3. RRF（混合检索）- 推荐

BM25 和嵌入结果的倒数排名融合。

**特点：**
- 两全其美
- BM25 和嵌入搜索的并行执行
- 使用 RRF 算法融合结果
- 平衡的准确性和速度

**何时使用：**
- 大多数场景的默认选择
- 需要关键词和语义匹配
- 需要在各种查询类型中实现稳健的检索

**示例：**
```python
{
    "query": "What are user's weekend activities?",
    "retrieve_method": "rrf"
}
```

### 智能重排

可选的重排步骤以提高结果相关性：

- **批量并发处理**，具有指数退避重试
- **深度相关性评分**，使用重排模型
- **优先化**最关键的信息
- **高吞吐量**稳定性

重排自动应用于 `hybrid` 和 `agentic` 检索方法。对于程序化控制，请参阅[智能体检索指南](../dev_docs/agentic_retrieval_guide.md)。

---

## 智能体检索

使用 LLM 进行查询扩展和融合的智能、多轮检索。

### 工作原理

1. **查询分析** - LLM 分析用户查询
2. **查询扩展** - 生成 2-3 个互补查询
3. **并行检索** - 为每个查询检索记忆
4. **RRF 融合** - 使用多路径 RRF 融合结果
5. **上下文整合** - 将记忆与当前对话连接

### 特点

- **更高延迟**（~2-5 秒，包括 LLM 调用）
- **更好覆盖**复杂意图
- **多方面查询**有效处理
- **自适应**查询复杂度

### 何时使用

- 复杂、多方面的查询
- 需要上下文理解的查询
- 准确性比速度更重要
- 轻量级模式的结果不足

### 示例工作流程

**用户查询：** "Tell me about my work-life balance"

**步骤 1 - 查询扩展：**
- 原始："Tell me about my work-life balance"
- 扩展 1："work schedule and working hours"
- 扩展 2："hobbies and leisure activities"
- 扩展 3："stress and relaxation"

**步骤 2 - 并行检索：**
每个查询使用 RRF 检索 top-k 记忆

**步骤 3 - 融合：**
使用多路径 RRF 合并结果

**步骤 4 - 响应：**
LLM 基于检索到的记忆生成响应

---

## 选择策略

### 决策流程

```
延迟是否关键（< 100ms）？
├─ 是 → 使用关键词
└─ 否 → 继续

是否需要语义理解？
├─ 否 → 使用关键词
└─ 是 → 继续

查询是否复杂或多方面？
├─ 是 → 使用智能体
└─ 否 → 继续

默认选择 → 使用 RRF
```

### 用例矩阵

| 用例 | 推荐策略 | 原因 |
|----------|---------------------|--------|
| 精确短语搜索 | 关键词 | 快速、精确的关键词匹配 |
| 按名称搜索产品 | 关键词或 RRF | 关键词很重要 |
| 对话式查询 | RRF 或智能体 | 需要语义理解 |
| 复杂分析问题 | 智能体 | 多方面覆盖 |
| 实时聊天 | RRF | 速度和准确性的平衡 |
| 后台索引 | 任何 | 无延迟约束 |
| 自动完成/建议 | 关键词 | 速度至关重要 |
| 研究/分析 | 智能体 | 准确性至关重要 |

---

## API 示例

### 轻量级 - 关键词

```bash
curl -X GET http://localhost:1995/api/v1/memories/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "soccer",
    "user_id": "user_001",
    "memory_types": ["episodic_memory"],
    "retrieve_method": "keyword",
    "top_k": 5
  }'
```

### 轻量级 - 向量

```bash
curl -X GET http://localhost:1995/api/v1/memories/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What sports does user like?",
    "user_id": "user_001",
    "memory_types": ["episodic_memory"],
    "retrieve_method": "vector",
    "top_k": 5
  }'
```

### 轻量级 - RRF（推荐）

```bash
curl -X GET http://localhost:1995/api/v1/memories/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Tell me about user hobbies",
    "user_id": "user_001",
    "memory_types": ["episodic_memory"],
    "retrieve_method": "rrf",
    "top_k": 5
  }'
```

### 智能体检索

```bash
curl -X GET http://localhost:1995/api/v1/memories/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is my work-life balance like?",
    "user_id": "user_001",
    "memory_types": ["episodic_memory"],
    "retrieve_method": "agentic",
    "top_k": 10
  }'
```

---

## 性能比较

### 延迟

| 策略 | 典型延迟 | 备注 |
|----------|----------------|-------|
| 关键词 | 50-100ms | 最快 |
| 向量 | 200-500ms | 取决于 Milvus 性能 |
| RRF | 200-600ms | 并行关键词 + 向量 |
| 智能体 | 2-5 秒 | 包括 LLM 查询扩展 |

### 准确性

在 LoCoMo 基准测试上测量：

| 策略 | 精确率 | 召回率 | F1 分数 |
|----------|-----------|--------|----------|
| 关键词 | 0.72 | 0.68 | 0.70 |
| 向量 | 0.78 | 0.75 | 0.77 |
| RRF | 0.85 | 0.82 | 0.84 |
| 智能体 | 0.91 | 0.89 | 0.90 |

*注意：实际性能因查询类型和数据而异*

### 资源使用

| 策略 | CPU | 内存 | 网络 |
|----------|-----|--------|---------|
| 关键词 | 低 | 低 | 最小 |
| 向量 | 中 | 中 | 中等（嵌入 API） |
| RRF | 中 | 中 | 中等 |
| 智能体 | 中-高 | 中 | 高（多次 LLM 调用） |

---

## 最佳实践

### 1. 从 RRF 开始

对于大多数应用程序，RRF 提供最佳平衡：
- 良好的准确性
- 合理的延迟
- 在各种查询类型中稳健

### 2. 对已知模式使用关键词搜索

当用户搜索特定关键词或短语时：
- 产品名称
- 精确引用
- 技术术语

### 3. 为复杂查询保留智能体

在以下情况下使用智能体检索：
- 用户查询模糊或复杂
- 标准检索返回结果不足
- 需要分析或推理

### 4. 调整 top_k 参数

- **关键词**：较低的 top_k（3-5）以获得精确匹配
- **向量/RRF**：中等的 top_k（5-10）以获得覆盖
- **智能体**：较高的 top_k（10-20）以获得全面结果

### 5. 监控和优化

- 跟踪查询延迟并调整策略
- 监控结果相关性并切换模式
- 考虑缓存频繁查询

### 6. 组合策略

为不同的查询类型使用不同的策略：

```python
def select_strategy(query):
    # 精确短语（在引号中）
    if query.startswith('"') and query.endswith('"'):
        return "keyword"

    # 复杂问题
    if any(word in query.lower() for word in ["why", "how", "explain", "analyze"]):
        return "agentic"

    # 默认
    return "rrf"
```

---

## 另请参阅

- [架构：记忆感知](../ARCHITECTURE.md#memory-perception-architecture) - 技术架构
- [API 文档](../api_docs/memory_api.md) - 完整 API 参考
- [智能体检索指南](../dev_docs/agentic_retrieval_guide.md) - 深入的智能体检索
- [评估指南](../../evaluation/README.md) - 基准测试检索策略
- [使用示例](../usage/USAGE_EXAMPLES.md) - 实用示例