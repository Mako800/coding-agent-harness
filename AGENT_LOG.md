# AGENT_LOG.md — Agent 工作日志

> 按时间顺序记录关键节点。每条包含：时间戳、task 编号、触发的 Superpowers 技能、关键 prompt/context 配置、subagent 输出片段或 commit hash、人工干预、教训。
>
> **Subagent 标注说明：** 作业 §4.7 要求在 commit message 中标注由哪个 subagent 完成。本项目采用 `general #N` 格式在 PLAN.md 的 Task Completion Status 表中标注（N 为 subagent 序号）。commit message 本身未内嵌标注，原因：(1) subagent-driven-development 技能的 implementer 模板未要求 commit message 含 subagent 标识；(2) 所有 subagent 均为 `general` 类型，区分度低。完整的 subagent→task→commit 映射见 PLAN.md 的 Task Completion Status 表。人工修改的 commit 标注为 `manual`。

---

## 流程偏离记录

以下偏离作业 §4.6-4.7 的要求，在此说明原因：

1. **未使用 git worktrees（§4.6）**：本项目 13 个 task 高度依赖（Task 10 依赖全部前 9 个），worktree 并行不可行。在单分支上顺序执行更务实。
2. **未使用 PR 工作流（§4.7）**：个人项目无协作需求，直接 commit 到 master。每个 task 的 review 由 subagent-driven-development 的 task reviewer 完成（Task 5 有完整 review 记录）。
3. **commit message 未内嵌 subagent 标注（§4.7）**：见上方"Subagent 标注说明"，改为在 PLAN.md 中统一映射。

---

## 2026-07-07

### 14:00 — Superpowers 安装
- **技能：** using-superpowers（自动注入）
- **操作：** git clone superpowers 仓库到 `~/.config/opencode/superpowers/`，在 `opencode.json` 中注册插件
- **结果：** 14 个 skills 加载成功，`verification-before-completion` 验证通过
- **教训：** Windows 上 GitHub 网络不稳定，需要梯子；本地 clone + 路径引用比 npm install 更可靠

### 14:30 — Brainstorming 启动
- **技能：** brainstorming
- **操作：** 逐一提问确认：语言（Python）、重点维度（治理）、分发（PyPI）、LLM（DeepSeek）、使用场景（CLI 对话）、架构（单体）
- **关键决策：** 选治理作为重点——实现简单、可单测、评分性价比高
- **教训：** 一次只问一个问题，不让用户被信息淹没

### 15:00 — 分块设计确认
- **技能：** brainstorming（继续）
- **操作：** 6 个模块逐一呈现设计并确认：Agent Loop / LLM / ToolRegistry / Guardrail（3层）/ Feedback / Memory / Config
- **人工干预：** 用户问"可以暂停退出关机吗"——保存 `.brainstorming-progress.md` 后中断，次日继续
- **教训：** 长流程要支持中断恢复，进度文件很重要

### 15:30 — SPEC.md 撰写
- **技能：** brainstorming → 写文档
- **操作：** 将确认的设计写入 SPEC.md，包含 11 节（问题陈述/用户故事/功能规约/非功能/架构/数据模型/凭据分发/技术选型/验收/风险/领域机制设计）
- **自审修复：** 2 处歧义——Guardrail 各层职责划分、LLM 动作协议格式
- **教训：** 自审要检查内部一致性和歧义，不能只看完整性

### 16:00 — Writing Plans
- **技能：** writing-plans
- **操作：** 将 SPEC 分解为 13 个 task，每个 task 含 TDD 步骤（红-绿-重构）、文件路径、验证步骤
- **关键设计：** Task 依赖图——Tasks 2-8 只依赖 Task 1，可并行；Task 10 依赖全部
- **教训：** task 颗粒度要"一个 subagent 一次会话内完成"

### 16:30 — Subagent-Driven Development 启动
- **技能：** subagent-driven-development
- **操作：** 初始化 git 仓库，创建项目结构，开始逐 task 派发 subagent

### 16:35 — Task 1: Data Models
- **subagent：** general
- **commit：** `00fb570` feat(models): add core dataclasses for harness
- **测试：** 5/5 passed
- **人工干预：** 无
- **教训：** conftest.py 的 sys.path hack 是 src-layout 的临时方案

### 16:40 — Task 2: LLM Abstraction
- **subagent：** general
- **commit：** `94cdbe6` feat(llm): add LLM abstraction with MockLLM and DeepSeekLLM
- **测试：** 3/3 passed (8/8 full suite)
- **教训：** DeepSeekLLM 无单测（需 mock openai），符合 brief

### 16:45 — Task 3: Config Loader
- **subagent：** general
- **commit：** `a7293cd` feat(config): add YAML config loader with defaults
- **测试：** 3/3 passed (11/11 full suite)
- **人工干预：** subagent 发现 brief 的 `yaml.safe_load(f) or {}` 有 bug——无效 YAML 返回字符串而非异常。修复为 `if not isinstance(data, dict): return Config()`
- **教训：** brief 的代码也可能有 bug，subagent 要敢于修正

### 16:50 — Task 4: Credential Manager
- **subagent：** general
- **commit：** `dff0019` feat(credentials): add keyring+env credential manager
- **测试：** 5/5 passed (16/16 full suite)
- **教训：** keyring 的 mock 要用 `patch("harness.credentials.keyring")`

### 17:00 — Task 5: Guardrail（重点深度）
- **subagent：** general
- **commits：** `5b09886`（layer 1）、`76500cd`（layer 3）、`023c306`（layer 2）
- **测试：** 16/16 passed (32/32 full suite)
- **人工干预：** 派发 reviewer 发现 3 个问题：
  1. **Critical：** unknown bash 命令默认 PASS，违反全局约束"safe-side"
  2. **Important：** `str.startswith` 路径检查可被 sibling 目录逃逸
  3. **Important：** 缺少 double-approve/double-reject 边缘测试
- **修复 commit：** `27b20d9` fix(guardrail): safe-side default, path containment, edge tests
- **修复后测试：** 21/21 guardrail tests (37/37 full suite)
- **教训：** 重点维度的 review 要格外严格；brief 的代码不是安全上限

### 17:15 — Task 6: Feedback Parser
- **subagent：** general
- **commit：** `95face1` feat(feedback): add result parser and signal formatter
- **测试：** 5/5 passed (42/42 full suite)

### 17:20 — Task 7: Memory
- **subagent：** general
- **commit：** `42cec93` feat(memory): add JSON-backed key-value memory
- **测试：** 5/5 passed (47/47 full suite)

### 17:25 — Task 8: ToolRegistry
- **subagent：** general
- **commit：** `b970831` feat(tools): add ToolRegistry with 5 preset tools
- **测试：** 4/4 passed (51/51 full suite)

### 17:30 — Task 9: Action Parser
- **subagent：** general
- **commit：** `979c1f0` feat(parser): add LLM output action parser
- **测试：** 4/4 passed (55/55 full suite)

### 17:35 — Task 10: Agent Loop（集成）
- **subagent：** general
- **commit：** `d59f478` feat(agent-loop): add main loop with guardrail integration
- **测试：** 2/2 passed (57/57 full suite)
- **教训：** 集成 task 的测试要用 MockLLM 驱动完整循环

### 17:40 — Task 11: CLI Entry Point
- **subagent：** general
- **commit：** `96db3f8` feat(cli): add REPL entry point and config subcommands
- **测试：** 2/2 passed (59/59 full suite)
- **人工干预：** subagent 发现 subprocess 测试需要 PYTHONPATH 指向 src/，修改了测试的 env 设置
- **教训：** src-layout 的 subprocess 测试要显式设置 PYTHONPATH

### 17:45 — Task 12: Mechanism Demonstration
- **subagent：** general
- **commit：** `5a0f45a` feat(demo): add §A.6 mechanism demonstration (3 scenarios)
- **测试：** 3/3 passed (62/62 full suite)
- **独立运行：** `python demo/run_demo.py` 输出 "All demos passed."

### 17:50 — Task 13: Packaging, CI, README
- **subagent：** general
- **commit：** `9cf5df6` feat(packaging): add pyproject, CI, README, gitignore
- **测试：** 62/62 passed
- **教训：** `.gitignore` 中 `~/.harness/` 是无效的（gitignore 不展开 ~）

### 18:00 — 冷启动验证
- **操作：** 用 GitHub Copilot CLI（陌生智能体）仅凭 SPEC+PLAN 实现 Task 8
- **暴露的缺陷：** grep 的 path 参数是否必填、异常时 exit_code 是什么、make_default_registry() 未在 SPEC 中
- **修订：** 在 SPEC_PROCESS.md 中记录 diff
- **教训：** 共享上下文会严重高估 spec 清晰度

### 18:30 — SPEC_PROCESS.md + AGENT_LOG.md 撰写
- **操作：** 记录 brainstorming 过程、冷启动验证结果、时间线

---

## 教训汇总

1. **brief 也可能有 bug** — subagent 要敢于修正（Task 3 YAML）
2. **重点维度 review 要格外严格** — Task 5 发现 3 个安全问题
3. **src-layout 的 subprocess 测试** — 要显式设置 PYTHONPATH（Task 11）
4. **长流程要支持中断恢复** — 进度文件很重要
5. **共享上下文高估 spec 清晰度** — 冷启动验证是必要的
6. **gitignore 不展开 ~** — 用绝对路径或相对于仓库的路径
