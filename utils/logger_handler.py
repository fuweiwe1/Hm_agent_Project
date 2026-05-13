import json
import logging
import os
import sys
from contextvars import ContextVar
from datetime import datetime, timezone

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from utils.path_tool import get_abs_path

LOG_ROOT = get_abs_path("logs")
os.makedirs(LOG_ROOT, exist_ok=True)

# ── requestId 全链路追踪 ──
request_id_var: ContextVar[str] = ContextVar("request_id", default="-")


class RequestIdFilter(logging.Filter):
    """将 contextvars 中的 request_id 注入每条 LogRecord。"""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get()  # type: ignore[attr-defined]
        return True


# ── Formatters ──
PLAIN_FORMAT = logging.Formatter(
    '%(asctime)s - %(name)s -%(levelname)s -[%(request_id)s] %(filename)s:%(lineno)d -%(message)s'
)


class JsonFormatter(logging.Formatter):
    """结构化 JSON 日志，便于 ELK / Loki 等日志平台采集。"""

    # extra 中内置字段名，不重复输出
    _BUILTIN = frozenset({
        "name", "msg", "args", "created", "relativeCreated", "exc_info", "exc_text",
        "stack_info", "lineno", "funcName", "pathname", "filename", "module",
        "levelno", "levelname", "thread", "threadName", "process", "processName",
        "msecs", "taskName", "message", "request_id",
    })

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "request_id": getattr(record, "request_id", "-"),
            "message": record.getMessage(),
            "module": record.module,
            "line": record.lineno,
        }
        # 将 extra 中的结构化字段展开到顶层
        for key, value in record.__dict__.items():
            if key not in self._BUILTIN and not key.startswith("_"):
                log_entry[key] = value
        if record.exc_info and record.exc_info[1] is not None:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry, ensure_ascii=False, default=str)


def get_logger(
    name: str = "agent",
    console_level: int = logging.INFO,
    file_level: int = logging.DEBUG,
    log_file: str | None = None,
    json_file: bool = True,
) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    if logger.handlers:
        return logger

    # 全局注入 requestId
    logger.addFilter(RequestIdFilter())

    # 控制台 — 可读纯文本（带 request_id）
    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_level)
    console_handler.setFormatter(PLAIN_FORMAT)
    console_handler.addFilter(RequestIdFilter())
    logger.addHandler(console_handler)

    # 文件 — JSON 结构化
    if not log_file:
        log_file = os.path.join(LOG_ROOT, f"{name}_{datetime.now().strftime('%Y%m%d')}.log")

    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(file_level)
    file_handler.setFormatter(JsonFormatter() if json_file else PLAIN_FORMAT)
    file_handler.addFilter(RequestIdFilter())
    logger.addHandler(file_handler)

    return logger


logger = get_logger()

if __name__ == '__main__':
    # 演示：设置 request_id 后，所有日志自动带上
    request_id_var.set("demo-req-001")
    logger.info("信息日志")
    logger.error("错误日志")
    logger.warning("警告日志")
    logger.debug("调试日志")
