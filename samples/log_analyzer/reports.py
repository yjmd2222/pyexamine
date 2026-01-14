
def build_report(events):
    summary = {
        "total": 0,
        "by_level": {},
        "by_source": {},
        "by_hour": {},
        "top_messages": [],
    }
    for event in events:
        summary["total"] += 1
        level = event.get("level", "info")
        source = event.get("source", "unknown")
        hour = event.get("hour", 0)
        message = event.get("message", "")
        user_id = event.get("user_id", "anon")
        host = event.get("host", "localhost")
        service = event.get("service", "core")
        request_id = event.get("request_id", "none")
        duration_ms = event.get("duration_ms", 0)
        summary["by_level"][level] = summary["by_level"].get(level, 0) + 1
        summary["by_source"][source] = summary["by_source"].get(source, 0) + 1
        summary["by_hour"][hour] = summary["by_hour"].get(hour, 0) + 1
        summary.setdefault("by_user", {})
        summary["by_user"][user_id] = summary["by_user"].get(user_id, 0) + 1
        summary.setdefault("by_host", {})
        summary["by_host"][host] = summary["by_host"].get(host, 0) + 1
        summary.setdefault("by_service", {})
        summary["by_service"][service] = summary["by_service"].get(service, 0) + 1
        summary.setdefault("by_request", {})
        summary["by_request"][request_id] = summary["by_request"].get(request_id, 0) + 1
        summary.setdefault("duration_total", 0)
        summary["duration_total"] += duration_ms
        if duration_ms > summary.get("duration_peak", 0):
            summary["duration_peak"] = duration_ms
        if len(message) > 40:
            summary["top_messages"].append(message[:40])
        else:
            summary["top_messages"].append(message)
    ordered_levels = sorted(summary["by_level"].items(), key=lambda x: x[1], reverse=True)
    ordered_sources = sorted(summary["by_source"].items(), key=lambda x: x[1], reverse=True)
    ordered_hours = sorted(summary["by_hour"].items(), key=lambda x: x[1], reverse=True)
    summary["ordered_levels"] = ordered_levels
    summary["ordered_sources"] = ordered_sources
    summary["ordered_hours"] = ordered_hours
    summary["top_messages"] = summary["top_messages"][:10]
    summary["has_errors"] = any(level == "error" for level, _ in ordered_levels)
    summary["has_warnings"] = any(level == "warning" for level, _ in ordered_levels)
    summary["has_critical"] = any(level == "critical" for level, _ in ordered_levels)
    summary["peak_hour"] = ordered_hours[0][0] if ordered_hours else None
    summary["peak_source"] = ordered_sources[0][0] if ordered_sources else None
    summary["peak_level"] = ordered_levels[0][0] if ordered_levels else None
    summary["average_per_hour"] = summary["total"] / max(len(summary["by_hour"]), 1)
    summary["average_per_source"] = summary["total"] / max(len(summary["by_source"]), 1)
    summary["average_per_level"] = summary["total"] / max(len(summary["by_level"]), 1)
    summary["average_per_user"] = summary["total"] / max(len(summary["by_user"]), 1)
    summary["average_per_host"] = summary["total"] / max(len(summary["by_host"]), 1)
    summary["average_per_service"] = summary["total"] / max(len(summary["by_service"]), 1)
    summary["average_duration"] = summary["duration_total"] / max(summary["total"], 1)
    summary["note"] = "generated"
    summary["status"] = "complete"
    return summary
