# Issue tracker：本地 Markdown

本仓库的 issue 和 PRD 以 markdown 文件形式存放在 `.scratch/` 下，不使用 GitHub Issues。

## 约定

- 一个功能一个目录：`.scratch/<feature-slug>/`
- PRD 放在 `.scratch/<feature-slug>/PRD.md`
- 实现类 issue 放在 `.scratch/<feature-slug>/issues/<NN>-<slug>.md`，编号从 `01` 起
- triage 状态记在每个 issue 文件靠顶部的 `Status:` 行（角色字符串见 `triage-labels.md`）
- 评论和对话历史追加到文件末尾的 `## Comments` 标题下

## 当 skill 说「发布到 issue tracker」

在 `.scratch/<feature-slug>/` 下新建文件（目录不存在就创建）。

## 当 skill 说「取出相关的 ticket」

读取被引用路径上的文件。通常用户会直接给出路径或 issue 编号。

## 探路操作

供 `/wayfinder` 使用。**map** 是一个文件，每张票对应一个 **child** 文件。

- **Map**：`.scratch/<effort>/map.md` —— 包含 Notes / Decisions-so-far / Fog 三部分正文。
- **Child ticket**：`.scratch/<effort>/issues/NN-<slug>.md`，编号从 `01` 起，正文写问题。`Type:` 行记录票的类型（`research` / `prototype` / `grilling` / `task`）；`Status:` 行记录 `claimed` / `resolved`。
- **Blocking**：靠顶部写一行 `Blocked by: NN, NN`。它列出的文件全部 `resolved` 时，这张票才解除阻塞。
- **Frontier**：扫描 `.scratch/<effort>/issues/`，找出未关闭、未被阻塞、未被认领的文件；编号小的优先。
- **Claim**：动手前先把 `Status:` 设为 `claimed` 并保存。
- **Resolve**：在 `## Answer` 标题下追加答案，把 `Status:` 设为 `resolved`，然后往 `map.md` 的 Decisions-so-far 追加一条上下文指针（要点 + 链接）。

上面这些结构性标记（`Status:`、`Type:`、`Blocked by:`、`## Comments`、`## Answer`）以及探路票的 `claimed` / `resolved` 取值是 skill 用来定位内容的，保持英文原样，不要翻译。
