import json, re, time, random, os, sys, requests
from typing import List, Dict, Any

# Local SDK client
from client import DataEaseClient
from engine import DataEaseChartEngine

class MultiDataEaseChartEngineV2(DataEaseChartEngine):
    def __init__(self, base_url, ak, sk):
        super().__init__(base_url, ak, sk)

    def extract_chart_payload(self, chart_type: str, dataset_id: str, x_names: list, y_names: list, view_id: str, layout: dict):
        """
        Reads the single chart template, applies parameters, and extracts the componentData & canvasViewInfo.
        """
        base_dir = os.path.dirname(os.path.abspath(__file__))
        # Templates are in the parent directory of 'test' or 'scripts'
        tpl_dir = os.path.join(base_dir, "..", "templates", f"chart_{chart_type}")

        if not os.path.exists(tpl_dir):
            raise FileNotFoundError(f"Template directory {tpl_dir} not found")

        with open(os.path.join(tpl_dir, "template.j2")) as f:
            template_str = f.read()

        with open(os.path.join(tpl_dir, "params.json")) as f:
            raw_params = json.load(f)

        # Build Context (Flatten params + dynamic IDs)
        ctx = {}
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

        # Runtime Randomization
        # SCENE_ID is usually "0" for base
        ctx.update({"VIEW_ID": view_id, "SCENE_ID": "0"})

        # Sub placeholder
        def rep(m):
            k = m.group(1).strip()
            if k in ctx:
                return str(ctx[k])
            return m.group(0)

        rendered = re.sub(r"\{\{\s*(\w+)\s*\}\}", rep, template_str)
        payload = json.loads(rendered)

        # Extract canvasViewInfo
        canvas_view_info = payload.get("canvasViewInfo", {})
        target_view_info = canvas_view_info.get(view_id)
        if not target_view_info:
            raise ValueError(f"View ID {view_id} not found in the rendered template!")

        # Extract componentData
        component_data_str = payload.get("componentData", "[]")
        components = json.loads(component_data_str)
        if not components:
            raise ValueError(f"No component data found in the rendered template")

        # We only take the first component as it was a single chart template
        target_component = components[0]

        # Override layout
        if "layout" in layout:
            layout = layout["layout"] # in case it's nested

        if "style" not in target_component:
            target_component["style"] = {}

        if "x" in layout: target_component["x"] = layout["x"]
        if "y" in layout: target_component["y"] = layout["y"]
        if "sizeX" in layout: target_component["sizeX"] = layout["sizeX"]
        if "sizeY" in layout: target_component["sizeY"] = layout["sizeY"]

        # Ensure pixel-level styling is updated if provided, or calculated if missing
        # DataEase V2 components often use both grid (x, y, sizeX, sizeY) and absolute (width, height, left, top)
        if "width" in layout: target_component["style"]["width"] = layout["width"]
        if "height" in layout: target_component["style"]["height"] = layout["height"]
        if "left" in layout: target_component["style"]["left"] = layout["left"]
        if "top" in layout: target_component["style"]["top"] = layout["top"]

        return target_component, target_view_info

    def deploy_multi(self, title: str, charts_config: List[Dict[str, Any]], dry_run: bool = False):
        """
        Deploy multiple charts into a single dashboard.
        """
        content_id = self.rand_id()
        board_name = f"{title}_{int(time.time())}"

        # Load base dashboard style from template
        base_dir = os.path.dirname(os.path.abspath(__file__))
        dashboard_tpl_path = os.path.join(base_dir, "..", "templates", "dashboard", "base.json")
        if os.path.exists(dashboard_tpl_path):
            with open(dashboard_tpl_path) as f:
                base_tpl = json.load(f)
                canvas_style_data = json.loads(base_tpl.get("canvasStyleData", "{}"))
        else:
            # Fallback
            canvas_style_data = {
                "width": 1920, "height": 1080, "screenAdaptor": "widthFirst",
                "dashboard": {"gap": "yes", "gapSize": 5, "matrixBase": 4}
            }

        final_component_data = []
        final_canvas_view_info = {}
        active_view_ids = []

        # Process each chart sequentially
        for idx, c_conf in enumerate(charts_config):
            view_id = self.rand_id()
            active_view_ids.append(view_id)

            comp_data, view_info = self.extract_chart_payload(
                chart_type=c_conf["type"],
                dataset_id=c_conf["dataset_name"],
                x_names=c_conf.get("x_axis", []),
                y_names=c_conf.get("y_axis", []),
                view_id=view_id,
                layout=c_conf["layout"]
            )

            # Use `_dragId` to maintain unique ordering for DataEase frontend
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

        if dry_run:
            print(f"Dry run: Dashboard '{title}' payload generated.")
            return dashboard_payload

        headers = self.client._get_headers()
        print(f"Deploying multi-chart dashboard '{title}' with {len(charts_config)} charts...")

        save_r = requests.post(
            f"{self.base_url}/dataVisualization/saveCanvas",
            headers=headers, json=dashboard_payload, verify=False, timeout=30
        )

        if save_r.status_code != 200:
            raise Exception(f"saveCanvas failed: {save_r.text}")

        dashboard_id = str(save_r.json()["data"])

        # Publish the new dashboard
        requests.post(
            f"{self.base_url}/dataVisualization/updatePublishStatus",
            headers=headers, verify=False, timeout=30,
            json={
                "id": dashboard_id,
                "name": board_name,
                "activeViewIds": active_view_ids,
                "status": 1,
                "type": "dashboard",
                "mobileLayout": False
            }
        )

        base_preview_url = self.base_url.split('/de2api')[0] if '/de2api' in self.base_url else self.base_url
        return dashboard_id, f"{base_preview_url}/#/preview?dvId={dashboard_id}&dvType=dashboard&ignoreParams=true"
