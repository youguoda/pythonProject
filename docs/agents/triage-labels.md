# Triage 标签

skill 内部用五个固定的 triage 角色来说话。这张表把那些角色映射到本仓库实际使用的标签字符串。

| skill 里的角色 | 本仓库标签 | 含义 |
| --- | --- | --- |
| `needs-triage` | `待分拣` | 需要维护者评估这个 issue |
| `needs-info` | `缺信息` | 等待报告者补充信息 |
| `ready-for-agent` | `可交agent` | 描述已完整，agent 可无人值守接手 |
| `ready-for-human` | `需人工` | 需要人来实现 |
| `wontfix` | `不做` | 不会处理 |

skill 提到某个角色时（例如「打上 AFK-ready 的 triage 标签」），使用表中右列对应的标签字符串。

标签写在 issue 文件顶部的 `Status:` 行里，例如：

```markdown
Status: 待分拣
```

**注意区分**：`Status:` 这一行在 `/wayfinder` 的探路票上含义不同 —— 那里放的是 `claimed` / `resolved`，属于 wayfinder 的内部状态，与上面这五个 triage 标签不是一回事，保持英文不要翻译。详见 `issue-tracker.md` 的「探路操作」一节。

想换说法直接改右列即可，左列是 skill 的固定词汇，不要动。
