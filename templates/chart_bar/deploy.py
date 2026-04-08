"""
deploy.py  ——  从 template.j2 + params.json 创建 DataEase 仪表板
用法: python3 deploy.py
适用: chart_line / chart_bar / chart_pie（放在各自目录下即可）
"""
import json, sys, re, time, os, requests

sys.path.append("/root/code/dataease-tools/dataease_sdk_v2")
from client import DataEaseClient

ACCESS_KEY = "VoHddKYWG3PTp1IS"
SECRET_KEY = "89kNcEeLdSWLkFWA"
BASE_URL   = "https://de2.zevin.xin:20000/de2api"

HERE          = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_FILE = os.path.join(HERE, "template.j2")
PARAMS_FILE   = os.path.join(HERE, "params.json")


def render(template: str, ctx: dict) -> str:
    def rep(m):
        k = m.group(1).strip()
        if k not in ctx:
            raise KeyError(f"占位符 '{k}' 不在 ctx 中")
        return ctx[k]
    return re.sub(r"\{\{\s*(\w+)\s*\}\}", rep, template)


def flatten(p: dict) -> dict:
    """把嵌套 params.json 拍平为 {KEY: value}"""
    out = {}
    for v in p.values():
        if isinstance(v, dict):
            for v2 in v.values():
                if isinstance(v2, dict):
                    out.update(v2)
            for k2, v2 in v.items():
                if isinstance(v2, str) and not k2.startswith("_"):
                    out[k2] = v2
    return out


def main():
    with open(PARAMS_FILE) as f:
        params = flatten(json.load(f))
    with open(TEMPLATE_FILE) as f:
        template = f.read()

    print("已加载参数:", list(params.keys()))

    # 先用 params 里的占位值渲染（SCENE_ID 会在 saveCanvas 后被真实 ID 替代）
    rendered  = render(template, params)
    payload   = json.loads(rendered)
    view_id   = list(payload["canvasViewInfo"].keys())[0]
    board_name = os.path.basename(HERE) + "_" + str(int(time.time()))

    payload.update({
        "id": None, "name": board_name, "pid": "0",
        "type": "dashboard", "status": 0,
        "dataState": "ready", "selfWatermarkStatus": True,
        "checkVersion": "2.10.20", "mobileLayout": False
    })

    client  = DataEaseClient(BASE_URL, ACCESS_KEY, SECRET_KEY)
    headers = client._get_headers()

    # Step 1: saveCanvas（一步创建 + 写入图表数据）
    print("\n── saveCanvas ──")
    r = requests.post(
        f"{BASE_URL}/dataVisualization/saveCanvas",
        headers=headers, json=payload, verify=False, timeout=30
    )
    print(f"  → {r.status_code}")
    if r.status_code != 200:
        print("  !!", r.text[:400])
        return

    dashboard_id = str(r.json()["data"])
    print(f"  仪表板 ID = {dashboard_id}")

    # Step 2: 发布
    print("\n── 发布 ──")
    r = requests.post(
        f"{BASE_URL}/dataVisualization/updatePublishStatus",
        headers=headers, verify=False, timeout=30,
        json={
            "id": dashboard_id, "name": board_name,
            "mobileLayout": False, "activeViewIds": [view_id],
            "status": 1, "type": "dashboard"
        }
    )
    print(f"  → {r.status_code}")
    if r.status_code != 200:
        print("  !!", r.text[:400])
        return

    print(f"\n✅ 完成！访问地址：")
    print(f"   https://de2.zevin.xin:20000/de2/#/dashboard/{dashboard_id}")


if __name__ == "__main__":
    main()
