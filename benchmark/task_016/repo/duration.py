def format_duration(total_minutes: int) -> str:
    hours = total_minutes // 60
    minutes = total_minutes
    return f"{hours}h {minutes}m"
