from langchain_core.tools import tool

from rag.rag_service import get_rag_service
from schemas.app_models import UserContext
from services.business_service import BusinessService


def build_agent_tools(user_context: UserContext, business_service: BusinessService):
    _rag = get_rag_service()

    @tool(description="从向量知识库中检索扫地机器人相关资料并生成总结")
    def rag_summarize(query: str) -> str:
        return _rag.rag_summarize(query)

    @tool(description="获取指定城市的天气信息；如果未提供城市则默认使用当前用户所在城市")
    def get_weather(city: str = "") -> str:
        target_city = city or user_context.city
        weather = business_service.get_weather(target_city)
        return weather.to_prompt_text()

    @tool(description="获取当前请求用户所在城市")
    def get_user_location() -> str:
        return user_context.city

    @tool(description="获取当前请求用户的用户ID")
    def get_user_id() -> str:
        return user_context.user_id

    @tool(description="获取当前系统月份，格式为 YYYY-MM")
    def get_current_month() -> str:
        return business_service.get_current_month()

    @tool(description="查询指定用户在指定月份的真实业务使用记录；找不到时返回空字符串")
    def fetch_external_data(user_id: str, month: str) -> str | dict[str, str]:
        try:
            record = business_service.get_usage_record(user_id, month)
        except KeyError:
            return ""

        return {
            "特征": record.feature,
            "效率": record.efficiency,
            "耗材": record.consumables,
            "对比": record.comparison,
        }

    return [
        rag_summarize,
        get_weather,
        get_user_location,
        get_user_id,
        get_current_month,
        fetch_external_data,
    ]
