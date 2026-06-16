import threading
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

from app.graph.builder import build_graph
from app.data.platform_rules import PLATFORM_RULES, ASSET_TYPES
from app.schemas.requests import BatchGenerateRequest, GenerateRequest
from app import jobs

app = FastAPI(title="Ecom Visual Factory", version="0.1.0")
graph = build_graph()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/v1/examples")
def get_examples() -> dict:
    return {
        "smart_detail": {
            "product_name": "智能保温杯",
            "brand": "METIS",
            "product_type": "家居",
            "target_market": "美国",
            "selling_points": ["316不锈钢内胆", "12小时长效保温"],
            "specs": {"text": "容量：500ml / 材质：316不锈钢"},
            "constraints": {
                "platform": "amazon",
                "generation_mode": "smart_detail",
                "enable_web_enhancement": False,
                "enable_image_generation": False,
            }
        },
        "custom_assets_detail": {
            "product_name": "蓝牙耳机",
            "brand": "SoundPro",
            "product_type": "数码",
            "target_market": "美国",
            "selling_points": ["主动降噪", "续航40小时"],
            "specs": {"text": "蓝牙5.3，IPX5防水"},
            "asset_types": [
                {"type_name": "主图", "count": 3},
                {"type_name": "使用场景图", "count": 2},
            ],
            "constraints": {
                "platform": "amazon",
                "generation_mode": "custom_assets",
                "include_detail_screens": True,
                "enable_web_enhancement": False,
                "enable_image_generation": False,
            }
        },
        "custom_assets_no_detail": {
            "product_name": "蓝牙耳机",
            "brand": "SoundPro",
            "product_type": "数码",
            "target_market": "美国",
            "selling_points": ["主动降噪", "续航40小时"],
            "specs": {"text": "蓝牙5.3，IPX5防水"},
            "asset_types": [
                {"type_name": "主图", "count": 3},
                {"type_name": "使用场景图", "count": 2},
            ],
            "constraints": {
                "platform": "amazon",
                "generation_mode": "custom_assets",
                "include_detail_screens": False,
                "enable_web_enhancement": False,
                "enable_image_generation": False,
            }
        },
        "hybrid": {
            "product_name": "智能运动手环",
            "brand": "FitTrack",
            "product_type": "数码",
            "target_market": "美国",
            "selling_points": ["心率监测", "血氧检测", "IP68防水"],
            "specs": {"text": "1.5寸AMOLED，续航14天"},
            "asset_types": [
                {"type_name": "主图", "count": 2},
                {"type_name": "使用场景图", "count": 1},
            ],
            "constraints": {
                "platform": "tmall",
                "generation_mode": "hybrid",
                "enable_web_enhancement": False,
                "enable_image_generation": False,
            }
        }
    }


@app.get("/api/v1/platforms")
def list_platforms() -> dict:
    return {"platforms": list(PLATFORM_RULES.keys())}


@app.get("/api/v1/platform-rules/{platform_key}")
def get_platform_rules(platform_key: str) -> dict:
    if platform_key not in PLATFORM_RULES:
        raise HTTPException(status_code=404, detail=f"Platform '{platform_key}' not found")
    return PLATFORM_RULES[platform_key]


@app.post("/api/v1/generate")
def generate(payload: GenerateRequest) -> dict:
    state = payload.to_state()
    return graph.invoke(state)


@app.post("/api/v1/jobs")
def create_job(payload: GenerateRequest) -> dict:
    job_id = jobs.create_job(payload.model_dump())
    t = threading.Thread(
        target=jobs.run_job,
        args=(job_id, graph.invoke, payload.model_dump()),
        daemon=True
    )
    t.start()
    return {"job_id": job_id, "status": "pending"}


@app.get("/api/v1/jobs/{job_id}")
def get_job_status(job_id: str) -> dict:
    j = jobs.get_job(job_id)
    if j is None:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    resp = {"job_id": j["job_id"], "status": j["status"]}
    if j["result"] is not None:
        resp["result"] = j["result"]
    if j["error"] is not None:
        resp["error"] = j["error"]
    return resp


@app.post("/api/v1/batch-generate")
def batch_generate(payload: BatchGenerateRequest) -> dict:
    results = []
    for item in payload.items:
        results.append(graph.invoke(item.to_state()))
    return {"count": len(results), "results": results}


@app.get("/")
def index() -> HTMLResponse:
    html_path = Path(__file__).resolve().parent / "static" / "index.html"
    if html_path.exists():
        return HTMLResponse(content=html_path.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>index.html not found</h1>", status_code=404)
