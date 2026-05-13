from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from api.auth import ensure_current_user_access, get_authenticated_user, get_user_context
from api.request_id import RequestIdMiddleware
from api.security import SecurityHeadersMiddleware
from schemas.app_models import (
    AuthenticatedUser,
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
from utils.logger_handler import logger

# ── 限流器 ──
limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])

app = FastAPI(title="Robot Agent API", version="1.0.0")

# 中间件（注册顺序：最后注册的最先执行）
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestIdMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应替换为具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 限流
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

business_service = get_business_service()
chat_service = ChatService(business_service)
report_workflow = ReportWorkflowService(business_service)


@app.get("/health", response_model=HealthResponse)
def health_check():
    try:
        business_service.list_user_ids()
    except Exception as exc:
        logger.error("health_check_db_failed", extra={"error": str(exc)[:200]})
        raise HTTPException(status_code=503, detail="database unhealthy") from exc
    return HealthResponse(status="ok")


@app.get("/auth/me", response_model=AuthenticatedUser)
def auth_me(current_user: AuthenticatedUser = Depends(get_authenticated_user)):
    return current_user


@app.get("/business/users", response_model=list[str])
def list_users(user_context: UserContext = Depends(get_user_context)):
    return [user_context.user_id]


@app.get("/business/me", response_model=UserProfile)
def get_my_profile(user_context: UserContext = Depends(get_user_context)):
    try:
        return business_service.get_user_profile(user_context)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/business/users/{user_id}", response_model=UserProfile)
def get_user_profile(user_id: str, current_user: AuthenticatedUser = Depends(get_authenticated_user)):
    try:
        ensure_current_user_access(user_id, current_user)
        return business_service.get_user_profile(current_user.to_user_context())
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/business/me/months", response_model=list[str])
def list_my_months(user_context: UserContext = Depends(get_user_context)):
    try:
        return business_service.list_available_months(user_context.user_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/business/users/{user_id}/months", response_model=list[str])
def list_user_months(user_id: str, current_user: AuthenticatedUser = Depends(get_authenticated_user)):
    try:
        ensure_current_user_access(user_id, current_user)
        return business_service.list_available_months(user_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/business/me/usage-records/latest", response_model=UsageRecord)
def get_my_latest_usage_record(user_context: UserContext = Depends(get_user_context)):
    try:
        return business_service.get_latest_usage_record(user_context.user_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/business/users/{user_id}/usage-records/latest", response_model=UsageRecord)
def get_latest_usage_record(user_id: str, current_user: AuthenticatedUser = Depends(get_authenticated_user)):
    try:
        ensure_current_user_access(user_id, current_user)
        return business_service.get_latest_usage_record(user_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/business/me/usage-records/{month}", response_model=UsageRecord)
def get_my_usage_record(month: str, user_context: UserContext = Depends(get_user_context)):
    try:
        return business_service.get_usage_record(user_context.user_id, month)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/business/users/{user_id}/usage-records/{month}", response_model=UsageRecord)
def get_usage_record(
    user_id: str,
    month: str,
    current_user: AuthenticatedUser = Depends(get_authenticated_user),
):
    try:
        ensure_current_user_access(user_id, current_user)
        return business_service.get_usage_record(user_id, month)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/business/current-month", response_model=str)
def get_current_month(_: AuthenticatedUser = Depends(get_authenticated_user)):
    return business_service.get_current_month()


@app.get("/business/weather/{city}", response_model=WeatherInfo)
def get_weather(city: str, _: AuthenticatedUser = Depends(get_authenticated_user)):
    return business_service.get_weather(city)


@app.post("/api/chat", response_model=ChatResponse)
@limiter.limit("10/minute")
def chat(request: Request, body: ChatRequest, user_context: UserContext = Depends(get_user_context)):
    try:
        return chat_service.handle(body, user_context)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/api/report", response_model=ReportResponse)
@limiter.limit("5/minute")
def build_report(request: Request, body: ReportRequest, user_context: UserContext = Depends(get_user_context)):
    try:
        return report_workflow.generate_report(body, user_context=user_context)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        logger.error("report_endpoint_failed", extra={"error": str(exc)[:300]})
        raise HTTPException(status_code=503, detail="报告生成服务暂时不可用，请稍后重试。") from exc
