import functools
import time

from .stdout import console


def retry(retry_count=3, backoff=1.0):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(retry_count):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < retry_count - 1:
                        delay = backoff * (2 ** attempt)
                        console.print(f"[red]Retry {attempt + 1}/{retry_count}: {func.__name__} failed - {str(e)}, waiting {delay:.1f}s[/red]")
                        time.sleep(delay)
                    else:
                        console.print(f"[red]Final failure: {func.__name__} failed after {retry_count} retries - {str(e)}[/red]")
            raise last_exception
        return wrapper
    return decorator


def snake_to_pascal(snake_str: str) -> str:
    return ''.join(word.title() for word in snake_str.split('_'))
