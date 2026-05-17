import os
import json
import pickle
import numpy as np
import faiss
import dashscope
from gensim import corpora
from gensim.similarities import SparseMatrixSimilarity, MatrixSimilarity
import jieba
import tiktoken

class BM25:
    """简单的BM25实现"""
    def __init__(self, tokenized_corpus, k1=1.5, b=0.75):
        self.corpus_size = len(tokenized_corpus)
        self.avg_doc_length = sum(len(doc) for doc in tokenized_corpus) / self.corpus_size
        self.doc_freqs = []
        self.idf = {}
        self.doc_lengths = []
        self.k1 = k1
        self.b = b
        
        # 统计文档频率
        for doc in tokenized_corpus:
            frequencies = {}
            for word in doc:
                frequencies[word] = frequencies.get(word, 0) + 1
            self.doc_freqs.append(frequencies)
            self.doc_lengths.append(len(doc))
        
        # 计算IDF
        self._calculate_idf()
    
    def _calculate_idf(self):
        """计算逆文档频率"""
        from math import log
        
        # 统计每个词出现的文档数
        nd = {}
        for doc in self.doc_freqs:
            for word, freq in doc.items():
                nd[word] = nd.get(word, 0) + 1
        
        # 计算IDF
        for word, freq in nd.items():
            self.idf[word] = log((self.corpus_size - freq + 0.5) / (freq + 0.5) + 1.0)
    
    def get_scores(self, query):
        """获取查询对所有文档的BM25分数"""
        scores = []
        for i in range(self.corpus_size):
            score = 0.0
            doc_freqs = self.doc_freqs[i]
            doc_length = self.doc_lengths[i]
            
            for word in query:
                if word not in doc_freqs:
                    continue
                
                freq = doc_freqs[word]
                numerator = self.idf.get(word, 0) * freq * (self.k1 + 1)
                denominator = freq + self.k1 * (1 - self.b + self.b * doc_length / self.avg_doc_length)
                score += numerator / denominator
            
            scores.append(score)
        
        return scores

class EmbeddingRetrieval:
    def __init__(self, api_key, embedding_model="text-embedding-v3"):
        self.api_key = api_key
        self.embedding_model = embedding_model
        os.environ["DASHSCOPE_API_KEY"] = api_key
        dashscope.api_key = api_key
        # 初始化tokenizer用于检查token数
        try:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
        except:
            self.tokenizer = None
        # 设置最大token限制和向量维度
        self.max_tokens = 8192
        # 根据模型类型设置向量维度
        if "v3" in embedding_model:
            self.vector_dim = 768
        elif "v4" in embedding_model:
            self.vector_dim = 1024
        else:
            self.vector_dim = 768  # 默认使用v3的维度
    
    def _count_tokens(self, text):
        """计算文本的token数"""
        if self.tokenizer:
            return len(self.tokenizer.encode(text))
        # 如果没有tokenizer，使用粗略估算（1个中文字约1.3 token）
        return int(len(text) * 1.3)
    
    def get_embedding(self, text):
        """获取单个文本的向量嵌入"""
        # 检查token数
        token_count = self._count_tokens(text)
        if token_count > self.max_tokens:
            print(f"⚠️  警告：文本token数({token_count})超过限制({self.max_tokens})，将截断")
            # 简单截断（实际应该更智能）
            text = text[:int(len(text) * self.max_tokens / token_count * 0.9)]
        
        response = dashscope.TextEmbedding.call(
            model=self.embedding_model,
            input=[text]
        )
        # 兼容不同的响应格式
        if response.status_code == 200:
            if 'output' in response and 'embeddings' in response['output']:
                return response['output']['embeddings'][0]['embedding']
            elif 'output' in response and 'embedding' in response['output']:
                return response['output']['embedding']
            else:
                raise ValueError(f"无法从响应中提取embedding: {response}")
        else:
            error_msg = response.get('message', '') if hasattr(response, 'get') else str(response)
            raise RuntimeError(f"API调用失败，状态码: {response.status_code}, 错误: {error_msg}")
    
    def get_embeddings_batch(self, texts, batch_size=25):
        """批量获取文本的向量嵌入（优化性能）"""
        all_embeddings = []
        
        # 过滤空文本和无效文本
        valid_texts = []
        valid_indices = []
        for i, text in enumerate(texts):
            if text and isinstance(text, str) and text.strip():
                # 检查token数
                token_count = self._count_tokens(text)
                if token_count > self.max_tokens:
                    print(f"⚠️  警告：文本块{i}的token数({token_count})超过限制({self.max_tokens})，将跳过")
                    continue
                valid_texts.append(text.strip())
                valid_indices.append(i)
        
        if not valid_texts:
            raise ValueError("没有有效的文本可用于生成embedding")
        
        print(f"   过滤后有效文本数: {len(valid_texts)}/{len(texts)}")
        
        # 批量处理
        for i in range(0, len(valid_texts), batch_size):
            batch = valid_texts[i:i+batch_size]
            try:
                response = dashscope.TextEmbedding.call(
                    model=self.embedding_model,
                    input=batch
                )
                
                if response.status_code == 200:
                    if 'output' in response and 'embeddings' in response['output']:
                        batch_embeddings = [emb['embedding'] for emb in response['output']['embeddings']]
                        all_embeddings.extend(batch_embeddings)
                    elif 'output' in response and 'embedding' in response['output']:
                        all_embeddings.append(response['output']['embedding'])
                    else:
                        raise ValueError(f"无法从响应中提取embeddings: {response}")
                else:
                    error_msg = response.get('message', '') if hasattr(response, 'get') else str(response)
                    print(f"❌ 批量处理失败 (批次 {i//batch_size + 1})，状态码: {response.status_code}")
                    print(f"   错误信息: {error_msg}")
                    print(f"   尝试逐个处理该批次...")
                    # 如果批量失败，尝试逐个处理
                    for text in batch:
                        try:
                            emb = self.get_embedding(text)
                            all_embeddings.append(emb)
                        except Exception as e:
                            print(f"   ⚠️  单个文本处理也失败: {e}")
                            # 使用零向量作为占位符
                            all_embeddings.append([0.0] * self.vector_dim)  # 根据模型类型动态调整维度
            except Exception as e:
                print(f"❌ 批次处理异常 (批次 {i//batch_size + 1}): {e}")
                # 尝试逐个处理
                for text in batch:
                    try:
                        emb = self.get_embedding(text)
                        all_embeddings.append(emb)
                    except Exception as e2:
                        print(f"   ⚠️  单个文本处理失败: {e2}")
                        all_embeddings.append([0.0] * self.vector_dim)
        
        # 为跳过的文本添加占位符向量
        if len(all_embeddings) < len(texts):
            print(f"⚠️  警告：部分文本未能生成embedding，使用零向量占位")
            final_embeddings = [None] * len(texts)
            for idx, emb in zip(valid_indices, all_embeddings):
                final_embeddings[idx] = emb
            # 用零向量填充None
            for i, emb in enumerate(final_embeddings):
                if emb is None:
                    final_embeddings[i] = [0.0] * self.vector_dim
            return final_embeddings
        
        return all_embeddings
    
    def create_vector_db(self, chunks, output_path):
        """创建Faiss向量数据库（使用批量处理优化性能）"""
        print(f"   📌 创建向量库，输出路径: {output_path}")
        # 提取文本
        texts = [chunk["text"] for chunk in chunks]
        print(f"   正在生成{len(texts)}个文本块的向量嵌入...")
        
        # 使用批量处理 - 调整为10以符合API限制
        embeddings = self.get_embeddings_batch(texts, batch_size=10)
        
        # 转换为numpy数组
        embeddings_np = np.array(embeddings, dtype=np.float32)
        
        # 创建Faiss索引（内积相似度）
        dimension = embeddings_np.shape[1]
        index = faiss.IndexFlatIP(dimension)
        index.add(embeddings_np)
        
        # 保存索引和块信息
        try:
            # 处理中文文件名问题：使用英文文件名作为备用
            base_dir = os.path.dirname(output_path)
            original_filename = os.path.basename(output_path).replace('.faiss', '')
            
            # 生成英文文件名（使用企业名称+文件类型+时间戳）
            import hashlib
            import time
            timestamp = int(time.time())
            hash_suffix = hashlib.md5(original_filename.encode('utf-8')).hexdigest()[:8]
            safe_filename = f"hangtian_changfeng_{timestamp}_{hash_suffix}"
            
            # 使用安全的英文文件名
            faiss_path = os.path.join(base_dir, f"{safe_filename}.faiss")
            chunks_path = os.path.join(base_dir, f"{safe_filename}_chunks.pkl")
            
            # 确保目录存在
            os.makedirs(base_dir, exist_ok=True)
            
            # 保存索引
            faiss.write_index(index, faiss_path)
            
            # 保存块信息
            with open(chunks_path, "wb") as f:
                pickle.dump(chunks, f)
            
            print(f"   ✅ 向量库创建完成，维度: {dimension}")
            print(f"   ✅ 向量库路径: {faiss_path}")
            print(f"   ✅ 文本块路径: {chunks_path}")
            return index, chunks
        except Exception as e:
            print(f"❌ 保存向量库失败: {str(e)}")
            print(f"   尝试使用内存模式...")
            # 在内存模式下，我们仍然需要返回index和chunks
            return index, chunks
            
            # 直接返回内存中的索引，不保存到磁盘
            return index, chunks
    
    def load_vector_db(self, faiss_path, chunks_path):
        """加载Faiss向量数据库"""
        from pathlib import Path
        import os.path as osp
        
        # 规范化路径，确保FAISS能正确读取
        # 使用pathlib来规范化路径，处理特殊字符
        faiss_path_obj = Path(faiss_path)
        chunks_path_obj = Path(chunks_path)
        
        # 转换为绝对路径并解析
        faiss_path_resolved = str(faiss_path_obj.resolve())
        chunks_path_resolved = str(chunks_path_obj.resolve())
        
        # 验证文件确实存在
        if not faiss_path_obj.exists():
            raise FileNotFoundError(f"FAISS文件不存在: {faiss_path_resolved}")
        if not chunks_path_obj.exists():
            raise FileNotFoundError(f"Chunks文件不存在: {chunks_path_resolved}")
        
        # 尝试读取FAISS索引
        # FAISS的C++库可能对路径中的特殊字符敏感
        # 先尝试使用规范化后的路径
        index = None
        last_error = None
        
        # 方法1: 使用规范化路径
        try:
            index = faiss.read_index(faiss_path_resolved)
            print(f"✅ 使用规范化路径成功加载FAISS文件")
        except Exception as e1:
            last_error = e1
            print(f"⚠️  规范化路径加载失败: {str(e1)}")
            
            # 方法2: 使用原始路径（如果不同）
            if faiss_path_resolved != faiss_path:
                try:
                    index = faiss.read_index(faiss_path)
                    print(f"✅ 使用原始路径成功加载FAISS文件")
                except Exception as e2:
                    print(f"⚠️  原始路径加载也失败: {str(e2)}")
                    last_error = e2
            
            # 方法3: Windows系统尝试使用短路径名（8.3格式）
            if index is None and os.name == 'nt':
                try:
                    import ctypes
                    from ctypes import wintypes
                    
                    # 获取短路径名
                    GetShortPathNameW = ctypes.windll.kernel32.GetShortPathNameW
                    GetShortPathNameW.argtypes = [wintypes.LPCWSTR, wintypes.LPWSTR, wintypes.DWORD]
                    GetShortPathNameW.restype = wintypes.DWORD
                    
                    buffer = ctypes.create_unicode_buffer(260)
                    result = GetShortPathNameW(faiss_path_resolved, buffer, 260)
                    
                    if result > 0:
                        faiss_path_short = buffer.value
                        print(f"⚠️  尝试使用短路径名: {faiss_path_short}")
                        index = faiss.read_index(faiss_path_short)
                        print(f"✅ 使用短路径名成功加载FAISS文件")
                except Exception as e3:
                    print(f"⚠️  短路径名方法失败: {str(e3)}")
                    if last_error is None:
                        last_error = e3
        
        # 如果所有方法都失败，抛出错误
        if index is None:
            error_msg = f"无法读取FAISS文件: {faiss_path_resolved}"
            if last_error:
                error_msg += f"\n错误详情: {str(last_error)}"
            error_msg += "\n提示: 路径中可能包含特殊字符，FAISS的C++库无法处理。"
            error_msg += "\n建议: 将项目移动到不包含特殊字符（如冒号）的路径。"
            raise RuntimeError(error_msg)
        
        # 读取chunks
        with open(chunks_path_resolved, "rb") as f:
            chunks = pickle.load(f)
        
        return index, chunks
    
    def create_bm25_db(self, chunks, output_path):
        """创建BM25数据库"""
        # 对每个块进行分词
        tokenized_chunks = [list(jieba.cut_for_search(chunk["text"])) for chunk in chunks]
        
        # 创建BM25模型
        bm25 = BM25(tokenized_chunks)
        
        # 保存BM25模型和块信息
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "wb") as f:
            pickle.dump((bm25, chunks, tokenized_chunks), f)
        
        return bm25
    
    def load_bm25_db(self, bm25_path):
        """加载BM25数据库"""
        with open(bm25_path, "rb") as f:
            bm25, chunks, tokenized_chunks = pickle.load(f)
        return bm25, chunks, tokenized_chunks
    
    def hybrid_search(self, query, vector_index, vector_chunks, bm25, bm25_chunks, 
                     k=10, vector_weight=0.3, bm25_weight=0.7):
        """混合搜索：向量检索 + BM25"""
        # 1. 向量检索
        query_embedding = self.get_embedding(query)
        query_embedding_np = np.array([query_embedding], dtype=np.float32)
        vector_scores, vector_indices = vector_index.search(query_embedding_np, k)
        vector_scores = vector_scores[0]
        vector_indices = vector_indices[0]
        
        # 2. BM25检索
        tokenized_query = list(jieba.cut_for_search(query))
        bm25_scores = bm25.get_scores(tokenized_query)
        bm25_indices = np.argsort(bm25_scores)[::-1][:k]
        bm25_scores = [bm25_scores[i] for i in bm25_indices]
        
        # 3. 归一化分数
        def normalize_scores(scores):
            # 确保scores是普通列表，避免numpy数组导致的歧义
            if isinstance(scores, np.ndarray):
                scores = scores.tolist()
            
            if not scores or len(scores) == 0:
                return [1.0]
            
            min_score = min(scores)
            max_score = max(scores)
            
            if max_score == min_score:
                return [1.0 for _ in scores]
            
            return [(score - min_score) / (max_score - min_score) for score in scores]
        
        vector_scores_norm = normalize_scores(vector_scores)
        bm25_scores_norm = normalize_scores(bm25_scores)
        
        # 4. 合并结果并去重
        combined_results = {}
        
        # 添加向量检索结果
        for score, idx in zip(vector_scores_norm, vector_indices):
            chunk = vector_chunks[idx]
            chunk_id = f"{chunk['metadata']['title']}_{chunk['metadata']['page_num']}_{chunk['metadata']['chunk_id']}"
            if chunk_id not in combined_results:
                combined_results[chunk_id] = {
                    "chunk": chunk,
                    "vector_score": score,
                    "bm25_score": 0.0
                }
        
        # 添加BM25检索结果
        for score, idx in zip(bm25_scores_norm, bm25_indices):
            chunk = bm25_chunks[idx]
            chunk_id = f"{chunk['metadata']['title']}_{chunk['metadata']['page_num']}_{chunk['metadata']['chunk_id']}"
            if chunk_id in combined_results:
                combined_results[chunk_id]["bm25_score"] = score
            else:
                combined_results[chunk_id] = {
                    "chunk": chunk,
                    "vector_score": 0.0,
                    "bm25_score": score
                }
        
        # 5. 计算混合分数
        for result in combined_results.values():
            result["hybrid_score"] = vector_weight * result["vector_score"] + bm25_weight * result["bm25_score"]
        
        # 6. 按混合分数排序
        sorted_results = sorted(
            combined_results.values(),
            key=lambda x: x["hybrid_score"],
            reverse=True
        )[:k]
        
        return sorted_results
