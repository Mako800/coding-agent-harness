# SPEC_PROCESS.md — 规约与计划生成过程

> 本文档记录与 Superpowers 协作生成 SPEC.md 与 PLAN.md 的全过程，包括 brainstorming 关键节点、关键迭代、AI 建议的采纳/推翻，以及冷启动验证结果。

---

## 一、Brainstorming 关键节点

### 节点 1：项目类型确认

**智能体追问：** "你选的是 Project A: Coding Agent Harness——自己从头构建一个智能体编排系统。"

**我的决策：** 确认选择 Project A。这个项目类型最契合课程命题——"用一个 harness（Superpowers）去造另一个 harness"，能形成第一手的批判性理解。

### 节点 2：语言选型

**智能体追问：** "你打算用哪门语言实现？"

**我的决策：** Python。理由是语法简洁、生态丰富（openai/keyring/pyyaml 库成熟）、学生熟悉。智能体未提出异议。

### 节点 3：重点维度选择

**智能体追问：** "你打算把哪个维度作为'主要贡献'做深？"

**我的决策过程：** 我问"哪个最简单"。智能体推荐**治理（护栏/沙箱/HITL）**，理由是：
- 实现简单直接：一个 `guardrail()` 函数配上模式匹配
- 天然可单测：`guardrail(Action("rm -rf /"))` → 断言拦截
- 评分性价比最高：作业建议"治理"作为重点维度

**我采纳了**这个推荐。事后证明这是正确的——治理的三层机制（检测/HITL/围栏）在 review 时确实暴露了真实安全问题（safe-side default、path containment），体现了工程深度。

### 节点 4：LLM 供应商

**智能体追问：** "真实 LLM 你打算接哪家？"

**我的决策：** DeepSeek。智能体确认 DeepSeek 兼容 OpenAI API 格式，LLM 抽象层设计成 OpenAI-compatible 即可对接。

### 节点 5：使用场景

**智能体追问：** "你希望这个 harness 的核心使用场景是什么？"

**我的决策：** CLI 对话模式（类似 OpenCode/Claude Code）。这决定了 Agent Loop 的设计——REPL 循环 + 自然语言指令。

### 节点 6：架构方案

**智能体提出 2 种方案：**
- 方案 A：单体架构（6 模块一一对应作业 6 维度）
- 方案 B：事件驱动架构（Dispatcher → Event Bus → Handlers）

**我选择方案 A**，因为方案 B 对个人项目来说过度工程。智能体也推荐 A。

---

## 二、至少 3 轮关键迭代

### 迭代 1：Guardrail "其余工具默认 PASS" 的歧义

**问题：** SPEC 初稿中 Guardrail 第一层写"其余工具默认 PASS"，但第三层（范围围栏）又检查 read/write/glob/grep 的路径。这看起来矛盾。

**处理：** 修改为"第一层只检查 bash 工具的 command 参数；read/write/glob/grep 由第三层（范围围栏）检查"。明确了各层职责划分。

### 迭代 2：LLM 动作协议未定义

**问题：** SPEC 初稿没有说明 LLM 如何返回动作——Agent Loop 怎么知道 LLM 想调用工具？

**处理：** 增加了"LLM 动作协议"一节，定义了 `<action name="X" args='{"k":"v"}' />` 的 XML 标签格式，以及解析失败时回灌错误让 LLM 重试（最多 3 次）的策略。

### 迭代 3：Guardrail safe-side default（review 驱动）

**问题：** Task 5 实现后，reviewer 发现 unknown bash 命令默认返回 PASS，违反了全局约束"unknown → HITL_PENDING"。

**处理：** 增加 `allowed_commands` 白名单概念（ls/cat/pytest/python 等安全命令），unknown 命令默认 HITL_PENDING。这是 brainstorming 阶段未预见到的——SPEC 写的是"其余 → PASS"，但全局约束要求 safe-side。review 机制捕获了这个矛盾。

---

## 三、AI 建议的采纳与推翻

### 采纳的建议
1. **推荐治理作为重点维度** — AI 推荐，我采纳，事后证明正确
2. **单体架构方案 A** — AI 推荐，我采纳，6 模块对应 6 维度评审清晰
3. **keyring + .env 凭据方案** — AI 提出，我采纳
4. **safe-side default** — reviewer 发现，AI 修复，我确认

### 推翻/修正的建议
1. **"其余 → PASS"** — SPEC 初稿的措辞，reviewer 发现违反全局约束，修正为 safe-side
2. **`str.startswith` 路径检查** — brief 中的代码，reviewer 发现可被 sibling 目录逃逸，修正为 `Path.parents` 检查

---

## 四、冷启动验证（§4.5）

### 操作

用与主开发智能体（OpenCode + Superpowers）不同的 agent，在不提供对话历史的前提下，仅凭 SPEC.md + PLAN.md 尝试实现 Task 8（ToolRegistry）。

**第二个智能体：** GitHub Copilot CLI（全新 session，不导入任何先前会话或 memory）

### 结果

**第二个 agent 暴露的 SPEC 缺陷：**

1. **"5 个预设工具"的参数格式不明确** — Copilot 问："grep 工具的 path 参数是必填还是可选？" SPEC 写的是 `grep(pattern, path)` 但没说 path 是否必填。**修订：** 在 PLAN.md 的 tools.py 实现中明确 `path = args.get("path", ".")`（可选，默认当前目录）。

2. **ToolRegistry.execute 的返回类型** — Copilot 问："execute 返回 ToolResult，但如果工具函数抛异常怎么办？" SPEC 只说"工具异常被捕获，作为 stderr 回灌"，没说 exit_code 是什么。**修订：** PLAN.md 明确 `exit_code=1` 用于工具异常。

3. **make_default_registry() 未在 SPEC 中提及** — Copilot 问："测试里用 `make_default_registry()`，但 SPEC 的功能规约里没有这个函数。" **修订：** 这是 PLAN.md 新增的工厂函数，SPEC 的功能规约只描述了 ToolRegistry 类，工厂函数是实现细节。

### 修订 diff

```diff
- grep(pattern, path) → 匹配行列表
+ grep(pattern, path=".") → 匹配行列表（path 可选，默认当前目录）

- 错误处理 | 工具异常被捕获，作为 stderr 回灌
+ 错误处理 | 工具异常被捕获，exit_code=1，stderr=异常信息
```

### 反思

冷启动验证确实暴露了 spec 的隐性假设。最常见的问题是"参数是否必填"和"异常时的 exit_code"——这些在主 agent 的对话上下文里是"显然的"，但写进 SPEC 时被遗漏了。这验证了作业的核心论点：**你和主 agent 沉淀的共享上下文会让你严重高估 spec 的清晰度。**

---

## 五、对 brainstorming 技能的反思

### 做得好的地方
- **逐一提问**：一次只问一个问题，不让用户被信息淹没
- **方案对比**：提出 2-3 种方案并给出推荐，降低决策成本
- **分块确认**：每个模块设计后单独确认，避免一次性呈现过多内容

### 让我不满的地方
- **未主动追问边界条件**：brainstorming 产出的 SPEC 在参数必填性、异常 exit_code 等细节上留白，直到冷启动验证才暴露
- **未交叉检查全局约束**：SPEC 写"其余 → PASS"与全局约束"unknown → HITL_PENDING"矛盾，brainstorming 阶段未发现，直到 review 才捕获
- **LLM 动作协议后补**：这是 Agent Loop 的核心接口，但 brainstorming 阶段未主动追问"LLM 怎么告诉 harness 它要调用工具"
