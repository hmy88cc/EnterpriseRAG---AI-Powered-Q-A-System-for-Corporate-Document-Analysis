# 企航智投 - 企业级 RAG 智能问答系统

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Gradio](https://img.shields.io/badge/UI-Gradio-orange.svg)](https://gradio.app/)

## 📖 项目简介

**企航智投**是一个基于 RAG（Retrieval-Augmented Generation）技术的企业级智能问答系统，专门用于处理和分析企业文档（包括年度报告、专利技术文档、股东大会资料等），结合实时金融数据，提供智能化的知识检索和问答服务。

### 核心特性

- 🎯 **多源数据融合**：支持 PDF 文档、向量数据库、BM25 检索、Elasticsearch 等多种数据源
- 🔍 **混合检索策略**：结合向量语义检索 + BM25 关键词检索 + 数据库路由，提升检索准确率
- 🔄 **智能重排序**：使用 LLM 对检索结果进行二次排序，优化答案质量
- 📊 **实时数据集成**：集成股票实时数据、K线数据等金融信息
- 🌐 **外部搜索增强**：支持 Tavily 搜索引擎，扩展知识边界
- 💬 **友好交互界面**：基于 Gradio 构建的现代化 Web 界面
- 🏢 **企业知识库管理**：支持多企业、多类型文档的知识库创建和管理

## 🏗️ 技术架构

### 技术栈

- **前端界面**: Gradio
- **大语言模型**: Dashscope (阿里云通义千问)
- **向量数据库**: FAISS
- **全文检索**: Elasticsearch, BM25
- **Embedding 模型**: 阿里云文本嵌入模型
- **数据处理**: PyPDF2, pdfplumber, pandas
- **金融数据**: AkShare, easyquotation
- **外部搜索**: Tavily API

### 系统架构图

```
┌─────────────────────────────────────────────────────┐
│                   Gradio Web UI                      │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│                RAG Pipeline Core                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │
│  │ Query    │→ │ Database │→ │ Embedding        │  │
│  │ Analysis │  │ Router   │  │ Retrieval        │  │
│  └──────────┘  └──────────┘  └──────────────────┘  │
│                                    │                 │
│  ┌──────────┐  ┌──────────┐       │                 │
│  │ Answer   │← │ LLM      │←──────┘                 │
│  │ Gen      │  │ Rerank   │                          │
│  └──────────┘  └──────────┘                          │
└─────────────────────────────────────────────────────┘
         │              │              │
         ▼              ▼              ▼
   ┌──────────┐  ┌──────────┐  ┌──────────┐
   │ Vector   │  │ BM25     │  │ Elastic- │
   │ DB       │  │ Index    │  │ search   │
   └──────────┘  └──────────┘  └──────────┘
         │
         ▼
   ┌──────────┐  ┌──────────┐
   │ Real-time│  │ Tavily   │
   │ Data     │  │ Search   │
   └──────────┘  └──────────┘
```

## 📁 项目结构

```
CASE RAGSHISHI/
├── 📄 核心程序
│   ├── gradio_app.py                 # Web 应用入口
│   ├── rag_pipeline.py               # RAG 核心管道
│   ├── pdf_parser.py                 # PDF 解析器
│   ├── text_splitter.py              # 文本分割器
│   ├── embedding_retrieval.py        # 向量检索模块
│   ├── llm_reranking.py              # LLM 重排序模块
│   ├── database_router.py            # 数据库路由器
│   ├── prompts.py                    # 提示词管理
│   ├── elasticsearch_integration.py  # Elasticsearch 集成
│   ├── tavily_search.py              # Tavily 搜索集成
│   └── real_time_data.py             # 实时数据服务
│
├── 🛠️ 工具脚本
│   ├── create_knowledge_base_custom.py  # 知识库创建工具
│   ├── process_pdf_files.py             # PDF 批量处理工具
│   └── investing_kline_spider.py        # K线数据爬虫
│
├── 📊 数据目录
│   ├── data/
│   │   ├── vector_dbs/              # 向量数据库文件
│   │   ├── bm25_dbs/                # BM25 索引文件
│   │   ├── chunked_reports/         # 分块后的文本数据
│   │   └── parsed_reports/          # 解析后的原始数据
│   ├── ECMO发明专利全文/             # 专利文档
│   ├── 股东大会资料/                 # 股东大会文档
│   └── 航天长峰年报及摘要/           # 年报文档
│
├── 📝 配置文件
│   ├── requirements.txt             # Python 依赖包
│   └── .env                         # 环境变量配置（需自行创建）
│
└── 📚 文档
    ├── README.md                    # 项目说明文档
    ├── 企业RAG系统核心程序位置.md    # 核心程序说明
    └── logs/                        # 运行日志
```

## 🚀 快速开始

### 环境要求

- Python 3.8+
- Windows / Linux / macOS

### 安装步骤

1. **克隆项目**

```bash
git clone https://github.com/your-username/CASE-RAGSHISHI.git
cd CASE-RAGSHISHI
```

2. **安装依赖**

```bash
pip install -r requirements.txt
```

3. **配置环境变量**

创建 `.env` 文件并配置以下变量：

```env
# 阿里云 Dashscope API Key
DASHSCOPE_API_KEY=your_api_key_here

# Tavily Search API Key（可选）
TAVILY_API_KEY=your_tavily_api_key_here

# Elasticsearch 配置（如果使用）
ELASTICSEARCH_HOST=localhost
ELASTICSEARCH_PORT=9200
```

4. **创建知识库**

```bash
# 处理自定义 PDF 文件
python create_knowledge_base_custom.py

# 或批量处理 PDF 文件
python process_pdf_files.py
```

5. **启动应用**

```bash
python gradio_app.py
```

6. **访问界面**

打开浏览器访问：`http://localhost:7860`

## 💡 使用指南

### 1. 知识库创建

系统支持多种类型的企业文档：

- **年度报告**：企业年报、ESG 报告等
- **专利文档**：发明专利、实用新型专利等
- **治理文件**：董事会决议、股东大会资料等

### 2. 问答功能

在 Web 界面中输入问题，系统会：

1. 分析问题意图
2. 路由到合适的数据库
3. 检索相关文档片段
4. LLM 重排序优化结果
5. 生成最终答案并引用来源

### 3. 支持的查询类型

- 📊 **财务数据查询**：营收、利润、增长率等
- 📋 **文档内容检索**：专利技术方案、治理规则等
- 📈 **实时股票信息**：股价、成交量、K线数据等
- 🔍 **综合知识问答**：跨文档的综合分析问题

## ⚙️ 核心模块说明

### RAG Pipeline (`rag_pipeline.py`)

核心协调模块，整合所有子模块：
- 查询意图分析
- 数据库路由选择
- 检索结果融合
- 答案生成与优化

### 数据库路由 (`database_router.py`)

智能路由机制，根据查询类型选择最优数据源：
- 向量数据库（语义相似性）
- BM25 索引（关键词匹配）
- Elasticsearch（全文检索）
- 实时数据接口

### 向量检索 (`embedding_retrieval.py`)

基于 FAISS 的向量相似度检索：
- 支持多知识库切换
- 混合检索策略
- Top-K 结果返回

### LLM 重排序 (`llm_reranking.py`)

使用大语言模型对检索结果进行相关性重排序，提升答案质量。

### 实时数据服务 (`real_time_data.py`)

集成金融实时数据：
- 股票实时行情
- K线历史数据
- 财务指标计算

## 📊 示例应用场景

### 场景 1：企业年报分析

```
用户提问："XXXX公司2024年的营业收入是多少？同比增长情况如何？"

系统响应：
- 检索 2024 年年度报告
- 提取财务数据
- 计算同比增长率
- 生成结构化回答
```

### 场景 2：专利技术查询

```
用户提问："主动脉支架的核心技术方案是什么？"

系统响应：
- 检索相关专利文档
- 提取技术方案要点
- 总结核心创新点
- 引用专利来源
```

### 场景 3：实时股票查询

```
用户提问："XXXX股票今天的股价是多少？"

系统响应：
- 调用实时数据接口
- 获取最新行情
- 展示关键指标
```

## 🔧 开发指南

### 添加新的数据源

1. 在 `database_router.py` 中注册新数据源
2. 实现对应的检索接口
3. 更新查询分类逻辑

### 自定义提示词

在 `prompts.py` 中修改或添加新的提示词模板：

```python
def get_custom_prompt():
    return """
    你的自定义提示词模板
    """
```

### 扩展检索策略

在 `embedding_retrieval.py` 中添加新的检索算法或优化现有策略。

## 📝 依赖包说明

主要依赖包（详见 `requirements.txt`）：

```
gradio>=4.0.0          # Web 界面框架
dashscope>=1.14.0      # 阿里云大模型 SDK
faiss-cpu>=1.7.4       # 向量相似度搜索
elasticsearch>=8.0.0   # 全文搜索引擎
akshare>=1.12.0        # 金融数据接口
pandas>=2.0.0          # 数据处理
pdfplumber>=0.9.0      # PDF 解析
```

## ⚠️ 注意事项

1. **API Key 安全**：请勿将 `.env` 文件上传到公开仓库
2. **数据隐私**：确保处理的文档不包含敏感信息
3. **资源占用**：向量数据库和 Elasticsearch 需要足够的内存
4. **网络依赖**：部分功能需要访问外部 API（Dashscope、Tavily 等）

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 📧 联系方式

如有问题或建议，请通过以下方式联系：

- 提交 Issue
- 发送邮件至：[your-email@example.com]

## 🙏 致谢

感谢以下开源项目和技术：

- [Gradio](https://gradio.app/) - 友好的 Web 界面框架
- [FAISS](https://faiss.ai/) - 高效的向量相似度搜索
- [Dashscope](https://dashscope.aliyun.com/) - 阿里云大模型服务
- [AkShare](https://akshare.xyz/) - 开源金融数据接口

---

**⭐ 如果这个项目对您有帮助，请给个 Star！**
