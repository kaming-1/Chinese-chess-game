# 中国象棋

这是一个使用 Python 和 Kivy 编写的桌面版中国象棋小游戏，支持本地对弈、AI 对手和游戏设置。

## 环境要求

- Python 3.11 或更高版本
- Windows、macOS 或 Linux
- Kivy 2.3.1

## 安装与运行

```bash
python -m venv .venv
```

Windows PowerShell：

```powershell
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python gm1.py
```

项目图片资源位于 `image/` 目录。不要将本地 `.venv/`、`__pycache__/` 或 IDE 配置上传到 GitHub。

## 主要文件

- `gm1.py`：Kivy 应用入口、棋盘界面和游戏流程
- `chessboard.py`：棋盘状态与走法
- `chess_pieces.py`：棋子规则
- `ai_opponent.py`：AI 对手
- `main_interface.py`：主菜单
- `setting_interface.py`：设置界面
