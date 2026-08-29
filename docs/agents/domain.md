# Domain 文档

engineering 类 skill 在探查代码库时，应当如何消费本仓库的领域文档。

## 探查之前先读这些

- 根目录的 **`CONTEXT.md`**
- 根目录的 **`docs/adr/`** —— 读与你即将动手的区域相关的 ADR

本仓库是**单上下文**布局，没有 `CONTEXT-MAP.md`，不需要去子目录找分上下文的 glossary。

这些文件不存在时**静默继续**。不要提示它们缺失，也不要一上来就建议创建。它们由 `/domain-modeling`（经 `/grill-with-docs` 和 `/improve-codebase-architecture` 触达）在术语或决策真正定下来的那一刻懒创建。

## 文件结构

```
/
├── CONTEXT.md
├── docs/
│   ├── adr/
│   │   ├── 0001-....md
│   │   └── 0002-....md
│   └── agents/
└── gamepad_mapper_qt/
```

## 使用 glossary 的词汇

输出中提到某个领域概念时（issue 标题、重构提案、假设、测试名），使用 `CONTEXT.md` 里定义的那个术语。不要漂移到 glossary 明确回避的同义词上。

如果你需要的概念还不在 glossary 里，这本身是个信号 —— 要么你在发明这个项目并不使用的说法（重新考虑），要么这里有个真实的空缺（记下来交给 `/domain-modeling`）。

## 标出与 ADR 的冲突

如果你的输出和某条既有 ADR 相抵触，明确指出来，不要默默覆盖：

> _与 ADR-0007（事件溯源的订单）相抵触 —— 但值得重开，因为……_
