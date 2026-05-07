import os
import sys

from utils.config_handler import prompts_conf
from utils.logger_handler import logger
from utils.path_tool import get_abs_path

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


def _load_prompt_from_config(config_key: str, loader_name: str) -> str:
    try:
        prompt_path = get_abs_path(prompts_conf[config_key])
    except KeyError as e:
        logger.error(f"[{loader_name}] 配置中缺少 {config_key}")
        raise e

    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        logger.error(f"[{loader_name}] 读取提示词失败: {str(e)}")
        raise e


def load_system_prompts():
    return _load_prompt_from_config("main_prompt_path", "load_system_prompts")


def load_rag_prompts():
    return _load_prompt_from_config("rag_summarize_prompt_path", "load_rag_prompts")


def load_report_prompts():
    return _load_prompt_from_config("report_prompt_path", "load_report_prompts")


def load_report_workflow_prompt():
    return _load_prompt_from_config("report_workflow_prompt_path", "load_report_workflow_prompt")
