"""
PDF解析模块
支持两种解析方式：
1. MINERU API（推荐）：使用云端API解析，支持表格、图片等复杂元素
2. PyMuPDF（备用）：本地解析，速度快但功能有限
"""
import os
import json
import time
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# 尝试导入PyMuPDF作为备用方案
try:
    import fitz
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False


class PDFParser:
    def __init__(self, use_mineru: bool = True):
        """
        初始化PDF解析器
        
        Args:
            use_mineru: 是否使用MINERU API（默认True）
                       如果为False或MINERU_API_KEY未设置，则使用PyMuPDF
        """
        self.use_mineru = use_mineru
        self.mineru_api_key = os.getenv("MINERU_API_KEY")
        self.mineru_base_url = "https://mineru.net/api/v4/extract"
        
        # 检查是否可以使用MINERU
        if use_mineru and not self.mineru_api_key:
            print("⚠️  警告：MINERU_API_KEY未设置，将使用PyMuPDF作为备用方案")
            self.use_mineru = False
        
        if self.use_mineru:
            print("✅ 使用MINERU API进行PDF解析")
        elif PYMUPDF_AVAILABLE:
            print("✅ 使用PyMuPDF进行PDF解析")
        else:
            raise ImportError("无法使用MINERU API，且PyMuPDF未安装。请安装PyMuPDF或配置MINERU_API_KEY")
    
    def parse_pdf_with_mineru(self, pdf_path: str) -> Dict[str, Any]:
        """使用MINERU API解析PDF文件"""
        pdf_path_obj = Path(pdf_path)
        if not pdf_path_obj.exists():
            raise FileNotFoundError(f"PDF文件不存在: {pdf_path}")
        
        print(f"📄 开始使用MINERU解析PDF: {pdf_path_obj.name}")
        
        # 1. 上传文件并获取任务ID
        task_id = self._get_mineru_task_id(pdf_path_obj)
        print(f"   任务ID: {task_id}")
        
        # 2. 等待并获取解析结果
        print("   等待解析完成...")
        mineru_result = self._get_mineru_result(task_id)
        
        # 3. 转换为标准格式
        parsed_data = self._convert_mineru_to_standard_format(pdf_path_obj, mineru_result)
        
        print(f"✅ MINERU解析完成，共{len(parsed_data['pages'])}页")
        return parsed_data
    
    def _get_mineru_task_id(self, pdf_path: Path) -> str:
        """上传PDF文件到MINERU并获取任务ID"""
        url = f"{self.mineru_base_url}/task"
        
        with open(pdf_path, "rb") as f:
            files = {
                "file": (pdf_path.name, f, "application/pdf")
            }
            headers = {
                "Authorization": f"Bearer {self.mineru_api_key}"
            }
            
            response = requests.post(url, headers=headers, files=files, timeout=60)
            response.raise_for_status()
            result = response.json()
            
            # 兼容不同的响应格式
            if "task_id" in result:
                return result["task_id"]
            elif "data" in result and "task_id" in result["data"]:
                return result["data"]["task_id"]
            else:
                raise ValueError(f"无法获取任务ID，响应: {result}")
    
    def _get_mineru_result(self, task_id: str, max_wait: int = 300) -> Dict[str, Any]:
        """获取MINERU解析结果，轮询直到完成"""
        url = f"{self.mineru_base_url}/result/{task_id}"
        headers = {
            "Authorization": f"Bearer {self.mineru_api_key}"
        }
        
        start_time = time.time()
        last_status = None
        
        while time.time() - start_time < max_wait:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            result = response.json()
            
            # 兼容不同的响应格式
            status = None
            if "status" in result:
                status = result["status"]
            elif "data" in result:
                data = result["data"]
                if "state" in data:
                    status_map = {"pending": "processing", "running": "processing", "done": "completed", "failed": "failed"}
                    status = status_map.get(data["state"], "processing")
                else:
                    status = "completed"
            
            if status != last_status:
                print(f"   状态: {status}")
                last_status = status
            
            if status == "completed":
                # 返回解析结果
                if "result" in result:
                    return result["result"]
                elif "data" in result:
                    return result["data"]
                else:
                    return result
            elif status == "failed":
                error_msg = result.get("message", result.get("err_msg", "未知错误"))
                raise RuntimeError(f"MINERU解析失败: {error_msg}")
            
            # 等待3秒后重试
            time.sleep(3)
        
        raise TimeoutError(f"MINERU解析超时，超过{max_wait}秒")
    
    def _convert_mineru_to_standard_format(self, pdf_path: Path, mineru_result: Dict[str, Any]) -> Dict[str, Any]:
        """将MINERU返回的结果转换为标准格式"""
        parsed_data = {
            "title": pdf_path.name,
            "pages": [],
            "metadata": {
                "num_pages": len(mineru_result.get("pages", [])),
                "created_at": datetime.now().isoformat(),
                "parser": "MINERU"
            }
        }
        
        # 处理每一页
        for page_num, page_data in enumerate(mineru_result.get("pages", []), 1):
            # 提取页面文本（合并所有文本块）
            page_text_parts = []
            
            # 处理文本块
            for text_block in page_data.get("text_blocks", []):
                text = text_block.get("text", "").strip()
                if text:
                    page_text_parts.append(text)
            
            # 处理表格（转换为文本）
            for table in page_data.get("tables", []):
                # 优先使用markdown格式
                if "markdown" in table and table["markdown"]:
                    page_text_parts.append(f"\n[表格]\n{table['markdown']}\n")
                elif "html" in table and table["html"]:
                    # 简单提取HTML表格文本
                    import re
                    html_text = re.sub(r'<[^>]+>', ' ', table["html"])
                    page_text_parts.append(f"\n[表格]\n{html_text.strip()}\n")
            
            # 合并页面文本
            page_text = "\n".join(page_text_parts)
            
            parsed_data["pages"].append({
                "page_num": page_num,
                "text": page_text,
                "metadata": {
                    "width": page_data.get("width", 0),
                    "height": page_data.get("height", 0),
                    "text_blocks_count": len(page_data.get("text_blocks", [])),
                    "tables_count": len(page_data.get("tables", [])),
                    "figures_count": len(page_data.get("figures", []))
                }
            })
        
        return parsed_data
    
    def parse_pdf_with_pymupdf(self, pdf_path: str) -> Dict[str, Any]:
        """使用PyMuPDF解析PDF文件（备用方案），支持表格和图片提取"""
        if not PYMUPDF_AVAILABLE:
            raise ImportError("PyMuPDF未安装，无法使用本地解析")
        
        print(f"📄 使用PyMuPDF解析PDF: {os.path.basename(pdf_path)}")
        
        doc = fitz.open(pdf_path)
        parsed_data = {
            "title": os.path.basename(pdf_path),
            "pages": [],
            "metadata": {
                "num_pages": len(doc),
                "created_at": datetime.now().isoformat(),
                "parser": "PyMuPDF"
            }
        }
        
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            
            # 获取页面文本
            text = page.get_text()
            
            # 提取页面文本块（包含位置信息）
            text_blocks = page.get_text("blocks")
            
            # 提取页面图片
            images = page.get_images(full=True)
            images_count = len(images)
            
            # 尝试提取表格（使用PyMuPDF的表格检测功能）
            tables = []
            try:
                # 使用PyMuPDF 1.24+的表格检测功能
                table_detections = page.find_tables()
                for table in table_detections:
                    # 获取表格数据
                    table_data = table.extract()
                    if table_data:
                        # 转换为Markdown格式
                        markdown_table = self._convert_table_to_markdown(table_data)
                        tables.append(markdown_table)
            except AttributeError:
                # PyMuPDF版本不支持find_tables方法
                print(f"   第{page_num+1}页：PyMuPDF版本不支持表格检测")
            except Exception as e:
                print(f"   第{page_num+1}页：表格提取失败：{e}")
            
            # 合并文本和表格
            page_content_parts = [text]
            if tables:
                for i, table_md in enumerate(tables):
                    page_content_parts.append(f"\n[表格{i+1}]\n{table_md}\n")
            
            full_page_content = "\n".join(page_content_parts)
            
            parsed_data["pages"].append({
                "page_num": page_num + 1,
                "text": full_page_content,
                "metadata": {
                    "width": page.rect.width,
                    "height": page.rect.height,
                    "text_blocks_count": len(text_blocks),
                    "tables_count": len(tables),
                    "images_count": images_count
                }
            })
        
        doc.close()
        print(f"✅ PyMuPDF解析完成，共{len(parsed_data['pages'])}页")
        return parsed_data
    
    def _convert_table_to_markdown(self, table_data: list) -> str:
        """将表格数据转换为Markdown格式"""
        if not table_data or not table_data[0]:
            return ""
        
        # 计算每列的最大宽度
        col_widths = []
        for i in range(len(table_data[0])):
            max_width = max(len(str(row[i])) for row in table_data)
            col_widths.append(max_width)
        
        # 生成Markdown表格
        markdown_lines = []
        
        # 表头
        header = "|"
        for i, col in enumerate(table_data[0]):
            header += f" {str(col).ljust(col_widths[i])} |"
        markdown_lines.append(header)
        
        # 分隔线
        separator = "|"
        for width in col_widths:
            separator += f" {'-' * width} |"
        markdown_lines.append(separator)
        
        # 数据行
        for row in table_data[1:]:
            data_line = "|"
            for i, cell in enumerate(row):
                data_line += f" {str(cell).ljust(col_widths[i])} |"
            markdown_lines.append(data_line)
        
        return "\n".join(markdown_lines)
    
    def parse_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """
        解析PDF文件，提取文本和元数据
        
        Args:
            pdf_path: PDF文件路径
            
        Returns:
            包含解析结果的字典，格式：
            {
                "title": "文件名",
                "pages": [
                    {
                        "page_num": 1,
                        "text": "页面文本内容",
                        "metadata": {...}
                    },
                    ...
                ],
                "metadata": {...}
            }
        """
        if self.use_mineru:
            try:
                return self.parse_pdf_with_mineru(pdf_path)
            except Exception as e:
                print(f"⚠️  MINERU解析失败: {e}")
                print("   尝试使用PyMuPDF作为备用方案...")
                if PYMUPDF_AVAILABLE:
                    return self.parse_pdf_with_pymupdf(pdf_path)
                else:
                    raise
        else:
            return self.parse_pdf_with_pymupdf(pdf_path)
    
    def save_parsed_data(self, parsed_data: Dict[str, Any], output_path: str):
        """保存解析后的数据到JSON文件"""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(parsed_data, f, ensure_ascii=False, indent=2)
    
    def load_parsed_data(self, input_path: str) -> Dict[str, Any]:
        """加载已解析的数据"""
        with open(input_path, 'r', encoding='utf-8') as f:
            return json.load(f)
