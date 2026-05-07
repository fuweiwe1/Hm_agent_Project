from fastapi import FastAPI, HTTPException

from schemas.app_models import (
    ChatRequest,
    ChatResponse,
    HealthResponse,
    ReportRequest,
    ReportResponse,
    UserProfile,
    UserContext,
    UsageRecord,
    WeatherInfo,
)
from services.business_service import get_business_service
from services.chat_service import ChatService
from services.report_workflow import ReportWorkflowService

app = FastAPI(title="Robot Agent API", version="1.0.0")

business_service = get_business_service()
chat_service = ChatService(business_service)
report_workflow = ReportWorkflowService(business_service)


@app.get("/health", response_model=HealthResponse)
def health_check():
    return HealthResponse(status="ok")


@app.get("/business/users", response_model=list[str])
def list_users():
    return business_service.list_user_ids()


@app.get("/business/users/{user_id}", response_model=UserProfile)
def get_user_profile(user_id: str, city: str):
    try:
        return business_service.get_user_profile(UserContext(user_id=user_id, city=city))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/business/users/{user_id}/usage-records/latest", response_model=UsageRecord)
def get_latest_usage_record(user_id: str):
    try:
        return business_service.get_latest_usage_record(user_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/business/users/{user_id}/usage-records/{month}", response_model=UsageRecord)
def get_usage_record(user_id: str, month: str):
    try:
        return business_service.get_usage_record(user_id, month)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/business/current-month", response_model=str)
def get_current_month():
    return business_service.get_current_month()


@app.get("/business/weather/{city}", response_model=WeatherInfo)
def get_weather(city: str):
    return business_service.get_weather(city)


@app.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    try:
        return chat_service.handle(request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/api/report", response_model=ReportResponse)
def build_report(request: ReportRequest):
    try:
        return report_workflow.generate_report(request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
