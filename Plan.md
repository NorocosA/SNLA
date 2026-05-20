# SPSS Natural Language Assistant (SNLA)
### 用说话的方式完成统计分析

---

## 一、项目目标
构建一个对话式工具，让**没有统计和编程背景**的用户，能用自然语言描述分析需求，自动生成并执行SPSS语法，最终以通俗语言返还结果，实现SPSS操作零门槛。

> ⚠️ **坦诚声明："零门槛"的边界**  
> 完全零门槛是不可能的——当 LLM 推荐了错误方法时，不懂统计的用户没有能力判断对错。本项目的"零门槛"实际含义是：**将用户需要掌握的统计知识从"知道用什么方法 + 会写语法"降低到"能读懂系统给出的白话解释 + 在关键决策点做出确认"**。对于假设违背、方法边界等情况，系统将强制展示差异（不可跳过），用极通俗语言帮助用户做出知情选择。

### MVP 目标用户画像（优先级排序）

| 优先级 | 用户类型 | 特征 | 核心诉求 | 对本系统的影响 |
|--------|----------|------|----------|---------------|
| **P0** | 社科本科生 | 正在做毕业论文，需要知道"我的数据该用哪种方法"，看得懂基本统计解释 | 方法推荐 + 语法生成 + 白话解读 + 报告导出 | MVP 默认服务对象。解释文案面向此群体深度设计 |
| **P2** | 临床医生 | 需要快速、合规、可复制的统计报告；可能连"变量"概念都不清楚 | 极度简化的交互 + 自动合规报告 | 需要额外的引导式对话层，MVP 阶段不做深度适配 |
| **P3** | 企业分析师 | 懂一些统计，讨厌写语法 | 语法生成 + 白话解读（黑名单限制可能嫌多） | 灰名单/高级模式，P3 后评估 |

> 明确 MVP 只深度服务**社科本科生**。其他用户类型在后续迭代中按各自诉求调优。

**成功标准（MVP）**
- 用户输入一句需求（如“比较男女生在成绩上的差异”），系统能：
  1. 推荐合适的统计方法（独立样本t检验）
  2. 生成正确的SPSS语法
  3. 自动在SPSS中执行（若用户已安装）
  4. 返回带解释的结果（包含显著性、效应量等的口语化解读）

---

## 二、核心功能范围（MVP）
1. **对话式需求采集**  
   - 用户上传数据（.sav或.csv）  
   - 系统自动读取变量名称、标签、类型  
   - 聊天窗口交互，引导用户明确分析意图（无需使用“独立样本”、“方差齐性”等术语）

2. **智能语法生成与校验**  
   - 基于LLM生成SPSS Syntax，并内置常见错误自检（如变量名不存在、括号不匹配）  
   - 对统计方法选择进行规则辅助审核（例如检查连续变量、正态性提示）
   - **假设违背强制确认**：当系统检测到数据不满足检验假设时（如方差不齐、非正态、样本量不足），以极通俗语言展示差异，**设为不可跳过的确认节点**——例如：
     > *"男女生收入差异确实存在，但因为数据分布不均匀（偏态），更准确的方法是用 Mann-Whitney U 检验代替 t 检验。两种方法的结论可能不同。是否要再看一次？"*
   - 此确认节点不可跳过、不可一键全选"确定"，确保用户在关键决策点知情

3. **一键执行与结果抓取**  
   - 通过SPSS批处理或COM接口将语法送入SPSS运行  
   - 自动提取输出中的关键表格、数字（p值、t值、均值等）

4. **白话解读与报告输出**  
   - 将统计结果转化为自然语言解释，例如：  
     *“男女生成绩存在显著差异（t=2.34, p=0.021<0.05），女生平均分84.2高于男生79.5”*  
   - 可选：生成符合APA/毕业论文格式的简要文字报告

---

## 三、技术方案
### 3.1 整体架构
前端：**PyWebView 桌面窗口**（Windows 原生 Edge WebView2），fallback 浏览器；替代已弃用的 Streamlit  
后端：Python 核心引擎 + Flask 内嵌 API 服务器  
大模型：支持在线API（GPT/Claude/DeepSeek）和本地离线模型（如Llama 3, Qwen等），适应数据隐私需求

> **前端决策**：P0 阶段使用 Streamlit 快速原型，P4 阶段因 Streamlit 与 PyInstaller 打包兼容性问题（静态文件丢失、无官方 hook），切换为 Flask + PyWebView 桌面方案。无 pywebview 时自动回退浏览器模式。

桌面窗口 (PyWebView / 浏览器 fallback)
↕ (HTTP REST API)
Flask API 服务器 (snla/ui/server.py)
↕
对话管理 & 变量信息存储 (session.py)
↕
LLM调用模块 (意图识别 → 统计方法推荐 → 语法生成)
↕
语法校验 + 危险操作拦截 (黑名单机制，详见 3.6 安全沙箱)
↕
SPSS执行器 (subprocess调用statistics.exe -batch / win32com)
↕
输出解析器 (提取表格关键行，转成JSON)
↕
LLM结果解释模块
↕
前端展示 (解释文本 + 可视化表格/图形)

### 3.2 关键依赖
- **Python 3.9+**  
- **spss**（SPSS自带的Python开发包，用于内部语法执行）或**subprocess**批处理  
- **win32com**（Windows下COM自动化，可选）  
- **pandas/ pyreadstat**（读取.sav文件元数据）  
- **LLM接口**：openai库/requests调用API，或llama.cpp/ollama本地推理  
- **前端**：streamlit（MVP阶段唯一前端）

> **解析器数据源双通道**：除了解析 SPSS 原始输出文本（.spo/.lst），MVP 阶段应同时利用 `OMS` 命令导出结构化格式（XML/CSV）作为备选数据源：
> ```
> OMS /SELECT TABLES /DESTINATION FORMAT=OXML OUTFILE='output.xml'.
> OMS /SELECT TABLES /DESTINATION FORMAT=CSV OUTFILE='output.csv'.
> ```
> OMS XML 输出结构固定、跨版本一致，远优于正则解析原始输出。原始输出解析仅在 OMS 不可用时作为降级方案。

### 3.3 模块架构

```
snla/
├── config.py                  # 集中配置（SPSS路径、LLM endpoint、模型选择）
├── session.py                 # 多轮对话状态管理（SessionState类）
├── data/
│   ├── reader.py              # 文件读取（.sav→pyreadstat, .csv→pandas）
│   └── sanitizer.py           # 隐私过滤器（决定什么可发给云端LLM）
├── llm/
│   ├── client.py              # LLM API 抽象层（OpenAI / DeepSeek / ollama 统一接口）
│   └── prompts/
│       ├── intent.py          # Prompt: 意图识别
│       ├── method.py          # Prompt: 统计方法推荐
│       └── syntax.py          # Prompt: SPSS 语法生成
├── syntax/
│   ├── validator.py           # 语法校验 + 危险操作拦截
│   └── templates.py           # 常见分析的语法模板（兜底用）
├── executor/
│   └── spss.py                # SPSS 进程管理器（subprocess spss.exe -batch）
├── parser/
│   ├── output.py              # SPSS 输出解析（正则+固定位置双保险）
│   └── schema.py              # 解析结果 JSON Schema 定义
├── explainer/
│   └── naturalize.py          # 统计结果 → 自然语言解读
├── ui/
│   ├── server.py              # Flask REST API 服务器
│   └── index.html              # 前端页面 (HTML/CSS/JS)
├── tests/
│   ├── conftest.py              # pytest fixtures: mock LLM, mock SPSS output
│   ├── test_validator.py        # 安全沙箱 + 变量校验
│   ├── test_parser.py           # 中/英输出解析
│   ├── test_sanitizer.py        # 隐私过滤器
│   ├── test_integration.py      # 端到端集成测试 (mock SPSS)
│   └── fixtures/                # 测试用 .sav 文件、期望输出、恶意语法
│       ├── test_data.sav
│       ├── expected_outputs/     # 每种分析 × 中/英
│       │   ├── ttest_en.xml
│       │   ├── ttest_zh.lst
│       │   └── ...
│       └── malicious_syntax.sps
```

**关键模块接口：**

| 模块 | 输入 | 输出 |
|------|------|------|
| `data/sanitizer.py` | `pyreadstat` 元数据对象 | `{"variables": [{"name","type","label","value_labels"}], "row_count": N}` |
| `llm/prompts/syntax.py` | `{intent, method, variables, dataset_summary}` | SPSS 语法字符串 |
| `syntax/validator.py` | SPSS 语法字符串 + 变量名列表 | `{valid: bool, errors: [...], warnings: [...]}` |
| `executor/spss.py` | SPSS 语法字符串 + 数据文件路径 | `{exit_code, stdout, stderr, output_file_path}` |
| `parser/output.py` | SPSS 输出原始文本 | `{analysis_type, tables: [{title, rows, statistics}], notes: [...]}` |

### 3.4 LLM Prompt 设计规范

每个 LLM 调用必须遵循以下约束，确保输出可被下游模块可靠消费。

#### 3.4.1 通用设计原则
- **输出格式约束**：所有 Prompt 必须要求 LLM 返回结构化格式（JSON with schema），禁止自由文本输出
- **Few-shot 策略**：每种分析类型提供 2-3 个 `(用户问题, SPSS 语法, 统计方法)` 示例对
- **角色设定**：`你是 SPSS 统计专家，精通 SPSS Syntax 和常用统计检验`
- **变量清单注入**：每次调用自动注入当前数据集的变量名、类型、标签（仅云端安全字段），格式：
  ```
  [DATASET CONTEXT]
  Variables:
  - gender (Numeric, 1=男 2=女)
  - score (Numeric, 考试成绩)
  - class (String, 班级名)
  - age (Numeric, 年龄)
  N = 200
  ```

#### 3.4.2 各 Prompt 模块规范

**`intent.py` — 意图识别**
| 维度 | 规范 |
|------|------|
| 输入 | 用户自然语言语句 + `last_analysis: dict \| None`（上一轮分析上下文） |
| 输出格式 | `{"intent": "describe" \| "compare_groups" \| "relationship" \| "visualize" \| "follow_up" \| "unknown", "confidence": 0.0-1.0, "rationale": "...", "modified_variable": "class"}` |
| Few-shot 示例数 | ≥8（覆盖常见分析描述 + 追问场景） |

> **`follow_up` 意图处理**：当用户说"那换成班级差异呢？""再看看年级的"等追问语句时，意图识别返回 `follow_up`，并自动将 `last_analysis` 的结构（方法、分组变量、检验变量）以模板注入 LLM：
> ```
> [上一次分析]
> 方法: Independent T-Test, 分组变量: gender, 检验变量: score
> ```
> LLM 据此将 "换成班级差异" 推导为：分组变量改为 `class`，检验变量不变。输出中的 `modified_variable` 字段明确标注被替换的变量名。

**`method.py` — 统计方法推荐**
| 维度 | 规范 |
|------|------|
| 输入 | `{intent, variables: [{name, type, label}], conversation_context}` |
| 输出格式 | `{"recommended_method": "independent_t_test" \| "paired_t_test" \| "oneway_anova" \| ..., "alternatives": [...], "assumptions_check": ["normality", "homogeneity_of_variance"], "grouping_variable": "gender", "test_variable": "score"}` |
| 安全机制 | LLM 推荐后，由 `syntax/templates.py` 的规则引擎做二重校验：a) 分组变量是否分类变量 b) 检验变量是否连续变量 c) 样本量是否满足检验前提 |
| Few-shot 示例数 | ≥3 每种方法 |

**`syntax.py` — SPSS 语法生成**
| 维度 | 规范 |
|------|------|
| 输入 | `{method, variables, dataset_summary, output_language}` |
| 输出格式 | `{"syntax": "T-TEST GROUPS=gender(1 2) ...", "required_variables": ["gender", "score"], "notes": "..."}` |
| 输出约束 | ① 仅生成单一分析语句块 ② 变量名必须来自变量清单 ③ 禁止生成 SHOW 等无关命令 ④ 语法中注释使用 `*` 开头 |
| Few-shot 示例数 | ≥5（覆盖 T-TEST、ANOVA、REGRESSION、CROSSTABS、FREQUENCIES） |

#### 3.4.3 Prompt 模板结构（标准三段式）

```
[SYSTEM]
{role_definition}

[DATASET CONTEXT]
{variable_catalog}

[USER REQUEST]
{user_message}

[FORMAT REQUIREMENT]
Return ONLY the JSON object specified above. No explanation.
```

#### 3.4.4 Token 控制策略
- 变量清单在超过 20 个变量时压缩：仅发送变量名 + 类型，省略标签
- 对话历史仅保留最近 3 轮（可配置）
- 单次 LLM 调用 token 上限：input ≤ 4000, output ≤ 2000

---

### 3.5 输出解析器策略

**核心挑战**：SPSS 输出格式因版本 (v26—v29)、语言（中文 vs 英文）、分析类型而异。单一策略不可靠。

#### 3.5.1 三重解析策略（按优先级）

```
优先级 1: OMS XML 输出 (结构化, 跨版本一致)
   ↓ 不可用时降级
优先级 2: 正则 + 固定位置解析 (raw .lst 文本)
   ↓ 解析失败时兜底
优先级 3: LLM 辅助解析 (限 emergency 场景, 成本高)
```

#### 3.5.2 OMS XML 解析（推荐主策略）
在生成的 SPSS 语法中自动包裹 OMS 命令：
```python
# executor/spss.py 在执行前自动注入
OMS_WRAPPER = """
OMS /SELECT TABLES /DESTINATION FORMAT=OXML OUTFILE='{output_xml}'.
{user_syntax}
OMSEND.
"""
```
- OMS XML Schema 固定，`category="Tables"` 的 `<dimension>` 和 `<category>` 节点包含所有统计量
- 中文/英文输出在 XML 中统一使用英文标签（`<dimension axis="statistics">`），不受界面语言影响

> ⚠️ **OMS 不是银弹——两个被低估的风险**：
> 1. **每种 PROCEDURE 的 XML 结构不同**：CROSSTABS 的 OMS 输出与 T-TEST 结构差异巨大，REGRESSION 的系数表与 ANOVA 表结构也不同。这意味着**每种分析类型都需要独立的 XML 解析路径**——工作量不是"写一个通用 OMS 解析器"，而是"为 5 种分析各写一个解析器"。
> 2. **版本兼容性不绝对**：IBM v28→v29 稳定，但不同 hotfix、不同语言安装包的 OMS XML 命名空间（namespace）可能变化。P0 仅测两版本样本不足以覆盖。
> 
> **应对**：P0 验证清单中必须包含"每种分析类型单独验证 OMS XML 解析"（而非笼统的"OMS XML 可用"）。测试数据集需覆盖至少 2 个 SPSS 版本 × 2 种语言 = 4 种环境。

> ⚠️ **多层表头陷阱**：复杂分析（如多因素 ANOVA 的"主体间效应检验"）会产生**嵌套表头**——分组变量 × 因子会导致 OMS XML 中出现额外的 `<dimension axis="variable">` 维度。解析器必须按完整表结构**递归遍历所有 `<dimension>`**，而不是仅查找 `axis="statistics"` 的单个节点。示例：
> ```xml
> <!-- 多因素 ANOVA 的 OMS 输出结构 -->
> <dimension axis="variable">   ← 分组变量维度（性别 × 年级）
>   <category text="男"/>
>   <category text="女"/>
> </dimension>
> <dimension axis="variable">   ← 因子维度
>   <category text="年级一"/>
>   <category text="年级二"/>
> </dimension>
> <dimension axis="statistics"> ← 统计量维度
>   <category text="F"/>
>   <category text="Sig."/>
> </dimension>
> ```
> **处理策略**：用递归 DFS 遍历所有 dimension，按 `axis` 类型分别建立索引树，最后按交叉维度提取统计量。若仅按单维度抽取，多因素分析的关键统计量将完全遗漏。

#### 3.5.3 正则 + 固定位置解析（降级方案）
每种分析类型维护独立的字段提取规则：

```python
# parser/output.py 设计
EXTRACTION_RULES = {
    "T-TEST": {
        "group_stats": {  # "组统计" 表格
            "regex": r"(男|女|\\S+?)\\s+(\\d+)\\s+([\\d.]+)\\s+([\\d.]+)",
            "positional": {  # 固定列位备选 (中文版)
                "group_col": (0, 15),
                "n_col": (15, 25),
                "mean_col": (25, 35),
                "std_dev_col": (35, 45)
            }
        },
        "independent_test": {  # "独立样本检验" 表格
            "regex": r"(假设方差相等|假设方差不等).*?t=([\\-\\d.]+).*?Sig\\.?\\s*\\(双尾\\)\\s*=?\\s*([\\d.]+)",
            "fallback_regex": r"t\\s*=\\s*([\\-\\d.]+)\\s+df\\s*=\\s*(\\d+)\\s+Sig.*?\\s+([\\d.]+)"
        }
    },
    "ANOVA": { ... },
    "REGRESSION": { ... },
    "CROSSTABS": { ... },
    "FREQUENCIES": { ... },
}
```

#### 3.5.4 中文 SPSS 输出适配策略
中文版 SPSS 输出的表头是中文标签（如"组统计""独立样本检验"），且数字格式（千分位逗号）与英文版不同：

| 差异点 | 英文输出 | 中文输出 | 应对策略 |
|--------|----------|----------|----------|
| 表格标题 | "Group Statistics" | "组统计" | 维护中英双标题映射表 |
| 小数点 | `.` (period) | `.` (period, 中文版也用英文点) | 无需特殊处理 |
| 缺失值标记 | `.` | `.` | 一致 |
| p值标签 | "Sig. (2-tailed)" | "Sig.（双尾）" | 同时匹配两种格式 |
| 样本量标签 | "N" | "个案数" | 列位优先于关键词匹配 |

**必须做到**：P0 阶段收集至少 2 个 SPSS 版本的输出样本（英文版 + 中文版各 ≥1），编写差异对比文档。

> **LLM 辅助解析（优先级 3）**：当 OMS 不可用且正则均失败时，将原始输出文本 + 预期提取的统计量发送给 LLM 做解析。需额外注意：发送给云端 LLM 的输出文本中不得包含个体数据行。

---

### 3.6 安全沙箱（完整黑名单）

```
# ====== 黑名单（任何情况下禁止执行） ======
FORBIDDEN_KEYWORDS = [
    # 文件写操作（不可逆的磁盘 I/O）
    "SAVE", "XSAVE", "SAVE TRANSLATE", "EXPORT",
    # 文件删除 / 系统操作
    "DELETE", "ERASE", "HOST COMMAND",
    # 数据集破坏（不可逆）
    "DATASET CLOSE", "DATASET ACTIVATE", "NEW FILE",
    # 任意代码执行
    "BEGIN PROGRAM", "BEGIN PROGRAM PYTHON",
    # 数据集结构变更（隐藏写入风险）
    "AGGREGATE",        # 生成聚合数据集，可能覆盖当前活动数据集
    "ADD FILES",        # 合并外部文件
    "MATCH FILES",      # 横向合并外部文件
]

# ====== 灰名单 — 必要预处理（触发用户确认 + 在临时副本上执行） ======
GREYLIST_KEYWORDS = [
    # 数据变换（高频刚需，禁止将严重阉割体验）
    "COMPUTE",          # "把收入分成高、中、低三组" → 必须用 COMPUTE
    "RECODE",           # "把学历合并成小学/中学/大学" → 必须用 RECODE
    "SELECT IF",        # "只看女性的数据" → 必须用 SELECT IF
    "FILTER",           # "临时排除异常值" → 必须用 FILTER
    # 元数据变更（可能影响 LLM 后续变量引用）
    "RENAME VARIABLES", # 不丢数据，但可能破坏变量引用
    "SORT CASES",       # 不丢数据，但用户可能无意触发
    "WEIGHT",           # 加权可能改变统计量解读
]

# ====== 临时副本机制（灰名单通过时必须） ======
# 1. 灰名单命令确认后，executor 先将当前数据集另存为临时副本
# 2. 在临时副本上执行预处理语法
# 3. 后续分析在预处理后的临时副本上进行
# 4. 会话结束时清理临时副本，用户原始文件始终不变
# 5. 前端提示："此操作将在临时副本上进行，不会修改您的原始数据文件"

# ====== 校验流程 ======
# 1. 语法解析 → 提取所有命令关键字
# 2. 黑名单比对 → 命中则拒绝执行 + 提示用户
# 3. 灰名单比对 → 命中则弹出确认对话框（说明风险 + 临时副本机制），用户同意后放行
# 4. 变量名校验 → 引用的变量是否存在于数据集中
# 5. 括号/引号配对检查
```

### 3.7 隐私协议实现

```python
class DataTier:
    CLOUD_SAFE = "cloud_safe"       # 可发送到云端LLM
    LOCAL_ONLY = "local_only"       # 仅保留在本地

# 云端安全数据（白名单）
CLOUD_SAFE_FIELDS = {
    "variable_names": True,         # 变量名（如 "gender", "score"）
    "variable_types": True,         # 类型（numeric, string, date）
    "variable_labels": True,        # 标签（如 "性别", "成绩"）
    "value_labels": True,           # 值标签（如 {1: "男", 2: "女"}）
    "aggregate_stats": True,        # 聚合结果（均值、p值、样本量）
}

# 本地仅存数据（黑名单）
LOCAL_ONLY_FIELDS = {
    "raw_data": False,              # 原始数据行
    "identifiers": False,           # 身份证、姓名、手机号等
    "free_text_responses": False,   # 开放式文本回答
}
```

**策略**：LLM 调用前，所有 prompt 参数必须经过 `sanitizer.py` 过滤，只传白名单字段。

**变量名隐私增强**（`sanitizer.py` 额外职责）：
```python
# 敏感关键词扫描 — 变量名/标签若命中，自动脱敏
SENSITIVE_VAR_PATTERNS = [
    "姓名", "name", "身份证", "id_card", "手机", "phone", "mobile",
    "电话", "地址", "address", "住址", "邮箱", "email", "工号",
    "学号", "病历号", "病案号", "patient_id",
]

def sanitize_variables(variables: list[dict]) -> list[dict]:
    """检测变量名/标签中的敏感词，命中则替换为通用名 (var_01, var_02, ...)"""
    renamed = []
    sensitive_count = 0
    for v in variables:
        name = v["name"].lower()
        label = v.get("label", "").lower()
        if any(p in name or p in label for p in SENSITIVE_VAR_PATTERNS):
            new_name = f"var_{sensitive_count + 1:02d}"
            renamed.append({**v, "original_name": v["name"], "name": new_name, "desensitized": True})
            sensitive_count += 1
        else:
            renamed.append(v)
    return renamed, sensitive_count  # 返回脱敏后的列表 + 被脱敏的变量数
```
- 检测到敏感变量时，前端弹出提示"检测到 X 个变量含隐私信息，已自动脱敏"
- 脱敏后的 `original_name` 仅保留在本地内存，不会发送给任何 LLM

**变量名双向映射路径**（关键设计——防止用户困惑）：
```
┌──────────────────────────────────────────────────────────┐
│  本地(用户可见)          │  云端 LLM 请求                  │
│──────────────────────────│────────────────────────────────│
│  原始名: "患者年龄"       │  脱敏名: var_01                 │
│  原始名: "治疗效果"       │  脱敏名: var_02                 │
│                          │                                │
│  语法审查界面:            │  语法生成 prompt:                │
│  显示原始名 + 脱敏名对照  │  "变量: var_01(Numeric)..."     │
│  "var_01(患者年龄)"      │                                │
│                          │  返回语法:                       │
│                          │  "T-TEST GROUPS=var_02..."      │
│  执行前映射回原始名:      │                                │
│  "T-TEST GROUPS=治疗效果" │                                │
└──────────────────────────────────────────────────────────┘
```
- `session.py` 维护 `var_name_map: dict[str, str]`（脱敏名 → 原始名）
- 发往云端 LLM 前：原始名 → 脱敏名
- LLM 返回语法后：脱敏名 → 原始名（在本地完成映射）
- 用户可见的语法审查界面：始终展示原始变量标签，括号中标注脱敏名（如 `var_01(患者年龄)`）

### 3.8 多轮对话状态管理

```python
class SessionState:
    """MVP 阶段：内存存储，无持久化"""
    dataset_meta: dict          # 当前数据集元数据
    variables: list[dict]        # 变量列表（name, type, label, value_labels）
    history: list[dict]          # 对话历史
    last_analysis: dict | None   # 最近一次分析上下文（允许追问）
    active_syntax: str | None    # 当前活跃的SPSS语法（供用户审查）
    active_process: Popen | None # 正在运行的 SPSS 子进程句柄（用于中断）
    cancellation_token: bool     # 用户是否请求取消当前操作
```

**跨轮一致性保证**：
- 每轮 LLM 调用前，自动注入当前数据集的变量清单（仅云端安全字段）
- 追问场景（如"再看看年级的差异"）：复用 `last_analysis` 上下文，自动关联变量

**操作中断机制**：
- 前端提供「停止」按钮，设置 `cancellation_token = True`
- `executor/spss.py` 在执行循环中检查 token，触发时调用 `active_process.terminate()` 杀掉 SPSS 进程
- 终止后清理临时文件，回滚状态到操作前

---

### 3.9 错误恢复与降级链路

SPSS 语法执行失败是高频场景（LLM 幻觉、变量名错误、数据不满足检验前提）。需分层处理：

```
第1层: 语法预校验 (validator.py)
  ├─ 黑名单检查 → 拦截并提示用户
  ├─ 变量名存在性 → 将缺失变量名反馈给 LLM 重新生成
  └─ 语法结构（括号/引号配对）→ 自动修复或拒绝

第2层: SPSS 执行失败 (exit code ≠ 0)
  ├─ 提取 stderr 错误信息
  ├─ 将错误信息 + 原始语法 + 变量清单发给 LLM，要求修正
  └─ 最多重试 2 次

第3层: 模板语法兜底 (templates.py)
  ├─ 当 LLM 修正仍失败时，使用预置统计模板语法
  └─ 模板覆盖 MVP 5 种分析类型 (FREQUENCIES, DESCRIPTIVES, T-TEST, CROSSTABS, REGRESSION)

第4层: 用户介入
  ├─ 显示 LLM 生成的语法 + 错误信息
  └─ 用户手动编辑语法后重新执行
```

**降级链示例**：
```
用户: "比较男女成绩差异"
  → LLM 生成 T-TEST 语法
    → validator 通过
      → SPSS 执行失败 (变量 "gender" 是字符串类型)
        → LLM 修正: 添加 AUTORECODE 或提示用户
          → 再次失败
            → 使用 template.TTEST_INDEPENDENT 模板语法
              → 成功 → 返回结果
```

> **关键设计决策**：降级到第3层（模板）时，需向用户明确说明"自动修正已用尽，已切换至标准模板语法，可能无法完全匹配您的原始意图"。

> **降级时的前端 UX 规范**：当触发模板兜底时，前端以**对比卡片**形式展示差异，让无统计背景的用户也能理解发生了什么变化：
> ```
> ┌─────────────────────────────────────────────┐
> │ ⚠ 语法自动修正已用尽，已切换至标准模板        │
> │                                              │
> │ 您原本要执行的分析：【独立样本 t 检验】       │
> │ → 因语法生成失败，已切换为标准模板            │
> │                                              │
> │ 具体差异：                                   │
> │  分组变量 gender 值标签从 1/2 自动重编码      │
> │  为 0/1（见语法第 3 行）                     │
> │                                              │
> │ [查看完整语法]  [仍要执行]  [取消]            │
> └─────────────────────────────────────────────┘
> ```

---

### 3.10 LLM 解读约束层（防过度推断）

**核心设计原则**：规则判断在前，LLM 润色在后。LLM 只负责措辞表达，不负责统计判断。

#### 问题
LLM 在看到统计数字时，可能生成看似合理但过度推断的表述。例如：
- SPSS 输出：`p = 0.051, r = 0.3`
- ❌ LLM 错误解读：*"收入和受教育年限之间存在中等程度的正相关，虽然 p 值略高于 0.05，但仍具有一定的实际意义。"*
- 这个表述在统计上不严谨（p > 0.05 就不能说"存在相关"），但对不懂统计的用户听起来非常专业可信，**构成严重误导**。

#### 约束层架构

```
SPSS 输出解析结果
       ↓
┌──────────────────────────────────┐
│  naturalize.py — 规则约束层      │  先于 LLM 执行
│                                  │
│  if p > 0.05:                    │
│    significance = "NOT_SIG"      │
│    forced_phrase = "未发现统计   │
│      学上的显著差异/关系"         │
│                                  │
│  if p <= 0.05:                   │
│    significance = "SIGNIFICANT"  │
│    forced_phrase = "存在统计学   │
│      上的显著差异/关系"           │
│                                  │
│  if effect_size == "small":      │
│    forced_phrase += "，但效应量  │
│      较小"                       │
└──────────────────┬───────────────┘
                   ↓
          ┌──────────────────┐
          │  LLM 润色层       │  ← 仅负责措辞表达
          │                   │
          │  Prompt:          │
          │  "以下是强制使用  │
          │   的结论：        │
          │   '{forced_phrase}'│
          │   请用自然口语   │
          │   复述，添加      │
          │   具体数值，但    │
          │   不得修改结论    │
          │   的统计含义。"   │
          └──────────────────┘
```

#### 约束规则表

| 统计量 | 判断条件 | 强制表述 |
|--------|----------|----------|
| p 值 | ≤ 0.05 | "存在统计学上的显著差异/关系" |
| p 值 | > 0.05 | "未发现统计学上的显著差异/关系" |
| p 值 | 0.05 < p < 0.10 | "未达统计学显著水平，但接近边缘显著（p={value}），建议增加样本量后再次检验" |
| 效应量 (d) | < 0.2 | "但效应量较小" |
| 效应量 (d) | 0.2–0.5 | "效应量中等" |
| 效应量 (d) | > 0.8 | "效应量较大" |
| R² | < 0.1 | "模型解释力有限" |
| R² | ≥ 0.1 | "模型具有一定解释力" |

#### LLM Prompt 注入格式

```
[STATISTICAL FACTS — 必须严格遵守以下事实，不得修改]
- 显著性结论: {forced_phrase}
- 具体数值: t={t_value}, p={p_value}, 均值A={mean_a}, 均值B={mean_b}
- 不允许使用的措辞: "存在相关"(如果 p>0.05)、"具有实际意义"、"接近显著"（除非 p 在边缘范围）
- 允许使用的措辞: 仅上述强制表述 + 数值的通俗化表达

请用面向社科本科生的通俗语言复述以上结论，可添加数值解释，但统计结论必须与上述完全一致。
```

> **测试验证**：对 `explainer/naturalize.py` 的单元测试必须覆盖边界情况——当 p=0.051 时，输出必须包含"未发现统计学上的显著差异"，不得出现"相关"、"有意义"等过度推断措辞。这应作为 `tests/test_explainer.py` 的必测用例。

---

## 四、实施阶段与里程碑
总时长建议：**12～16周**（**12周为激进计划，16周为合理计划**；以下基于 16 周展开）

> **可降级的模块清单**（在不破坏 MVP 完整性的前提下）：
> - 报告导出（Word/PDF）→ 可从 P3 推迟到 P4
> - Electron 桌面化评估 → 可独立为 P5（不阻塞 MVP 发布）
> - 多因素 ANOVA 等复杂分析 → 仅做单因素 MVP，其余留到 v2
> - LLM 增强版解读 → 先用模板解读兜底，LLM 解读按 A/B 测试逐步开启

| 阶段 | 周期 | 主要任务 | 交付物 |
|------|------|----------|--------|
| **P0 技术验证** | 第1-2周 | ① 项目环境搭建（repo、venv、目录骨架、config）② 验证SPSS批处理/OMS XML导出 ③ 收集中/英 SPSS 输出样本 ④ 测试LLM生成SPSS语法的准确率 ⑤ 验证安全沙箱（黑白灰名单） ⑥ 搭建最小端到端链路 ⑦ 设计 50 例测试用例清单 | 技术可行性报告、可运行 demo 脚本、`.sav` 测试数据集、中英输出样本库、**50 例测试用例清单（Excel/CSV）** |
| **P1 核心链路MVP** | 第3-6周（可延长至7周） | 开发对话模块、变量元数据提取、LLM语法生成（含三阶段 prompt）、SPSS OMS 执行、XML/正则双解析器。**P1 仅做单轮请求闭环**，不包含多轮对话 | Streamlit 聊天窗（基础UI），完成"输入一句话 → 输出结构化结果 + 白话解读" |
| **P2 结果解读与安全** | 第7-9周（若P1延长则压缩至8-10周） | 输出解析器完善（含多层表头递归解析）；LLM解释模块；错误恢复链路（四层降级）；隐私过滤器联调；统计方法推荐二重校验 | 完整链路闭环：NL 问题 → 白话答案（含错误恢复），隐私自动脱敏 |
| **P3 交互优化与报告** | 第10-12周 | **多轮对话（追问能力 + follow_up 意图）**；Streamlit 前端美化；中断/取消能力；降级对比卡片 UX；一键导出 Word/PDF 解释报告；评估 Electron 桌面化可行性 | 可演示的 Web 应用，完整多轮对话体验 |
| **P4 测试与发布** | 第13-16周 | 用 P0 设计的 50 例测试清单逐条验收；编写用户手册；PyInstaller 打包（若选桌面方案） | 安装包、测试报告、用户指南、50 例验收报告 |

> ✅ **P4 已完成** (2026-05-20)。详细验收数据见 `.sisyphus/assessment.md`。
> 改进计划见 `.sisyphus/improvement-plan.md`。

### P4 实际交付物（超额完成）

| 交付物 | 状态 |
|--------|------|
| Flask + PyWebView 前端迁移（替代 Streamlit） | ✅ |
| Server 重写：灰名单确认、取消中断、设置持久化 | ✅ |
| 模板语法生成（LLM 仅负责意图+方法） | ✅ |
| 56 单元/集成测试 | ✅ |
| 50 例 Mock 验证 — 50/50 语法有效 | ✅ |
| 65 例真实 LLM 验证 (含 airline.sav 25K 行) — 100% 语法有效 | ✅ |
| PyInstaller 打包 → `SNLA.exe` (78 MB) | ✅ |
| 3 条 E2E 真实 SPSS 全部通过 | ✅ |
| AGENTS.md / README 更新 | ✅ |

### P0 补充细节

**P0 交付物明细**：
```
snla/
├── requirements.txt
├── config.py (SPSS路径可配置)
├── .env.example
├── data/
│   └── fixtures/
│       ├── test_data.sav          # 测试数据集
│       ├── expected_outputs/       # 预期输出：每种分析类型 × 中/英
│       │   ├── ttest_en.xml
│       │   ├── ttest_en.lst
│       │   ├── ttest_zh.lst
│       │   ├── frequencies_en.xml
│       │   └── ...
│       └── malicious_syntax.sps    # 安全沙箱测试用恶意语法
├── scripts/
│   └── verify_spss.py             # P0 验证脚本：自动测试 5 种语法连通性
└── README.md (开发环境搭建指南)
```

**P1 准出条件**（进入 P2 前必须满足）：
- [ ] OMS XML 解析器对 5 种分析类型均提取正确
- [ ] 安全沙箱 5/5 拦截
- [ ] LLM 语法生成 ≥8/10 校验通过
- [ ] 端到端链路至少 1 次完整闭环

**50 例测试用例设计**（P0 阶段完成清单，P1-P2 边开发边验收）：
| 分类 | 数量 | 示例 |
|------|------|------|
| 基础描述统计 | 10 | "计算各班级语文成绩的平均分、标准差""画出年龄的直方图" |
| 组间比较 | 15 | 独立 t 检验、配对 t 检验、单因素 ANOVA、非参数检验（Mann-Whitney, Kruskal-Wallis） |
| 相关与回归 | 10 | Pearson/Spearman 相关、简单线性回归、多元回归 |
| 交叉表与卡方 | 5 | "性别和是否通过考试之间有关系吗" |
| 图表生成 | 5 | 箱线图、散点图、分组条形图 |
| 中文口语化表达 | 5 | "算一下男女在语文分数上有没得差别""帮我瞅瞅年纪大的是不是工资也高" |

> 清单用 Excel/CSV 管理，列字段：`编号, NL描述, 预期统计方法, 预期分组变量, 预期检验变量, 验收状态, 验收人, 备注`。P0 仅实际执行 5 条，但清单全部定义，作为 P1-P4 的渐进验收标准。

---

## 五、关键指标与演示场景
**度量指标**
- 语法生成准确率（测试50个常见分析描述，≥90%可被SPSS无错执行）
- 结果解释正确率（由1-2位统计专业学生评定，≥85%）
- 零基础用户完成典型任务的时间（对比学习SPSS图形界面操作，时间缩短70%以上）

**Demo预设案例**
1. 描述统计：“计算各班级语文成绩的平均分、标准差”
2. 差异检验：“分析实验组和对照组在焦虑量表得分上是否有差异”
3. 关系分析：“研究收入和受教育年限之间的关系”
4. 图表需求：“画一个按性别分组的成绩箱线图”

---

## 六、资源需求
- **人员**：1名全栈/ Python开发者（若跨学科可搭配1名统计顾问）  
- **软件**：IBM SPSS Statistics（带Python扩展的版本），Windows环境优先  
- **算力**：若使用本地LLM，需至少8GB显存的GPU（可租用或使用CPU版量化模型）  
- **经费**：在线API费用（约200-500元测试预算）；若纯本地模型则无

> ⚠️ **开发者能力缺口**：本项目要求开发者同时具备 SPSS 内部机制理解（OMS、batch、licensing）、LLM prompt 工程、Streamlit 前端、以及足够的统计知识（至少能读懂 ANOVA/回归输出表才能写解析器）。统计顾问大概率不懂 OMS XML 结构。
>
> **P0 必读清单**（开发者在 P0 期间完成）：
> - IBM SPSS Statistics 官方 OMS 命令语法指南（至少读完 `OMS`、`OXML`、`TABLES` 三章）
> - OMS XML Schema 文档（理解 `<dimension axis="statistics|variable|...">` 的含义）
> - SPSS batch mode 手册（`spss.exe -batch` 的参数、退出码、输出重定向机制）
> - 至少 2 个不同版本 SPSS 的输出样本对比（手工执行相同语法，对比 `.lst` 差异）
>
> **统计顾问介入节点**：
> | 节点 | 顾问职责 |
> |------|----------|
> | P0 解析器规则设计 | 审核每种分析类型的字段提取规则是否覆盖关键统计量 |
> | P2 解读文案审查 | 审核 naturalize.py 的强制表述措辞是否统计严谨 |
> | P4 50 例验收 | 逐条审核系统输出，判断结果解读是否正确 |

---

## 七、主要风险与应对

| 风险 | 影响 | 预案 |
|------|------|------|
| LLM生成错误统计方法 | 分析结果误导用户 | 引入方法选择规则库和用户确认机制，关键决策让用户从推荐列表中选择 |
| 用户原始数据隐私 | 若用云端API造成泄露 | 默认设计为**仅发送变量名、类型和标签**，不发送实际数值；鼓励本地模型 |
| SPSS自动化不稳定 | 语法错误、输出格式变化 | 构建重试机制，输出解析用正则+固定位置双保险 |
| SPSS 版本/语言差异导致输出格式变化 | 解析器失效，无法提取统计量 | 输出解析使用 locale-agnostic 正则 + 固定列位双策略；P0 阶段收集至少 2 个版本的输出样本 |
| LLM token 消耗失控 | 单次分析成本过高 | 实现 prompt 缓存；将变量信息压缩为精简摘要而非完整字典；设置单次调用 token 上限 |
| **中文 SPSS 输出表头不匹配** | 正则解析器完全失效 | 维护中英双语表格标题映射表；OMS XML 作为主策略可规避此问题；P0 必须同时测试中文版 SPSS 输出 |
| **LLM API 不可用** | 核心链路完全中断 | ① 本地模型自动切换（ollama/llama.cpp 作为 fallback endpoint）② 模板语法直接执行（跳过 LLM，用户从模板列表手动选择分析方法）③ 错误提示明确区分"LLM 不可用"vs"SPSS 执行失败" |

---

## 八、P0 技术验证清单

### 8.0 项目环境搭建（在验证前完成）

| # | 搭建项 | 具体操作 | 产出 |
|---|--------|----------|------|
| E1 | 仓库初始化 | `git init`；创建 `.gitignore`（排除 `*.spv`, `__pycache__`, `.env`）；初始化 `README.md` | Git 仓库就绪 |
| E2 | Python 环境 | `python -m venv venv`；`pip install pyreadstat pandas openai streamlit`；锁定 `requirements.txt` | 可复现的开发环境 |
| E3 | 目录骨架 | 按 3.3 模块架构创建全部目录和 `__init__.py` | 空模块树就绪 |
| E4 | 配置模板 | `config.py` 包含 `SPSS_PATH`, `LLM_ENDPOINT`, `LLM_API_KEY`（从 `.env` 读取） | 配置中心可用 |
| E5 | SPSS 路径验证 | 在目标机器上确认 `spss.exe` / `statistics.exe` 路径；运行 `--version` 确认可调用 | SPSS 路径已配置 |

### 8.1 P0 验证项

| # | 验证项 | 具体操作 | 成功标准 |
|---|--------|----------|----------|
| 1 | SPSS 批处理连通性 | 用 5 条语法（FREQUENCIES, DESCRIPTIVES, T-TEST, CROSSTABS, REGRESSION）调用 `spss.exe -batch` | 5/5 返回 exit code 0，正确捕获 stdout/stderr |
| 2 | **每种分析 OMS XML 独立验证** | 对 5 种分析**分别**生成 OMS XML 输出文件，验证每种分析的结构完整性（T-TEST 的组统计表、ANOVA 的效应检验表、REGRESSION 的系数表、CROSSTABS 的卡方表、FREQUENCIES 的频数表各自结构不同） | 5/5 产生有效 XML 文件，各分析的结构可被解析器正确提取（非笼统的"OMS OK"） |
| 3 | 输出解析鲁棒性 | 对上述 5 种分析，用 XML 解析（主）+ 正则（备）提取关键统计量 | 每种分析类型的关键统计量准确率 100% |
| 4 | **中文 SPSS 输出兼容** | 在中文版 SPSS 上重复验证项 1-3 | 解析器在中英两种输出中均正常工作 |
| 5 | LLM 语法生成准确率 | 10 条 NL 描述（覆盖描述统计、差异检验、关系分析、**含数据预处理需求如"只看女性""分成三组"**），用 LLM 生成语法 | ≥8/10 可通过 validator 校验且变量名正确 |
| 6 | 安全沙箱有效性 | 构造 8 条恶意语法（含 SAVE、DELETE、HOST COMMAND、BEGIN PROGRAM、AGGREGATE、ADD FILES、COMPUTE；另含 2 条灰名单 COMPUTE + FILTER — 验证临时副本机制和确认对话框流程） | 黑名单 7/7 拦截；灰名单弹出确认对话框，在临时副本上正常执行 |
| 7 | 错误恢复链路 | ① 构造变量名错误的语法 → LLM 自动修正 ② 构造数据不满足检验前提 → 假设违背强制确认节点弹出 | 修正链路能自动恢复或正确提示；强制确认不可跳过 |
| 8 | **SPSS 进程异常终止恢复** | 连续 3 次强制终止 (`process.terminate()`) SPSS 进程后，检查：① 临时文件 (`.tmp`, `.jnl`) 是否已清理 ② SPSS licensing service 是否可正常启动 ③ 第 4 次分析能否正常执行 | SPSS 在 3 次强制终止后仍能正常启动和执行 |
| 9 | 最小链路端到端 | 一条完整链路：NL输入 → 语法生成 → 校验 → SPSS执行 → 输出捕获 → 解析器提取 → 约束层强制表述 → LLM 润色 | 成功产生结构化 JSON + 白话解读，解读措辞符合约束规则 |

### 8.2 P0 验证所需测试数据

| 数据集 | 变量 | 用途 |
|--------|------|------|
| `test_data.sav` | gender (Numeric, 1/2), score (Numeric), class (String), age (Numeric) | 所有 P0 测试的基准数据集 |
| 期望输出样例 (每种分析 ≥1 份) | 手动执行的标准 SPSS 输出 `.lst` 文件 + OMS `.xml` 文件 | 解析器开发的对齐基准 |

### 8.3 P0 测试策略

| 层级 | 工具 | 覆盖范围 |
|------|------|----------|
| 单元测试 | `pytest` | `validator.py`, `sanitizer.py`, `parser/output.py` — 纯逻辑模块 |
| 集成测试 | `pytest` + mock SPSS 输出 | LLM prompt 模块（使用 mock LLM 响应）、executor 错误处理 |
| 手动验证 | 真实 SPSS | SPSS 连通性、端到端链路（SPSS 依赖环境，无法 CI 自动化） |

> **CI 策略**：单元测试和集成测试可在 GitHub Actions（Windows runner）上运行。涉及真实 SPSS 调用的测试仅能本地手动执行。

---

## 九、P0 启动命令模板

以下命令可直接复制执行，用于环境搭建和 P0 验证：

### 环境初始化
```powershell
# 创建虚拟环境
python -m venv venv
venv\Scripts\activate

# 安装核心依赖
pip install pyreadstat pandas openai streamlit python-dotenv lxml

# 锁定版本
pip freeze > requirements.txt
```

### 配置 .env
```bash
# .env (加入 .gitignore)
SPSS_PATH=C:\Program Files\IBM\SPSS\Statistics\29\stats.exe
LLM_ENDPOINT=https://api.openai.com/v1/chat/completions
LLM_API_KEY=sk-xxxxxxxx
LLM_MODEL=gpt-4o
LOCAL_LLM_ENDPOINT=http://localhost:11434/api/chat  # ollama fallback
```

### P0 验证脚本
```powershell
# SPSS 连通性测试（5 条语法）
python scripts/verify_spss.py --spss-path "%SPSS_PATH%" --output-dir ./p0_output

# 安全沙箱测试（恶意语法 8 条，含黑名单+灰名单）
python -m pytest tests/test_validator.py -v

# 输出解析器测试（中英双版本）
python -m pytest tests/test_parser.py -v

# LLM 语法生成测试（需先配置 .env）
python -m pytest tests/test_integration.py::test_llm_syntax -v

# 隐私过滤器测试
python -m pytest tests/test_sanitizer.py -v
```

### 启动
```powershell
# 桌面模式 (需要 pywebview)
python launcher.py

# 或命令行 Demo
python scripts/e2e_demo.py --data-file data/fixtures/test_data.sav

# Flask API 独立运行
python snla/ui/server.py
```