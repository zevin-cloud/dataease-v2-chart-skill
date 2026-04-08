import json, re, time, random, os, sys, requests
import urllib3
urllib3.disable_warnings()

# Add SDK path
sys.path.append("/root/code/dataease-tools/dataease_sdk_v2")
try:
    from client import DataEaseClient
except ImportError:
    print("Error: DataEase SDK not found at /root/code/dataease-tools/dataease_sdk_v2")
    sys.exit(1)

class DataEaseChartEngine:
    def __init__(self, base_url, ak, sk):
        self.client = DataEaseClient(base_url, ak, sk)
        self.base_url = base_url.rstrip('/')

    def resolve_dataset_id(self, name_or_id):
        """Resolve dataset name to ID using /datasetTree/tree if needed"""
        if str(name_or_id).isdigit() and len(str(name_or_id)) > 10:
            return name_or_id

        url = f"{self.base_url}/datasetTree/tree"
        headers = self.client._get_headers()
        resp = requests.post(url, headers=headers, json={"busiFlag": "dataset"}, verify=False, timeout=30)

        if resp.status_code != 200:
            raise Exception(f"Failed to fetch dataset tree: {resp.text}")

        nodes = resp.json().get('data', [])

        def find_in_tree(items, target_name):
            for item in items:
                if item.get('name') == target_name:
                    return item.get('id')
                children = item.get('children', [])
                if children:
                    found = find_in_tree(children, target_name)
                    if found: return found
            return None

        dataset_id = find_in_tree(nodes, name_or_id)
        if not dataset_id:
            raise ValueError(f"Dataset '{name_or_id}' not found in DataEase")

        return dataset_id

    def get_dataset_ctx(self, dataset_name_or_id, x_names, y_names):
        """Fetch dataset metadata and build rendering context"""
        dataset_id = self.resolve_dataset_id(dataset_name_or_id)

        # DataEase v2 often uses datasetGroup for the tree structure
        url = f"{self.base_url}/datasetTree/details/{dataset_id}"
        headers = self.client._get_headers()
        resp = requests.get(url, headers=headers, verify=False, timeout=30)

        if resp.status_code != 200:
            # Fallback to the original method if the specific tree detail endpoint fails
            resp = self.client.post(f"/datasetField/listByDatasetGroup/{dataset_id}")
            fields = resp.json().get('data', [])
        else:
            data = resp.json().get('data', {})
            fields = data.get('allFields', [])
            if not fields:
                # Try to get from datasetField/listByDatasetGroup if tree details is empty
                resp = self.client.post(f"/datasetField/listByDatasetGroup/{dataset_id}")
                fields = resp.json().get('data', [])

        if not fields:
            raise ValueError(f"No fields found for dataset {dataset_id}")

        f_map = {f['name']: f for f in fields}

        # Get table/datasource IDs from the first field (they should be common)
        datasource_id = fields[0].get('datasourceId', "")
        table_id = fields[0].get('datasetTableId', "")

        ctx = {
            "DATASET_GROUP_ID": dataset_id,
            "DATASOURCE_ID": datasource_id,
            "DATASET_TABLE_ID": table_id,
        }

        # Map axis fields (supports multi-measure if needed)
        for i, name in enumerate(x_names):
            suffix = "" if i == 0 else str(i+1)
            f = f_map.get(name)
            if not f: raise ValueError(f"X-Axis Field '{name}' not found")
            ctx[f"XAXIS{suffix}_FIELD_ID"] = f['id']
            ctx[f"XAXIS{suffix}_DE_NAME"] = f['dataeaseName']

        for i, name in enumerate(y_names):
            suffix = "" if i == 0 else str(i+1)
            f = f_map.get(name)
            if not f: raise ValueError(f"Y-Axis Field '{name}' not found")
            ctx[f"YAXIS{suffix}_FIELD_ID"] = f['id']
            ctx[f"YAXIS{suffix}_DE_NAME"] = f['dataeaseName']
            ctx[f"YAXIS{suffix}_SERIES_ID"] = f"{f['id']}-yAxis"

            # Additional keys for deep parameterization
            if i == 0:
                ctx["YAXIS_FIELD_ID"] = f['id']
                ctx["YAXIS_DE_NAME"] = f['dataeaseName']
                ctx["YAXIS_SERIES_ID"] = f"{f['id']}-yAxis"
            elif i == 1:
                ctx["YAXIS2_FIELD_ID"] = f['id']
                ctx["YAXIS2_DE_NAME"] = f['dataeaseName']
                ctx["YAXIS2_SERIES_ID"] = f"{f['id']}-yAxis"

        return ctx

    def deploy(self, chart_type, title, dataset_id, x_names, y_names):
        # 1. Directory standardization
        # Use relative path from this script (scripts/engine.py) to templates/
        base_dir = os.path.dirname(os.path.abspath(__file__))
        tpl_dir = os.path.join(base_dir, "..", "templates", f"chart_{chart_type}")

        if not os.path.exists(tpl_dir):
            raise FileNotFoundError(f"Template directory {tpl_dir} not found")

        with open(os.path.join(tpl_dir, "template.j2")) as f: template_str = f.read()
        with open(os.path.join(tpl_dir, "params.json")) as f:
            raw_params = json.load(f)

        # 2. Build Context (Flatten params + dynamic IDs)
        ctx = {}
        # Flatten nested params.json
        def flatten_dict(d):
            items = {}
            for k, v in d.items():
                if isinstance(v, dict):
                    items.update(flatten_dict(v))
                elif not k.startswith("_"):
                    items[k] = v
            return items

        ctx.update(flatten_dict(raw_params))
        ctx.update(self.get_dataset_ctx(dataset_id, x_names, y_names))

        # 3. Runtime Randomization
        view_id, content_id = self.rand_id(), self.rand_id()
        ctx.update({"VIEW_ID": view_id, "CONTENT_ID": content_id, "SCENE_ID": "0"})

        # 4. Thorough Parameterization (Global substitution)
        def rep(m):
            k = m.group(1).strip()
            if k in ctx:
                return str(ctx[k])
            return m.group(0) # Keep placeholder if not found

        rendered = re.sub(r"\{\{\s*(\w+)\s*\}\}", rep, template_str)
        payload = json.loads(rendered)

        # 5. Type Closure & Payload Finalization
        board_name = f"{title}_{int(time.time())}"
        payload.update({
            "id": None,
            "name": board_name,
            "type": "dashboard",
            "status": 0,
            "dataState": "ready",
            "selfWatermarkStatus": True,
            "checkVersion": "2.10.20",
            "pid": "0",
            "mobileLayout": False
        })

        headers = self.client._get_headers()
        print(f"Deploying chart '{title}' (Type: {chart_type})...")

        save_r = requests.post(
            f"{self.base_url}/dataVisualization/saveCanvas",
            headers=headers, json=payload, verify=False, timeout=30
        )

        if save_r.status_code != 200:
            raise Exception(f"saveCanvas failed: {save_r.text}")

        dashboard_id = str(save_r.json()["data"])

        # 6. Publish
        requests.post(
            f"{self.base_url}/dataVisualization/updatePublishStatus",
            headers=headers, verify=False, timeout=30,
            json={
                "id": dashboard_id,
                "name": board_name,
                "activeViewIds": [view_id],
                "status": 1,
                "type": "dashboard",
                "mobileLayout": False
            }
        )

        return dashboard_id, f"https://de2.zevin.xin:20000/de2/#/dashboard/{dashboard_id}"

    @staticmethod
    def rand_id():
        return str(int(time.time() * 1000) + random.randint(1000, 9999))
