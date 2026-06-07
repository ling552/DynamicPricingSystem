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
- WhiteNoise

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

### 一键启动（推荐）

仓库根目录提供了一键启动脚本，会自动创建虚拟环境、安装依赖、初始化数据库与演示数据，并启动服务后自动打开浏览器。

Windows：双击 `start.bat`，或在命令行执行：

```bat
start.bat
```

Linux / macOS：

```bash
./start.sh
```

首次运行会创建 `.venv` 虚拟环境并联网安装依赖；之后再次运行会直接复用，启动更快。演示账号见下方 `seed_demo` 说明。

### 手动运行

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

## Docker 镜像启动

### 从 Release 镜像包启动

下载 `dynamicpricingsystem-v1.0.3-docker-image.tar.gz` 后，先加载镜像：

```bash
docker load -i dynamicpricingsystem-v1.0.3-docker-image.tar.gz
```

加载完成后会得到镜像 `dynamicpricingsystem:v1.0.3`。

推荐使用单行命令启动，最不容易因为换行符出错：

```bash
docker run --rm -p 8000:8000 -e DPS_SECRET_KEY="replace-with-a-random-secret" -e DPS_DEBUG=0 -v dynamic_pricing_data:/app/data dynamicpricingsystem:v1.0.3
```

如需启动时自动写入演示数据：

```bash
docker run --rm -p 8000:8000 -e DPS_SECRET_KEY="replace-with-a-random-secret" -e DPS_DEBUG=0 -e DPS_SEED_DEMO=1 -v dynamic_pricing_data:/app/data dynamicpricingsystem:v1.0.3
```

Linux/macOS 也可以使用多行命令。注意：每个反斜杠 `\` 必须是该行最后一个字符，后面不能有空格。

```bash
docker run --rm -p 8000:8000 \
  -e DPS_SECRET_KEY="replace-with-a-random-secret" \
  -e DPS_DEBUG=0 \
  -v dynamic_pricing_data:/app/data \
  dynamicpricingsystem:v1.0.3
```

Windows PowerShell 多行命令使用反引号：

```powershell
docker run --rm -p 8000:8000 `
  -e DPS_SECRET_KEY="replace-with-a-random-secret" `
  -e DPS_DEBUG=0 `
  -v dynamic_pricing_data:/app/data `
  dynamicpricingsystem:v1.0.3
```

启动后访问：

- <http://127.0.0.1:8000/>
- <http://localhost:8000/>

容器启动时会自动执行数据库迁移和静态资源收集；`DPS_DEBUG=0` 下也会正常显示页面图片、CSS 等静态资源。

### 本地构建镜像

如果要从源码本地构建镜像：

```bash
docker build -t dynamicpricingsystem:latest .
docker run --rm -p 8000:8000 -e DPS_SECRET_KEY="replace-with-a-random-secret" -e DPS_DEBUG=0 -v dynamic_pricing_data:/app/data dynamicpricingsystem:latest
```

## 常见问题

### docker: invalid reference format

如果使用多行命令时出现：

```text
docker: invalid reference format.
-e: command not found
-v: command not found
```

通常是因为 Linux/macOS 的续行符 `\` 后面有空格，或者复制时把命令拆坏了。请优先使用 README 中的单行命令：

```bash
docker run --rm -p 8000:8000 -e DPS_SECRET_KEY="replace-with-a-random-secret" -e DPS_DEBUG=0 -v dynamic_pricing_data:/app/data dynamicpricingsystem:v1.0.3
```

### 找不到 vX.Y.Z 镜像

`vX.Y.Z` 只是版本占位符。当前 Release 镜像加载后实际标签是：

```text
dynamicpricingsystem:v1.0.3
```

因此启动命令末尾必须使用 `dynamicpricingsystem:v1.0.3`。

## GitHub Actions Release

仓库包含 `.github/workflows/docker-release.yml`。推送 `v*` 标签或手动运行 workflow 时，会：

1. 构建 Docker 镜像；
2. 将镜像保存为 `*.tar.gz`；
3. 创建或更新对应 GitHub Release；
4. 将 Docker 镜像压缩包上传为 Release 附件。

示例：

```bash
git tag v1.0.3
git push origin v1.0.3
```

## 环境变量

| 变量名 | 默认值 | 说明 |
| --- | --- | --- |
| `DPS_SECRET_KEY` | `django-insecure-change-me` | Django Secret Key，生产环境必须覆盖 |
| `DPS_DEBUG` | `1` | 是否开启调试模式，Docker 默认设置为 `0` |
| `DPS_ALLOWED_HOSTS` | `*` | Django 允许访问的 Host，多个值用逗号分隔 |
| `DPS_CSRF_TRUSTED_ORIGINS` | `http://127.0.0.1,http://localhost` | CSRF 信任来源，多个值用逗号分隔。**自 v1.0.3 起**，系统会在每个请求中把 `<scheme>://<Host>`（同时包含 http 与 https）自动追加到信任列表，公网 IP / 域名 / 反向代理 HTTPS 部署不再需要手动配置该变量 |
| `DPS_DATA_DIR` | `price_strategy_system/data` | SQLite 数据库保存目录 |
| `DPS_SEED_DEMO` | 空 | Docker 启动时设为 `1` 会自动执行演示数据初始化 |

### 用域名 / 公网 IP 访问会报「CSRF 验证失败 (403)」吗？

v1.0.3 已修复。系统通过 `DynamicCsrfTrustedOriginsMiddleware` 中间件，把通过 `DPS_ALLOWED_HOSTS` 校验过的 Host 自动加入 CSRF 信任来源，因此：

- 直接用公网 IP（如 `http://1.2.3.4:8000/`）访问后表单提交不会再 403；
- 通过域名（如 `https://pricing.example.com/`）访问也不会再 403；
- 反向代理终结 TLS（浏览器看到 `https://`、容器内 Django 看到 `http://`）的常见部署同样工作。

如需更严格的安全策略，可以把 `DPS_ALLOWED_HOSTS` 显式列为具体域名（而不是默认的 `*`），中间件就只会信任这些域名。

## 开源协议

本项目使用 MIT License，详见 [LICENSE](LICENSE)。
