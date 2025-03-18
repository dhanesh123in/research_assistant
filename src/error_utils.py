from typing import Callable, TypeVar, Any
import time
from functools import wraps

T = TypeVar('T')

class ResearchError(Exception):
    """Base exception class for research-related errors"""
    pass

class ArxivError(ResearchError):
    """Exception for Arxiv-related errors"""
    pass

class OllamaError(ResearchError):
    """Exception for Ollama-related errors"""
    pass

def retry_with_backoff(
    retries: int = 3,
    backoff_in_seconds: int = 1,
    max_backoff_in_seconds: int = 10
) -> Callable:
    """
    Retry decorator with exponential backoff
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            retry_count = 0
            wait_time = backoff_in_seconds

            while retry_count < retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    retry_count += 1
                    if retry_count == retries:
                        raise e

                    time.sleep(min(wait_time, max_backoff_in_seconds))
                    wait_time *= 2

        return wrapper
    return decorator 