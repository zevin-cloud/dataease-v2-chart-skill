# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Deployment
- **Deploy a chart**: `python3 scripts/deploy.py <type> <title> <dataset_name_or_id> <x_axis_fields> <y_axis_fields>`
  - `type`: `line` or `pie` (`bar` is currently under maintenance).
  - `title`: Desired chart title.
  - `dataset_name_or_id`: Name of the dataset in DataEase or its 19-digit ID.
  - `x_axis_fields`: Dimension field name.
  - `y_axis_fields`: Measure field name(s), comma-separated.
- **Example**: `python3 scripts/deploy.py line 'Sales Trend' 'ecommerce_data' 'platform' 'orders,revenue'`

### Environment Setup
- Required environment variables: `DATAEASE_ACCESS_KEY`, `DATAEASE_SECRET_KEY`, `DATAEASE_BASE_URL`.
- These can be set in a `.env` file in the root directory.

## Code Architecture

### Overview
This repository implements a DataEase V2 Chart Skill. It uses a template-based approach to generate DataEase dashboard JSON payloads and deploy them via the DataEase API.

### Core Components
- **`scripts/engine.py`**: The core logic (`DataEaseChartEngine`).
  - `resolve_dataset_id()`: Resolves dataset names to internal DataEase IDs.
  - `get_dataset_ctx()`: Fetches dataset metadata (field IDs, table IDs) to populate templates.
  - `deploy()`: Orchestrates template loading, parameter substitution, and API calls (`saveCanvas`, `updatePublishStatus`).
- **`scripts/deploy.py`**: CLI wrapper for the engine.
- **`templates/`**: Contains chart-specific templates.
  - `template.j2`: JSON structure of the DataEase dashboard with `{{ PLACEHOLDERS }}`.
  - `params.json`: Default configuration and parameter mapping for the template.
- **SDK Dependency**: Relies on a DataEase SDK located at `/root/code/dataease-tools/dataease_sdk_v2`.

### Important Notes
- **Chart Support**: `line` and `pie` are supported. `bar` is currently hidden/under maintenance in `scripts/deploy.py` and `scripts/engine.py`.
- **ID Generation**: `VIEW_ID` and `CONTENT_ID` are randomized at runtime using `time.time()`.
- **Placeholder Substitution**: Uses a custom regex-based substitution in `engine.py` (not a full Jinja2 engine, despite the `.j2` extension).
- **External Network**: Requires access to the `DATAEASE_BASE_URL` endpoint.
