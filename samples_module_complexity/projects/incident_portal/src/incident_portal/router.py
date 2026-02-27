from __future__ import annotations
from .models import Ticket
from . import handlers

def route(ticket: Ticket, *, channel: str, verbose: bool) -> str:
    # channel and verbose are control parameters that drive behavior across module boundaries
    if channel == "ops":
        return handlers.handle_ops(ticket, verbose=verbose)
    if channel == "security":
        return handlers.handle_security(ticket, verbose=verbose)
    return handlers.handle_general(ticket, verbose=verbose)
