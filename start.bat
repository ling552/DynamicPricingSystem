@echo off
chcp 65001 >nul
rem 动态价格策略模拟与分析系统 —— Windows 一键启动脚本
rem 自动完成：创建虚拟环境 -> 安装依赖 -> 数据库迁移 -> 写入演示数据 -> 启动服务并打开浏览器
setlocal

rem 切换到脚本所在目录（即仓库根目录）
cd /d "%~dp0"

rem 检查 Python 是否可用
where python >nul 2>nul
if errorlevel 1 (
  echo [错误] 未找到 python，请先安装 Python 3.11+ 并加入 PATH。
  pause
  exit /b 1
)

rem 首次运行时创建虚拟环境
if not exist ".venv" (
  echo [1/4] 创建虚拟环境 .venv ...
  python -m venv .venv
) else (
  echo [1/4] 已存在虚拟环境 .venv，跳过创建。
)

rem 激活虚拟环境
call ".venv\Scripts\activate.bat"

rem 安装 / 更新依赖
echo [2/4] 安装依赖（requirements.txt）...
python -m pip install --upgrade pip >nul
python -m pip install -r "requirements.txt"
if errorlevel 1 (
  echo [错误] 依赖安装失败，请检查网络或 Python 环境。
  pause
  exit /b 1
)

cd price_strategy_system

rem 数据库迁移 + 演示数据
echo [3/4] 初始化数据库并写入演示数据...
python manage.py migrate
python manage.py seed_demo

rem 启动服务（launcher.py 会自动选择空闲端口并打开浏览器）
echo [4/4] 启动服务，浏览器将自动打开。关闭本窗口或按 Ctrl+C 可停止。
python launcher.py

endlocal
