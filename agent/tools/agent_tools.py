import csv
import os
import random
from datetime import datetime
from functools import lru_cache

from langchain_core.tools import tool

from rag.rag_service import RagSummarizeService
from utils.config_handler import agent_conf
from utils.logger_handler import logger
from utils.path_tool import get_abs_path

user_ids = ["1001", "1002", "1003", "1004", "1005", "1006", "1007", "1008", "1009", "1010"]
external_data: dict[str, dict[str, dict[str, str]]] = {}


@lru_cache(maxsize=1)
def get_rag_service() -> RagSummarizeService:
    return RagSummarizeService()


@tool(description="从向量存储中检索参考资料并生成总结")
def rag_summarize(query: str) -> str:
    return get_rag_service().rag_summarize(query)


@tool(description="获取指定城市的天气信息，并以字符串形式返回")
def get_weather(city: str) -> str:
    return (
        f"城市{city}天气为晴天，气温26摄氏度，空气湿度50%，南风2级，AQI21，"
        "未来1小时降雨概率极低"
    )


@tool(description="获取用户所在城市名称，并以字符串形式返回")
def get_user_location() -> str:
    return random.choice(["深圳", "合肥", "杭州"])


@tool(description="获取用户ID，并以字符串形式返回")
def get_user_id() -> str:
    return random.choice(user_ids)


@tool(description="获取当前月份，并以 YYYY-MM 格式返回")
def get_current_month() -> str:
    return datetime.now().strftime("%Y-%m")


def generate_external_data() -> None:
    if external_data:
        return

    external_data_path = get_abs_path(agent_conf["external_data_path"])
    if not os.path.exists(external_data_path):
        raise FileNotFoundError(f"外部数据文件不存在: {external_data_path}")

    with open(external_data_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        next(reader, None)

        for row in reader:
            if len(row) < 6:
                logger.warning(f"[generate_external_data] 跳过格式异常的数据行: {row}")
                continue

            user_id, feature, efficiency, consumables, comparison, month = row[:6]
            if user_id not in external_data:
                external_data[user_id] = {}

            external_data[user_id][month] = {
                "特征": feature,
                "效率": efficiency,
                "耗材": consumables,
                "对比": comparison,
            }


@tool(description="从外部系统中获取指定用户在指定月份的使用记录；如果未检索到则返回空字符串")
def fetch_external_data(user_id: str, month: str) -> str | dict[str, str]:
    generate_external_data()

    try:
        return external_data[user_id][month]
    except KeyError:
        logger.warning(f"[fetch_external_data] 未能检索到用户 {user_id} 在 {month} 的使用记录数据")
        return ""


@tool(description="无入参；调用后触发中间件注入报告上下文，供后续动态切换提示词使用")
def fill_context_for_report() -> str:
    return "fill_context_for_report已调用"
