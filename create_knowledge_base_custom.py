#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
专门处理用户指定的三个PDF文件，创建知识库
1. 董事会提名及薪酬考核委员会实施细则.pdf
2. 2024年航天长峰年度报告摘要.pdf
3. ECMO发明专利全文（只处理第一页）
"""
import os
import sys
import json
from datetime import datetime

# 添加自定义库路径
sys.path.append('E:\pythonLib\site-packages')

from rag_pipeline import RAGPipeline
from pdf_parser import PDFParser


def process_single_pdf(rag_pipeline, pdf_path, enterprise_name, file_type, is_invention=False):
    """
    处理单个PDF文件，支持发明专利只处理第一页
    
    Args:
        rag_pipeline: RAGPipeline实例
        pdf_path: PDF文件路径
        enterprise_name: 企业名称
        file_type: 文件类型，"annual_report"或"patent"
        is_invention: 是否为发明专利文件（只处理第一页）
        
    Returns:
        处理后的文本块列表
    """
    print(f"\n📄 处理指定文件: {os.path.basename(pdf_path)}")
    print(f"📊 文件类型: {file_type}")
    
    try:
        # 1. 解析PDF
        parsed_data = rag_pipeline.pdf_parser.parse_pdf(pdf_path)
        
        # 2. 如果是发明专利文件，只保留第一页
        if is_invention:
            print(f"📄 发明专利文件，只保留第一页")
            parsed_data['pages'] = parsed_data['pages'][:1] if parsed_data['pages'] else []
            parsed_data['metadata']['num_pages'] = 1
        
        # 保存解析后的数据
        parsed_output_path = os.path.join(rag_pipeline.data_dir, "parsed_reports", f"{enterprise_name}_{file_type}_{os.path.basename(pdf_path).replace('.pdf', '')}.json")
        rag_pipeline.pdf_parser.save_parsed_data(parsed_data, parsed_output_path)
        print(f"✅ PDF解析完成，共{len(parsed_data['pages'])}页")
        
        # 3. 分块
        chunks = rag_pipeline.text_splitter.split_parsed_pdf(parsed_data)
        
        # 关键修复：给每个chunk添加file_type元数据
        for chunk in chunks:
            if "metadata" not in chunk:
                chunk["metadata"] = {}
            chunk["metadata"]["file_type"] = file_type  # 添加类型标识（annual_report/patent）
        
        chunked_output_path = os.path.join(rag_pipeline.data_dir, "chunked_reports", f"{enterprise_name}_{file_type}_{os.path.basename(pdf_path).replace('.pdf', '')}.json")
        os.makedirs(os.path.dirname(chunked_output_path), exist_ok=True)
        with open(chunked_output_path, "w", encoding="utf-8") as f:
            json.dump(chunks, f, ensure_ascii=False, indent=2)
        print(f"✅ 文本分块完成，共{len(chunks)}个文本块，已添加file_type元数据: {file_type}")
        
        # 4. 创建向量库 - 按类型生成专属库（强化命名隔离）
        base_filename = os.path.basename(pdf_path).replace('.pdf', '')
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")  # 新增时间戳，避免重名
        if file_type == "annual_report":
            vector_db_path = os.path.join(rag_pipeline.data_dir, "vector_dbs", 
                                         f"{enterprise_name}_年报_{base_filename}_{timestamp}.faiss")
            bm25_db_path = os.path.join(rag_pipeline.data_dir, "bm25_dbs", 
                                       f"{enterprise_name}_年报_{base_filename}_{timestamp}_bm25.pkl")
        elif file_type == "patent":
            vector_db_path = os.path.join(rag_pipeline.data_dir, "vector_dbs", 
                                         f"{enterprise_name}_专利_{base_filename}_{timestamp}.faiss")
            bm25_db_path = os.path.join(rag_pipeline.data_dir, "bm25_dbs", 
                                       f"{enterprise_name}_专利_{base_filename}_{timestamp}_bm25.pkl")
        else:
            vector_db_path = os.path.join(rag_pipeline.data_dir, "vector_dbs", 
                                         f"{enterprise_name}_{file_type}_{base_filename}_{timestamp}.faiss")
            bm25_db_path = os.path.join(rag_pipeline.data_dir, "bm25_dbs", 
                                       f"{enterprise_name}_{file_type}_{base_filename}_{timestamp}_bm25.pkl")
        
        rag_pipeline.embedding_retrieval.create_vector_db(chunks, vector_db_path)
        print("✅ 向量库创建完成")
        
        # 5. 创建BM25库
        rag_pipeline.embedding_retrieval.create_bm25_db(chunks, bm25_db_path)
        print("✅ BM25库创建完成")
        
        # 6. 检查是否需要将数据添加到Elasticsearch
        print("📦 检查Elasticsearch连接...")
        try:
            print("📤 将数据添加到Elasticsearch...")
            rag_pipeline.es_integration.index_chunks(chunks, enterprise_name)
            print("✅ 成功添加到Elasticsearch")
        except Exception as e:
            print(f"⚠️ Elasticsearch操作失败: {str(e)}")
            print("⚠️ 跳过Elasticsearch索引")
        
        return chunks
        
    except Exception as e:
        print(f"❌ 处理失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return []


def main():
    """主函数"""
    # 获取当前目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(current_dir, "data")
    
    # 初始化RAG流水线
    print("✅ 初始化RAG系统...")
    rag_pipeline = RAGPipeline(data_dir)
    
    # 企业名称
    enterprise_name = "航天长峰"
    
    # 指定的三个PDF文件，添加file_type参数
    pdf_files = [
        {
            "path": "D:/AI CASES/CASE RAGSHISHI/股东大会资料/北京航天长峰股份有限公司董事会提名及薪酬考核委员会实施细则.pdf",
            "file_type": "annual_report",
            "is_invention": False
        },
        {
            "path": "D:/AI CASES/CASE RAGSHISHI/航天长峰年报及摘要/2024年航天长峰年度报告摘要.pdf",
            "file_type": "annual_report",
            "is_invention": False
        },
        {
            "path": "D:/AI CASES/CASE RAGSHISHI/ECMO发明专利全文/2 公开全文 一种泵头氧合器组件和体外膜肺氧合系统.pdf",
            "file_type": "patent",
            "is_invention": True
        }
    ]
    
    total_chunks = 0
    
    # 处理每个PDF文件
    for pdf_info in pdf_files:
        chunks = process_single_pdf(
            rag_pipeline,
            pdf_info["path"],
            enterprise_name,
            pdf_info["file_type"],  # 传递file_type参数
            pdf_info["is_invention"]  # 传递is_invention参数
        )
        total_chunks += len(chunks)
    
    print(f"\n🎉 知识库创建完成！")
    print(f"📊 共处理3个文件，生成{total_chunks}个文本块")
    print(f"📦 所有数据已保存到: {data_dir}")
    print("\n📋 测试步骤：")
    print("1. 启动Gradio应用: python gradio_app.py")
    print("2. 访问 http://localhost:7861")
    print("3. 输入问题进行测试")
    

if __name__ == "__main__":
    main()