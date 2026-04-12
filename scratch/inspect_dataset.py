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

def inspect_dataset(name):
    sdk_path = os.environ.get("DATAEASE_SDK_PATH", "")
    if sdk_path and sdk_path not in sys.path:
        sys.path.append(sdk_path)
        
    engine = DataEaseChartEngine(BASE_URL, ACCESS_KEY, SECRET_KEY)
    
    try:
        ds_id = engine.resolve_dataset_id(name)
        print(f"Dataset '{name}' ID: {ds_id}")
        
        headers = engine.client._get_headers()
        url = f"{engine.base_url}/datasetField/listByDatasetGroup/{ds_id}"
        resp = requests.post(url, headers=headers, verify=False, timeout=30)
        
        if resp.status_code == 200:
            fields = resp.json().get('data', [])
            print(f"\nFields for dataset '{name}':")
            for f in fields:
                print(f"  - {f['name']} (ID: {f['id']}, Type: {f['deType']}, GroupType: {f.get('groupType')})")
        else:
            print(f"Failed to fetch details: {resp.text}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        inspect_dataset("年终述职")
    else:
        inspect_dataset(sys.argv[1])
