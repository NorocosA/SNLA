# StatsTalk 人工验证指南

> 项目路径: `D:\Projects\StatsTalk` | Python 3.10+

---

## 一、环境准备（5 分钟）

```powershell
cd D:\Projects\StatsTalk

# 1. 虚拟环境
python -m venv venv
venv\Scripts\activate

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置文件
copy .env.example .env
```

编辑 `.env`，确保以下配置：
```ini
LLM_MOCK=true           # 先用 mock 模式，无需 API Key
STATS_BACKEND=python    # 无需 SPSS
```

---

## 二、快速验证：跑测试（1 分钟）

```powershell
# 全部 CI-safe 测试（87 tests）
python -m pytest snla/tests/ -v -m "not slow"
```

**预期输出**：
```
====================== 86 passed, 1 deselected in ~1s =======================
```

如果有失败，检查是否缺少依赖：`pip install flask lxml pingouin matplotlib`

---

## 三、Mock 模式启动 Web 界面（5 分钟）

```powershell
# 启动 Flask 服务器
python snla/ui/server.py
```

浏览器打开 **http://localhost:8501**

### 测试流程：

| 步骤 | 操作 | 预期结果 |
|------|------|----------|
| 1 | 点击 "选择文件"，上传 `data/fixtures/test_data.sav` | 显示 4 个变量：gender, score, class, age |
| 2 | 输入框键入 "**比较男女成绩差异**"，点分析 | 返回 t 检验结果（Mock 模式下会有分析结果） |
| 3 | 输入 "**显示成绩的描述统计**"，点分析 | 返回均值、标准差等 |
| 4 | 输入 "**成绩和年龄的相关性**"，点分析 | 返回相关系数 |
| 5 | 点击 **取消** 按钮 | 状态恢复 |
| 6 | 点击 **设置** | 可修改 LLM 配置 |
| 7 | 分析完成后点击 **导出 Word** | 下载 .docx 报告 |

### 验证灰名单流程：
| 步骤 | 操作 | 预期 |
|------|------|------|
| 1 | 输入 "**计算新变量 z_score = (score - 70) / 10**" | 弹出确认对话框 |
| 2 | 点击 **取消** | 不执行 |
| 3 | 重新输入并点击 **确认执行** | 在临时副本执行，原始文件不变 |

---

## 四、真实 LLM 验证（需要 API Key）

修改 `.env`：
```ini
LLM_MOCK=false
LLM_API_KEY=你的Key
```

```powershell
# 65 例真实 LLM 验证
python scripts/verify_combined.py
```

**预期**: 方法匹配率 > 90%，无崩溃。

或手动测试：
```powershell
python snla/ui/server.py
# 浏览器访问，输入真实查询如：
# "比较不同班级的成绩是否有显著差异"
# "成绩分布是什么样的"
# "性别和班级是否相关"
```

---

## 五、MCP Server 验证（2 分钟）

```powershell
# 集成测试
python scripts/mcp_integration_test.py
```

**预期输出**：
```
[import]         PASS
[tool_count]     PASS
[tool_names]     PASS
[error_format]   PASS
[engine_busy_format] PASS
[session_isolation] PASS
[status_tool]    PASS
----------------------------------------
  7 tests: 7 passed, 0 failed
```

---

## 六、Python 后端验证（无需 SPSS）

```powershell
# Python 后端 24 个单元测试
python -m pytest snla/tests/test_python_backend.py -v
```

**预期**: 22 passed, 2 xfailed（卡方 expected.values bug，已知问题）。

---

## 七、Flask API 验证

```powershell
# API 端点 23 个测试
python -m pytest snla/tests/test_server.py -v
```

**预期**: 23 passed。

---

## 八、边界条件测试

| 测试 | 操作 | 预期 |
|------|------|------|
| 空输入 | 不输入文字点分析 | 400 "Empty input" |
| 未上传数据 | 直接输入查询 | 400 "upload first" |
| 超长输入 | 输入 3000+ 字 | 400 "输入文本过长" |
| 大文件 | 上传 >500MB | 413 拒绝 |
| 非法文件 | 上传 .txt | 400 拒绝 |
| 连续快速请求 | 1 分钟内点 11 次分析 | 第 11 次 429 "请求过于频繁" |
| 敏感变量 | 上传含 "患者姓名" 的数据 | 自动脱敏为 var_01 |
| 批量变量 | 输入 "分析 Q1 到 Q5" | 范围自动展开 |

---

## 九、代码质量检查

```powershell
# Lint
python -m ruff check snla/

# Format
python -m ruff format snla/ --check
```

---

## 十、常见问题

| 问题 | 解决方案 |
|------|----------|
| `ModuleNotFoundError: flask` | `pip install flask` |
| `ModuleNotFoundError: lxml` | `pip install lxml` |
| 端口 8501 被占用 | 修改 `server.py` 末尾 `port=8501` |
| Mock 模式无返回 | 检查 `.env` 中 `LLM_MOCK=true` |
| 中文乱码 | 确认 `.env` 文件编码为 UTF-8 |
| PyWebView 窗口不显示 | 安装 Edge WebView2 Runtime |

---

**快速启动一句话**：
```powershell
cd D:\Projects\StatsTalk && venv\Scripts\activate && python -m pytest snla/tests/ -q -m "not slow" && python snla/ui/server.py
```
