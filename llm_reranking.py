"""
LLM重排序模块
使用LLM对检索结果进行重排序
"""
import dashscope
import json
from prompts import get_rerank_prompt

class LLM_Reranking:
    def __init__(self, api_key, model="qwen-turbo-latest"):
        self.api_key = api_key
        self.model = model
    
    def rerank_chunks(self, query, chunks_with_scores, top_k=5):
        """使用LLM对检索到的块进行重排序"""
        # 使用集中管理的提示词
        prompt = get_rerank_prompt(query, chunks_with_scores)
        
        # 调用LLM
        dashscope.api_key = self.api_key
        response = dashscope.Generation.call(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            result_format='message'
        )
        
        # 解析结果
        try:
            content = response.output.choices[0].message.content
            # 尝试提取JSON（可能包含markdown代码块）
            if "```json" in content:
                json_start = content.find("```json") + 7
                json_end = content.find("```", json_start)
                content = content[json_start:json_end].strip()
            elif "```" in content:
                json_start = content.find("```") + 3
                json_end = content.find("```", json_start)
                content = content[json_start:json_end].strip()
            
            # 使用json.loads代替eval，更安全
            rerank_scores = json.loads(content)
        except Exception as e:
            print(f"⚠️  重排序解析失败，使用原始排序: {e}")
            # 如果解析失败，返回原始排序
            return chunks_with_scores[:top_k]
        
        # 应用重排序
        reranked_results = []
        for i, item in enumerate(chunks_with_scores):
            # 兼容字符串和整数键
            key = str(i+1)
            if key in rerank_scores:
                rerank_score = float(rerank_scores[key])
            elif (i+1) in rerank_scores:
                rerank_score = float(rerank_scores[i+1])
            else:
                # 如果没有评分，使用原始混合分数
                rerank_score = item["hybrid_score"]
            
            # 结合原始混合分数和重排序分数（0.3+0.7）
            final_score = 0.3 * item["hybrid_score"] + 0.7 * rerank_score
            reranked_results.append({
                **item,
                "rerank_score": rerank_score,
                "final_score": final_score
            })
        
        # 按最终分数排序
        reranked_results.sort(key=lambda x: x["final_score"], reverse=True)
        
        return reranked_results[:top_k]
