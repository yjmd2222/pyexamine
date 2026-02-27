from __future__ import annotations
from .models import Ticket

def handle_ops(ticket: Ticket, *, verbose: bool) -> str:
    if verbose:
        return f"[ops] {ticket.id} {ticket.summary} payload={ticket.payload}"
    return f"[ops] {ticket.id} {ticket.summary}"

def handle_security(ticket: Ticket, *, verbose: bool) -> str:
    if verbose:
        return f"[sec] {ticket.id} {ticket.summary} payload={ticket.payload}"
    return f"[sec] {ticket.id} {ticket.summary}"

def handle_general(ticket: Ticket, *, verbose: bool) -> str:
    if verbose:
        return f"[gen] {ticket.id} {ticket.summary} payload={ticket.payload}"
    return f"[gen] {ticket.id} {ticket.summary}"
