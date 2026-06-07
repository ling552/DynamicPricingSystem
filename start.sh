#!/usr/bin/env bash
# 动态价格策略模拟与分析系统 —— Linux / macOS 一键启动脚本
# 自动完成：创建虚拟环境 -> 安装依赖 -> 数据库迁移 -> 写入演示数据 -> 启动服务并打开浏览器
set -euo pipefail

# 定位到脚本所在目录（即仓库根目录），保证从任意位置运行都正确
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

# 选择可用的 Python 解释器（优先 python3）
if command -v python3 >/dev/null 2>&1; then
  PY=python3
elif command -v python >/dev/null 2>&1; then
  PY=python
else
  echo "[错误] 未找到 python3 / python，请先安装 Python 3.11+。" >&2
  exit 1
fi

VENV_DIR="$ROOT_DIR/.venv"

# 首次运行时创建虚拟环境
if [ ! -d "$VENV_DIR" ]; then
  echo "[1/4] 创建虚拟环境 .venv ..."
  "$PY" -m venv "$VENV_DIR"
else
  echo "[1/4] 已存在虚拟环境 .venv，跳过创建。"
fi

# 激活虚拟环境
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

# 安装 / 更新依赖
echo "[2/4] 安装依赖（requirements.txt）..."
python -m pip install --upgrade pip >/dev/null
python -m pip install -r "$ROOT_DIR/requirements.txt"

cd "$ROOT_DIR/price_strategy_system"

# 数据库迁移 + 演示数据
echo "[3/4] 初始化数据库并写入演示数据..."
python manage.py migrate
python manage.py seed_demo

# 启动服务（launcher.py 会自动选择空闲端口并打开浏览器）
echo "[4/4] 启动服务，浏览器将自动打开。按 Ctrl+C 可停止。"
exec python launcher.py
