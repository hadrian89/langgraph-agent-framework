from functools import wraps

from opentelemetry import trace

tracer = trace.get_tracer("agent-platform")


def trace_node(name: str):

    def decorator(func):

        @wraps(func)
        def wrapper(*args, **kwargs):

            with tracer.start_as_current_span(name):

                return func(*args, **kwargs)

        return wrapper

    return decorator
