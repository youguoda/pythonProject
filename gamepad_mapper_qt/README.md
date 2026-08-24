# Gamepad Mapper (PyQt6)

单手柄按键映射工具：将手柄 24 项输入映射为键盘按键。

## 快速使用

### 1. 安装依赖

```powershell
cd E:\Project\Python\pythonProject\gamepad_mapper_qt
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. 启动

```powershell
python main.py
```

### 3. 三步映射

1. 连接手柄，点击 **「⟳ 刷新」**，确认顶部显示已连接
2. 在右侧映射表点击 **「绑定」**（或双击行），按下要映射的键盘键（支持组合键，如 `Left Ctrl+C`、`Right Shift+A`；可区分左右 Ctrl/Shift/Alt）
3. 点击 **「▶ 启动映射」**（或按 **F9**），按手柄键即可输出键盘操作

## 支持的手柄输入（24 项）

| 类型 | 按键 |
|------|------|
| 面键 | A, B, X, Y |
| 肩键 | LB, RB, LT, RT |
| 功能键 | Back, Start, L3, R3 |
| 十字键 | 上/下/左/右 |
| 左摇杆 | 上/下/左/右 |
| 右摇杆 | 上/下/左/右 |

## 快捷键

| 按键 | 功能 |
|------|------|
| F9 | 启动/停止映射 |

## 配置

映射自动保存到 `config/mapping.json`：

```json
{
  "mappings": { "0": "a", "1": "b" },
  "threshold": 0.5
}
```

- `mappings`：手柄键索引 → 键盘键名
- `threshold`：摇杆触发阈值（0.1–0.9，可在底部滑块调节）

## 项目结构

```
gamepad_mapper_qt/
├── main.py
├── core/           # pygame + pynput 底层
├── ui/             # PyQt6 界面
└── config/         # 映射配置
```

## 技术栈

- **PyQt6** — 界面
- **pygame** — 手柄检测与轮询
- **pynput** — 键盘模拟输出
