from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator


class UserContext(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=64, description="Authenticated user id")
    city: str = Field(..., min_length=1, max_length=64, description="Authenticated user's city")


class AuthenticatedUser(BaseModel):
    user_id: str
    city: str
    tenant_id: Optional[str] = None
    roles: list[str] = Field(default_factory=list)
    token_subject: Optional[str] = None

    def to_user_context(self) -> UserContext:
        return UserContext(user_id=self.user_id, city=self.city)


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
            f"City: {self.city}\n"
            f"Condition: {self.condition}\n"
            f"Temperature: {self.temperature_c}C\n"
            f"Humidity: {self.humidity_percent}%\n"
            f"Wind: {self.wind_level}\n"
            f"AQI: {self.aqi}\n"
            f"Rain probability: {self.rain_probability}"
        )


class UserProfile(BaseModel):
    user_id: str
    city: str
    household_profile: str
    available_months: list[str]

    def to_prompt_text(self) -> str:
        months = ", ".join(self.available_months)
        return (
            f"User ID: {self.user_id}\n"
            f"City: {self.city}\n"
            f"Household profile: {self.household_profile}\n"
            f"Available months: {months}"
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
            f"User ID: {self.user_id}\n"
            f"Month: {self.month}\n"
            f"Feature: {self.feature}\n"
            f"Efficiency: {self.efficiency}\n"
            f"Consumables: {self.consumables}\n"
            f"Comparison: {self.comparison}"
        )


class BusinessLookupResult(BaseModel):
    requested_month: Optional[str] = None
    resolved_month: str
    used_latest_available: bool
    usage_record: UsageRecord


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000, description="User chat message")
    user_context: Optional[UserContext] = Field(
        default=None,
        description="Deprecated. User identity now comes from the bearer token.",
    )

    @field_validator("message")
    @classmethod
    def message_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("message must not be blank")
        return v


class ChatResponse(BaseModel):
    mode: Literal["agent", "report_workflow"]
    reply: str
    user_context: UserContext
    report_month: Optional[str] = None
    used_latest_available: bool = False


class ReportRequest(BaseModel):
    user_context: Optional[UserContext] = Field(
        default=None,
        description="Deprecated. User identity now comes from the bearer token.",
    )
    month: Optional[str] = Field(
        default=None,
        pattern=r"^\d{4}-\d{2}$",
        description="Month in YYYY-MM format",
    )


class ReportResponse(BaseModel):
    report: str
    user_context: UserContext
    requested_month: Optional[str] = None
    resolved_month: str
    used_latest_available: bool


class HealthResponse(BaseModel):
    status: Literal["ok"]
