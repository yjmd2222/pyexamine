from __future__ import annotations

def render(counts: dict[str, int], top: list[str]) -> str:
    lines: list[str] = []
    for k, v in sorted(counts.items()):
        lines.append(f"{k}: {v}")
    if top:
        lines.append("")
        lines.append("top messages:")
        for m in top:
            lines.append(f"- {m}")
    return "\n".join(lines)
