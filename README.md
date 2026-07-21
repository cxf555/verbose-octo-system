# 个人项目集

## 项目列表

### 图书管理系统
C 语言编写的命令行图书管理程序，支持图书录入、读者管理、借阅归还、数据统计等功能。

- **技术栈**：C
- **运行**：Windows 下执行 `build.bat` 编译

### Thread Monitor
Windows 进程与线程实时监控工具，提供图形化界面查看系统运行状态。

- **技术栈**：Python 3、PySide6
- **运行**：`pip install -r requirements.txt && python -m thread_monitor.main`

### 地牢探险 (Dungeon Quest)
俯视角实时动作 Roguelike 地牢探险游戏，随机生成地下城、多种武器与敌人。

- **技术栈**：Python 3、Pygame
- **运行**：`python main.py`

### goblog
基于 Go 语言开发的博客系统后端，支持文章管理、分类标签、用户认证、文件上传。

- **技术栈**：Go、Gin、MySQL、Redis、JWT
- **运行**：`make run` 或 `go run cmd/server/main.go`
