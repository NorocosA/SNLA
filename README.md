# StatsTalk

用说话的方式完成统计分析。支持 **SPSS** 和 **Python (pingouin)** 双引擎，15 种分析方法。

## 快速开始

```powershell
# 1. 安装
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# 2. 配置（复制 .env.example 为 .env，填入 LLM Key，SPSS 可选）
copy .env.example .env

# 3. 启动
python launcher.py

# 无 SPSS 模式（纯 Python 后端）
# 在 .env 中设置 STATS_BACKEND=python 即可

# 命令行 Demo
python scripts/e2e_demo.py --data-file data/fixtures/test_data.sav
```

## 功能

| 功能 | 说明 |
|------|------|
| 🗣 自然语言输入 | "比较男女成绩差异" → 自动执行 t 检验 |
| 🧠 LLM 智能规划 | DeepSeek V4 Flash + RAG 知识库增强，识别意图、推荐方法、匹配变量 |
| 🔀 双统计引擎 | SPSS (Python Submit / Batch) 或 Python (pingouin 15 方法)，可自动检测、可配置切换 |
| 📋 模板语法生成 | 15 种预置模板，零幻觉，100% 通过校验 |
| 📊 白话解读 | 统计约束层 + 非参数检验专用模板（Mann-Whitney/Kruskal-Wallis），LLM 润色 |
| 🔁 多轮对话 | "那换成班级差异呢？" 自动切换分析变量，范围展开（Q1-Q10） |
| 💾 会话持久化 | SQLite 自动保存，重启桌面不丢数据 |
| 🛑 取消中断 | 长任务可随时取消，自动清理进程和临时文件 |
| ⚠️ 灰名单确认 | COMPUTE/RECODE 等修改操作触发确认，在临时副本上执行 |
| 📥 Word 导出 | APA 格式报告一键下载 |
| 📈 图表生成 | matplotlib 柱状图/散点图/直方图，base64 嵌入报告 |
| 🔒 隐私保护 | 仅变量结构信息发云端 LLM，value_labels 自动剥离，原始数据永不过网 |
| 🛡 安全沙箱 | 黑名单拦截 + 500MB 上传限制 + MIME 白名单 + 输入长度限制 + 速率限制 |
| 🖥 桌面应用 | PyWebView 原生窗口（fallback 浏览器），`StatsTalk.exe` 单文件分发 |
| 🔧 设置持久化 | API 配置保存 `.env`，下次启动自动加载，支持热重载无需重启 |
| 🌐 多渠道支持 | MCP Server（7 工具）+ OpenClaw Skill，支持 Claude Desktop 等客户端 |
| 🔐 TLS 加固 | endpoint 白名单式 TLS，仅 opencode.ai 使用宽松证书 |

## 支持的分析

独立样本 t · 单因素 ANOVA · 配对 t · Pearson 相关 · Spearman 相关 · 简单回归 · 卡方检验 · 交叉表 · 描述统计 · 频率分析 · Mann-Whitney U · Kruskal-Wallis · **Wilcoxon** · **多元回归** · **Logistic 回归**

**双后端覆盖**: 11/12 方法经 SPSS-Python 交叉验证。Python 后端 15 方法，SPSS 可选。

## 测试

```powershell
python -m pytest snla/tests/ -v                    # 87 单元/集成测试（不需要 SPSS/LLM）
python -m pytest snla/tests/ -v -m "not slow"      # CI-safe (85 tests)
python -m pytest snla/tests/test_server.py -v      # API 测试 (23 tests)
python -m pytest snla/tests/test_python_backend.py -v  # Python 后端 (24 tests)
python scripts/mcp_integration_test.py              # MCP 集成测试 (7/7)
python scripts/verify_combined.py                   # 65 例真实 LLM 验证
python scripts/verify_50_cases.py --mock            # 50 例 Mock 语法验证
```

## 项目结构

```
snla/
├── config.py          # 集中配置 (从 .env 读取, 支持热重载)
├── session.py         # 多轮对话状态管理
├── trust.py           # 统计方法信任白名单
├── mcp_server.py      # MCP Server — FastMCP 7 工具
├── data/
│   ├── reader.py      # .sav/.csv 数据读写
│   ├── sanitizer.py   # 隐私过滤 + 敏感变量脱敏
│   ├── persistence.py # SQLite 会话持久化
│   └── range_expander.py  # Q1-Q10 变量范围展开
├── llm/               # LLM 客户端 (指数退避重试 + TLS 加固) + Prompt 模板
├── syntax/            # 15 种语法模板 + 安全校验 (黑/灰名单)
├── executor/          # SPSS/Python 双后端适配器 + 进程管理
├── parser/
│   ├── output.py      # 统一入口
│   ├── _oms.py        # OMS XML 解析器 (7 专用提取器)
│   └── _lst.py        # LST 文本解析器 (正则回退)
├── explainer/
│   ├── naturalize.py  # 统计约束层 + 非参数模板 + 白话解读
│   ├── export.py      # Word .docx 导出
│   └── charts.py      # matplotlib 图表生成 (bar/scatter/histogram)
├── orchestrator/      # 分析规划器 + 灰名单状态机 (RAG 增强)
├── ui/
│   ├── server.py      # Flask REST API (11 端点)
│   ├── _helpers.py    # 通用辅助函数
│   ├── _pipeline.py   # 分析流水线函数
│   └── index.html     # 单文件前端
├── rag/               # RAG 知识库 (566 chunks, 20 commands, 已集成)
└── tests/             # 87 单元/集成测试 (10 文件)

scripts/               # E2E Demo / 验证脚本 / MCP 集成测试
docs/                  # 用户指南 + 重命名评估 + 测试指南
data/fixtures/         # test_data.sav + airline.sav (25K 行)
.opencode/skills/snla/ # OpenClaw Skill 配置
pyproject.toml         # Ruff 格式化配置
launcher.py            # 桌面启动器
snla.spec              # PyInstaller → StatsTalk.exe
```

## MCP 多渠道接入

```powershell
# 启动 MCP Server（stdio 传输）
python snla/mcp_server.py

# OpenClaw 配置
openclaw mcp set snla --command python --args "snla/mcp_server.py"
```

提供 7 个工具: `snla_status`, `snla_upload`, `snla_variables`, `snla_analyze`, `snla_confirm`, `snla_cancel`, `snla_export`

## 打包

```powershell
pyinstaller snla.spec --noconfirm
# 输出: dist/StatsTalk.exe (约 78 MB 单文件)
```

## 许可

内部项目
