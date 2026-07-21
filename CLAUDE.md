# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository structure

Four independent projects. Each has its own build/run system and dependencies.

### 图书管理系统/ — C语言图书管理系统

- **Build:** 运行 `build.bat`（依赖 VS2022 MSVC 编译器，输出到 `build/library_system.exe`）
- **架构:** 6个源文件用单链表管理内存数据，二进制文件持久化到 `data/` 目录。`main.c` 驱动4个菜单模块（图书/读者/借阅/统计），`utils.c` 提供跨模块共享的辅助函数和安全输入

### thread_monitor/ — Windows 进程线程监控 (Python + PySide6)

- **运行:** `pip install -r requirements.txt && python -m thread_monitor.main`
- **架构:** 分层 MVC — `collectors/` 通过 psutil + ctypes 直调 kernel32/ntdll 采集数据，`services/data_service.py` 在 QThread 中定时采集并发射信号，`views/` 消费信号更新 UI。`utils/win32_api.py` 包含约50个 ctypes 结构体和 API 绑定

### 地牢探险-提交版/ — Roguelike 地牢游戏 (Python + Pygame)

- **运行:** `pip install pygame && python main.py`，也有 `DungeonQuest.exe`（PyInstaller 打包）
- **架构:** `game.py` 通过 `GameState` 状态机驱动主循环。`dungeon.py` 用 BSP 递归生成地图。`fov.py` 用 Bresenham 射线投射做战争迷雾。`enemy.py` 包含5个 Boss 类，各自覆盖 `_update_ai` 和 `_perform_attack`。`combat.py` 处理扇形近战判定和稀有度掉落

### goblog/ — Go 博客 API 后端 (Gin + GORM + Redis)

- **运行:** `make run` 或 `go run ./cmd/server/ -config ./configs/config.yaml`
- **构建:** `make build` → `goblog.exe`
- **测试:** `make test` → `go test ./... -v -count=1`
- **架构:** 严格分层 Handler → Service → Repository → GORM。双 token JWT 认证（短期 access + 持久化 refresh）。Redis 做缓存和限流，不可用时优雅降级（nil-safe 封装）。评论通过 `ParentID` 自引用支持嵌套回复树。所有响应统一 `Response{Code, Message, Data}` 格式

## Git push workflow

凭据已通过 `git credential-manager` 存储。推送命令：

```bash
cd /c/Users/dream/Desktop/verbose-octo-system
git add .
git commit -m "改动说明"
git push
```
