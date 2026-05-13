import os

import yaml

from utils.path_tool import get_abs_path


def load_yaml_config(config_path: str, encoding: str = "utf-8"):
    with open(config_path, "r", encoding=encoding) as f:
        return yaml.load(f, Loader=yaml.FullLoader) or {}


def merge_config(base_config: dict, override_config: dict) -> dict:
    merged = dict(base_config)
    merged.update(override_config)
    return merged


def load_rag_config(config_path: str = get_abs_path("config/rag.yml"), encoding: str = "utf-8"):
    config = load_yaml_config(config_path, encoding)

    local_config_path = get_abs_path("config/rag.local.yml")
    if os.path.exists(local_config_path):
        config = merge_config(config, load_yaml_config(local_config_path, encoding))

    env_api_key = os.getenv("DASHSCOPE_API_KEY")
    if env_api_key:
        config["dashscope_api_key"] = env_api_key

    return config


def load_chroma_config(config_path: str = get_abs_path("config/chroma.yml"), encoding: str = "utf-8"):
    return load_yaml_config(config_path, encoding)


def load_prompts_config(config_path: str = get_abs_path("config/prompts.yml"), encoding: str = "utf-8"):
    return load_yaml_config(config_path, encoding)


def load_agent_config(config_path: str = get_abs_path("config/agent.yml"), encoding: str = "utf-8"):
    return load_yaml_config(config_path, encoding)


def load_business_config(config_path: str = get_abs_path("config/business.yml"), encoding: str = "utf-8"):
    return load_yaml_config(config_path, encoding)


def load_auth_config(config_path: str = get_abs_path("config/auth.yml"), encoding: str = "utf-8"):
    config = load_yaml_config(config_path, encoding)

    local_config_path = get_abs_path("config/auth.local.yml")
    if os.path.exists(local_config_path):
        config = merge_config(config, load_yaml_config(local_config_path, encoding))

    env_secret = os.getenv("APP_JWT_SECRET") or os.getenv("JWT_SECRET")
    if env_secret:
        config["jwt_secret"] = env_secret

    env_issuer = os.getenv("APP_JWT_ISSUER")
    if env_issuer:
        config["jwt_issuer"] = env_issuer

    env_audience = os.getenv("APP_JWT_AUDIENCE")
    if env_audience:
        config["jwt_audience"] = env_audience

    return config


rag_conf = load_rag_config()
chroma_conf = load_chroma_config()
prompts_conf = load_prompts_config()
agent_conf = load_agent_config()
business_conf = load_business_config()
auth_conf = load_auth_config()


if __name__ == "__main__":
    print(rag_conf["chat_model_name"])
