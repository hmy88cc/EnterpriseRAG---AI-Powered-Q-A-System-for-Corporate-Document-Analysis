import os
from elasticsearch import Elasticsearch, helpers
import json
from typing import List, Dict, Any

class ElasticsearchIntegration:
    def __init__(self, api_key: str = None, embedding_model: str = None):
        self.api_key = api_key
        self.embedding_model = embedding_model
        self.es = None
        self.index_name = "enterprise_annual_reports"
        self.is_connected = False  # 添加is_connected属性
        
    def connect(self, host: str = "http://localhost", port: int = 9200, 
                user: str = "elastic", password: str = None, 
                index_name: str = "enterprise_annual_reports"):
        """连接到Elasticsearch服务器"""
        self.index_name = index_name
        
        try:
            # 构建Elasticsearch客户端
            client = Elasticsearch(
                f"{host}:{port}",
                basic_auth=(user, password) if user and password else None,
                verify_certs=False,  # 开发环境可以设置为False，生产环境建议True
                ssl_show_warn=False
            )
            
            self.es = client
            
            if self.es.ping():
                print(f"✅ 成功连接到Elasticsearch服务器: {host}:{port}")
                self.is_connected = True
                return True
            else:
                print(f"❌ 无法连接到Elasticsearch服务器: {host}:{port}")
                self.is_connected = False
                return False
        except Exception as e:
            print(f"❌ 连接Elasticsearch失败: {str(e)}")
            self.is_connected = False
            import traceback
            traceback.print_exc()
            return False
    
    def create_index(self, index_name: str = None):
        """创建索引"""
        if not self.es:
            print("❌ 请先连接到Elasticsearch服务器")
            return False
        
        if index_name:
            self.index_name = index_name
        
        try:
            # 检查索引是否已存在
            if self.es.indices.exists(index=self.index_name):
                print(f"⚠️  索引 {self.index_name} 已存在")
                return True
            
            # 创建索引
            mapping = {
                "mappings": {
                    "properties": {
                        "text": {
                            "type": "text",
                            "analyzer": "ik_max_word",
                            "search_analyzer": "ik_smart"
                        },
                        "metadata": {
                            "type": "object"
                        },
                        "embedding": {
                            "type": "dense_vector",
                            "dims": 1024,  # 对应text-embedding-v4的维度
                            "index": True,
                            "similarity": "cosine"
                        }
                    }
                }
            }
            
            self.es.indices.create(index=self.index_name, body=mapping)
            print(f"✅ 成功创建索引: {self.index_name}")
            return True
        except Exception as e:
            print(f"❌ 创建索引失败: {str(e)}")
            return False
    
    def index_documents(self, chunks: List[Dict[str, Any]], embeddings: List[List[float]]):
        """批量索引文档"""
        if not self.es:
            print("❌ 请先连接到Elasticsearch服务器")
            return False
        
        try:
            # 准备批量操作
            actions = []
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                action = {
                    "_index": self.index_name,
                    "_source": {
                        "text": chunk["text"],
                        "metadata": chunk["metadata"],
                        "embedding": embedding
                    }
                }
                actions.append(action)
            
            # 执行批量操作
            helpers.bulk(self.es, actions)
            print(f"✅ 成功索引 {len(chunks)} 个文档到 {self.index_name}")
            return True
        except Exception as e:
            print(f"❌ 批量索引失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def index_chunks(self, chunks: List[Dict[str, Any]], enterprise_name: str):
        """将文本块索引到Elasticsearch"""
        if not self.es:
            print("❌ 请先连接到Elasticsearch服务器")
            return False
        
        try:
            # 准备批量操作
            actions = []
            for i, chunk in enumerate(chunks):
                action = {
                    "_index": self.index_name,
                    "_source": {
                        "text": chunk["text"],
                        "metadata": {
                            **chunk["metadata"],
                            "enterprise_name": enterprise_name
                        },
                        "embedding": chunk.get("embedding", [])
                    }
                }
                actions.append(action)
            
            # 执行批量操作
            helpers.bulk(self.es, actions)
            print(f"✅ 成功索引 {len(chunks)} 个文档到 {self.index_name}")
            return True
        except Exception as e:
            print(f"❌ 批量索引失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def search(self, query: str, k: int = 10):
        """混合搜索：关键词搜索 + 向量搜索（简化版本，只使用关键词搜索）"""
        if not self.es:
            print("❌ 请先连接到Elasticsearch服务器")
            return []
        
        try:
            # 构建搜索请求（只使用关键词搜索）
            body = {
                "size": k,
                "query": {
                    "match": {
                        "text": query
                    }
                }
            }
            
            # 执行搜索
            response = self.es.search(index=self.index_name, body=body)
            
            # 处理搜索结果
            results = []
            for hit in response["hits"]["hits"]:
                results.append({
                    "chunk": {
                        "text": hit["_source"]["text"],
                        "metadata": hit["_source"]["metadata"]
                    },
                    "score": hit["_score"],
                    "final_score": hit["_score"]
                })
            
            return results
        except Exception as e:
            print(f"❌ 搜索失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return []
    
    def search_by_intent(self, query: str, intent: str, k: int = 10):
        """按意图检索Elasticsearch文档
        
        Args:
            query: 搜索查询
            intent: 查询意图，"annual_report"或"patent"
            k: 返回结果数量
            
        Returns:
            搜索结果列表
        """
        if not self.is_connected:
            print("❌ 未连接到Elasticsearch")
            return []
        
        try:
            # 将意图转换为file_type
            file_type_map = {
                "annual_report": "annual_report",
                "patent": "patent"
            }
            file_type = file_type_map.get(intent, intent)
            
            # 构建查询：全文检索 + 意图过滤
            search_body = {
                "size": k,
                "query": {
                    "bool": {
                        "must": [
                            {"match": {"text": query}}  # 全文检索
                        ],
                        "filter": [
                            {"term": {"metadata.file_type": file_type}}  # 过滤年报/专利类型
                        ]
                    }
                }
            }
            
            # 执行搜索
            response = self.es.search(index=self.index_name, body=search_body)
            
            # 处理搜索结果
            results = []
            for hit in response["hits"]["hits"]:
                results.append({
                    "chunk": {
                        "text": hit["_source"]["text"],
                        "metadata": hit["_source"]["metadata"]
                    },
                    "score": hit["_score"],
                    "final_score": hit["_score"]
                })
            
            return results
        except Exception as e:
            print(f"❌ Elasticsearch按意图检索失败: {str(e)}")
            import traceback
            traceback.print_exc()
            # 如果按意图检索失败，回退到普通搜索
            return self.search(query, k)
    
    def delete_index(self, index_name: str = None):
        """删除索引"""