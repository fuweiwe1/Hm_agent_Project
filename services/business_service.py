import csv
from datetime import datetime
from functools import lru_cache

from schemas.app_models import BusinessLookupResult, UsageRecord, UserProfile, UserContext, WeatherInfo
from utils.config_handler import agent_conf
from utils.path_tool import get_abs_path


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
    def __init__(self):
        self._records_by_user: dict[str, dict[str, UsageRecord]] = {}
        self._load_usage_records()

    def _load_usage_records(self) -> None:
        data_path = get_abs_path(agent_conf["external_data_path"])
        with open(data_path, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                record = UsageRecord(
                    user_id=row["用户ID"],
                    month=row["时间"],
                    feature=row["特征"],
                    efficiency=row["清洁效率"],
                    consumables=row["耗材"],
                    comparison=row["对比"],
                )
                self._records_by_user.setdefault(record.user_id, {})[record.month] = record

    def list_user_ids(self) -> list[str]:
        return sorted(self._records_by_user.keys())

    def get_current_month(self) -> str:
        return datetime.now().strftime("%Y-%m")

    def get_user_profile(self, user_context: UserContext) -> UserProfile:
        records = self._records_by_user.get(user_context.user_id)
        if not records:
            raise KeyError(f"用户 {user_context.user_id} 不存在")

        ordered_months = sorted(records.keys())
        latest_record = records[ordered_months[-1]]
        return UserProfile(
            user_id=user_context.user_id,
            city=user_context.city,
            household_profile=latest_record.feature,
            available_months=ordered_months,
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
        try:
            return self._records_by_user[user_id][month]
        except KeyError as exc:
            raise KeyError(f"未找到用户 {user_id} 在 {month} 的使用记录") from exc

    def get_latest_usage_record(self, user_id: str) -> UsageRecord:
        records = self._records_by_user.get(user_id)
        if not records:
            raise KeyError(f"用户 {user_id} 不存在")

        latest_month = sorted(records.keys())[-1]
        return records[latest_month]

    def resolve_usage_record(self, user_id: str, preferred_month: str | None = None) -> BusinessLookupResult:
        if preferred_month:
            record = self._records_by_user.get(user_id, {}).get(preferred_month)
            if record is not None:
                return BusinessLookupResult(
                    requested_month=preferred_month,
                    resolved_month=preferred_month,
                    used_latest_available=False,
                    usage_record=record,
                )

        latest_record = self.get_latest_usage_record(user_id)
        return BusinessLookupResult(
            requested_month=preferred_month,
            resolved_month=latest_record.month,
            used_latest_available=preferred_month is not None and preferred_month != latest_record.month,
            usage_record=latest_record,
        )


@lru_cache(maxsize=1)
def get_business_service() -> BusinessService:
    return BusinessService()
