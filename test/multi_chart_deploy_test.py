import sys
import os
import json

# Add local path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "scripts"))
sys.path.append(os.path.dirname(__file__))

from multi_engine_v2 import MultiDataEaseChartEngineV2

# --- Configuration from Environment ---
def load_dotenv():
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip().strip('"').strip("'")

load_dotenv()

ACCESS_KEY = os.environ.get("DATAEASE_ACCESS_KEY")
SECRET_KEY = os.environ.get("DATAEASE_SECRET_KEY")
BASE_URL   = os.environ.get("DATAEASE_BASE_URL")

def main():
    if not all([ACCESS_KEY, SECRET_KEY, BASE_URL]):
        print("Error: Missing required environment variables.")
        sys.exit(1)

    engine = MultiDataEaseChartEngineV2(BASE_URL, ACCESS_KEY, SECRET_KEY)

    dataset = "电商用户购买行为"
    if len(sys.argv) > 1:
        dataset = sys.argv[1]

    # Real deployment test with 4 charts
    charts_config = [
        {
            "type": "bar",
            "dataset_name": dataset,
            "x_axis": ["访问平台"],
            "y_axis": ["访问次数"],
            "layout": {"x": 1, "y": 1, "sizeX": 36, "sizeY": 14, "width": 519, "height": 65, "left": 0, "top": 0}
        },
        {
            "type": "line",
            "dataset_name": dataset,
            "x_axis": ["访问平台"],
            "y_axis": ["访问次数"],
            "layout": {"x": 37, "y": 1, "sizeX": 36, "sizeY": 14, "width": 519, "height": 65, "left": 519, "top": 0}
        },
        {
            "type": "pie",
            "dataset_name": dataset,
            "x_axis": ["访问平台"],
            "y_axis": ["访问次数"],
            "layout": {"x": 1, "y": 15, "sizeX": 36, "sizeY": 14, "width": 519, "height": 65, "left": 0, "top": 65}
        },
        {
            "type": "table_info",
            "dataset_name": dataset,
            "x_axis": ["访问平台", "访问次数"],
            "layout": {"x": 37, "y": 15, "sizeX": 36, "sizeY": 14, "width": 519, "height": 65, "left": 519, "top": 65}
        }
    ]

    try:
        payload = engine.deploy_multi("多图表端到端测试", charts_config, dry_run=True)
        # Save payload to file for user inspection
        with open("test/last_request_payload.json", "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        print(f"Payload saved to test/last_request_payload.json")

        did, url = engine.deploy_multi("多图表端到端测试", charts_config)
        print(f"\n✅ Successfully deployed multi-chart dashboard!")
        print(f"Dashboard ID: {did}")
        print(f"URL: {url}")
    except Exception as e:
        print(f"\n❌ Deployment failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
