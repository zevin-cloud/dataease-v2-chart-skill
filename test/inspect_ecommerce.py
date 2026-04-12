import os, json, sys, requests
sys.path.append(os.path.join(os.getcwd(), "scripts"))
from client import DataEaseClient

def load_dotenv():
    env_path = ".env"
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip().strip('"').strip("'")

load_dotenv()
ak = os.environ.get("DATAEASE_ACCESS_KEY")
sk = os.environ.get("DATAEASE_SECRET_KEY")
url = os.environ.get("DATAEASE_BASE_URL")
client = DataEaseClient(url, ak, sk)

target_ds = "电商用户购买行为"
headers = client._get_headers()
# Resolve ID
resp = requests.post(f"{url.rstrip('/')}/datasetTree/tree", headers=headers, json={"busiFlag": "dataset"}, verify=False)
nodes = resp.json().get('data', [])
def find_id(items, name):
    if not items: return None
    for i in items:
        if i.get('name') == name: return i.get('id')
        res = find_id(i.get('children'), name)
        if res: return res
    return None
ds_id = find_id(nodes, target_ds)
print(f"Dataset: {target_ds}, ID: {ds_id}")

# Fetch fields
resp_f = client.post(f"/datasetField/listByDatasetGroup/{ds_id}")
fields = resp_f.json().get('data', [])
for f in fields:
    print(f"- {f['name']} (Type: {f.get('deType')})")
