import os
import requests
from typing import List, Dict, Any

class TavilySearch:
    def __init__(self, api_key: str = None):
        """初始化Tavily搜索客户端"""
        self.api_key = api_key or os.getenv("TAVILY_API_KEY")
        self.base_url = "https://api.tavily.com/search"
        
        if not self.api_key:
            print("⚠️  警告：未配置TAVILY_API_KEY环境变量")
    
    def search(self, query: str, max_results: int = 5, search_depth: str = "basic") -> List[Dict[str, Any]]:
        """执行搜索
        
        Args:
            query: 搜索查询
            max_results: 返回结果数量
            search_depth: 搜索深度，可选值：basic, advanced
            
        Returns:
            搜索结果列表
        """
        if not self.api_key:
            print("❌ 请先配置TAVILY_API_KEY")
            return []
        
        try:
            payload = {
                "query": query,
                "api_key": self.api_key,
                "max_results": max_results,
                "search_depth": search_depth,
                "include_raw_content": False,
                "include_answer": True,
                "include_images": False
            }
            
            response = requests.post(self.base_url, json=payload, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            
            # 处理搜索结果
            search_results = []
            
            # 优先使用Tavily提供的直接答案
            if result.get("answer"):
                search_results.append({
                    "type": "answer",
                    "content": result["answer"],
                    "source": "Tavily AI Answer",
                    "relevance": 1.0
                })
            
            # 添加网页搜索结果
            for item in result.get("results", []):
                search_results.append({
                    "type": "webpage",
                    "title": item.get("title", ""),
                    "content": item.get("content", ""),
                    "url": item.get("url", ""),
                    "source": item.get("domain", ""),
                    "relevance": item.get("score", 0.0)
                })
            
            return search_results[:max_results]
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Tavily搜索请求失败: {str(e)}")
            return []
        except Exception as e:
            print(f"❌ Tavily搜索处理失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return []
    
    def batch_search(self, queries: List[str], max_results: int = 3) -> Dict[str, List[Dict[str, Any]]]:
        """批量执行搜索
        
        Args:
            queries: 搜索查询列表
            max_results: 每个查询返回的结果数量
            
        Returns:
            以查询为键，搜索结果列表为值的字典
        """
        results = {}
        for query in queries:
            results[query] = self.search(query, max_results)
        return results
    
    def search_with_relevance(self, query: str, threshold: float = 0.7) -> List[Dict[str, Any]]:
        """执行搜索并过滤相关度低于阈值的结果
        
        Args:
            query: 搜索查询
            threshold: 相关度阈值
            
        Returns:
            过滤后的搜索结果列表
        """
        all_results = self.search(query, max_results=10)
        return [result for result in all_results if result.get("relevance", 0.0) >= threshold]
