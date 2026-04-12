import os
import sys
import requests
import urllib3
import json

urllib3.disable_warnings()

# Add local path for engine import
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))

from engine import DataEaseChartEngine

def load_dotenv():
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
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

def list_datasets():
    engine = DataEaseChartEngine(BASE_URL, ACCESS_KEY, SECRET_KEY)
    
    url = f"{engine.base_url}/datasetTree/tree"
    headers = engine.client._get_headers()
    resp = requests.post(url, headers=headers, json={"busiFlag": "dataset"}, verify=False, timeout=30)
    
    if resp.status_code != 200:
        print(f"Failed to fetch dataset tree: {resp.text}")
        return

    nodes = resp.json().get('data', [])

    def print_tree(items, indent=""):
        for item in items:
            print(f"{indent}- {item.get('name')} (ID: {item.get('id')}, Type: {item.get('type')})")
            children = item.get('children', [])
            if children:
                print_tree(children, indent + "  ")

    print("Available Datasets:")
    print_tree(nodes)

    # If there are any datasets, try to list fields for one of them
    # Just as an example, fetch fields for the first leaf node
    def find_first_dataset(items):
        for item in items:
            if item.get('type') == 'dataset':
                return item
            children = item.get('children', [])
            if children:
                found = find_first_dataset(children)
                if found: return found
        return None

    first_ds = find_first_dataset(nodes)
    if first_ds:
        print(f"\nFields for dataset '{first_ds['name']}':")
        ds_id = first_ds['id']
        url = f"{engine.base_url}/datasetTree/details/{ds_id}"
        resp = requests.get(url, headers=headers, verify=False, timeout=30)
        if resp.status_code == 200:
            fields = resp.json().get('data', {}).get('allFields', [])
            for f in fields:
                print(f"  - {f['name']} (ID: {f['id']}, Type: {f['deType']}, DE Name: {f['dataeaseName']})")

if __name__ == "__main__":
    if not all([ACCESS_KEY, SECRET_KEY, BASE_URL]):
        print("Missing env vars")
    else:
        list_datasets()
