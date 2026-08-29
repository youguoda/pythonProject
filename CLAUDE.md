# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 仓库构成

| 路径 | 说明 |
|------|------|
| `gamepad_mapper_qt/` | **唯一活跃项目**：PyQt6 手柄映射器 v2.0 |
| `main.py`、`test1.py`（根目录） | 早期 argparse 脚手架残留，与手柄项目无关，可删 |

早期的 tkinter 版本（`gamepad_mapper/`，v1 / v2 / v3.5 Pro）曾以嵌套 Git 仓库的形式存在于此，remote 指向 `longsongline/gamepad_mapper`，现已从本地删除。它从未被根仓库跟踪，所以本仓库历史里找不到它。

## 常用命令（gamepad_mapper_qt）

项目自带 venv（Python 3.11），依赖已装好：

```powershell
cd E:\Project\Python\pythonProject\gamepad_mapper_qt; .\.venv\Scripts\Activate.ps1; python main.py
```

```bash
gamepad_mapper_qt/.venv/Scripts/python.exe gamepad_mapper_qt/main.py
```

```bash
gamepad_mapper_qt/.venv/Scripts/pip.exe install -r gamepad_mapper_qt/requirements.txt
```

跑测试（pytest，配置在 `gamepad_mapper_qt/pytest.ini`）：

```bash
gamepad_mapper_qt/.venv/Scripts/python.exe -m pytest
```

```bash
gamepad_mapper_qt/.venv/Scripts/python.exe -m pytest tests/test_edge_detector.py -k 长按
```

测试只覆盖 `core/gamepad_input.py`（边沿判定与接线），不需要手柄也不需要 Qt。**其余部分仍然没有测试覆盖** —— `MappingEngine.consume` 要断言「发出了什么按键」，得先把 `KeyboardOutput` / `MouseOutput` 的依赖改成注入（它们目前在 `__init__` 里自己 new pynput 和 `ctypes.windll`），那是独立的一项工作。

没有 linter、没有 CI，也没有打包步骤（不出 exe，直接跑源码）。开发依赖在 `requirements-dev.txt`。

Windows 专属：`core/mouse_output.py`、`core/window_focus.py`、`core/autostart.py` 直接调 `ctypes.windll` 和 `winreg`，非 Windows 上 import 即失败。

## 架构（gamepad_mapper_qt）

### 逻辑槽位索引是全局契约

`core/constants.py` 的 `BUTTON_NAMES` 是一个 24 项列表，**它的下标就是整个系统里唯一的按键标识符**：profile JSON 的 `mappings` 键、`MappingTable` 的行号、`MappingEngine._mappings` 的键、`PollResult.pressed` 的下标，全都是同一套 0–23。

因此**往 `BUTTON_NAMES` 中间插入或重排任何一项，都会静默改写磁盘上所有 profile 的含义**。要加按键只能追加到末尾。

注意 20–23 的顺序是 `Right Stick Up / Down / Right / Left`——右摇杆的左右和左摇杆（18=Left, 19=Right）是反的，这是有意的，`joystick_manager.poll()` 与之对应。

### 硬件 → 逻辑的转换层

`core/button_map.py` 负责把 pygame 的物理按钮号翻译成逻辑槽位。Xbox 布局下物理 6/7（Back/Start）落到逻辑 8/9，物理 8/9（L3/R3）落到逻辑 10/11；而逻辑 6/7（LT/RT）**不来自按钮，来自 axis 4/5**，由 `JoystickManager.poll()` 单独填充。手柄名称经 `detect_layout()` 判定用 `xbox` 还是 `direct` 布局。

### 唯一的 tick 与唯一的采样点

`MainWindow._tick`（`QTimer`，16ms ≈ 60Hz，主线程）是全应用唯一的循环。`GamepadInput.tick()` 是唯一调用 `JoystickManager.poll()` 的地方 —— 所有消费者读**同一帧**：

```
frame = input.tick(now)
engine.consume(frame)      # 键盘/鼠标输出
_分派保留槽位(frame)         # LT / Start
_更新表格高亮(frame)
每两帧 → panel.update_state(frame)   # 重绘维持 30Hz
```

`MappingEngine` 是 `QObject` 不是 `QThread`，自己不计时也不轮询。`JoystickManager` 里的 `RLock` 现在已无必要（只剩单线程调用），留着无害。

**不要再引入第二个 `poll()` 调用点** —— 之前正是两条回路各自采样、各自维护上一帧状态，导致 LT 长短按完全失效、Start 一半几率不响应。

### 边沿判定集中在 GamepadInput

`core/gamepad_input.py` 拥有全部边沿逻辑，对外只有 `tick(now) -> InputFrame` 一个方法。`InputFrame` 同时携带边沿集合（`just_pressed` / `just_released` / `just_long_pressed` / `just_short_released`）和连续量（`pressed` / `left_stick` / `right_stick` / `lt_value` / `rt_value`）。

长按阈值通过构造参数配置（`long_press_after={IDX_LT: LT_LONG_PRESS_SEC}`），module 因此不需要知道 LT 是什么意思 —— **语义在 `MainWindow`，判定在 module**。

内部的 `EdgeDetector` 是私有 seam，只有 `tests/test_edge_detector.py` 穿过它。改边沿逻辑先补测试。

**所有 24 个槽位共用一条按下/抬起规则**（`just_pressed` → press，`just_released` → release）。历史上 `MappingEngine` 里有个 `bi < 12` 的分支看似区分两种语义，实为同一逻辑的两种写法，已删除。

### 被硬编码占用的槽位（不走通用映射路径）

| 槽位 | 行为 | 位置 |
|------|------|------|
| 6 (LT) | 引擎跳过。短按 → 聚焦当前方案窗口；长按 ≥ `LT_LONG_PRESS_SEC`(0.4s) → 循环切方案 | `MainWindow._分派保留槽位` |
| 7 (RT) | 硬编码按住 `VOICE_KEY`（`ctrl_r`），**profile 里给 7 配的映射不生效** | `MappingEngine._处理语音` |
| 9 (Start) | 被主循环吃掉用于启停映射 | `MainWindow._分派保留槽位` |
| 10 / 11 (L3/R3) | 由 `UNIVERSAL_MOUSE_MAPPINGS` 提供哨兵动作 `@mouse:left` / `@mouse:right`，引擎特判为鼠标按下/抬起 | `constants.py` + `MappingEngine._按下` |

左摇杆 → 鼠标移动、右摇杆 Y → 滚轮同样**硬编码在 `MappingEngine._处理鼠标` 里，不由映射表驱动**；映射表中 16–23 的摇杆方向槽位是另一套并行机制（可同时把左摇杆映射成 WASD，但鼠标移动依然在跑）。

### 前台闸门（gate）

`MappingEngine` 每 tick 调用 `_gate_checker`，实际指向 `MainWindow._check_gate` → `window_focus.is_process_foreground(profile.process_names)`。

**`process_names` 为空列表时闸门恒开**（`general` / 通用方案就靠这个对任意窗口生效）。闸门关闭时引擎会 `release_all()` 并抬起鼠标键，防止切窗时按键卡住。

### 统一鼠标层的合并/剥离往返

这是 profile 读写中最容易被破坏的一环，两个方向必须成对理解：

- 读：`config_store.effective_mappings()` 把 `UNIVERSAL_MOUSE_MAPPINGS` 合并进 profile（profile 自己的同槽位配置优先覆盖）
- 写：`MainWindow._mappings_for_save()` 把与统一层**完全相同**的条目剔除再落盘

所以磁盘上的 profile JSON 里正常看不到 `"10"` / `"11"`，只有用户主动改成别的值才会出现。往 `UNIVERSAL_MOUSE_MAPPINGS` 加东西时，靠的就是这个往返保证老 profile 不被写脏。profile 设 `"universal_mouse": false` 可整体关掉这一层。

### 持久化

`core/config_store.py` 是唯一的读写入口：

- `config/profiles/<id>.json` —— 每个方案一份；`PROFILE_ORDER` 决定下拉框顺序，磁盘上多出来的 json 会排在后面
- `config/app_state.json` —— 当前方案 id、开机自启、启动后自动映射

`config/mapping.json` 和 `load_config()` / `save_config()` 是遗留兼容层，**当前代码没有任何地方调用**，改配置格式时不必迁就它。

保存时机很密：改映射、改滑块、切方案、关窗口都会立刻 `save_profile()`，没有"取消"路径。

### 键名格式

映射值是 pynput 风格的小写键名，`+` 分隔组合键（如 `ctrl+shift+tab`）。`KeyboardOutput._resolve_key` 里有一张别名表（`pageup`→`page_up`、`win`/`super`→`cmd`）。新增可绑定按键通常要同时动三处：`constants.KEYBOARD_KEYS`、`key_bind_dialog._QT_KEY_MAP`（Qt 键码 → pynput 名）、以及必要时的别名表。`_KEY_PRESETS` 里放的是对话框抓不到的系统级快捷键（Win+Tab 等），只能预设写入。

### 开机自启

`core/autostart.py` 写 HKCU 的 `Software\Microsoft\Windows\CurrentVersion\Run`，值名 `GamepadVibeController`，命令里把 `python.exe` 换成同目录 `pythonw.exe` 以免弹黑框。注册的是**源码路径 + 当前解释器**，移动项目目录或换 venv 后需要在 UI 里重新勾选一次。

## UI 层

`ui/main_window.py`（529 行）是全部胶水：持有 joystick / keyboard / mouse / engine 四个对象，widget 只通过 pyqtSignal 往上报，不直接碰 core。样式集中在 `ui/styles/theme.qss`，配色常量在 `constants.THEME`，两边需要手动保持一致。界面文案与注释统一用中文。

## Agent skills

### Issue tracker

本地 markdown —— issue 以文件形式存在 `.scratch/<feature>/` 下，不使用 GitHub Issues（本机也未安装 `gh`）。见 `docs/agents/issue-tracker.md`。

### Triage labels

五个 triage 角色使用中文标签：`待分拣` / `缺信息` / `可交agent` / `需人工` / `不做`。见 `docs/agents/triage-labels.md`。

### Domain docs

单上下文：根目录一份 `CONTEXT.md` + `docs/adr/`，两者都尚未创建，由 `/domain-modeling` 按需懒创建。见 `docs/agents/domain.md`。
