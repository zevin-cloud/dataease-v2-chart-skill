import json
import sys
import os
import time

# Add local paths
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "scripts"))
sys.path.append(os.path.dirname(__file__))

from multi_engine_v2 import MultiDataEaseChartEngineV2

def main():
    # Mock environment for dry-run
    os.environ["DATAEASE_ACCESS_KEY"] = "mock_ak"
    os.environ["DATAEASE_SECRET_KEY"] = "mock_sk"
    os.environ["DATAEASE_BASE_URL"] = "http://mock-dataease.com/de2api"

    # Initialize engine
    engine = MultiDataEaseChartEngineV2("http://mock-dataease.com/de2api", "mock_ak", "mock_sk")

    # Mock resolve_dataset_id and get_dataset_ctx to avoid API calls
    engine.resolve_dataset_id = lambda x: "1234567890123456789"
    engine.get_dataset_ctx = lambda ds, x, y: {
        "DATASET_GROUP_ID": "ds_group_id",
        "DATASOURCE_ID": "ds_id",
        "DATASET_TABLE_ID": "table_id",
        "XAXIS_FIELD_ID": "x_id",
        "XAXIS_DE_NAME": "x_de",
        "XAXIS2_FIELD_ID": "x2_id",
        "XAXIS2_DE_NAME": "x2_de",
        "YAXIS_FIELD_ID": "y_id",
        "YAXIS_DE_NAME": "y_de",
        "YAXIS_SERIES_ID": "y_id-yAxis"
    }

    # Define test configuration with 4 charts (including table)
    charts_config = [
        {
            "type": "bar",
            "dataset_name": "test_ds",
            "x_axis": ["field1"],
            "y_axis": ["field2"],
            "layout": {"x": 1, "y": 1, "sizeX": 36, "sizeY": 14, "width": 519, "height": 65, "left": 0, "top": 0}
        },
        {
            "type": "line",
            "dataset_name": "test_ds",
            "x_axis": ["field1"],
            "y_axis": ["field2"],
            "layout": {"x": 37, "y": 1, "sizeX": 36, "sizeY": 14, "width": 519, "height": 65, "left": 519, "top": 0}
        },
        {
            "type": "pie",
            "dataset_name": "test_ds",
            "x_axis": ["field1"],
            "y_axis": ["field2"],
            "layout": {"x": 1, "y": 15, "sizeX": 36, "sizeY": 14, "width": 519, "height": 65, "left": 0, "top": 65}
        },
        {
            "type": "table_info",
            "dataset_name": "test_ds",
            "x_axis": ["field1", "field2"],
            "layout": {"x": 37, "y": 15, "sizeX": 36, "sizeY": 14, "width": 519, "height": 65, "left": 519, "top": 65}
        }
    ]

    print("--- Starting Dry Run (Payload Generation Only) ---")

    # Run deploy_multi in dry_run mode
    payload = engine.deploy_multi("Four Charts Test", charts_config, dry_run=True)

    print("\nGenerated Dashboard Payload (Summary):")
    component_data = json.loads(payload["componentData"])
    print(f"Number of components: {len(component_data)}")
    print(f"Canvas View Info keys: {list(payload['canvasViewInfo'].keys())}")

    # Check each component type and layout
    for idx, comp in enumerate(component_data):
        print(f"\nComponent {idx} ({comp.get('innerType')}):")
        print(f"  ID: {comp.get('id')}")
        print(f"  _dragId: {comp.get('_dragId')}")
        print(f"  Layout: x={comp.get('x')}, y={comp.get('y')}, sizeX={comp.get('sizeX')}, sizeY={comp.get('sizeY')}")
        print(f"  Style: left={comp.get('style', {}).get('left')}, top={comp.get('style', {}).get('top')}")

    # Save to file for inspection
    base_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(base_dir, "generated_payload_4_charts.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    print(f"\nFull payload saved to {output_path}")
    print("\nDry run completed successfully.")

if __name__ == "__main__":
    main()
