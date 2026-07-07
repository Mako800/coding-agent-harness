# REFLECTION.md — 反思报告

> 本反思报告由学生本人撰写，AI 辅助润色已标注。

## 一、哪些 Superpowers 技能发挥了最大作用

**brainstorming** 是发挥最大的技能。它通过"一次只问一个问题"的方式，逼我把模糊想法变成明确设计。最典型的例子是重点维度选择——我问"哪个最简单"，智能体推荐治理并给出理由（实现简单、可单测、评分性价比高），我采纳后事实证明这是正确的。如果没有这个逐一提问的流程，我很可能会六个维度都浅尝辄止。

**subagent-driven-development** 是第二有用的技能。每个 task 派一个新鲜 subagent，context 不污染，质量有保障。最关键的是它强制了 review 机制——Task 5（Guardrail）的 reviewer 发现了 3 个真实安全问题（safe-side default、path containment、缺少边缘测试），这些问题如果靠我自己检查很可能漏掉。

**test-driven-development** 作为硬性要求，确保了每个模块都有测试。66 个测试全部用 MockLLM 驱动，不依赖网络和真实 LLM，这正好满足了作业 §A.6 的"确定性单元测试"要求。

**verification-before-completion** 在最后阶段发挥了作用——它提醒我"没有跑验证就不能宣称完成"，让我在每次说"done"之前都先跑 `pytest -v` 确认。

## 二、哪些技能"形式大于实质"

**using-git-worktrees** 在我的项目中形式大于实质。作业要求每个独立功能开一个 worktree 对应一个 PR，但我的项目是全新的、13 个 task 高度依赖的单体架构，worktree 隔离反而会增加合并冲突的成本。我最终在单个分支上顺序执行了所有 task，这在个人项目、模块高度耦合的情况下是更务实的选择。

**writing-skills** 完全没有用到——我的项目不需要创建自定义 skill。

## 三、TDD 强制在 AI 协作下是阻碍还是放大器

**TDD 是放大器，不是阻碍。**

最典型的例子是 Task 5（Guardrail）。如果我先写实现再补测试，我很可能会写一个"看起来对"的 `guardrail()` 函数，然后用一个"看起来对"的测试验证它。但 TDD 强制我先写测试，测试的断言（`rm -rf /` → BLOCK、`rm file` → HITL_PENDING、`ls` → PASS）逼我在写实现之前就想清楚每种命令应该返回什么。这种"先想清楚预期行为再写代码"的纪律，在 AI 协作下尤其重要——因为 AI 生成代码太快了，如果没有测试约束，很容易写出"能跑但行为不对"的代码。

TDD 唯一的阻碍是"红"阶段的心理压力——看着测试失败（ModuleNotFoundError）总觉得是在浪费时间。但实际上这个阶段只需要几秒钟，它确认了测试本身是有效的（不是永远通过的废测试）。

## 四、subagent-driven 工作流让智能体能自主运行多久而不偏离主题

**13 个 task 全程未偏离主题。** 这主要归功于：
1. 每个 task 的 brief 包含了完整的代码和测试，subagent 只需要"转录 + 测试"
2. 每个 task 颗粒度足够小（2-5 分钟），subagent 没有机会跑偏
3. review 机制在 Task 5 捕获了偏离（safe-side default 违反全局约束）

但有一个潜在偏离：Task 11 的 subagent 自行修改了测试代码（添加 PYTHONPATH env），这虽然是为了让测试通过，但偏离了 brief 的"exactly as specified"。这个偏离是合理的，但如果 brief 更严谨（提前考虑 src-layout 的 subprocess 问题），就不需要 subagent 自行判断。

## 五、什么样的 task 颗粒度最优

**最优颗粒度：一个 task = 一个文件 + 一个测试文件 + 5-15 个测试。**

- 太大（如"实现整个 Agent Loop + CLI + Demo"）：subagent context 不够，容易遗漏
- 太小（如"只写一个 dataclass"）：review 开销大于实现开销
- 刚好（如 Task 5 Guardrail：3 层 × 5 步 = 15 步，21 个测试）：subagent 一次会话完成，review 有实质内容

Task 5 是颗粒度最理想的例子——它足够大以体现深度（3 层机制、21 个测试、reviewer 发现 3 个问题），又足够小让一个 subagent 一次完成。

## 六、SPEC/PLAN 质量如何影响实现质量

**规约不清导致 subagent 偏离的具体案例：**

Task 3（Config Loader）中，brief 的代码写了 `data = yaml.safe_load(f) or {}`，假设 `safe_load` 对无效 YAML 会返回 None 或抛异常。但实际上，PyYAML 对 `":::not valid yaml:::["` 返回的是一个 truthy 字符串，导致 `data.get(...)` 抛 `AttributeError`。

这个 bug 的根源是 SPEC 的功能规约只写了"YAML 解析失败 → 使用默认配置"，没有定义"解析失败"的精确含义（是抛异常算失败，还是返回非 dict 算失败）。如果 SPEC 写得更精确——"safe_load 返回非 dict 时视为解析失败"——brief 的代码就不会有这个 bug。

冷启动验证也暴露了类似问题：grep 的 path 参数是否必填、异常时 exit_code 是什么——这些在主 agent 的对话上下文里是"显然的"，但写进 SPEC 时被遗漏了。

## 七、最有效的 prompt/context 策略

**最有效策略：task brief 包含完整代码。**

我的 PLAN.md 的每个 task 都包含了完整的测试代码和实现代码，subagent 只需要"转录 + 运行 + 提交"。这看起来像"过度详细"，但实际上：
1. subagent 不需要理解上下文，只需要执行
2. review 可以直接对比 brief 和实现，不需要判断"subagent 是否理解了需求"
3. 避免了 subagent 自行设计代码风格导致的 inconsistency

**为什么有效：** AI 生成代码的质量不稳定，但"转录已有代码"的质量是稳定的。把设计决策集中在 PLAN 阶段（由我 + brainstorming 做），把执行交给 subagent（只转录不设计），是质量最可控的分工。

## 八、凭据与分发迫使想清楚的问题

**凭据：** 我原本以为"API key 放环境变量就行了"。但作业要求"绝不进入 shell history"让我意识到 `export DEEPSEEK_API_KEY=xxx` 会进入 history，必须用 `.env` 文件或 keyring。最终实现了 keyring（主方案）+ .env（回退）的双层方案，并支持 `harness config set-key`（隐藏输入）。

**分发：** 我原本以为"pip install 就行了"。但作业要求"别人如何在一台全新机器上从零运行"让我想到了：首次运行时没有 key 怎么办？所以加了首次运行引导——检测到无 key 时提示用户配置。README 也必须写清 key 的安全配置方式。

这两个要求迫使我想清楚了"开发环境能跑"和"别人能跑"之间的差距。

## 九、如果重做会改变什么

1. **SPEC 阶段就定义 LLM 动作协议** — 我在自审时才补上 `<action>` 标签格式，这应该在 brainstorming 阶段就确定
2. **全局约束和 SPEC 交叉检查** — "unknown → HITL_PENDING"和"其余 → PASS"的矛盾应该在写 SPEC 时就发现，而不是等 review
3. **冷启动验证更早做** — 我在实现完成后才做冷启动验证，理想情况下应该在 SPEC 完成后、PLAN 开始前就做
4. **WebUI 从一开始就规划** — 作业要求 WebUI 但我在 SPEC 阶段没规划，最后补加导致 templates 路径处理比较 hacky

## 十、对 Superpowers 方法论的批判

**Superpowers 假设了什么：**

1. **假设 task 之间可以清晰隔离** — 但我的项目 13 个 task 高度依赖（Task 10 依赖全部前 9 个），worktree 并行不可行
2. **假设 brief 可以包含完整代码** — 这对小型项目可行，但大型项目的 task brief 不可能包含完整代码，subagent 就需要自行设计，质量就不可控了
3. **假设 review 能捕获所有问题** — reviewer 确实捕获了 Task 5 的 3 个问题，但对于跨 task 的集成问题（如 Agent Loop 和 Guardrail 的交互），单个 task 的 reviewer 看不到

**这些假设在我的项目里成立吗：**

1. 部分不成立——我用了顺序执行而非 worktree 并行
2. 成立——我的项目规模允许 brief 包含完整代码
3. 部分成立——Task 5 的 review 有效，但 Task 10（Agent Loop 集成）没有做 review，集成问题可能遗漏

总的来说，Superpowers 是一套有效的"流程脚手架"，它守住了 TDD、review、计划这些纪律。但它不能替你回答"做什么"和"做对了吗"——这两个问题，仍然是工程师的真正价值所在。
