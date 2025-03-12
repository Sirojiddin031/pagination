
from typing import Callable
from django.conf import settings
from django.utils.functional import lazy


def format_lazy(s: str, *args, **kwargs) -> str:
    return s.format(*args, **kwargs)

format_lazy: Callable = lazy(format_lazy, str)