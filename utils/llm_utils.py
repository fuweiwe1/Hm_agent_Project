import time
from functools import wraps

from utils.logger_handler import logger


def llm_retry(max_retries: int = 2, backoff_seconds: float = 1.0):
    """LLM 调用重试装饰器，指数退避。"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exc = None
            for attempt in range(1, max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as exc:
                    last_exc = exc
                    if attempt < max_retries:
                        wait = backoff_seconds * (2 ** (attempt - 1))
                        logger.warning("llm_retry", extra={
                            "function": func.__name__,
                            "attempt": attempt,
                            "max_retries": max_retries,
                            "wait_seconds": wait,
                            "error": str(exc)[:200],
                        })
                        time.sleep(wait)
            logger.error("llm_retry_exhausted", extra={
                "function": func.__name__,
                "max_retries": max_retries,
                "error": str(last_exc)[:200],
            })
            raise last_exc
        return wrapper
    return decorator
