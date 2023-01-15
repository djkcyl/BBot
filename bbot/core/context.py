from contextvars import ContextVar


class Context:
    push_id: ContextVar[str] = ContextVar("push_id")
    push_type: ContextVar[str] = ContextVar("push_type")
