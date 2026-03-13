from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.errors import AppError
from app.models import AnalysisRequest, AnalysisResult
from app.poker.solver import DecisionRequest, DecisionResponse
from app.services.decision_agent import decide_with_tools
from app.vlm_client import request_plan_suggestion

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="OpenFish")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@app.exception_handler(AppError)
async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content=exc.to_dict())


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"title": "OpenFish"},
    )


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/analyze", response_model=AnalysisResult)
async def analyze(request: AnalysisRequest) -> AnalysisResult:
    plan, raw_response = await request_plan_suggestion(request.image.data_url)
    return AnalysisResult(image=request.image, plan=plan, rawResponse=raw_response)


@app.post("/api/decide", response_model=DecisionResponse)
async def decide(request: DecisionRequest) -> DecisionResponse:
    return await decide_with_tools(request)
