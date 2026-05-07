from datetime import datetime
from functools import lru_cache

from repositories.business_repository import BusinessRepository, create_business_repository
from schemas.app_models import BusinessLookupResult, UsageRecord, UserProfile, UserContext, WeatherInfo


CITY_WEATHER = {
    "深圳": WeatherInfo(
        city="深圳",
        condition="多云",
        temperature_c=29,
        humidity_percent=72,
        wind_level="南风2级",
        aqi=24,
        rain_probability="未来2小时较低",
    ),
    "合肥": WeatherInfo(
        city="合肥",
        condition="晴",
        temperature_c=27,
        humidity_percent=55,
        wind_level="东南风2级",
        aqi=38,
        rain_probability="未来2小时极低",
    ),
    "杭州": WeatherInfo(
        city="杭州",
        condition="阴转多云",
        temperature_c=26,
        humidity_percent=68,
        wind_level="东风2级",
        aqi=31,
        rain_probability="晚间小概率降雨",
    ),
}


class BusinessService:
    def __init__(self, repository: BusinessRepository):
        self.repository = repository

    def list_user_ids(self) -> list[str]:
        return self.repository.list_user_ids()

    def list_available_months(self, user_id: str) -> list[str]:
        months = self.repository.list_available_months(user_id)
        if not months:
            raise KeyError(f"用户 {user_id} 不存在")
        return months

    def get_current_month(self) -> str:
        return datetime.now().strftime("%Y-%m")

    def get_user_profile(self, user_context: UserContext) -> UserProfile:
        latest_record = self.repository.get_latest_usage_record(user_context.user_id)
        if latest_record is None:
            raise KeyError(f"用户 {user_context.user_id} 不存在")

        return UserProfile(
            user_id=user_context.user_id,
            city=user_context.city,
            household_profile=latest_record.feature,
            available_months=self.list_available_months(user_context.user_id),
        )

    def get_weather(self, city: str) -> WeatherInfo:
        return CITY_WEATHER.get(
            city,
            WeatherInfo(
                city=city,
                condition="晴",
                temperature_c=26,
                humidity_percent=50,
                wind_level="南风2级",
                aqi=30,
                rain_probability="未来2小时极低",
            ),
        )

    def get_usage_record(self, user_id: str, month: str) -> UsageRecord:
        record = self.repository.get_usage_record(user_id, month)
        if record is None:
            raise KeyError(f"未找到用户 {user_id} 在 {month} 的使用记录")
        return record.to_usage_record()

    def get_latest_usage_record(self, user_id: str) -> UsageRecord:
        record = self.repository.get_latest_usage_record(user_id)
        if record is None:
            raise KeyError(f"用户 {user_id} 不存在")
        return record.to_usage_record()

    def resolve_usage_record(self, user_id: str, preferred_month: str | None = None) -> BusinessLookupResult:
        if preferred_month:
            record = self.repository.get_usage_record(user_id, preferred_month)
            if record is not None:
                return BusinessLookupResult(
                    requested_month=preferred_month,
                    resolved_month=preferred_month,
                    used_latest_available=False,
                    usage_record=record.to_usage_record(),
                )

        latest_record = self.repository.get_latest_usage_record(user_id)
        if latest_record is None:
            raise KeyError(f"用户 {user_id} 不存在")

        return BusinessLookupResult(
            requested_month=preferred_month,
            resolved_month=latest_record.month,
            used_latest_available=preferred_month is not None and preferred_month != latest_record.month,
            usage_record=latest_record.to_usage_record(),
        )


@lru_cache(maxsize=1)
def get_business_service() -> BusinessService:
    return BusinessService(create_business_repository())
