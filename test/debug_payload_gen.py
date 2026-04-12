import json, re, time, random, os, sys, requests
from typing import List, Dict, Any
import urllib3
urllib3.disable_warnings()

# Add scripts to path for imports
sys.path.append(os.path.join(os.getcwd(), "scripts"))
from client import DataEaseClient

class DebugDataEaseEngine:
    def __init__(self, base_url, ak, sk):
        self.client = DataEaseClient(base_url, ak, sk)
        self.base_url = base_url.rstrip('/')

    def resolve_dataset_id(self, name_or_id):
        if str(name_or_id).isdigit() and len(str(name_or_id)) > 10:
            return name_or_id
        url = f"{self.base_url}/datasetTree/tree"
        headers = self.client._get_headers()
        resp = requests.post(url, headers=headers, json={"busiFlag": "dataset"}, verify=False, timeout=30)
        nodes = resp.json().get('data', [])
        def find_in_tree(items, target_name):
            for item in items:
                if item.get('name') == target_name: return item.get('id')
                children = item.get('children', [])
                if children:
                    found = find_in_tree(children, target_name)
                    if found: return found
            return None
        return find_in_tree(nodes, name_or_id)

    def get_dataset_ctx(self, dataset_name_or_id, x_names, y_names):
        dataset_id = self.resolve_dataset_id(dataset_name_or_id)
        resp = self.client.post(f"/datasetField/listByDatasetGroup/{dataset_id}")
        fields = resp.json().get('data', [])
        f_map = {f['name']: f for f in fields}
        datasource_id = fields[0].get('datasourceId', "")
        table_id = fields[0].get('datasetTableId', "")
        ctx = {"DATASET_GROUP_ID": dataset_id, "DATASOURCE_ID": datasource_id, "DATASET_TABLE_ID": table_id}
        for i, name in enumerate(x_names):
            suffix = "" if i == 0 else str(i+1)
            f = f_map.get(name)
            ctx[f"XAXIS{suffix}_FIELD_ID"] = f['id']
            ctx[f"XAXIS{suffix}_DE_NAME"] = f['dataeaseName']
        for i, name in enumerate(y_names):
            suffix = "" if i == 0 else str(i+1)
            f = f_map.get(name)
            ctx[f"YAXIS{suffix}_FIELD_ID"] = f['id']
            ctx[f"YAXIS{suffix}_DE_NAME"] = f['dataeaseName']
            ctx[f"YAXIS{suffix}_SERIES_ID"] = f"{f['id']}-yAxis"
        return ctx

    def debug_deploy(self, chart_type, title, dataset_id, x_names, y_names):
        base_dir = os.getcwd()
        tpl_dir = os.path.join(base_dir, "templates", f"chart_{chart_type}")
        with open(os.path.join(tpl_dir, "template.j2")) as f: template_str = f.read()
        with open(os.path.join(tpl_dir, "params.json")) as f: raw_params = json.load(f)

        ctx = {}
        def flatten_dict(d):
            items = {}
            for k, v in d.items():
                if isinstance(v, dict): items.update(flatten_dict(v))
                elif not k.startswith("_"): items[k] = v
            return items
        ctx.update(flatten_dict(raw_params))
        dataset_ctx = self.get_dataset_ctx(dataset_id, x_names, y_names)
        ctx.update(dataset_ctx)
        view_id, content_id = str(int(time.time() * 1000)), str(int(time.time() * 1000) + 1)
        ctx.update({"VIEW_ID": view_id, "CONTENT_ID": content_id, "SCENE_ID": "0"})

        def rep(m):
            k = m.group(1).strip()
            return str(ctx[k]) if k in ctx else m.group(0)
        rendered = re.sub(r"\{\{\s*(\w+)\s*\}\}", rep, template_str)
        payload = json.loads(rendered)

        if "canvasViewInfo" in payload and view_id in payload["canvasViewInfo"]:
            view_info = payload["canvasViewInfo"][view_id]
            view_info["title"] = title
            def deep_update(obj, target_id, new_name):
                if isinstance(obj, dict):
                    if str(obj.get("id")) == str(target_id):
                        obj["name"] = new_name
                        obj["description"] = new_name
                        obj["originName"] = new_name
                        if "dbFieldName" in obj: obj["dbFieldName"] = None
                    for v in obj.values(): deep_update(v, target_id, new_name)
                elif isinstance(obj, list):
                    for item in obj: deep_update(item, target_id, new_name)
            for i, name in enumerate(x_names):
                f_id = dataset_ctx.get(f"XAXIS{'' if i==0 else i+1}_FIELD_ID")
                if f_id: deep_update(view_info, f_id, name)
            for i, name in enumerate(y_names):
                f_id = dataset_ctx.get(f"YAXIS{'' if i==0 else i+1}_FIELD_ID")
                if f_id: deep_update(view_info, f_id, name)

        if "componentData" in payload:
            components = json.loads(payload["componentData"])
            if components:
                components[0]["name"] = title
                components[0]["label"] = title
                payload["componentData"] = json.dumps(components, separators=(',', ':'), ensure_ascii=False)

        if "canvasStyleData" in payload:
            payload["canvasStyleData"] = json.dumps(json.loads(payload["canvasStyleData"]), separators=(',', ':'), ensure_ascii=False)

        # Save the exact payload to a file for the user to inspect
        debug_file = "test/final_debug_payload.json"
        with open(debug_file, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        print(f"DEBUG: Payload saved to {debug_file}")
        return payload

if __name__ == "__main__":
    ak, sk, url = "VoHddKYWG3PTp1IS", "89kNcEeLdSWLkFWA", "https://de2.zevin.xin:20000/de2api"
    engine = DebugDataEaseEngine(url, ak, sk)
    engine.debug_deploy("bar", "各门店成交额", "关联数据集", ["销售门店"], ["成交价格"])
