# DynamicPricingSystem

动态定价策略模拟与分析系统是一个基于 Django 的 Web 应用，用于录入商品与销售数据，模拟不同价格调整策略下的销量和利润变化，并通过图表辅助定价决策。

## 功能特性

- 用户注册、登录与退出
- 商品信息管理：成本、售价、分类、价格敏感系数
- 销售记录管理：销售日期、成交价格、销售数量
- 定价策略模拟：按价格调整比例预测销量与利润
- 分析看板：展示商品、销售与模拟结果的关键指标
- 演示数据初始化命令，便于快速体验系统

## 技术栈

- Python 3.11
- Django 4.2.21
- SQLite
- Bootstrap
- ECharts

## 目录结构

```text
.
├── price_strategy_system/
│   ├── manage.py
│   ├── price_system/          # Django 项目配置
│   ├── pricing_app/           # 核心业务应用
│   ├── static/                # CSS 与图片资源
│   └── templates/             # 页面模板
├── Dockerfile
├── docker-entrypoint.sh
├── environment.yml
├── requirements.txt
└── .github/workflows/docker-release.yml
```

`springbootAfter/` 与本项目无关，仓库中不会包含该目录。

## 本地运行

使用 Conda：

```bash
conda env create -f environment.yml
conda activate dynamic_pricing_system
cd price_strategy_system
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

使用 pip：

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
cd price_strategy_system
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

访问地址：

- 首页：<http://127.0.0.1:8000/>
- 登录：<http://127.0.0.1:8000/login/>
- 注册：<http://127.0.0.1:8000/register/>
- 后台：<http://127.0.0.1:8000/admin/>

演示账号由 `seed_demo` 命令创建：

```text
用户名：demo
密码：demo12345
```

## Docker 打包与启动

本地构建镜像：

```bash
docker build -t dynamicpricingsystem:latest .
```

启动容器：

```bash
docker run --rm -p 8000:8000 ^
  -e DPS_SECRET_KEY="replace-with-a-random-secret" ^
  -e DPS_DEBUG=0 ^
  -v dynamic_pricing_data:/app/data ^
  dynamicpricingsystem:latest
```

Linux/macOS 可将续行符 `^` 替换为 `\`。

如需启动时写入演示数据：

```bash
docker run --rm -p 8000:8000 ^
  -e DPS_SECRET_KEY="replace-with-a-random-secret" ^
  -e DPS_DEBUG=0 ^
  -e DPS_SEED_DEMO=1 ^
  -v dynamic_pricing_data:/app/data ^
  dynamicpricingsystem:latest
```

从 GitHub Release 下载 Docker 镜像压缩包后，可这样加载并启动：

```bash
docker load -i dynamicpricingsystem-vX.Y.Z-docker-image.tar.gz
docker run --rm -p 8000:8000 ^
  -e DPS_SECRET_KEY="replace-with-a-random-secret" ^
  -e DPS_DEBUG=0 ^
  -v dynamic_pricing_data:/app/data ^
  dynamicpricingsystem:vX.Y.Z
```

## GitHub Actions Release

仓库包含 `.github/workflows/docker-release.yml`。推送 `v*` 标签或手动运行 workflow 时，会：

1. 构建 Docker 镜像；
2. 将镜像保存为 `*.tar.gz`；
3. 创建或更新对应 GitHub Release；
4. 将 Docker 镜像压缩包上传为 Release 附件。

示例：

```bash
git tag v1.0.0
git push origin v1.0.0
```

## 环境变量

| 变量名 | 默认值 | 说明 |
| --- | --- | --- |
| `DPS_SECRET_KEY` | `django-insecure-change-me` | Django Secret Key，生产环境必须覆盖 |
| `DPS_DEBUG` | `1` | 是否开启调试模式，Docker 默认设置为 `0` |
| `DPS_ALLOWED_HOSTS` | `*` | Django 允许访问的 Host，多个值用逗号分隔 |
| `DPS_CSRF_TRUSTED_ORIGINS` | `http://127.0.0.1,http://localhost` | CSRF 信任来源，多个值用逗号分隔 |
| `DPS_DATA_DIR` | `price_strategy_system/data` | SQLite 数据库保存目录 |
| `DPS_SEED_DEMO` | 空 | Docker 启动时设为 `1` 会自动执行演示数据初始化 |

## 开源协议

本项目使用 MIT License，详见 [LICENSE](LICENSE)。
