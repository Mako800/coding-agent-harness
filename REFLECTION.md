# REFLECTION.md — 反思报告

> 本反思报告由学生本人撰写，AI 辅助润色已标注。

---

## 一、哪些 Superpowers 技能发挥了最大作用

**brainstorming** 对我来说是这轮项目里最实在的技能。它那种“一次只问一个问题”的节奏，硬生生逼着我从一团浆糊似的想法里，一点一点抠出明确的设计来。最明显的就是选重点维度的时候，我当时其实心里没底，就顺着流程问了句“哪个最简单”，智能体直接推荐了“治理”，还给出了理由——实现不复杂、能单独测、性价比高。我听了，做了，后来证明这个选择确实靠谱。如果不是这种一步步追问的机制，我很可能会把六个维度都蜻蜓点水地碰一遍，最后什么都做不深。

**subagent-driven-development** 排第二。每个 task 都派一个新的 subagent，最大的好处就是上下文不会相互污染，而且每次 review 都是独立的。Task 5 做 Guardrail 的时候，reviewer 硬是给我揪出了三个真实的安全漏洞——safe-side default、路径穿越、还有边缘测试缺失。说实话，如果让我自己肉眼检查，这几个点大概率会漏过去。

**test-driven-development** 就不多说了，作业本身要求必须 TDD，这让我每个模块都老老实实写了测试。最后统计下来 70 个测试，全是 MockLLM 驱动，不碰网络也不碰真实 LLM，正好满足作业 §A.6 里“确定性单元测试”的要求。

**verification-before-completion** 在收尾阶段很管用——它反复提醒我“没跑验证就不算完成”，所以我每次说“done”之前都会老老实实敲一遍 `pytest -v`，确认没问题才敢提交。

## 二、哪些技能“形式大于实质”

**using-git-worktrees** 说实话，在我这项目里有点走过场。作业要求每个独立功能开一个 worktree 对应一个 PR，但我这个项目是全新搭建的，13 个 task 之间高度耦合，基本上是串行推进的。硬要切 worktree 的话，合并冲突反而会把人搞疯。最后我选择在单分支上顺序完成所有 task，对个人项目、模块紧密依赖的场景来说，这更实在，也更省时间。

**writing-skills** 完全没用上，因为我压根不需要创建自定义 skill，所以这块对我来说就是摆设。

## 三、TDD 强制在 AI 协作下是阻碍还是放大器

我自己的体感是——**TDD 绝对是放大器，不是绊脚石**。

拿 Task 5 的 Guardrail 来说吧。如果按老习惯先写实现再补测试，我大概率会写一个“看着差不多对”的 `guardrail()` 函数，然后用一个“看着差不多对”的测试去糊弄一下。但 TDD 逼着我先把测试摆出来，测试里那些断言——比如 `rm -rf /` 要返回 BLOCK，`rm file` 要返回 HITL_PENDING，`ls` 要返回 PASS——这些具体的期望值让我在写实现之前，就必须把每种命令的行为逻辑想清楚。AI 生成代码的速度太快了，如果没有测试这层硬约束，很容易写出“能跑但行为是错的”代码。

唯一觉得有点别扭的，就是“红”阶段那种心理上的不适感——看着测试报 ModuleNotFoundError，总觉得自己在浪费时间。但其实这个过程就几秒钟，它至少证明了测试本身不是个永远通过的废测试。

## 四、subagent-driven 工作流让智能体能自主运行多久而不偏离主题

**13 个 task 全程没有跑偏过。** 我觉得主要原因有三点：第一，每个 task 的 brief 里直接塞了完整的代码和测试，subagent 只要“照抄 + 跑通”就行；第二，每个 task 颗粒度很小，基本两三分钟就能搞定，没机会让它自由发挥；第三，review 机制在 Task 5 的时候确实挡住了偏离——那个 safe-side default 违反全局约束的问题就是 review 抓出来的。

不过 Task 11 有个小插曲，subagent 自己改了测试代码，加了 PYTHONPATH 环境变量，虽然是为了让测试能过，但严格来说跟 brief 里“exactly as specified”的指令不太一致。这个偏离还算合理，但如果 brief 能提前考虑到 src-layout 下 subprocess 调用的问题，就不需要它自己临时判断了。

## 五、什么样的 task 颗粒度最优

我觉得最舒服的颗粒度是：**一个 task = 一个实现文件 + 一个测试文件 + 大概 5 到 15 个测试用例**。

太大不行，比如“实现整个 Agent Loop + CLI + Demo”这种，subagent 的上下文根本装不下，很容易丢三落四。太小也没意思，像“只写一个 dataclass”这种，review 的功夫比实现本身还多。Task 5 的 Guardrail 算是个标杆——三层逻辑、21 个测试、reviewer 还挖出三个问题，既足够深，又能在一次会话里完成，review 也能看到实质性的东西。

## 六、SPEC/PLAN 质量如何影响实现质量

规约写得不够细，确实会让 subagent 在实现时踩坑。

Task 3 的 Config Loader 就是个典型。brief 里写了 `data = yaml.safe_load(f) or {}`，暗示 `safe_load` 遇到无效 YAML 会返回 None 或者抛异常。但 PyYAML 的实际行为是，对 `":::not valid yaml:::["` 这种字符串，返回的是一个 truthy 值，结果 `data.get(...)` 直接抛了 `AttributeError`。这个 bug 的根子在于 SPEC 只说了“YAML 解析失败 → 使用默认配置”，但没有定义“解析失败”到底指什么——是抛异常算失败，还是返回非 dict 也算失败。如果 SPEC 当初写清楚“safe_load 返回非 dict 就按失败处理”，brief 里的代码就不会中招。

冷启动验证也暴露了类似的问题——grep 的 path 参数是不是必填、异常退出时 exit_code 应该是多少，这些在主 agent 的对话里感觉是“明摆着的事”，但落到 SPEC 里就是空白的，直接被漏掉了。

## 七、最有效的 prompt/context 策略

我的经验是，**最管用的策略就是让 task brief 自带完整代码**。

PLAN.md 里每个 task 都直接贴好了测试代码和实现代码，subagent 只需要“复制粘贴 + 跑测试 + 提交”。看起来有点像过度设计，但实际上好处很明显：subagent 不需要自己去理解上下文，只需要机械执行；review 的时候直接拿 brief 和实现对比就行，不用琢磨“它到底有没有理解需求”；而且避免了不同 subagent 写出风格不统一的代码。

这种做法的本质是把设计决策集中到 PLAN 阶段，由我和 brainstorming 来完成，而执行阶段只交给 subagent 做“转录”，这样质量是最可控的。

## 八、凭据与分发迫使想清楚的问题

关于**凭据**，我一开始想得很简单——“API key 放环境变量不就行了”。但作业里那句“绝不进入 shell history”让我反应过来，`export DEEPSEEK_API_KEY=xxx` 这种操作确实会留在 history 里，不安全。所以最后搞了个双层方案：主用 keyring，回退到 `.env`，还加了 `harness config set-key` 支持隐藏输入。

关于**分发**，我原来觉得“pip install 就完事了”。但作业要求“别人在全新机器上从零运行”，这就逼着我考虑首次运行没有 key 的情况。所以加了首次运行引导，检测到无 key 就提示用户去配置，README 里也得写清楚 key 的安全配置方式。这两件事让我真正意识到“自己开发环境能跑”和“让别人也能跑”之间有多大的差距。

## 九、如果重做会改变什么

- **SPEC 阶段就把 LLM 动作协议定下来** — 我当时是后来自审才补的 `<action>` 标签格式，这事应该在 brainstorming 阶段就敲定。
- **全局约束和 SPEC 交叉检查** — “unknown → HITL_PENDING” 和 “其余 → PASS” 之间的矛盾，本来应该在写 SPEC 时就能发现，结果拖到 review 才暴露。
- **冷启动验证提前做** — 我是在所有实现都完成后才做冷启动验证，理想情况下应该在 SPEC 完成、PLAN 开始之前就做一轮。
- **WebUI 从一开始就纳入规划** — 作业其实要求 WebUI，但我前期完全没考虑，最后补加的时候 templates 路径处理搞得挺狼狈的。

## 十、对 Superpowers 方法论的批判

Superpowers 这套流程背后其实藏着几个前提假设：

- 它假设 task 之间可以分得清清楚楚、互不干扰 — 但我这 13 个 task 里，Task 10 依赖前面所有的，根本没法并行 worktree。
- 它假设 brief 里能塞进完整代码 — 对小型项目还行，但如果是大项目，task brief 不可能完整到那种程度，subagent 就得自己设计，质量就没谱了。
- 它假设 review 能兜住所有问题 — reviewer 确实在 Task 5 里抓到了三个问题，但像 Agent Loop 和 Guardrail 之间的集成问题，单 task 的 reviewer 是看不到的。

这些假设在我这项目里，有的成立，有的不成立。worktree 并行我没用上，但 brief 塞完整代码是可行的；Task 5 的 review 有效，但 Task 10 的集成部分没做 review，可能还有隐患。

总的来说，Superpowers 像是一套“流程脚手架”，能帮你守住 TDD、review、计划这些纪律。但它没法替你想清楚“到底该做什么”，也没法直接告诉你“做对了没有”——这两个问题，最终还是得靠工程师自己来判断。