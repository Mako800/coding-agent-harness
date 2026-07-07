# SPEC.md — Coding Agent Harness

> 项目类型：A · Coding Agent Harness
> 主攻维度：治理（护栏 / 沙箱 / HITL 状态机 / 范围围栏）
> 文档版本：v1.0 · 2026-07-07

---

## 1. 问题陈述

### 1.1 要解决什么问题

当前主流的编码智能体（Claude Code、OpenCode、Cursor 等）都内置了 agent loop、工具系统、治理机制。但这些机制藏在框架内部，使用者难以理解其工作原理，也难以定制。

本项目从零构建一个最小但完整的 Coding Agent Harness，让使用者：

- **看清 agent 内部如何运转**：主循环、工具分发、治理拦截、反馈回灌，每一环都是显式代码，可读、可改、可测。
- **用确定性代码守护安全边界**：危险动作拦截不靠提示词，而是 `guardrail()` 函数硬编码的规则与状态机。
- **以可单测的方式验证机制**：移除真实 LLM 后，每个核心机制仍能用 mock 驱动的单元测试验证。

### 1.2 目标用户

- 学习 AI4SE 课程、希望理解 agent harness 内部原理的学生
- 想要一个可定制、可审计的轻量编码 agent 的开发者
- 对 agent 治理机制（护栏、HITL）感兴趣的研究者

### 1.3 为什么值得做

当 LLM 能完成大部分编码工作时，工程师的真正价值落在 harness 这层工程：治理、反馈、上下文、安全、分发。本项目通过亲手实现一个 harness，让学生对"一个可靠的系统到底需要哪些工程"形成第一手理解，而不是停留在调用现成框架的层面。

---

## 2. 用户故事

遵循 INVEST 原则（Independent / Negotiable / Valuable / Estimable / Small / Testable）。

### US-1：启动 CLI 对话
**作为**开发者，**我想**在终端运行 `harness` 命令进入对话模式，**以便**用自然语言指挥 agent 完成编码任务。
- 验收：`harness` 启动后显示提示符，输入消息后 agent 响应。

### US-2：执行文件读写
**作为**开发者，**我想**让 agent 读写我指定目录下的文件，**以便**让它查看和修改我的代码。
- 验收：agent 调用 `read`/`write` 工具，文件内容正确读写。

### US-3：执行 shell 命令
**作为**开发者，**我想**让 agent 执行 shell 命令（如 `pytest`、`ls`），**以便**它能运行测试和探查环境。
- 验收：agent 调用 `bash` 工具，stdout/stderr/exit_code 回灌。

### US-4：危险命令被拦截
**作为**开发者，**我想** agent 执行 `rm -rf /` 这类高危命令时被自动拦截，**以便**保护我的系统不被破坏。
- 验收：`guardrail(Action(command="rm -rf /"))` 返回 `BLOCK`，命令不执行。

### US-5：可疑命令需人工确认
**作为**开发者，**我想** agent 执行 `rm somefile` 这类可疑命令时暂停并询问我，**以便**我对危险动作有最终决定权。
- 验收：`guardrail` 返回 `HITL_PENDING`，CLI 打印动作详情并等待 y/N 输入。

### US-6：跨会话记忆
**作为**开发者，**我想** agent 记住我上一次告诉它的项目约定（如"用 pytest"），**以便**新会话不用重复说明。
- 验收：`memory.store("test_framework", "pytest")` 后，新会话启动时该信息出现在系统提示中。

### US-7：配置驱动行为
**作为**开发者，**我想**通过 YAML 配置文件约束 agent 的行为（白名单目录、拦截规则），**以便**不同项目用不同安全策略。
- 验收：修改 `config.yaml` 的 `blocked_commands` 后，新会话立即应用新规则。

---

## 3. 功能规约（按模块）

### 3.1 Agent Loop（主循环）

| 项 | 说明 |
|----|------|
| 输入 | 用户消息（str） |
| 行为 | 组装上下文 → 调 LLM → 解析动作 → 过 Guardrail → 执行工具 → Feedback 解析 → 回灌 → 停机判断 |
| 输出 | 工具执行结果 + LLM 最终回答 |
| 边界 | 单次用户消息触发最多 20 次工具调用，超出则停机 |
| 错误处理 | LLM 调用失败 → 打印错误并退出循环；工具异常 → stderr 回灌给 LLM |

**停机条件：**
- LLM 返回 `<FINAL_ANSWER>` 标记
- 用户输入 `exit` / `quit` 或 Ctrl+C
- 达到单次用户消息的工具调用上限（20）

**LLM 动作协议：**
LLM 返回的文本中，动作以特定格式标记，Agent Loop 解析为 `Action`：
```
<action name="bash" args='{"command": "ls -la"}' />
```
- 解析失败时回灌错误让 LLM 重试，最多 3 次
- 无动作标记的纯文本视为最终回答，循环结束

### 3.2 LLM 抽象层

| 项 | 说明 |
|----|------|
| 输入 | `messages: list[Message]`（role + content） |
| 行为 | 调用底层 LLM 返回文本响应 |
| 输出 | `str`（LLM 生成的文本） |
| 边界 | 单次调用超时 60s |
| 错误处理 | 网络错误重试 3 次，仍失败则抛 `LLMError` |

**实现：**
- `MockLLM`：接收预设回复列表，依次返回，用于单测。
- `DeepSeekLLM`：通过 `openai` Python 库调用 DeepSeek API（OpenAI-compatible）。

### 3.3 ToolRegistry（工具注册与分发）

| 项 | 说明 |
|----|------|
| 输入 | `Action(name, args)` |
| 行为 | 查找已注册工具 → 过 Guardrail → 执行 → 返回结果 |
| 输出 | `ToolResult(stdout, stderr, exit_code)` |
| 边界 | 未注册工具返回 `exit_code=-1`，stderr="unknown tool" |
| 错误处理 | 工具异常被捕获，作为 stderr 回灌 |

**预设工具：**
- `read(file_path)` → 文件内容
- `write(file_path, content)` → 写入确认
- `bash(command)` → stdout/stderr/exit_code
- `glob(pattern)` → 匹配文件列表
- `grep(pattern, path)` → 匹配行列表

### 3.4 Guardrail（治理核心 — 重点深度）

三层机制，每层都是确定性代码：

**第一层：危险命令检测**

| 项 | 说明 |
|----|------|
| 输入 | `Action(name, args)` |
| 行为 | 按规则匹配动作，返回 PASS / BLOCK / HITL_PENDING |
| 输出 | `GuardrailResult(decision, reason)` |
| 边界 | 第一层只检查 `bash` 工具的 command 参数；`read`/`write`/`glob`/`grep` 由第三层（范围围栏）检查 |
| 错误处理 | 规则加载失败 → 默认全部 HITL_PENDING（安全侧倒） |

规则分类（可配置）：
- `blocked_commands`：`rm -rf /`、`dd if=`、`format`、`mkfs`、`:(){:|:&};:` → **BLOCK**
- `hitl_commands`：`rm`、`sudo`、`DROP TABLE`、`ALTER TABLE`、`git push --force` → **HITL_PENDING**
- 其余 → **PASS**

**第二层：HITL 状态机**

```
状态：PENDING → APPROVED | REJECTED → (执行 | 拦截)
```

| 项 | 说明 |
|----|------|
| 输入 | `GuardrailResult(HITL_PENDING)` + 用户输入 |
| 行为 | 挂起 Agent Loop → 打印动作详情 → 等待 y/N → 转换状态 |
| 输出 | `APPROVED`（继续执行）或 `REJECTED`（拦截结果回灌 LLM） |
| 边界 | 超时 60s 无输入 → 默认 REJECTED |

**第三层：范围围栏**

| 项 | 说明 |
|----|------|
| 输入 | `Action` |
| 行为 | 检查 `read`/`write`/`glob`/`grep` 的 path 是否在 `allowed_directories` 内 |
| 输出 | 不在白名单 → BLOCK |
| 边界 | 默认 `allowed_directories = ["."]`（当前目录） |

### 3.5 Feedback（反馈信号解析）

| 项 | 说明 |
|----|------|
| 输入 | `ToolResult(stdout, stderr, exit_code)` |
| 行为 | 判定 SUCCESS / FAILURE / ERROR，构造自然语言摘要 |
| 输出 | `Signal(status, summary)` |
| 边界 | timeout / 文件不存在归为 ERROR |
| 错误处理 | 解析失败 → 默认 FAILURE |

### 3.6 Memory（跨会话记忆）

| 项 | 说明 |
|----|------|
| 输入 | `key, value`（store）或 `key`（recall） |
| 行为 | 读写 JSON 文件 `~/.harness/memory.json` |
| 输出 | 存储确认 / 检索值 |
| 边界 | 文件不存在时自动创建；单条 value 最大 4KB |
| 错误处理 | 文件损坏 → 备份后重建空 memory |

### 3.7 Config（配置）

| 项 | 说明 |
|----|------|
| 输入 | `~/.harness/config.yaml` |
| 行为 | 启动时加载，分发给各模块 |
| 输出 | `Config` 对象 |
| 边界 | 配置缺失 → 使用默认值 |
| 错误处理 | YAML 解析失败 → 打印错误并使用默认配置 |

---

## 4. 非功能性需求

### 4.1 性能
- 单轮工具调用延迟 < 5s（不含 LLM 响应时间）
- Memory 加载 < 100ms
- Guardrail 检查 < 10ms

### 4.2 安全（含凭据威胁模型）

**威胁模型：**

| 威胁 | 来源 | 对策 |
|------|------|------|
| API Key 泄露到 Git | 开发者误提交 | `.env` 加入 `.gitignore`；README 警告 |
| API Key 进入 shell history | 命令行 `export` | 通过 `.env` 文件加载；不使用 `export` |
| Agent 执行危险命令 | LLM 生成恶意/错误命令 | Guardrail 三层拦截 |
| Agent 读写敏感文件 | LLM 访问白名单外路径 | 范围围栏 |
| 进程环境变量被其他进程读取 | 共享主机 | 文档说明风险；推荐 keyring 存储 |

**凭据存储方案：**
- 主方案：`.env` 文件 + `python-dotenv` 加载（明文，文档说明风险）
- 增强方案：Windows Credential Manager / macOS Keychain / Linux Secret Service（通过 `keyring` 库）
- 首次运行引导：CLI 检测到无 key 时提示用户输入（隐藏输入），存入 keyring
- 查看/更新/清除：`harness config show-key`（显示状态不回显明文）、`set-key`、`clear-key`

### 4.3 可用性
- CLI 启动 < 2s
- 错误信息含修复建议
- HITL 提示清晰显示动作详情和风险等级

### 4.4 可观测性
- 每轮循环打印：[step N] tool=X decision=PASS/BLOCK/HITL exit=0
- 可选 `--verbose` 打印完整 LLM 请求/响应
- 日志写入 `~/.harness/harness.log`

---

## 5. 系统架构

### 5.1 组件图

```
┌─────────────────────────────────────────────────────┐
│                    CLI (main.py)                     │
│             用户输入 → agent loop → 输出              │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│                   Agent Loop                         │
│  组装上下文 → 调LLM → 解析动作 → 分发执行 → 回灌结果    │
│  → 停机判断                                          │
└──────┬──────┬──────┬──────┬──────┬──────────────────┘
       │      │      │      │      │
       ▼      ▼      ▼      ▼      ▼
   ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐
   │LLM │ │Tool│ │Guard│ │Feed│ │Mem │
   │层  │ │注册│ │rail │ │back│ │ory │
   └────┘ └────┘ └────┘ └────┘ └────┘
```

### 5.2 数据流

1. 用户输入 → Agent Loop
2. Agent Loop 组装上下文（含 Memory 摘要）→ 调 LLM
3. LLM 返回动作文本 → Agent Loop 解析为 `Action(name, args)`
4. Action → ToolRegistry 查找工具 → **先过 Guardrail**
5. Guardrail 判断：PASS 放行 / BLOCK 拦截 / HITL_PENDING 暂停等人工
6. 工具执行 → Feedback 解析结果
7. 结果回灌到下一轮 LLM 调用
8. 循环直到停机条件

### 5.3 外部依赖

| 依赖 | 用途 | 必需 |
|------|------|------|
| `openai` Python 库 | 调用 DeepSeek API | 是 |
| `python-dotenv` | 加载 `.env` 凭据 | 是 |
| `keyring` | OS 钥匙串存储（增强方案） | 否 |
| `pyyaml` | 配置文件解析 | 是 |
| DeepSeek API | 真实 LLM 调用 | 是（真实运行时） |

---

## 6. 数据模型

### 6.1 核心实体

```python
@dataclass
class Message:
    role: str          # "system" | "user" | "assistant" | "tool"
    content: str

@dataclass
class Action:
    name: str          # 工具名：read/write/bash/glob/grep
    args: dict         # 工具参数

@dataclass
class ToolResult:
    stdout: str
    stderr: str
    exit_code: int

@dataclass
class GuardrailResult:
    decision: str      # "PASS" | "BLOCK" | "HITL_PENDING"
    reason: str

@dataclass
class Signal:
    status: str        # "SUCCESS" | "FAILURE" | "ERROR"
    summary: str
```

### 6.2 存储文件

- `~/.harness/config.yaml` — 配置
- `~/.harness/memory.json` — 记忆（key-value 字典）
- `~/.harness/harness.log` — 运行日志

---

## 7. 凭据与分发设计

### 7.1 凭据存储方案

**首次运行引导：**
1. CLI 启动检测 `DEEPSEEK_API_KEY` 环境变量
2. 若无 → 提示 "未检测到 API Key，是否现在配置？[y/N]"
3. 用户输入 y → 隐藏输入读取 key → 存入 keyring
4. 后续运行优先从 keyring 读取，回退到 `.env`

**查看/更新/清除：**
- `harness config show-key` → 显示 "已配置 / 未配置"（不回显明文）
- `harness config set-key` → 隐藏输入新 key，覆盖
- `harness config clear-key` → 从 keyring 删除

**明文风险说明（写入 README）：**
- `.env` 为明文文件，进程环境变量对同主机其他进程可见
- 推荐使用 keyring 方案；`.env` 仅作为开发便利

### 7.2 分发形态：PyPI

- 包名：`coding-agent-harness`
- 安装：`pip install coding-agent-harness`
- 启动：`harness`（console_scripts 入口）
- 目标平台：跨平台（Windows / macOS / Linux）
- 依赖前提：Python 3.10+
- key 在目标机配置：首次运行引导或 `harness config set-key`

---

## 8. 技术选型与理由

| 选型 | 理由 |
|------|------|
| Python 3.10+ | 语法简洁，生态丰富，`openai`/`keyring`/`pyyaml` 库成熟；学生熟悉 |
| `openai` 库 | DeepSeek 兼容 OpenAI API 格式，无需单独 SDK |
| `python-dotenv` | `.env` 加载标准方案 |
| `keyring` | 跨平台 OS 钥匙串访问，一行代码存取 |
| `pyyaml` | 配置文件可读性好 |
| 单体架构 | 项目规模不需要分布式；6 模块一一对应作业 6 维度，评审清晰 |
| DeepSeek | 价格低、中文好、OpenAI-compatible |

本项目为纯 CLI，无前端，豁免 Open Design 要求。

---

## 9. 验收标准

| 功能 | 完成判定标准 |
|------|-------------|
| Agent Loop | `harness` 启动后能多轮对话，工具调用正确分发 |
| LLM 抽象层 | MockLLM 驱动下跑通完整循环；DeepSeekLLM 真实调用成功 |
| ToolRegistry | 5 个预设工具均可用，未注册工具返回错误 |
| Guardrail | `rm -rf /` 被 BLOCK；`rm file` 触发 HITL；白名单外路径被拦截 |
| Feedback | exit_code=0 → SUCCESS；非零 → FAILURE + stderr 摘要 |
| Memory | store 后 recall 返回正确值；新会话加载摘要注入系统提示 |
| Config | 修改 YAML 后行为变化；缺失配置使用默认值 |
| 凭据 | key 不出现在源码/Git/日志；首次运行引导可用 |
| 分发 | `pip install` 后 `harness` 命令可用 |
| 单测 | mock-LLM 驱动下所有核心机制可单测验证，不依赖网络 |

---

## 10. 风险与未决问题

| 风险 | 影响 | 缓解 |
|------|------|------|
| LLM 返回非预期格式 | Agent Loop 解析失败 | 解析失败时回灌错误让 LLM 重试，最多 3 次 |
| DeepSeek API 限流 | 真实运行中断 | 单测不依赖真实 API；文档说明限流对策 |
| 规则匹配漏判 | 危险命令未被拦截 | 默认安全侧倒（未知命令 HITL）；规则可配置扩展 |
| HITL 阻塞循环 | 用户不响应时卡死 | 60s 超时默认 REJECTED |
| Windows 路径差异 | 范围围栏路径匹配错误 | 统一用 `pathlib.Path` 规范化 |

---

## 11. 领域与机制设计（Project A 专属）

### 11.1 领域：Coding

### 11.2 四类机制

| 机制 | 设计 | 编码实现方式 |
|------|------|-------------|
| 动作/工具 | read/write/bash/glob/grep | `ToolRegistry` 类 + 工具函数注册 |
| 客观反馈信号 | exit_code + stderr 解析 | `Feedback.parse()` 确定性函数 |
| 危险动作 | 三层 Guardrail（检测/HITL/围栏） | `guardrail()` 函数 + 状态机 |
| 记忆 | JSON 文件 key-value | `Memory` 类自实现存储 |

### 11.3 重点维度：治理（Guardrail）

**为什么选治理：**
- 天然由代码构成，最契合 §A.4 "机制必须是代码" 要求
- 三层机制（检测 / HITL / 围栏）各有独立逻辑，深度足够
- 确定性极强，单测容易写：`guardrail(Action("rm -rf /"))` → BLOCK，每次都成立

**如何编码实现（呼应 §A.4）：**
- `guardrail(action)` 是纯函数，输入 Action 输出 GuardrailResult，不依赖 LLM
- HITL 状态机是显式状态转换代码，mock 用户输入即可验证
- 范围围栏是路径匹配代码，`pathlib.Path` 比较
- 移除 LLM 后，三层机制全部可单测验证

### 11.4 机制演示（§A.6）

将提交可重复运行的演示脚本，在 MockLLM 下确定性复现：
1. **治理护栏拦截危险动作**：MockLLM 返回 `bash("rm -rf /")` → Guardrail 返回 BLOCK → 命令不执行
2. **反馈闭环驱动自我修正**：MockLLM 第一次返回错误命令 → Feedback 解析 FAILURE → 回灌后第二次返回正确命令
3. **重点维度行为**：HITL 状态机 — MockLLM 返回 `bash("rm file")` → Guardrail 返回 HITL_PENDING → mock 用户输入 "y" → 状态转为 APPROVED → 执行
