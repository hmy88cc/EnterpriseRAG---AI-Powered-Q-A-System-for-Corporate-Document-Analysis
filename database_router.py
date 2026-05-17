import os

class DatabaseRouter:
    def __init__(self, data_dir):
        self.data_dir = data_dir
        self.db_mapping = self._load_db_mapping()
    
    def _load_db_mapping(self):
        """加载数据库映射关系，根据企业名称映射到对应的向量库和BM25库，支持按类型识别"""
        db_mapping = {}
        
        # 扫描vector_dbs目录下的所有faiss文件
        vector_db_dir = os.path.join(self.data_dir, "vector_dbs")
        bm25_dir = os.path.join(self.data_dir, "bm25_dbs")
        
        print(f"🔍 扫描向量库目录: {vector_db_dir}")
        print(f"🔍 扫描BM25库目录: {bm25_dir}")
        
        if os.path.exists(vector_db_dir):
            # 获取所有faiss文件
            faiss_files = [f for f in os.listdir(vector_db_dir) if f.endswith(".faiss")]
            print(f"📁 找到 {len(faiss_files)} 个向量库文件")
            
            for filename in faiss_files:
                print(f"\n📄 处理向量库文件: {filename}")
                # 构建完整路径
                faiss_path = os.path.join(vector_db_dir, filename)
                chunks_path = os.path.join(vector_db_dir, filename.replace(".faiss", "_chunks.pkl"))
                
                # 检查文件是否存在
                if os.path.exists(faiss_path) and os.path.exists(chunks_path):
                    print(f"✅ 向量库文件存在: {faiss_path}")
                    print(f"✅ 文本块文件存在: {chunks_path}")
                    
                    # 寻找合适的BM25文件
                    # 1. 首先尝试寻找与向量库同名的BM25文件
                    bm25_filename = filename.replace(".faiss", "_bm25.pkl")
                    bm25_path = os.path.join(bm25_dir, bm25_filename)
                    print(f"🔍 查找对应的BM25文件: {bm25_filename}")
                    
                    # 2. 如果没有找到，尝试寻找同名不同大小写或格式的BM25文件
                    found_bm25 = False
                    if os.path.exists(bm25_path):
                        found_bm25 = True
                        print(f"✅ 找到与向量库同名的BM25文件: {bm25_filename}")
                    else:
                        print(f"⚠️  未找到与向量库同名的BM25文件: {bm25_path}")
                        print("   尝试寻找其他可能的BM25文件...")
                        
                        # 3. 寻找所有包含相同核心名称的BM25文件
                        core_name = filename.replace(".faiss", "")
                        all_bm25_files = [f for f in os.listdir(bm25_dir) if f.endswith("_bm25.pkl")]
                        print(f"📁 找到 {len(all_bm25_files)} 个BM25文件")
                        
                        if all_bm25_files:
                            # 按修改时间排序，取最新的文件
                            all_bm25_files.sort(key=lambda x: os.path.getmtime(os.path.join(bm25_dir, x)), reverse=True)
                            bm25_path = os.path.join(bm25_dir, all_bm25_files[0])
                            print(f"   使用最新的BM25文件: {all_bm25_files[0]}")
                            found_bm25 = True
                    
                    if found_bm25:
                        # 添加到映射
                        db_mapping[filename[:-6]] = {
                            "faiss_path": faiss_path,
                            "chunks_path": chunks_path,
                            "bm25_path": bm25_path
                        }
                        print(f"✅ 添加到数据库映射: {filename[:-6]}")
                        
                        # 获取BM25文件名，用于判断文件类型
                        bm25_filename = os.path.basename(bm25_path)
                        
                        # 4. 按类型添加特殊映射（同时检查向量库文件名和BM25文件名）
                        is_annual_report = ("_年报_" in filename or "年报" in filename or "_年报_" in bm25_filename or "年报" in bm25_filename)
                        is_patent = ("_专利_" in filename or "专利" in filename or "_专利_" in bm25_filename or "专利" in bm25_filename)
                        
                        if is_annual_report:
                            # 年报库映射
                            enterprise_name = "航天长峰"
                            # 添加类型专属映射
                            type_specific_key = f"{enterprise_name}_年报"
                            db_mapping[type_specific_key] = {
                                "faiss_path": faiss_path,
                                "chunks_path": chunks_path,
                                "bm25_path": bm25_path
                            }
                            print(f"✅ 添加年报专属映射: {type_specific_key} -> {filename} (BM25: {bm25_filename})")
                            
                            # 强制添加航天长峰年报映射
                            db_mapping["航天长峰_年报"] = {
                                "faiss_path": faiss_path,
                                "chunks_path": chunks_path,
                                "bm25_path": bm25_path
                            }
                            print(f"✅ 强制添加航天长峰年报映射: 航天长峰_年报 -> {filename}")
                        elif is_patent:
                            # 专利库映射
                            enterprise_name = "航天长峰"
                            # 添加类型专属映射
                            type_specific_key = f"{enterprise_name}_专利"
                            db_mapping[type_specific_key] = {
                                "faiss_path": faiss_path,
                                "chunks_path": chunks_path,
                                "bm25_path": bm25_path
                            }
                            print(f"✅ 添加专利专属映射: {type_specific_key} -> {filename} (BM25: {bm25_filename})")
                            
                            # 强制添加航天长峰专利映射
                            db_mapping["航天长峰_专利"] = {
                                "faiss_path": faiss_path,
                                "chunks_path": chunks_path,
                                "bm25_path": bm25_path
                            }
                            print(f"✅ 强制添加航天长峰专利映射: 航天长峰_专利 -> {filename}")
                        
                        # 5. 额外检查：如果BM25文件是年报，但向量库文件名没有年报标识，也添加年报映射
                        if "年报" in bm25_filename and "航天长峰_年报" not in db_mapping:
                            db_mapping["航天长峰_年报"] = {
                                "faiss_path": faiss_path,
                                "chunks_path": chunks_path,
                                "bm25_path": bm25_path
                            }
                            print(f"✅ 基于BM25文件添加年报映射: 航天长峰_年报 -> {filename} (BM25: {bm25_filename})")
                        
                        # 6. 额外检查：如果BM25文件是专利，但向量库文件名没有专利标识，也添加专利映射
                        if "专利" in bm25_filename and "航天长峰_专利" not in db_mapping:
                            db_mapping["航天长峰_专利"] = {
                                "faiss_path": faiss_path,
                                "chunks_path": chunks_path,
                                "bm25_path": bm25_path
                            }
                            print(f"✅ 基于BM25文件添加专利映射: 航天长峰_专利 -> {filename} (BM25: {bm25_filename})")
                    else:
                        print(f"❌ 未找到任何可用的BM25文件，跳过该向量库: {filename}")
                else:
                    print(f"⚠️  向量库或文本块文件不存在，跳过: {filename}")
                    if not os.path.exists(faiss_path):
                        print(f"   ❌ 向量库文件不存在: {faiss_path}")
                    if not os.path.exists(chunks_path):
                        print(f"   ❌ 文本块文件不存在: {chunks_path}")
    
        # 确保航天长峰的专利和年报映射存在
        if "航天长峰_专利" not in db_mapping:
            print("⚠️  未找到航天长峰_专利映射，尝试手动创建")
            # 查找所有包含"专利"的映射
            patent_keys = [k for k in db_mapping.keys() if "_专利_" in k or "专利" in k]
            if patent_keys:
                patent_db = db_mapping[patent_keys[0]]
                db_mapping["航天长峰_专利"] = patent_db
                print(f"✅ 手动创建航天长峰_专利映射")
        
        if "航天长峰_年报" not in db_mapping:
            print("⚠️  未找到航天长峰_年报映射，尝试手动创建")
            
            # 1. 查找所有包含年报相关BM25文件的映射
            annual_report_mappings = []
            for k, v in db_mapping.items():
                bm25_path = v['bm25_path']
                bm25_filename = os.path.basename(bm25_path)
                if "年报" in bm25_filename:
                    annual_report_mappings.append((k, v))
            
            if annual_report_mappings:
                # 使用第一个年报相关的映射
                annual_db = annual_report_mappings[0][1]
                db_mapping["航天长峰_年报"] = annual_db
                print(f"✅ 手动创建航天长峰_年报映射，使用BM25文件: {os.path.basename(annual_db['bm25_path'])}")
            else:
                # 2. 如果没有找到年报相关的映射，尝试查找年报相关的BM25文件并创建映射
                print("   尝试查找年报相关的BM25文件...")
                if os.path.exists(bm25_dir):
                    bm25_files = os.listdir(bm25_dir)
                    annual_bm25_files = [f for f in bm25_files if "年报" in f and f.endswith("_bm25.pkl")]
                    
                    if annual_bm25_files:
                        # 找到年报相关的BM25文件，使用第一个向量库文件和这个BM25文件创建映射
                        # 选择第一个向量库文件
                        first_vector_key = next(iter(db_mapping.keys()))
                        first_vector_db = db_mapping[first_vector_key]
                        
                        # 使用年报BM25文件
                        annual_bm25_path = os.path.join(bm25_dir, annual_bm25_files[0])
                        
                        # 创建年报映射
                        db_mapping["航天长峰_年报"] = {
                            "faiss_path": first_vector_db["faiss_path"],
                            "chunks_path": first_vector_db["chunks_path"],
                            "bm25_path": annual_bm25_path
                        }
                        print(f"✅ 基于年报BM25文件创建航天长峰_年报映射: {annual_bm25_files[0]}")
                    else:
                        print("   ❌ 未找到任何年报相关的BM25文件")
                else:
                    print(f"   ❌ BM25目录不存在: {bm25_dir}")
        
        print(f"\n📊 最终数据库映射: {list(db_mapping.keys())}")
        return db_mapping

    def get_database(self, enterprise_name):
        """根据企业名称获取对应的数据库路径"""
        # 每次调用时重新加载数据库映射，确保能找到新创建的数据库
        self.db_mapping = self._load_db_mapping()
        
        # 如果企业名称为空，直接返回第一个可用的数据库（如果有的话）
        if not enterprise_name or enterprise_name.strip() == "":
            if len(self.db_mapping) > 0:
                return list(self.db_mapping.values())[0]
            return None
        
        # 精确匹配
        if enterprise_name in self.db_mapping:
            return self.db_mapping[enterprise_name]
        
        # 如果找不到精确匹配，尝试多种模糊匹配策略
        
        # 策略1: 检查企业名称是否包含在数据库名称中
        for key in self.db_mapping.keys():
            if enterprise_name in key:
                return self.db_mapping[key]
        
        # 策略2: 检查数据库名称是否包含在企业名称中
        for key in self.db_mapping.keys():
            if key in enterprise_name:
                return self.db_mapping[key]
        
        # 策略3: 检查企业名称是否包含关键词
        keywords = ['航天长峰', '航天', '长峰', 'beijing', 'hangtian', 'changkeng', '2025', '2024', '2023']
        for key in self.db_mapping.keys():
            for keyword in keywords:
                if keyword in enterprise_name and keyword in key:
                    return self.db_mapping[key]
        
        # 策略4: 检查是否有唯一的数据库，直接返回
        if len(self.db_mapping) == 1:
            return list(self.db_mapping.values())[0]
        
        # 如果仍然找不到，返回None
        return None
    
    def list_enterprises(self):
        """列出所有可用的企业数据库"""
        return list(self.db_mapping.keys())
    
    def get_database_by_type(self, enterprise_name, query_type):
        """根据企业名称和查询类型获取对应的数据库路径
        
        Args:
            enterprise_name: 企业名称
            query_type: 查询类型，"annual_report"或"patent"
            
        Returns:
            数据库信息字典，如果找不到则返回None
        """
        # 每次调用时重新加载数据库映射
        self.db_mapping = self._load_db_mapping()
        
        # 根据查询类型过滤知识库
        if query_type == "annual_report":
            # 只查找年报相关的知识库
            target_keys = [k for k in self.db_mapping.keys() 
                          if "_年报_" in k or (enterprise_name in k and "专利" not in k)]
        elif query_type == "patent":
            # 只查找专利相关的知识库
            target_keys = [k for k in self.db_mapping.keys() 
                          if "_专利_" in k or (enterprise_name in k and "专利" in k)]
        else:
            # 通用查询，优先年报
            target_keys = [k for k in self.db_mapping.keys() 
                          if "_年报_" in k or (enterprise_name in k and "专利" not in k)]
        
        # 尝试精确匹配
        for key in target_keys:
            if enterprise_name in key or key in enterprise_name:
                return self.db_mapping[key]
        
        # 如果找不到精确匹配，返回第一个匹配的知识库
        if target_keys:
            return self.db_mapping[target_keys[0]]
        
        return None