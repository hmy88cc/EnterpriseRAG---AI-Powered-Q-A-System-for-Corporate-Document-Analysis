# Qihang Zhitou - Enterprise RAG Intelligent Q&A System

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Gradio](https://img.shields.io/badge/UI-Gradio-orange.svg)](https://gradio.app/)

##  Project Overview

**Qihang Zhitou** is an enterprise-grade intelligent Q&A system based on RAG (Retrieval-Augmented Generation) technology, specifically designed to process and analyze enterprise documents (including annual reports, patent technical documents, shareholder meeting materials, etc.), combined with real-time financial data, providing intelligent knowledge retrieval and Q&A services.

### Core Features

- 🎯 **Multi-source Data Integration**: Supports PDF documents, vector databases, BM25 retrieval, Elasticsearch, and other data sources
- 🔍 **Hybrid Retrieval Strategy**: Combines vector semantic retrieval + BM25 keyword retrieval + database routing to improve retrieval accuracy
- 🔄 **Intelligent Reranking**: Uses LLM to rerank retrieval results for optimized answer quality
- 📊 **Real-time Data Integration**: Integrates real-time stock data, K-line data, and other financial information
- 🌐 **External Search Enhancement**: Supports Tavily search engine to expand knowledge boundaries
- 💬 **User-friendly Interface**: Modern web interface built with Gradio
- 🏢 **Enterprise Knowledge Base Management**: Supports knowledge base creation and management for multiple enterprises and document types

## 🏗️ Technical Architecture

### Technology Stack

- **Frontend Interface**: Gradio
- **Large Language Model**: Dashscope (Alibaba Cloud Tongyi Qianwen)
- **Vector Database**: FAISS
- **Full-text Search**: Elasticsearch, BM25
- **Embedding Model**: Alibaba Cloud Text Embedding Model
- **Data Processing**: PyPDF2, pdfplumber, pandas
- **Financial Data**: AkShare, easyquotation
- **External Search**: Tavily API

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────┐
│                   Gradio Web UI                      │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│                RAG Pipeline Core                     │
│  ┌──────────┐  ──────────┐  ┌──────────────────  │
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
   └──────────┘  └──────────┘  ──────────┘
         │
         ▼
   ┌──────────┐  ┌──────────┐
   │ Real-time│  │ Tavily   │
   │ Data     │  │ Search   │
   └──────────┘  └──────────┘
```

##  Project Structure

```
CASE RAGSHISHI/
├── 📄 Core Programs
│   ├── gradio_app.py                 # Web application entry point
│   ├── rag_pipeline.py               # RAG core pipeline
│   ├── pdf_parser.py                 # PDF parser
│   ├── text_splitter.py              # Text splitter
│   ├── embedding_retrieval.py        # Vector retrieval module
│   ├── llm_reranking.py              # LLM reranking module
│   ├── database_router.py            # Database router
│   ├── prompts.py                    # Prompt management
│   ├── elasticsearch_integration.py  # Elasticsearch integration
│   ├── tavily_search.py              # Tavily search integration
│   └── real_time_data.py             # Real-time data service
│
├── 🛠️ Utility Scripts
│   ├── create_knowledge_base_custom.py  # Knowledge base creation tool
│   ├── process_pdf_files.py             # PDF batch processing tool
│   ── investing_kline_spider.py        # K-line data crawler
│
├── 📊 Data Directory
│   ├── data/
│   │   ├── vector_dbs/              # Vector database files
│   │   ├── bm25_dbs/                # BM25 index files
│   │   ├── chunked_reports/         # Chunked text data
│   │   └── parsed_reports/          # Parsed raw data
│   ├── 发明专利全文/                 # Patent documents
│   ├── 股东大会资料/                 # Shareholder meeting materials
│   └── 公司年报及摘要/               # Annual reports and summaries
│
── 📝 Configuration Files
│   ├── requirements.txt             # Python dependencies
│   └── .env                         # Environment variables (create your own)
│
└── 📚 Documentation
    ├── README.md                    # Project documentation (Chinese)
    ├── README_en.md                 # Project documentation (English)
    └── logs/                        # Runtime logs
```

## 🚀 Quick Start

### Requirements

- Python 3.8+
- Windows / Linux / macOS

### Installation Steps

1. **Clone the repository**

```bash
git clone https://github.com/your-username/CASE-RAGSHISHI.git
cd CASE-RAGSHISHI
```

2. **Install dependencies**

```bash
pip install -r requirements.txt
```

3. **Configure environment variables**

Create a `.env` file and configure the following variables:

```env
# Alibaba Cloud Dashscope API Key
DASHSCOPE_API_KEY=your_api_key_here

# Tavily Search API Key (optional)
TAVILY_API_KEY=your_tavily_api_key_here

# Elasticsearch configuration (if using)
ELASTICSEARCH_HOST=localhost
ELASTICSEARCH_PORT=9200
```

4. **Create knowledge base**

```bash
# Process custom PDF files
python create_knowledge_base_custom.py

# Or batch process PDF files
python process_pdf_files.py
```

5. **Start the application**

```bash
python gradio_app.py
```

6. **Access the interface**

Open your browser and visit: `http://localhost:7860`

## 💡 Usage Guide

### 1. Knowledge Base Creation

The system supports various types of enterprise documents:

- **Annual Reports**: Enterprise annual reports, ESG reports, etc.
- **Patent Documents**: Invention patents, utility model patents, etc.
- **Governance Documents**: Board resolutions, shareholder meeting materials, etc.

### 2. Q&A Functionality

When you input a question in the web interface, the system will:

1. Analyze query intent
2. Route to the appropriate database
3. Retrieve relevant document chunks
4. Rerank results using LLM
5. Generate final answer with source citations

### 3. Supported Query Types

- 📊 **Financial Data Queries**: Revenue, profit, growth rates, etc.
- 📋 **Document Content Retrieval**: Patent technical solutions, governance rules, etc.
-  **Real-time Stock Information**: Stock price, trading volume, K-line data, etc.
- 🔍 **Comprehensive Knowledge Q&A**: Cross-document comprehensive analysis questions

## ⚙️ Core Modules Description

### RAG Pipeline (`rag_pipeline.py`)

Core coordination module that integrates all sub-modules:
- Query intent analysis
- Database routing selection
- Retrieval result fusion
- Answer generation and optimization

### Database Router (`database_router.py`)

Intelligent routing mechanism that selects the optimal data source based on query type:
- Vector database (semantic similarity)
- BM25 index (keyword matching)
- Elasticsearch (full-text search)
- Real-time data interface

### Vector Retrieval (`embedding_retrieval.py`)

FAISS-based vector similarity retrieval:
- Support for multiple knowledge base switching
- Hybrid retrieval strategy
- Top-K result return

### LLM Reranking (`llm_reranking.py`)

Uses large language models to rerank retrieval results for improved answer quality.

### Real-time Data Service (`real_time_data.py`)

Integrates financial real-time data:
- Real-time stock quotes
- K-line historical data
- Financial indicator calculations

## 📊 Example Use Cases

### Use Case 1: Enterprise Annual Report Analysis

```
User Query: "What was the operating revenue of Hangtian Changfeng in 2024? What is the YoY growth?"

System Response:
- Retrieves 2024 annual report
- Extracts financial data
- Calculates YoY growth rate
- Generates structured answer
```

### Use Case 2: Patent Technology Query

```
User Query: "What is the core technical solution of the ECMO oxygenator?"

System Response:
- Retrieves relevant patent documents
- Extracts key points of technical solutions
- Summarizes core innovations
- Cites patent sources
```

### Use Case 3: Real-time Stock Query

```
User Query: "What is today's stock price of Hangtian Changfeng?"

System Response:
- Calls real-time data interface
- Retrieves latest quotes
- Displays key indicators
```

## 🔧 Development Guide

### Adding New Data Sources

1. Register new data source in `database_router.py`
2. Implement corresponding retrieval interface
3. Update query classification logic

### Customizing Prompts

Modify or add new prompt templates in `prompts.py`:

```python
def get_custom_prompt():
    return """
    Your custom prompt template
    """
```

### Extending Retrieval Strategies

Add new retrieval algorithms or optimize existing strategies in `embedding_retrieval.py`.

## 📝 Dependencies Description

Main dependency packages (see `requirements.txt` for details):

```
gradio>=4.0.0          # Web interface framework
dashscope>=1.14.0      # Alibaba Cloud LLM SDK
faiss-cpu>=1.7.4       # Vector similarity search
elasticsearch>=8.0.0   # Full-text search engine
akshare>=1.12.0        # Financial data interface
pandas>=2.0.0          # Data processing
pdfplumber>=0.9.0      # PDF parsing
```

## ⚠️ Important Notes

1. **API Key Security**: Do NOT upload `.env` file to public repositories
2. **Data Privacy**: Ensure processed documents do not contain sensitive information
3. **Resource Usage**: Vector databases and Elasticsearch require sufficient memory
4. **Network Dependencies**: Some features require access to external APIs (Dashscope, Tavily, etc.)

##  Contributing

Contributions are welcome! Please feel free to submit Issues and Pull Requests.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details

##  Contact

If you have any questions or suggestions, please contact us through:

- Submit an Issue
- Send email to: [your-email@example.com]

## 🙏 Acknowledgments

Thanks to the following open-source projects and technologies:

- [Gradio](https://gradio.app/) - Friendly web interface framework
- [FAISS](https://faiss.ai/) - Efficient vector similarity search
- [Dashscope](https://dashscope.aliyun.com/) - Alibaba Cloud LLM service
- [AkShare](https://akshare.xyz/) - Open-source financial data interface

---

**⭐ If this project is helpful to you, please give it a Star!**
