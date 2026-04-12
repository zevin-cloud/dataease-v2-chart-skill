import os
import json
import sys

# Add scripts to path
sys.path.append(os.path.join(os.getcwd(), "scripts"))

from engine import DataEaseChartEngine

def main():
    # Load environment variables from .env
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

    if not all([ak, sk, url]):
        print("Missing environment variables.")
        return

    engine = DataEaseChartEngine(url, ak, sk)

    # 1. Fetch dataset tree to find available datasets
    try:
        headers = engine.client._get_headers()
        import requests
        resp = requests.post(f"{url.rstrip('/')}/datasetTree/tree", headers=headers, json={"busiFlag": "dataset"}, verify=False)
        if resp.status_code == 200:
            nodes = resp.json().get('data', [])

            def list_datasets(items):
                datasets = []
                for item in items:
                    if item.get('leaf'):
                        datasets.append((item.get('name'), item.get('id')))
                    children = item.get('children', [])
                    if children:
                        datasets.extend(list_datasets(children))
                return datasets

            all_datasets = list_datasets(nodes)
            print("Available Datasets:")
            for name, ds_id in all_datasets:
                print(f"- {name} (ID: {ds_id})")

            # Pick a dataset other than "电商用户购买行为"
            target_ds = None
            for name, ds_id in all_datasets:
                if name != "电商用户购买行为":
                    target_ds = name
                    break

            if target_ds:
                print(f"\nSelected Dataset: {target_ds}")
                # 2. Fetch fields for the selected dataset
                # We can use get_dataset_ctx logic but simplified
                ds_id = engine.resolve_dataset_id(target_ds)
                url_detail = f"{url.rstrip('/')}/datasetTree/details/{ds_id}"
                resp_f = requests.get(url_detail, headers=headers, verify=False)
                fields = []
                if resp_f.status_code == 200:
                    fields = resp_f.json().get('data', {}).get('allFields', [])

                if not fields:
                    resp_f = engine.client.post(f"/datasetField/listByDatasetGroup/{ds_id}")
                    fields = resp_f.json().get('data', [])

                print("\nFields:")
                for f in fields:
                    print(f"- {f['name']} (Type: {f.get('deType')}, ID: {f['id']})")
        else:
            print(f"Failed to fetch tree: {resp.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
