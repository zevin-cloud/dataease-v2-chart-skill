---
name: dataease
description: Deploy parameterized charts to DataEase v2. Trigger when users ask for "分析" (analysis) or to create charts (折线图, 柱状图, 饼图). Currently only line charts (line) are fully supported. Bar charts (bar) are hidden pending fixes.
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

This skill allows you to deploy DataEase v2 charts using standardized templates. It automatically resolves dataset names to IDs and generates unique IDs for each deployment.

**Triggering:** This skill should be triggered whenever the user asks for data "分析" (analysis), or explicitly asks to generate a chart.

**Note on Chart Types:** Currently, **ONLY `line` (折线图)** and **`pie` (饼图)** charts are fully supported and should be recommended to the user. **DO NOT** suggest or use the `bar` (柱状图) chart type, as it is currently under maintenance and hidden. If a user asks for a bar chart, gently suggest a line or pie chart instead.

## Features

- **Dataset Discovery**: Pass the dataset name (e.g., "电商用户购买行为") and the skill finds the ID.
- **ID Randomization**: Generates unique `VIEW_ID` and `CONTENT_ID` at runtime.
- **Multi-Measure Support**: Supports multiple metrics for line charts.
- **Template Based**: Easy to extend with new chart types.

## Installation

```bash
# This is a local skill in this repository
```

## Environment Variables

The following environment variables are required:

```bash
DATAEASE_ACCESS_KEY=your_access_key
DATAEASE_SECRET_KEY=your_secret_key
DATAEASE_BASE_URL=https://your-dataease-domain/api
```

## Usage

```bash
python3 scripts/deploy.py <type> <title> <dataset_name_or_id> <x_axis_fields> <y_axis_fields>
```

### Parameters

- `type`: `line` or `pie`. (Do not use `bar`).
- `title`: Chart title.
- `dataset_name_or_id`: Dataset name or 19-digit ID.
- `x_axis_fields`: Dimension field name.
- `y_axis_fields`: Measure field name(s), comma-separated.

### Example

```bash
python3 scripts/deploy.py line 'Sales Trend' '电商用户购买行为' '访问平台' '访问次数,浏览量'
```
