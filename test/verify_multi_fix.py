import json, os, sys
from typing import List, Dict, Any

# Add scripts to path
sys.path.append(os.path.join(os.getcwd(), "scripts"))

from multi_engine import MultiDataEaseChartEngine

def main():
    # Load environment variables
    env_path = ".env"
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip().strip('"').strip("'")

    ak = os.environ.get("DATAEASE_ACCESS_KEY")
    sk = os.environ.get("DATAEASE_SECRET_KEY")
    url = os.environ.get("DATAEASE_BASE_URL")

    engine = MultiDataEaseChartEngine(url, ak, sk)

    charts_config = [
        {
            "type": "bar",
            "title": "门店成交额(柱状图)",
            "dataset_name": "关联数据集",
            "x_axis": ["销售门店"],
            "y_axis": ["成交价格"]
        },
        {
            "type": "line",
            "title": "门店成交额(折线图)",
            "dataset_name": "关联数据集",
            "x_axis": ["销售门店"],
            "y_axis": ["成交价格"]
        },
        {
            "type": "pie",
            "title": "门店成交额(饼图)",
            "dataset_name": "关联数据集",
            "x_axis": ["销售门店"],
            "y_axis": ["成交价格"]
        }
    ]

    # We need to mock some parts of deploy_multi to just get the payload
    # or just run it and catch the payload before it's sent.
    # Actually, I'll modify deploy_multi in the engine to return the payload if dry_run=True

    # But wait, I can just manually call the logic
    print("Generating multi-chart dashboard payload...")

    # We'll use a slightly modified version of deploy_multi logic here to save the payload
    content_id = engine.rand_id()
    title = "测试多图表修复"
    board_name = f"{title}_{int(1234567890)}"

    canvas_style_data = {
        "width": 1920, "height": 1080, "screenAdaptor": "widthFirst",
        "dashboard": {"gap": "yes", "gapSize": 5, "matrixBase": 4}
    }

    final_component_data = []
    final_canvas_view_info = {}
    active_view_ids = []

    CHART_WIDTH = 36
    CHART_HEIGHT = 14

    for idx, c_conf in enumerate(charts_config):
        view_id = f"view_{idx}_{engine.rand_id()}"
        active_view_ids.append(view_id)

        row = idx // 2
        col = idx % 2
        layout = {
            "x": col * CHART_WIDTH + 1,
            "y": row * CHART_HEIGHT + 1,
            "sizeX": CHART_WIDTH,
            "sizeY": CHART_HEIGHT,
            "width": 519, "height": 65,
            "left": col * 519, "top": row * 65
        }

        comp_data, view_info = engine.extract_chart_payload(
            chart_type=c_conf["type"],
            dataset_id=c_conf["dataset_name"],
            x_names=c_conf.get("x_axis", []),
            y_names=c_conf.get("y_axis", []),
            view_id=view_id,
            layout=layout,
            title=c_conf.get("title")
        )

        comp_data["_dragId"] = idx
        final_component_data.append(comp_data)
        final_canvas_view_info[view_id] = view_info

    dashboard_payload = {
        "id": None,
        "name": board_name,
        "type": "dashboard",
        "status": 0,
        "dataState": "ready",
        "selfWatermarkStatus": True,
        "checkVersion": "2.10.20",
        "pid": "0",
        "mobileLayout": False,
        "canvasStyleData": json.dumps(canvas_style_data, separators=(',', ':'), ensure_ascii=False),
        "componentData": json.dumps(final_component_data, separators=(',', ':'), ensure_ascii=False),
        "canvasViewInfo": final_canvas_view_info,
        "contentId": content_id
    }

    output_file = "test/multi_fix_payload.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(dashboard_payload, f, indent=2, ensure_ascii=False)

    print(f"Payload saved to {output_file}")

    # Check for forbidden strings
    with open(output_file, "r", encoding="utf-8") as f:
        content = f.read()
        for forbidden in ["访问平台", "访问次数", "浏览量"]:
            if forbidden in content:
                print(f"WARNING: Found forbidden string '{forbidden}' in payload!")
            else:
                print(f"SUCCESS: No '{forbidden}' found in payload.")

if __name__ == "__main__":
    main()
