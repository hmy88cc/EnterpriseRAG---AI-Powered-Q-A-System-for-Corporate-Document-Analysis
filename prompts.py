"""
提示词集中管理模块
统一管理所有提示词，便于维护和修改
"""

# ==================== LLM重排序提示词 ====================
RERANK_PROMPT_TEMPLATE = """请根据与查询的相关性对以下文本块进行评分，评分范围为0.0到1.0，步长为0.1。

查询：{query}

文本块：
{chunks_text}

请返回JSON格式的评分结果，其中键为块编号（从1开始），值为对应的相关性评分。

只返回JSON格式，不要其他文字说明。"""

def get_rerank_prompt(query: str, chunks_with_scores: list, max_chunk_length: int = 200) -> str:
    """
    生成重排序提示词
    
    Args:
        query: 用户查询
        chunks_with_scores: 检索到的文本块列表
        max_chunk_length: 每个文本块的最大显示长度
    
    Returns:
        格式化后的提示词
    """
    chunks_text = ""
    for i, item in enumerate(chunks_with_scores, 1):
        chunk_text = item['chunk']['text'][:max_chunk_length]
        chunks_text += f"{i}. {chunk_text}...\n"
    
    return RERANK_PROMPT_TEMPLATE.format(
        query=query,
        chunks_text=chunks_text.strip()
    )


# ==================== 答案生成提示词 ====================
ANSWER_GENERATION_PROMPT_TEMPLATE = """请基于以下上下文回答用户的问题，确保回答准确、简洁。

上下文来源：
1. 企业年报知识库
2. 实时网络搜索结果

企业年报知识库内容：
{context}

实时网络搜索结果：
{web_results}

用户问题：{query}

要求：
1. 优先使用企业年报知识库中的信息回答问题
2. 可以结合实时网络搜索结果补充最新信息
3. 回答要准确、简洁、有条理
4. 如果上下文中的信息不足以回答问题，请说明
5. 可以直接引用上下文中的关键信息

回答："""

def get_answer_generation_prompt(query: str, reranked_results: list, web_results: list = None) -> str:
    """
    生成答案生成提示词
    
    Args:
        query: 用户查询
        reranked_results: 重排序后的检索结果
        web_results: 网络搜索结果（可选）
    
    Returns:
        格式化后的提示词
    """
    # 构建企业年报知识库上下文
    context = ""
    for i, item in enumerate(reranked_results, 1):
        chunk = item['chunk']
        page_num = chunk['metadata'].get('page_num', '未知')
        title = chunk['metadata'].get('title', '未知')
        context += f"[来源{i}] 页码:{page_num} | 文档:{title}\n"
        context += f"{chunk['text']}\n\n"
    
    # 构建网络搜索结果上下文
    web_results_text = ""
    if web_results:
        for i, web_result in enumerate(web_results, 1):
            if web_result['type'] == 'answer':
                web_results_text += f"[网络搜索答案{i}]\n{web_result['content']}\n\n"
            else:
                web_results_text += f"[网络搜索{i}] 标题：{web_result['title']}\n"
                web_results_text += f"来源：{web_result['source']}\n"
                web_results_text += f"内容：{web_result['content'][:300]}...\n\n"
    else:
        web_results_text = "无相关网络搜索结果"
    
    return ANSWER_GENERATION_PROMPT_TEMPLATE.format(
        query=query,
        context=context.strip(),
        web_results=web_results_text.strip()
    )


# ==================== 结构化输出提示词（可选） ====================
STRUCTURED_ANSWER_PROMPT_TEMPLATE = """请基于以下上下文回答用户的问题，并以结构化格式返回结果。

上下文：
{context}

用户问题：{query}

请以JSON格式返回结果，包含以下字段：
- answer: 答案内容
- confidence: 置信度（0.0-1.0）
- sources: 数据来源列表，每个来源包含page_num和text字段

只返回JSON格式，不要其他文字说明。"""

def get_structured_answer_prompt(query: str, reranked_results: list) -> str:
    """
    生成结构化答案提示词
    
    Args:
        query: 用户查询
        reranked_results: 重排序后的检索结果
    
    Returns:
        格式化后的提示词
    """
    context = ""
    for i, item in enumerate(reranked_results, 1):
        chunk = item['chunk']
        context += f"[{i}] {chunk['text']}\n\n"
    
    return STRUCTURED_ANSWER_PROMPT_TEMPLATE.format(
        query=query,
        context=context.strip()
    )


# ==================== 问题类型分类提示词（为未来扩展预留） ====================
QUESTION_TYPE_CLASSIFICATION_PROMPT = """请判断以下问题的类型，并返回JSON格式的结果。

问题：{query}

问题类型包括：
- factual: 事实性问题（如数据、统计信息）
- analytical: 分析性问题（如比较、趋势分析）
- descriptive: 描述性问题（如说明、解释）
- comparison: 对比性问题（如两个事物的对比）
- other: 其他类型

请返回JSON格式：{"type": "问题类型", "reason": "判断理由"}"""


# ==================== 子问题拆解提示词（为未来扩展预留） ====================
SUBQUESTION_DECOMPOSITION_PROMPT = """请将以下复杂问题拆解为多个子问题。

原问题：{query}

要求：
1. 将复杂问题拆解为2-5个子问题
2. 每个子问题应该是独立的、可回答的问题
3. 子问题应该覆盖原问题的所有方面

请返回JSON格式：{"subquestions": ["子问题1", "子问题2", ...]}"""

