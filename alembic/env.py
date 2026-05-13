import sys
from pathlib import Path

# 项目根目录加入 Python 路径
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context
from utils.config_handler import business_conf

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = None


def _get_db_url() -> str:
    provider = business_conf.get("provider", "sqlite").lower()
    if provider == "postgresql":
        return business_conf.get("database_url", "").strip()
    # 默认 SQLite
    db_path = business_conf.get("database_path", "data/business.sqlite3")
    from utils.path_tool import get_abs_path
    return f"sqlite:///{get_abs_path(db_path)}"


def run_migrations_offline() -> None:
    url = _get_db_url()
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section, {})
    url = _get_db_url()
    configuration["sqlalchemy.url"] = url
    connectable = engine_from_config(configuration, prefix="sqlalchemy.", poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
