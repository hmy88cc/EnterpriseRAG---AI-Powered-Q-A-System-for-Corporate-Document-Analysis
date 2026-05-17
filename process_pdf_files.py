#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
处理用户提供的PDF文件，将其添加到知识库中
"""
import os
import sys
import glob
import re
from rag_pipeline import RAGPipeline

def main():
    """主函数"""
    # 获取当前目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(current_dir, "data")
    
    # 初始化RAG流水线
    print("✅ 初始化RAG系统...")
    rag_pipeline = RAGPipeline(data_dir)
    
    # 用户提供的PDF目录
    pdf_dirs = [
        "D:/AI CASES/16-项目实战：年报企业知识库+股票实时检索/股东大会资料",
        "D:/AI CASES/16-项目实战：年报企业知识库+股票实时检索/航天长峰年报及摘要"
    ]
    
    # 遍历所有PDF目录
    for pdf_dir in pdf_dirs:
        if not os.path.exists(pdf_dir):
            print(f"⚠️  目录不存在: {pdf_dir}")
            continue
        
        print(f"\n📂 处理目录: {pdf_dir}")
        
        # 获取所有PDF文件
        pdf_files = glob.glob(os.path.join(pdf_dir, "*.pdf"))
        
        if not pdf_files:
            print(f"⚠️  目录中没有PDF文件: {pdf_dir}")
            continue
        
        # 按照文件名长度排序，短文件名通常是摘要
        pdf_files.sort(key=lambda x: len(os.path.basename(x)))
        
        # 分组处理：优先处理摘要，跳过全文
        processed_years = set()
        summary_files = []
        full_files = []
        
        # 分类文件
        for pdf_path in pdf_files:
            filename = os.path.basename(pdf_path)
            lower_filename = filename.lower()
            
            # 跳过全文文件
            if "全文" in filename or "full" in lower_filename:
                full_files.append(pdf_path)
            # 优先处理摘要文件
            elif "摘要" in filename or "summary" in lower_filename:
                summary_files.append(pdf_path)
            # 跳过ESG报告
            elif "esg" in lower_filename:
                full_files.append(pdf_path)
            # 跳过实施细则和管理办法
            elif "细则" in filename or "办法" in filename or "规则" in filename:
                full_files.append(pdf_path)
            # 其他文件作为备选
            else:
                # 短文件名且包含年份的可能是摘要
                if len(filename) < 30 and re.search(r"20\d{2}", filename):
                    summary_files.append(pdf_path)
                else:
                    full_files.append(pdf_path)
        
        print(f"📋 找到 {len(summary_files)} 个摘要文件，{len(full_files)} 个全文文件")
        
        # 优先处理摘要文件
        for pdf_path in summary_files:
            print(f"\n📄 处理摘要文件: {os.path.basename(pdf_path)}")
            
            # 生成企业名称（从文件名中提取）
            filename = os.path.basename(pdf_path)
            enterprise_name = filename.replace(".pdf", "")
            
            # 简化企业名称，只保留核心信息
            enterprise_name = enterprise_name.lower()
            for keyword in ["航天长峰", "hangtian", "changkeng", "annual", "report", "年报", "半年度", "半年报"]:
                if keyword in enterprise_name:
                    enterprise_name = "航天长峰"
                    break
            
            # 提取年份信息
            year_match = re.search(r"(20\d{2})", filename)
            if year_match:
                year = year_match.group(1)
                if year in processed_years:
                    print(f"⚠️  已处理过该年份的摘要: {year}")
                    continue
                processed_years.add(year)
            
            try:
                # 处理PDF文件
                chunks = rag_pipeline.process_pdf(pdf_path, enterprise_name)
                print(f"✅ 成功处理 {len(chunks)} 个文本块")
                
                # 检查是否需要将数据添加到Elasticsearch
                print("📦 检查Elasticsearch连接...")
                if rag_pipeline.es_integration.is_connected():
                    print("📤 将数据添加到Elasticsearch...")
                    rag_pipeline.es_integration.index_chunks(chunks, enterprise_name)
                    print("✅ 成功添加到Elasticsearch")
                else:
                    print("⚠️ Elasticsearch未连接，跳过索引")
                    
            except Exception as e:
                print(f"❌ 处理失败: {str(e)}")
                import traceback
                traceback.print_exc()
        
        # 询问是否处理全文文件
        print("\n📋 摘要文件处理完成")
        print(f"⚠️  跳过了 {len(full_files)} 个全文文件")
    
    print("\n🎉 所有PDF文件处理完成！")

if __name__ == "__main__":
    main()