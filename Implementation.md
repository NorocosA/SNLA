# SNLA 分步骤执行方案

> 基于 `Plan.md` 的工程化展开。每一步 = 可独立完成的工作单元，含依赖、操作、产出、验证。

---

## P0：技术验证（第 1–2 周）

### 前置：环境搭建（Day 0）

| 步骤 | 操作 | 产出 | 验证 |
|------|------|------|------|
| 0.1 | `git init`；创建 `.gitignore`（排除 `*.spv`, `__pycache__`, `.env`, `*.tmp`, `*.jnl`, `p0_output/`） | Git 仓库 | `git status` 干净 |
| 0.2 | `python -m venv venv`；激活；`pip install pyreadstat pandas openai streamlit python-dotenv lxml pytest` | `requirements.txt` | `pip list` 含全部依赖 |
| 0.3 | 按 Plan.md 3.3 目录树创建全部目录 + 空 `__init__.py` | 模块骨架 | `tree snla` 结构与 Plan 一致 |
| 0.4 | 创建 `config.py`（从 `.env` 读取 `SPSS_PATH`, `LLM_ENDPOINT`, `LLM_API_KEY`） | 配置中心 | `python -c "from snla.config import *; print(SPSS_PATH)"` 输出路径 |
| 0.5 | 创建 `.env.example`（不含真实 Key） | 文档 | — |
| 0.6 | 创建 `scripts/verify_spss.py`（占位） | 验证脚本骨架 | — |
| 0.7 | **开发者必读清单**：IBM OMS 命令语法指南 → OMS XML Schema 文档 → SPSS batch mode 手册 → 2 个不同版本 SPSS 的 `.lst` 差异对比 | 技术背景就绪 | 能用自己的话解释 `<dimension axis="statistics">` 和 `<dimension axis="variable">` 的区别 |

---

### 步骤 1：SPSS 批处理连通性验证（Day 1）

**依赖**：步骤 0.4（SPSS_PATH 已配）

**操作**：
1. 在 `scripts/verify_spss.py` 中实现：接收 `--spss-path` 和 `--output-dir` 参数
2. 用 `subprocess.run` 调用 `spss.exe -batch test.sps`，5 条语法各一次：
   - `FREQUENCIES VARIABLES=gender.`
   - `DESCRIPTIVES VARIABLES=score.`
   - `T-TEST GROUPS=gender(1 2) /VARIABLES=score.`
   - `CROSSTABS TABLES=gender BY class.`
   - `REGRESSION /DEPENDENT=score /METHOD=ENTER age.`
3. 捕获 `exit_code`, `stdout`, `stderr`，写入 `{output_dir}/run_{N}.log`
4. 生成 `p0_output/connectivity_report.json`：`{test, exit_code, stdout_lines, stderr_lines, success}`

**测试数据**：`data/fixtures/test_data.sav`（手工在 SPSS 中创建：gender N 1/2, score N, class S, age N，填入 20 条假数据）

**验证**：5/5 `exit_code == 0`，日志文件可读

---

### 步骤 2：OMS XML **逐分析类型**导出验证（Day 1–2）

**依赖**：步骤 1（SPSS 批处理通）

**操作**：
1. 扩展 `verify_spss.py`：对 5 种分析各执行一次 OMS 包裹版本
2. 每条语法包裹为：
   ```
   OMS /SELECT TABLES /DESTINATION FORMAT=OXML OUTFILE='{output_dir}/ttest.xml'.
   T-TEST GROUPS=gender(1 2) /VARIABLES=score.
   OMSEND.
   ```
3. **逐分析验证结构完整性**（不能笼统的"XML 存在就行"）：
   - T-TEST XML → 确认"组统计"和"独立样本检验"两张表的结构完整
   - ANOVA XML → 确认"主体间效应检验"表的维度完整性
   - REGRESSION XML → 确认"系数"表 + "模型摘要"表均存在
   - CROSSTABS XML → 确认"交叉表" + "卡方检验"结构
   - FREQUENCIES XML → 确认"频数分布"结构
4. 收集中文版 SPSS 在**至少 2 个版本**上的输出样本（T-TEST + FREQUENCIES 的 `.lst` 和 `.xml`，放入 `data/fixtures/expected_outputs/`）
5. 记录 OMS XML 命名空间差异（如有），写入 `p0_output/oms_compatibility_report.md`

**产出**：`p0_output/{frequencies,descriptives,ttest,crosstabs,regression}.xml` + `oms_compatibility_report.md`

**验证**：5/5 分析类型的 XML 结构独立验证通过（非笼统的"OMS OK"）

---

### 步骤 3：安全沙箱验证（Day 2）

**依赖**：无（纯逻辑模块，不依赖 SPSS）

**操作**：
1. 实现 `syntax/validator.py`：
   - `extract_commands(syntax: str) -> list[str]`：匹配 SPSS 命令关键字
   - `check_blacklist(commands: list[str]) -> list[str]`：比对 `FORBIDDEN_KEYWORDS`（SAVE, DELETE, AGGREGATE, ADD FILES, MATCH FILES 等）
   - `check_greylist(commands: list[str]) -> list[str]`：比对 `GREYLIST_KEYWORDS`（COMPUTE, RECODE, SELECT IF, FILTER, RENAME VARIABLES, SORT CASES, WEIGHT）
   - `validate_variables(syntax: str, var_list: list[str]) -> list[str]`：检查变量名存在性
   - `check_brackets(syntax: str) -> list[str]`：配对检查
   - `validate(syntax, var_list) -> {"valid": bool, "errors": [...], "warnings": [...]}`
2. 实现 `FORBIDDEN_KEYWORDS` 和 `GREYLIST_KEYWORDS` 常量（按 Plan.md 3.6）
3. 在 `data/fixtures/malicious_syntax.sps` 中写入 10 条语法（7 黑名单 + 3 灰名单）
4. 编写 `tests/test_validator.py`：
   - `test_blacklist_blocks_save`：SAVE → 拦截
   - `test_blacklist_blocks_delete`：DELETE → 拦截
   - `test_blacklist_blocks_aggregate`：AGGREGATE → 拦截
   - `test_blacklist_blocks_add_files`：ADD FILES → 拦截
   - `test_greylist_compute_requires_confirmation`：COMPUTE → warning（非 error，需返回"需用户确认"）
   - `test_greylist_recode_requires_confirmation`：RECODE → warning
   - `test_greylist_select_if_requires_confirmation`：SELECT IF → warning
   - `test_variable_not_exists`：引用不存在变量 → error
   - `test_bracket_mismatch`：括号不配对 → error
   - `test_clean_syntax_passes`：合法语法 → 通过

**产出**：`syntax/validator.py`（完整实现）+ `tests/test_validator.py`（10 条用例）

**验证**：`pytest tests/test_validator.py -v` 10/10 pass

---

### 步骤 3.5：临时副本机制（Day 2 晚）

**依赖**：步骤 3（validator 灰名单逻辑就绪）

**操作**：
1. 在 `executor/spss.py` 中实现 `execute_on_temp_copy()`：
   - 灰名单命令确认后，将当前数据 `.sav` 复制为 `{original}_temp.sav`
   - 在临时副本上执行预处理语法
   - 后续分析在预处理后的临时副本上进行
   - 会话结束时清理所有临时副本
2. 在 `session.py` 中维护 `temp_files: list[str]`，注册/退出时自动清理

**验证**：执行一条 COMPUTE 语法 → 确认原始文件未被修改

---

### 步骤 3.6：SPSS 进程异常终止恢复测试（Day 2 晚）

**依赖**：步骤 1（SPSS 可调用）

**操作**：
1. 编写 `scripts/test_crash_recovery.py`：
   - 启动一个长时 SPSS 批处理（如睡眠语法 `BEGIN PROGRAM. import time; time.sleep(30). END PROGRAM.` ——注：实际用无输出的大循环语法）
   - 3 秒后调用 `process.terminate()`
   - 重复 3 次
   - 检查：① 临时文件 (.tmp, .jnl) 是否残留 ② 第 4 次正常分析能否成功
2. 若 SPSS licensing service 锁死，记录恢复步骤（如重启 SPSS Statistics 服务）

**产出**：`p0_output/crash_recovery_report.md`

**验证**：3 次强制终止后 SPSS 仍可正常启动和执行分析

---

### 步骤 4：LLM 语法生成准确率测试（Day 3）

**依赖**：步骤 0.4（LLM_API_KEY 已配）

**操作**：
1. 实现 `llm/client.py`：
   - `class LLMClient`：统一接口，支持 OpenAI / DeepSeek / ollama 三后端
   - `def chat(messages, system_prompt, output_format_instruction) -> dict`
   - 自动 fallback：云端 API 超时 → 本地 ollama
2. 实现 `llm/prompts/intent.py`：
   - `def build_intent_prompt(user_message, last_analysis=None) -> str`
   - 按 Plan.md 3.4.2 的 intent 规范构造 prompt
3. 实现 `llm/prompts/syntax.py`：
   - `def build_syntax_prompt(method, variables, dataset_summary) -> str`
   - 按 Plan.md 3.4.2 的 syntax 规范，含 5 个 few-shot 示例
4. 编写 `tests/test_integration.py`：
   - `test_llm_syntax_ttest`：给定变量清单 + "比较男女成绩差异" → LLM 返回语法含 `T-TEST GROUPS=gender`
   - `test_llm_syntax_frequencies`：→ FREQUENCIES
   - `test_llm_syntax_descriptives`：→ DESCRIPTIVES
   - `test_llm_syntax_regression`：→ REGRESSION
   - `test_llm_syntax_crosstabs`：→ CROSSTABS
   - `test_llm_syntax_forbidden_keyword`：不应生成 SAVE/DELETE
   - `test_llm_syntax_variable_validation`：生成的变量名必须在清单内
   - `test_llm_syntax_json_format`：返回 JSON 格式正确
   - `test_intent_describe`：意图识别 "计算平均分" → describe
   - `test_intent_compare`：→ compare_groups
5. 在 `.env` 中配置 mock 或真实 API key

**产出**：`llm/client.py`, `llm/prompts/intent.py`, `llm/prompts/syntax.py`, `tests/test_integration.py`

**验证**：`pytest tests/test_integration.py -v` ≥8/10 pass（LLM 调用不稳定，允许 20% 重试后仍失败）

---

### 步骤 5：输出解析器骨架 + 中文兼容（Day 4）

**依赖**：步骤 2（有 OMS XML 样本）

**操作**：
1. 创建 `parser/schema.py`：
   - `AnalysisResult` dataclass：`analysis_type, tables: list[TableResult], notes`
   - `TableResult` dataclass：`title, rows: list[dict], statistics: dict`
2. 实现 `parser/output.py`：
   - `parse_oms_xml(xml_path: str) -> AnalysisResult`：
     - 用 `lxml` 解析 XML
     - 递归遍历所有 `<dimension>`，按 axis 类型建索引树
     - 从 `axis="statistics"` 的 `<category>` 提取统计量值
     - 特殊处理多层表头（Plan.md 3.5.2）
   - `parse_raw_lst(lst_text: str, analysis_type: str) -> AnalysisResult`：
     - 按 `EXTRACTION_RULES` 中对应分析类型的正则 + 固定列位规则提取
     - 中文表头映射：`{"组统计": "Group Statistics", "独立样本检验": "Independent Samples Test", ...}`
   - `parse(oms_xml_path=None, lst_text=None, analysis_type=None) -> AnalysisResult`：自动选择优先级
3. 编写 `tests/test_parser.py`：
   - `test_oms_ttest_xml`：用步骤 2 生成的 `ttest.xml` → 提取 t 值、p 值、均值
   - `test_oms_frequencies_xml`：→ 提取频数、百分比
   - `test_lst_ttest_en`：用英文 `.lst` 样本 → 正则提取
   - `test_lst_ttest_zh`：用中文 `.lst` 样本 → 正则提取（验证中文表头映射）
   - `test_multi_dimension_anova`：多层表头递归解析（手工构造或真实多因素 ANOVA 输出）
   - `test_fallback_to_regex`：XML 无效时降级到正则

**产出**：`parser/schema.py`, `parser/output.py`, `tests/test_parser.py`

**验证**：`pytest tests/test_parser.py -v` 全部 pass + 中文 `.lst` 样本提取正确

---

### 步骤 6：最小端到端链路（Day 5）

**依赖**：步骤 3（validator）+ 步骤 4（LLM client）+ 步骤 5（parser）

**操作**：
1. 实现 `data/sanitizer.py`：
   - `filter_for_cloud(metadata) -> dict`：仅返回白名单字段
   - `sanitize_variables(variables) -> (list, int)`：变量名敏感词扫描（Plan.md 3.7）
2. 实现 `session.py`：
   - `SessionState` 增加 `var_name_map: dict[str, str]`（脱敏名 → 原始名）
   - `map_to_cloud(variables) -> list[dict]`：原始名 → 脱敏名（仅用于 LLM 请求）
   - `map_to_local(syntax: str) -> str`：LLM 返回语法中的脱敏名 → 原始名（在本地完成）
3. 实现 `executor/spss.py`：
   - `class SPSSExecutor`：
     - `run(syntax, data_path, output_dir) -> {"exit_code": int, "xml_path": str, "lst_text": str}`
     - 自动包裹 OMS 命令
     - 使用 `subprocess.Popen`（非 `run`），保存进程句柄到 session 供中断使用
4. 编写 `scripts/e2e_demo.py`：
   ```
   NL: "比较男女生在成绩上是否有显著差异"
   → intent.py 识别意图 → compare_groups
   → method.py 推荐 t_test（当前用规则 fallback）
   → syntax.py 生成语法 → validator 校验
   → executor 送入 SPSS → 输出 XML
   → parser 解析 XML → {"p_value": 0.021, "t_value": 2.34, ...}
   ```
4. 在 `session.py` 中初始化 `SessionState`

**产出**：`data/sanitizer.py`, `executor/spss.py`, `session.py`, `scripts/e2e_demo.py`

**验证**：执行 `python scripts/e2e_demo.py`，输出结构化 JSON（含 p 值、t 值）

---

### P0 收尾（Day 5）

- [ ] 50 例测试用例清单 Excel（按 Plan.md P0 补充的 6 分类填写）
- [ ] 更新 `README.md`（环境搭建指南）
- [ ] P0 技术验证报告（含：连通性结果、LLM 准确率、安全沙箱覆盖、已知问题）
- [ ] `git commit` 初始版本

---

## P1：核心链路 MVP（第 3–6 周）

### 步骤 7：变量元数据提取（Week 3, Day 1–2）

**依赖**：P0 完成

**操作**：
1. 实现 `data/reader.py`：
   - `read_sav(file_path) -> (pd.DataFrame, dict)`：用 `pyreadstat` 读取
   - `read_csv(file_path) -> (pd.DataFrame, dict)`：用 `pandas` 读取
   - `extract_metadata(df, meta) -> dict`：统一元数据格式 `{"variables": [...], "row_count": N}`
2. 编写 `tests/test_sanitizer.py`：
   - `test_filter_cloud_safe`：仅返回白名单字段
   - `test_sanitize_sensitive_variable`：变量名含"姓名"→ 替换为 var_01
   - `test_sanitize_no_sensitive`：正常变量名不变
   - `test_sanitize_count`：返回脱敏变量数

**产出**：`data/reader.py`, `tests/test_sanitizer.py`

**验证**：`pytest tests/test_sanitizer.py -v` 通过

---

### 步骤 8：三阶段 LLM Prompt 联调（Week 3, Day 3–5）

**依赖**：步骤 7（元数据提取）

**操作**：
1. 实现 `llm/prompts/method.py`：
   - `def build_method_prompt(intent, variables, conversation_context) -> str`
   - few-shot 含 3 种以上统计方法的 (`变量清单, 问题, 推荐方法, 理由`) 示例
2. 实现规则引擎二重校验（`syntax/templates.py` 新增函数）：
   - `validate_method(variables, recommended_method, grouping_var, test_var) -> bool`
   - 规则：a) 分组变量 type == "numeric" 且 value_labels 非空 → 分类变量 ✓ b) 检验变量 type == "numeric" → 连续变量 ✓ c) 每组样本量 ≥ 3
3. 扩展 `tests/test_integration.py`：
   - `test_method_recommendation_ttest`：intent=compare_groups + gender(分类) + score(连续) → 推荐 t_test
   - `test_method_recommendation_anova`：三组以上 → oneway_anova
   - `test_method_validation_rejects`：连续变量做分组 → 被规则引擎拒绝
   - `test_method_fallback`：LLM 推荐错误 → 规则引擎纠正

**产出**：`llm/prompts/method.py`, `syntax/templates.py`（规则引擎部分）

**验证**：集成测试 pass + 手动验证 3 个真实场景的推荐结果

---

### 步骤 9：Streamlit MVP 前端（Week 4–5, Day 1–5）

**依赖**：步骤 8（LLM 三阶段可用）

**操作**：
1. 实现 `ui/streamlit_app.py`（单文件，≤500 行）：
   ```
   页面布局：
   ┌──────────────────────────────────────────┐
   │  📊 SPSS Natural Language Assistant     │
   │  [上传 .sav / .csv 文件]  变量概览 ...... │
   ├──────────────────────────────────────────┤
   │  对话区                                  │
   │  ┌──────────────────────────────────┐    │
   │  │ 用户: 比较男女生成绩差异          │    │
   │  │ 系统: 推荐使用独立样本t检验...    │    │
   │  │       t=2.34, p=0.021<0.05       │    │
   │  │       女生平均分84.2 > 男生79.5   │    │
   │  │       [查看语法] [导出报告]        │    │
   │  └──────────────────────────────────┘    │
   │  [输入分析需求...] [发送] [停止]          │
   └──────────────────────────────────────────┘
   ```
2. 核心状态流：
   - `UPLOADING`：文件上传中
   - `READY`：等待用户输入分析需求
   - `THINKING`：LLM 处理中（显示 spinner + "正在分析..."）
   - `EXECUTING`：SPSS 执行中（显示进度 + 「停止」按钮可见）
   - `DONE`：展示结果（白话解读 + 可展开的语法/原始输出）
   - `ERROR`：错误信息 + 重试按钮
3. 文件上传回调：触发 `reader.py` → 元数据存入 `session_state`
4. 发送回调：
   - 拼接 `session_state.variables` → LLM 三阶段 → validator → executor → parser → naturalize → 渲染
   - 每一次 LLM 调用前过 `sanitizer.filter_for_cloud()`
5. 停止回调：设置 `session_state.cancellation_token = True`，executor 检测后 `kill` SPSS 进程

**产出**：`ui/streamlit_app.py`（完整交互流）

**验证**：`streamlit run ui/streamlit_app.py` → 上传 test_data.sav → 输入"比较男女生成绩差异" → 看到结果

---

### 步骤 10：LLM 解读约束层 + 白话解读（Week 5–6, Day 1–3）

**依赖**：步骤 5（parser 已完成）

> ⚠️ **关键设计**：规则判断在前，LLM 润色在后。LLM 只负责措辞表达，不负责统计判断本身。

**操作**：
1. 实现 `explainer/naturalize.py` — **约束层**（先于 LLM 执行）：
   - `def apply_constraints(analysis_result: AnalysisResult) -> dict`：
     - 按 Plan.md 3.10 的约束规则表强制判断
     - p ≤ 0.05 → `forced_phrase = "存在统计学上的显著差异/关系"`
     - p > 0.05 → `forced_phrase = "未发现统计学上的显著差异/关系"`
     - 0.05 < p < 0.10 → `forced_phrase = "未达统计学显著水平，但接近边缘显著，建议增加样本量"`
     - 效应量判断（d < 0.2 → "效应量较小"，d 0.2–0.5 → "效应量中等"，d > 0.8 → "效应量较大"）
     - 返回 `{"significance": "...", "forced_phrase": "...", "effect_size_desc": "..."}`
2. 实现 `explainer/naturalize.py` — **LLM 润色层**（在约束层之后执行）：
   - `def llm_polish(constraints: dict, analysis_result: AnalysisResult) -> str`：
     - Prompt 模板注入强制表述 + 数值（Plan.md 3.10 LLM Prompt 注入格式）
     - LLM 仅可润色措辞，不得修改统计结论
3. 编写 `tests/test_explainer.py`（**必须覆盖边界情况**）：
   - `test_significant_result`：p=0.01 → 包含"存在显著差异"
   - `test_non_significant_result`：p=0.30 → 包含"未发现显著差异"
   - **`test_boundary_p_051`**：p=0.051 → 必须包含"未发现显著差异"，**不得**出现"相关"、"有意义"等词
   - **`test_edge_significant_p_09`**：p=0.09 → 包含"边缘显著" + "建议增加样本量"
   - `test_effect_size_small`：d=0.1 → 包含"效应量较小"
   - `test_effect_size_large`：d=1.2 → 包含"效应量较大"
4. 实现 `def format_apa(analysis_result, method) -> str`：APA 格式简要报告（可选）

**产出**：`explainer/naturalize.py`（约束层 + 润色层）

**验证**：`pytest tests/test_explainer.py -v` 全部 pass，**尤其关注 p=0.051 约束是否生效**

---

### 步骤 11：模板语法兜底（Week 6, Day 1–2）

**依赖**：步骤 3（validator）、步骤 9（Streamlit 有错误显示）

**操作**：
1. 在 `syntax/templates.py` 中实现 MVP 5 种分析的预置模板：
   - `TTEST_INDEPENDENT(group_var, test_var, groups)` → 完整语法字符串
   - `ANOVA_ONEWAY(group_var, test_var)` → 完整语法字符串
   - `REGRESSION_SIMPLE(dep_var, indep_var)` → 完整语法字符串
   - `CROSSTABS(row_var, col_var)` → 完整语法字符串
   - `FREQUENCIES(var)` → 完整语法字符串
2. 在 `executor/spss.py` 中实现错误恢复四层链路（Plan.md 3.9）：
   - 语法失败 → `_retry_with_llm_fix(error, syntax, variables)`
   - 仍失败 → `_fallback_to_template(method, variables)`
   - 仍失败 → `_show_user_editor(syntax, error)`
3. 实现降级对比卡片渲染（`ui/streamlit_app.py` 中新增组件）

**产出**：`syntax/templates.py`（模板语法 + 规则引擎完善）

**验证**：手动模拟变量名错误 → 观察 LLM 修正 → 模板兜底 → 对比卡片展示

---

### P1 收尾（Week 6, Day 3–5）

- [ ] 设计 50 个 `.sav` 测试数据集（基于 P0 设计的用例清单，用 Python 脚本批量生成）
- [ ] 手动端到端测试 10 个核心场景（5 种分析 × 2 种数据）
- [ ] **约束层边界测试**：p=0.051, p=0.09 两个边界用例，确认解读措辞正确
- [ ] **临时副本机制验证**：执行 COMPUTE + FILTER 预处理场景，确认原始文件未被修改
- [ ] bug 修复 + 代码清理
- [ ] 更新 `README.md`（含截图）

---

## P2：结果解读与安全（第 7–9 周）

### 步骤 12：输出解析器完善（Week 7）

**依赖**：P1 完成 + 收集的真实 SPSS 输出样本

**操作**：
1. 补全 `parser/output.py` 的 `EXTRACTION_RULES`：
   - ANOVA：`"主体间效应检验"` 表格 → F 值、p 值、η²
   - REGRESSION：`"系数"` 表格 → β、t、p；`"模型摘要"` → R²
   - CROSSTABS：`"卡方检验"` 表格 → χ²、p
   - FREQUENCIES：`"统计"` 表格 → 频数、百分比、累积百分比
2. 实现多层表头递归解析（Plan.md 3.5.2）：
   - `_parse_dimensions_recursive(dim_elements, depth=0) -> dict`
3. 编写每种分析类型的期望输出 `.json`（手工标注，作为 parser 单元测试的黄金标准）：
   - `data/fixtures/expected_outputs/ttest_expected.json`
   - `data/fixtures/expected_outputs/anova_expected.json`
   - ...
4. 测试：`tests/test_parser.py` → 解析结果 vs 期望 JSON → 字段级对比

**产出**：`parser/output.py`（完整 5 种解析规则）+ 期望输出 JSON

**验证**：解析结果与手工标注的期望 JSON 逐字段一致

---

### 步骤 13：隐私过滤器联调（Week 8, Day 1–3）

**依赖**：P1 端到端链路可用

**操作**：
1. 在 Streamlit 端到端链路中插入 `sanitizer` 检查点：
   - LLM 调用前：检查 prompt 中的所有数据仅含白名单字段
   - 结果展示前：确认原始数据未泄露
2. 编写隐私渗透测试 `tests/test_privacy_integration.py`：
   - `test_no_raw_data_in_llm_request`：截获 LLM 请求 → 确保不含个体数据行
   - `test_sensitive_variable_desensitized`：变量名含"患者姓名" → LLM 请求中为 var_01
   - `test_lst_output_not_sent_to_llm`：SPSS 原始输出文本不发给云端 LLM（除非用户确认）
   - `test_variable_name_mapping`：脱敏名 ↔ 原始名双向映射正确（P0 步骤 6 实现）
3. 在 `config.py` 中新增 `LLM_CALL_LOG` 开关：开启后记录每次 LLM 请求的 sanitized prompt，供审计

**产出**：渗透测试用例 + 隐私检查日志

**验证**：渗透测试全部 through；审计日志可追溯

---

### 步骤 14：LLM 润色层 A/B 测试（Week 8–9）

**依赖**：步骤 10（约束层已完成）+ 步骤 12（parser 完善）

> ⚠️ 约束层是必须的，LLM 润色层是可选的。先用模板解读兜底，LLM 润色按 A/B 测试逐步开启。

**操作**：
1. 在 `explainer/naturalize.py` 中增加 A/B 切换开关（`config.py` 的 `USE_LLM_POLISH` 标志）：
   - `USE_LLM_POLISH = false` → 仅输出约束层的 `forced_phrase` + 数值（模板模式，100% 可控）
   - `USE_LLM_POLISH = true` → 约束层结果送 LLM 润色措辞
2. 人工评定 10 个解读样本，对比模板模式 vs LLM 润色的通顺度
3. LLM 版 ≥ 模板版质量时，才将 `USE_LLM_POLISH` 默认设为 true
4. 实现 APA 格式报告生成（`def format_apa_report(...)` → 纯文本段落）
5. 实现一键复制功能（Streamlit `st.code` + `st.button("复制")`）

**产出**：`explainer/naturalize.py`（A/B 可控模式 + APA 格式）

**验证**：模板模式下 p=0.051 → 强制输出"未发现显著差异"；LLM 润色模式下结论不变

**验证**：人工评定 5 个解读样本的通顺度和正确性

---

## P3：交互优化与报告（第 10–12 周）

### 步骤 15：多轮对话（Week 10）

**依赖**：P2 完成 + SessionState 已实现

**操作**：
1. 扩展 `llm/prompts/intent.py` 的 follow_up 逻辑：
   - `detect_follow_up(user_message, last_analysis) -> bool`
   - 自动注入 `[上一次分析]` 模板
2. 在 Streamlit 中维护对话历史：
   - 每轮追加 `history.append({"role": "user/assistant", "content": "...", "analysis": {...}})`
   - 渲染历史消息（Markdown 格式）
3. 追问场景测试：
   - "比较男女生成绩差异" → 得到 t-test 结果
   - "那换成班级呢？" → 自动切换分组变量为 class
   - "再看看年级和成绩的关系？" → 自动切换为 ANOVA

**产出**：完整多轮对话体验

**验证**：5 个追问场景均正确关联上下文

---

### 步骤 16：UX 打磨（Week 11）

**依赖**：步骤 15（多轮对话可用）

**操作**：
1. 实现降级对比卡片（Plan.md 3.9 UX 规范）
2. 实现「停止」按钮的中断逻辑（前端设置 token → executor 检测 → 终止 SPSS 进程）
3. 加载动画优化（LLM 处理中/SPSS 执行中分别显示不同动画 + 耗时提示）
4. 错误提示美化（区分 LLM 不可用 vs SPSS 执行失败 vs 语法错误）
5. 变量概览面板：可折叠侧栏，显示变量名、类型、标签、前 5 行预览
6. 移动端适配（Streamlit 默认支持，仅验证不布局破坏）

**产出**：UX 打磨版 Streamlit 应用

**验证**：用户测试（同事/朋友 3 人，各完成 3 个任务，收集反馈）

---

### 步骤 17：报告导出（Week 12）

**依赖**：步骤 14（APA 格式已实现）

**操作**：
1. 安装 `python-docx` → 实现 Word 导出：
   - 标题：`SPSS 分析报告`
   - 分析描述：用户的自然语言原始问题
   - 统计方法：推荐的方法 + 理由
   - 结果表格：关键统计量（均值、p 值、t 值…）
   - 白话解读
   - APA 格式报告
2. 实现 PDF 导出（若选 `reportlab` 或 `fpdf`）
3. Streamlit 中「导出报告」按钮 → 下载 `.docx`

**产出**：`explainer/export.py`

**验证**：导出 3 份不同分析的报告，在 Word 中打开确认格式

---

## P4：测试与发布（第 13–16 周）

### 步骤 18：50 例全量测试（Week 13–14）

**依赖**：P3 完成 + P0 设计的 50 例清单

**操作**：
1. 按 50 例清单逐条执行：
   - 输入 NL 描述 → 记录推荐方法 → 记录语法 → 记录执行结果 → 记录解析结果
2. 人工评定每条结果的正确性（统计专业学生或顾问）
3. 记录 fail 案例，分类归类：
   - LLM 推荐了错误方法 → 优化 method prompt
   - 语法正确但 SPSS 执行失败 → 优化 syntax prompt
   - 解析器提取失败 → 优化 parser 规则
4. 计算最终指标：语法准确率、解析准确率、端到端成功率

**产出**：`tests/results/p4_test_report.csv` + 50 例验收报告

**验证**：语法准确率 ≥ 90%，解析准确率 ≥ 95%

---

### 步骤 19：文档与打包（Week 15–16）

**依赖**：步骤 18（测试通过）

**操作**：
1. 编写用户手册（`docs/user_guide.md`）：
   - 安装指南（Windows）
   - 数据格式要求
   - 示例操作（图文化）
   - 常见问题 FAQ
2. 编写技术文档（`docs/technical.md`）：
   - 架构概述
   - 模块接口文档
   - 扩展指南（如何添加新统计方法）
3. PyInstaller 打包（若选桌面方案）：
   ```
   pyinstaller --onefile --add-data "snla;snla" ui/pywebview_app.py
   ```
4. `.exe` 在另一台 Windows 机器上测试（无 Python 环境）

**产出**：用户手册 + 技术文档 + 安装包

**验证**：另一台 Windows 机器全新安装 → 能完成一个端到端分析

---

## 附录 A：并行开发建议

以下模块可并行开发（互不依赖）：

| 并行组 | 模块 | 依赖 |
|--------|------|------|
| **组 1**：纯逻辑 | `syntax/validator.py`, `data/sanitizer.py`, `parser/schema.py` | 无 |
| **组 2**：SPSS 集成 | `executor/spss.py`, `parser/output.py`, `data/reader.py` | P0 步骤 1（SPSS 连通） |
| **组 3**：LLM 集成 | `llm/client.py`, `llm/prompts/*.py` | `.env` 配置 |
| **组 4**：前端 | `ui/streamlit_app.py` | 组 1 + 组 2 接口定义完成 |
| **组 5**：解读 | `explainer/naturalize.py` | 组 2（parser 完成） |

> 建议开发顺序：组 1 → 组 2 + 组 3 并行 → 组 4 → 组 5

---

## 附录 B：外部依赖风险节点

| 节点 | 风险 | 应对 |
|------|------|------|
| `spss.exe` 路径不确定 | 开发机器 vs 测试机器路径不同 | `config.py` 从 `.env` 读取 + `scripts/verify_spss.py` 启动时校验 |
| 中文 SPSS 输出格式未知 | 解析器开发时只有英文版 | P0 步骤 2 必须在中英文 SPSS 上各收 1 份样本，解析器双版本测试 |
| LLM API 不稳定 | 语法生成测试受阻 | `llm/client.py` 内置 mock 模式（`LLM_MOCK=true`），用固定响应开发 parser 和前端 |
| OMS XML 某些分析类型不输出 | 解析回退到正则 | OMS 失败时自动降级，不限次数重试（最多 1 次 OMS + 1 次 LST） |

---

## 附录 C：每天 check-in 清单

开发者在每天结束时自检：

- [ ] 今天完成了几步？对应的验证通过了吗？
- [ ] 有没有新的依赖风险（SPSS 挂了、LLM 没钱了）？
- [ ] 今天写的代码有没有丢到 git（至少 `git add -A && git commit -m "WIP: ..."`）？
- [ ] 测试跑过了吗（`pytest`）？
- [ ] 离 P0/P1 的准出条件还有多远？
