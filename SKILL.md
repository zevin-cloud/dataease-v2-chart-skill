---
name: dataease
description: 自动化部署 DataEase v2 图表。支持折线图 (line)、柱状图 (bar)、饼图 (pie) 和明细表 (table_info)。
environment:
  required:
    - DATAEASE_ACCESS_KEY
    - DATAEASE_SECRET_KEY
    - DATAEASE_BASE_URL
security:
  requiresSecrets: true
  sensitiveEnvironment: true
  externalNetworkAccess: true
---

# DataEase V2 Chart Skill

该 Skill 允许 AI Agent 通过预定义的模板，在 DataEase v2 仪表板中快速创建和部署图表。它具备自动解析数据集 ID、动态映射字段、生成唯一视觉 ID 以及发布仪表板的能力。

## 核心特性

- **接口驱动**: 直接通过 API 与 DataEase 交互，无需手动操作 UI。
- **模板化配置**: 图表样式、交互事件均由 `templates/` 下的 JSON 模板定义，支持参数化注入。
- **零配置依赖**: 内置 SDK，仅需配置 API 密钥即可运行。
- **多端支持**: 生成的 URL 默认为预览模式，支持立即查看和分享。

## 首次运行配置

1. **准备环境**: 确保已安装 Python 3 及依赖库 `requests`, `pyjwt`, `cryptography`。
2. **配置凭据**:
    - 将 `.env.example` 复制并重命名为 `.env`。
    - 打开 `.env` 并填写您的 `DATAEASE_ACCESS_KEY`, `DATAEASE_SECRET_KEY` 以及 `DATAEASE_BASE_URL`。

```bash
cp .env.example .env
# 然后编辑 .env 填写实际内容
```

```bash
python3 scripts/deploy.py <type> <title> <dataset> <x_fields> <y_fields>
```

### 参数说明

- `type`: 图表类型，可选 `line`, `bar`, `pie`, `table_info`。
- `title`: 期望展示的图表标题。
- `dataset`: 数据集名称（如：年终述职）或 ID。
- `x_fields`: 维度字段名。如果是明细表，可传入逗号分隔的多个字段。
- `y_fields`: 指标字段名，多个指标请用逗号分隔。明细表传空字符串 `''`。

### 示例

```bash
# 生成折线图
python3 scripts/deploy.py line '流量趋势' '电商数据' '日期' '访问量,成交额'

# 生成明细表
python3 scripts/deploy.py table_info '用户信息表' '用户数据集' '姓名,地区,手机号' ''
```

## 开发者说明

- **基础 URL**: 请确保 `DATAEASE_BASE_URL` 包含协议与端口（如 `https://de.example.com:20000/de2api`）。
- **模板自定义**: 修改 `templates/chart_<type>/template.j2` 可定制全局样式与交互逻辑。
- **内置 SDK**: 调用逻辑封装在 `scripts/client.py` 中，采用 AES-CBC 对接 DataEase 签名算法。
