# SNLA 项目评估与测试指南

> 评估日期: 2026-05-28 | 测试: 87 pass | 提交: 20+ commits

---

## 一、项目概览

### 架构

```
用户输入(自然语言)
    → LLM 意图识别 + 方法推荐 (planner)
    → 双后端路由:
        ├─ Python (pingouin, 12 方法, SPSS 可选)
        └─ SPSS (Python Submit / Batch)
    → 语法生成 (模板, 零幻觉)
    → 安全校验 (黑/灰名单)
    → 执行 + OMS XML 解析
    → 统计约束层 → 白话解读
    → Word 导出 / MCP 多渠道

入口: Flask REST API (localhost:8501) + PyWebView 桌面窗口 + MCP stdio
```

### 关键指标

| 指标 | 值 |
|------|-----|
| 测试总数 | **87** (86 CI-safe, 1 需 SPSS) |
| 分析方法 | **12** (SPSS + Python 双后端) |
| 后端覆盖 | **11/12** 可信 (simple_regression 策略 C 兜底) |
| MCP 工具 | **7** (snla_status/upload/variables/analyze/confirm/cancel/export) |
| API 端点 | **11** (Flask REST) |
| 代码行数 | ~11,000 (snla/) |
| Python 版本 | 3.10+ |

---

## 二、成熟度评估

### 核心能力 ✅

| 能力 | 状态 | 说明 |
|------|------|------|
| 自然语言→统计分析 | ✅ | LLM + 模板双保险 |
| SPSS 执行 | ✅ | Python Submit (26+) + Batch (legacy) |
| Python 后端 | ✅ | pingouin 12 方法, 无 SPSS 可用 |
| 安全沙箱 | ✅ | 黑/灰名单, 上传限制, 隐私过滤 |
| 白话解读 | ✅ | 统计约束→LLM 润色, 防过度推断 |
| 桌面应用 | ✅ | PyWebView + SNLA.exe (78MB) |
| 多渠道 | ✅ | MCP Server, OpenClaw Skill |

### 韧性 ✅

| 机制 | 状态 | 说明 |
|------|------|------|
| LLM 重试 | ✅ | 指数退避 1s/2s/4s, 跳过 4xx |
| 取消中断 | ✅ | SPSS 进程强制终止 + 临时文件清理 |
| 灰名单确认 | ✅ | 临时副本执行, 原始数据不可变 |
| Mock 模式 | ✅ | LLM_MOCK=true, 无 API Key 可运行 |
| RAG 知识库 | ✅ | 566 chunks, 20 commands, 增强语法修复 |
| 日志 | ✅ | logging 统一, 关键路径全覆盖 |

### 限制 ⚠️

| 限制 | 影响 | 建议 |
|------|------|------|
| 单用户设计 | 并发请求返回 409 | Flask 全局锁, 已知设计 |
| Windows 限定 | SPSS 绑定 Windows | Python 后端可跨平台, SPSS 不可 |
| 批量变量分析 | 不支持 Q1-Q10 语法 | P8 功能增强 |
| 会话不持久 | 重启丢失所有状态 | 设计选择 (MVP), 无 DB |
| Python/SPSS 数值差异 | 算法不同导致微小差异 | 文档声明, 未来加 tolerance |
| 无用户认证 | API 无鉴权 | localhost 单用户, 可接受 |

---

## 三、环境准备

### 必需

```powershell
# 1. Python 3.10+
python --version

# 2. 虚拟环境 + 依赖
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# 3. 配置
copy .env.example .env
```

### .env 关键配置

```ini
# LLM (必需, 或用 LLM_MOCK=true 跳过)
LLM_ENDPOINT=https://opencode.ai/zen/go/v1/chat/completions
LLM_API_KEY=your-key-here
LLM_MODEL=deepseek-v4-flash

# SPSS (可选, Python 后端可替代)
SPSS_PATH=C:\Program Files\IBM\SPSS\Statistics\26\stats.exe
SPSS_PYTHON_PATH=C:\Program Files\IBM\SPSS\Statistics\26\Python3\python.exe
SPSS_EXEC_MODE=python

# 后端选择
STATS_BACKEND=spss    # "spss" | "python" | "auto"

# 开发模式 (无 LLM 可用)
LLM_MOCK=true         # 返回确定性 mock 响应
SKIP_RAG=true         # 禁用 RAG 知识库
```

### 测试数据

| 文件 | 大小 | 用途 |
|------|------|------|
| `data/fixtures/test_data.sav` | 小 | 主测试数据 (gender, score, class, age) |
| `data/fixtures/airline.sav` | 25K 行 | 大规模真实数据 |
| `data/fixtures/test_data_extended.sav` | 中 | 扩展测试 |
| `data/fixtures/test_data_boundary.sav` | 小 | 边界条件 |

---

## 四、真人测试步骤

### 测试 1: 快速验证 (5 分钟, 无需 SPSS/LLM)

```powershell
# 1. 运行全部测试
python -m pytest snla/tests/ -v

# 2. MCP 集成测试
python scripts/mcp_integration_test.py

# 预期: 87 pass + 7/7 MCP pass
```

### 测试 2: Mock 模式启动 (10 分钟, 无需 LLM Key)

```powershell
# .env 设置
LLM_MOCK=true
STATS_BACKEND=python

# 启动 Flask 服务器
python snla/ui/server.py

# 浏览器访问 http://localhost:8501
```

**验证清单**:
- [ ] 页面加载无报错
- [ ] 上传 `data/fixtures/test_data.sav` → 显示变量列表
- [ ] 输入 "比较男女成绩差异" → 返回分析结果
- [ ] 输入 "显示成绩的描述统计" → 返回描述统计
- [ ] 点击取消按钮 → 状态恢复
- [ ] 设置页面 → 可修改配置

### 测试 3: 真实 LLM 验证 (需要 API Key)

```powershell
# .env 设置
LLM_MOCK=false
LLM_API_KEY=<你的Key>
STATS_BACKEND=python

# 启动 + 测试
python scripts/verify_combined.py
```

**预期**: 65 例验证通过, 方法匹配率 > 90%

### 测试 4: SPSS 真实执行 (需要安装 SPSS)

```powershell
# .env 设置
STATS_BACKEND=spss
SPSS_PATH=C:\Program Files\IBM\SPSS\Statistics\26\stats.exe

# 启动桌面应用
python launcher.py

# 或仅 API
python snla/ui/server.py
```

**验证清单**:
- [ ] SPSS 自动检测 → 显示版本号
- [ ] 上传数据 → 正常解析
- [ ] t 检验 → SPSS 执行成功
- [ ] ANOVA → SPSS 执行成功
- [ ] 灰名单: 输入 "计算新变量 score_z = (score - 均值)" → 弹出确认对话框
- [ ] 确认灰名单 → 临时副本执行, 原始文件不变
- [ ] 导出 Word → 下载 .docx

### 测试 5: MCP 多渠道 (需要 OpenClaw)

```powershell
# 配置 OpenClaw
openclaw mcp set snla --command python --args "snla/mcp_server.py"

# 或在 Claude Desktop 中配置 MCP
# 7 个工具应自动发现
```

**验证清单**:
- [ ] `snla_status` → 返回服务器状态
- [ ] `snla_upload` → 上传数据文件
- [ ] `snla_analyze` → 自然语言分析
- [ ] `snla_confirm` → 灰名单确认
- [ ] `snla_cancel` → 取消分析
- [ ] `snla_export` → 导出报告

### 测试 6: 边界条件

| 测试 | 操作 | 预期 |
|------|------|------|
| 空输入 | 不输入文字点分析 | 400 "Empty input" |
| 未上传数据 | 直接输入查询 | 400 "upload first" |
| 并发请求 | 两个 tab 同时分析 | 409 "already running" |
| 大文件 | 上传 >500MB | 413 拒绝 |
| 非法文件 | 上传 .txt | 400 拒绝 |
| 取消中分析 | 分析执行中点取消 | SPSS 进程终止, 状态恢复 |
| LLM 超时 | 断网后分析 | 指数退避重试 → 超时报错 |
| 无 SPSS | STATS_BACKEND=python | 自动降级, 11/12 方法可用 |
| 非法语法 | 注入 DELETE/SHELL | 黑名单拦截 |
| 敏感变量 | 变量名含 "患者姓名" | 自动脱敏 var_01 |

---

## 五、常用命令速查

```powershell
# 测试
python -m pytest snla/tests/ -v                    # 全量 (110 tests)
python -m pytest snla/tests/ -v -m "not slow"     # CI-safe (108 pass + 2 xfail)
python -m pytest snla/tests/test_server.py -v     # API 测试 (23 tests)
python scripts/mcp_integration_test.py             # MCP 测试 (7 tests)

# 启动
python launcher.py                                 # 桌面应用
python snla/ui/server.py                          # Flask API only
python snla/mcp_server.py                         # MCP stdio server

# 验证
python scripts/verify_combined.py                  # 65 例真实 LLM
python scripts/verify_50_cases.py --mock          # 50 例 Mock 语法

# 代码质量
python -m ruff check snla/                         # Lint
python -m ruff format snla/                        # Format

# 打包
pyinstaller snla.spec --noconfirm                  # → dist/SNLA.exe
```

---

## 六、已知问题

| # | 问题 | 严重度 | 状态 |
|---|------|--------|------|
| 1 | SPSSExecutor type hint 未导入 (F821) | Low | 已知, 不影响运行 |
| 2 | 单用户并发锁 → 409 | Medium | 设计限制, 非 Bug |
| 3 | 会话不持久化 | Medium | MVP 设计选择 |
| 4 | Python/SPSS 数值微小差异 | Low | 算法差异, 需文档化 |
| 5 | RAG 知识库无自动更新 | Low | 手动 build_kb.py |

---

## 七、P8 建议

| 优先级 | 任务 | 工时 |
|--------|------|------|
| 高 | 批量变量分析 (Q1-Q10 语法) | 4h |
| 中 | 会话持久化 (SQLite) | 4h |
| 中 | /api/health 端点 (深度检查) | 1h |
| 低 | 多用户支持 (移除全局锁) | 8h |
| 低 | i18n 英文界面 | 4h |
| 低 | Prometheus metrics | 2h |
| — | 项目重命名决策 (StatsTalk) | 决策 + 35min |
