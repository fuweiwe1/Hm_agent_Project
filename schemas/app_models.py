from typing import Literal, Optional

from pydantic import BaseModel, Field


class UserContext(BaseModel):
    user_id: str = Field(..., description="当前请求用户ID")
    city: str = Field(..., description="当前请求用户所在城市")


class WeatherInfo(BaseModel):
    city: str
    condition: str
    temperature_c: int
    humidity_percent: int
    wind_level: str
    aqi: int
    rain_probability: str

    def to_prompt_text(self) -> str:
        return (
            f"城市：{self.city}\n"
            f"天气：{self.condition}\n"
            f"气温：{self.temperature_c}摄氏度\n"
            f"湿度：{self.humidity_percent}%\n"
            f"风力：{self.wind_level}\n"
            f"AQI：{self.aqi}\n"
            f"降雨概率：{self.rain_probability}"
        )


class UserProfile(BaseModel):
    user_id: str
    city: str
    household_profile: str
    available_months: list[str]

    def to_prompt_text(self) -> str:
        months = ", ".join(self.available_months)
        return (
            f"用户ID：{self.user_id}\n"
            f"所在城市：{self.city}\n"
            f"家庭画像：{self.household_profile}\n"
            f"可用记录月份：{months}"
        )


class UsageRecord(BaseModel):
    user_id: str
    month: str
    feature: str
    efficiency: str
    consumables: str
    comparison: str

    def to_prompt_text(self) -> str:
        return (
            f"用户ID：{self.user_id}\n"
            f"月份：{self.month}\n"
            f"家庭画像：{self.feature}\n"
            f"清洁效率：{self.efficiency}\n"
            f"耗材状态：{self.consumables}\n"
            f"同类对比：{self.comparison}"
        )


class BusinessLookupResult(BaseModel):
    requested_month: Optional[str] = None
    resolved_month: str
    used_latest_available: bool
    usage_record: UsageRecord


class ChatRequest(BaseModel):
    message: str
    user_context: UserContext


class ChatResponse(BaseModel):
    mode: Literal["agent", "report_workflow"]
    reply: str
    user_context: UserContext
    report_month: Optional[str] = None
    used_latest_available: bool = False


class ReportRequest(BaseModel):
    user_context: UserContext
    month: Optional[str] = None


class ReportResponse(BaseModel):
    report: str
    user_context: UserContext
    requested_month: Optional[str] = None
    resolved_month: str
    used_latest_available: bool


class HealthResponse(BaseModel):
    status: Literal["ok"]
