import inspect
from functools import wraps

def debug_print(message: str):
    """
    🪶 Упрощённый логгер для отладки.
    Печатает имя текущей функции + сообщение.
    """
    frame = inspect.currentframe().f_back
    func_name = frame.f_code.co_name
    print(f"[{func_name}] {message}")


def log_function_call(func):
    """
    🧩 Декоратор для логирования начала и конца выполнения функции.
    Пример:
        @log_function_call
        def my_func():
            ...
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        print(f"🔻 {func.__name__}")
        result = func(*args, **kwargs)
        print(f"🔺{func.__name__}")
        return result
    return wrapper
