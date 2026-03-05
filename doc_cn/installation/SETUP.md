# 完整设置指南

[主页](../../README.md) > [文档](../README.md) > [安装](.) > 设置

本指南提供了 EverMemOS 的安装和设置的全面说明。

---

## 目录

- [系统要求](#system-requirements)
- [安装方法](#installation-methods)
- [Docker 安装（推荐）](#docker-installation-recommended)
- [环境配置](#environment-configuration)
- [启动服务器](#starting-the-server)
- [验证](#verification)
- [故障排除](#troubleshooting)
- [下一步](#next-steps)

---

## 系统要求

### 最低要求

- **Python**：3.10 或更高版本
- **uv**：包管理器（将在设置过程中安装）
- **Docker**：20.10+
- **Docker Compose**：2.0+
- **RAM**：至少 4GB 可用（用于 Elasticsearch 和 Milvus）
- **磁盘空间**：至少 10GB 可用空间

### 推荐要求

- **RAM**：8GB 或更多
- **CPU**：4 核或更多
- **磁盘空间**：20GB 或更多（特别是对于大型数据集）

### 操作系统

EverMemOS 已在以下系统上测试：
- macOS（Intel 和 Apple Silicon）
- Linux（Ubuntu 20.04+、Debian 等）
- Windows（通过 WSL2）

---

## 安装方法

EverMemOS 可以通过两种方式安装：

1. **Docker 安装（推荐）** - 使用 Docker Compose 安装所有依赖服务
2. **手动安装** - 手动安装和配置每个服务

本指南涵盖 Docker 安装方法。对于手动安装，请参阅[高级安装](#manual-installation-advanced)。

---

## Docker 安装（推荐）

### 步骤 1：克隆仓库

```bash
git clone https://github.com/EverMind-AI/EverMemOS.git
cd EverMemOS
```

### 步骤 2：启动 Docker 服务

使用一个命令启动所有依赖服务（MongoDB、Elasticsearch、Milvus、Redis）：

```bash
docker-compose up -d
```

这将启动：
- MongoDB 在端口 27017
- Elasticsearch 在端口 19200
- Milvus 在端口 19530
- Redis 在端口 6379

有关详细的服务配置，请参阅 [Docker 设置指南](DOCKER_SETUP.md)。

### 步骤 3：验证 Docker 服务

检查所有服务是否正在运行：

```bash
docker-compose ps
```

你应该看到所有服务都处于"Up"状态。

### 步骤 4：安装 uv 包管理器

如果你还没有安装 uv：

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

安装后，重启终端或运行：

```bash
source $HOME/.cargo/env
```

验证安装：

```bash
uv --version
```

### 步骤 5：安装项目依赖

```bash
uv sync
```

这将：
- 创建虚拟环境
- 安装所有必需的 Python 包
- 为开发设置项目

---

## 环境配置

### 步骤 1：复制环境模板

```bash
cp env.template .env
```

### 步骤 2：配置 API 密钥

编辑 `.env` 文件并填写必需的配置：

```bash
# 在你喜欢的编辑器中打开 .env
nano .env
# 或
vim .env
# 或
code .env
```

### 必需配置

#### LLM API 密钥（用于记忆提取）

选择以下选项之一：

```bash
# 选项 1：OpenAI
LLM_API_KEY=sk-your-openai-key-here
LLM_API_BASE=https://api.openai.com/v1

# 选项 2：OpenRouter
OPENROUTER_API_KEY=sk-or-v1-your-openrouter-key
OPENROUTER_API_BASE=https://openrouter.ai/api/v1

# 选项 3：其他 OpenAI 兼容 API
LLM_API_KEY=your-api-key
LLM_API_BASE=https://your-api-endpoint.com/v1
```

#### 向量化 API 密钥（用于嵌入和重排）

```bash
# DeepInfra（推荐）
VECTORIZE_API_KEY=your-deepinfra-key
VECTORIZE_API_BASE=https://api.deepinfra.com/v1/openai

# 或分别配置嵌入和重排
EMBEDDING_API_KEY=your-embedding-key
EMBEDDING_API_BASE=https://your-embedding-endpoint.com
RERANK_API_KEY=your-rerank-key
RERANK_API_BASE=https://your-rerank-endpoint.com
```

### 可选配置

```bash
# 模型选择
LLM_MODEL=gpt-4  # 或 gpt-3.5-turbo 等
EMBEDDING_MODEL=BAAI/bge-large-en-v1.5
RERANK_MODEL=BAAI/bge-reranker-large

# 服务端点（显示默认值）
MONGODB_URI=mongodb://admin:memsys123@localhost:27017
ELASTICSEARCH_URL=http://localhost:19200
MILVUS_HOST=localhost
MILVUS_PORT=19530
REDIS_URL=redis://localhost:6379
```

有关完整的配置选项，请参阅[配置指南](../usage/CONFIGURATION_GUIDE.md)。

---

## 启动服务器

### 启动 API 服务器

```bash
uv run python src/run.py --port 1995
```

服务器默认将在 `http://localhost:1995` 上启动。

你应该看到类似的输出：

```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:1995 (Press CTRL+C to quit)
```

### 自定义端口

默认端口是 1995。要使用不同的端口：

```bash
uv run python src/run.py --port 9000
```

---

## 验证

### 测试 API

打开新终端并测试 API：

```bash
curl http://localhost:1995/health
```

你应该收到指示服务健康的响应。

### 运行简单演示

使用简单演示测试完整工作流程：

```bash
# 在新终端中（保持服务器运行）
uv run python src/bootstrap.py demo/simple_demo.py
```

这将：
1. 存储示例对话消息
2. 等待索引
3. 搜索相关记忆
4. 显示结果

如果这能正常工作，你的安装就成功了！

---

## 故障排除

### Docker 服务无法启动

**问题**：`docker-compose up -d` 失败或服务无法启动

**解决方案**：
- 检查 Docker 是否正在运行：`docker info`
- 检查端口冲突：`lsof -i :27017,19200,19530,6379`
- 查看日志：`docker-compose logs -f`
- 重启服务：`docker-compose restart`

### 内存不足

**问题**：Elasticsearch 或 Milvus 由于 OOM 而崩溃

**解决方案**：
- 增加 Docker 内存限制（Docker Desktop > 首选项 > 资源）
- 减少 docker-compose.yml 中的堆大小
- 关闭其他内存密集型应用程序

### Python 依赖失败

**问题**：`uv sync` 失败并报错

**解决方案**：
- 更新 uv：`curl -LsSf https://astral.sh/uv/install.sh | sh`
- 清除缓存：`uv cache clean`
- 尝试详细输出：`uv sync -v`

### API 服务器无法启动

**问题**：服务器无法启动或崩溃

**解决方案**：
- 检查 .env 文件是否正确配置
- 验证所有 Docker 服务是否正在运行：`docker-compose ps`
- 检查日志中的具体错误
- 确保端口 1995 未被使用：`lsof -i :1995`

### 连接错误

**问题**：无法连接到 MongoDB/Elasticsearch/Milvus

**解决方案**：
- 验证服务是否正在运行：`docker-compose ps`
- 检查 .env 中的连接字符串
- 使用主机端口（27017、19200、19530）而不是容器端口
- 单独测试连接：
  ```bash
  # MongoDB
  mongosh mongodb://admin:memsys123@localhost:27017

  # Elasticsearch
  curl http://localhost:19200

  # Redis
  redis-cli -h localhost -p 6379 ping
  ```

有关更多故障排除帮助，请参阅：
- [Docker 设置指南](DOCKER_SETUP.md)
- [配置指南](../usage/CONFIGURATION_GUIDE.md)
- [GitHub 问题](https://github.com/EverMind-AI/EverMemOS/issues)

---

## 手动安装（高级）

如果你不想使用 Docker，可以手动安装每个服务：

### 必需服务

1. **MongoDB 7.0+**
   - 请参阅 [MongoDB 指南](../usage/MONGODB_GUIDE.md)

2. **Elasticsearch 8.x**
   - 从 [elastic.co](https://www.elastic.co/downloads/elasticsearch) 下载
   - 配置端口 9200

3. **Milvus 2.4+**
   - 遵循 [Milvus 安装指南](https://milvus.io/docs/install_standalone-docker.md)
   - 配置端口 19530

4. **Redis 7.x**
   - 通过包管理器安装或从 [redis.io](https://redis.io/download) 下载
   - 配置端口 6379

手动安装服务后，相应地更新 `.env` 中的连接字符串。

---

## 下一步

现在 EverMemOS 已安装，你可以：

1. **[尝试演示](../usage/DEMOS.md)** - 显示记忆提取和聊天的交互式示例
2. **[学习 API](../api_docs/memory_api.md)** - 将 EverMemOS 集成到你的应用中
3. **[探索使用示例](../usage/USAGE_EXAMPLES.md)** - 常见使用模式
4. **[运行评估](../../evaluation/README.md)** - 在基准数据集上测试

---

## 另请参阅

- [Docker 设置指南](DOCKER_SETUP.md) - 详细的 Docker 配置
- [配置指南](../usage/CONFIGURATION_GUIDE.md) - 完整的配置选项
- [MongoDB 指南](../usage/MONGODB_GUIDE.md) - MongoDB 安装和设置
- [快速开始（README）](../../README.md#quick-start) - 快速开始概述
- [开发者入门](../dev_docs/getting_started.md) - 开发设置