def parse_time_to_minutes(value):
    raw_value = str(value).strip()
    parts = raw_value.split(":")
    if len(parts) != 3:
        raise ValueError("Time values must look like hh:mm:ss or h:mm:ss.")

    try:
        hours = int(parts[0])
        minutes = int(parts[1])
        seconds = float(parts[2])
    except ValueError as exc:
        raise ValueError("Time values must contain numbers only.") from exc

    if hours < 0 or minutes < 0 or seconds < 0:
        raise ValueError("Time values cannot be negative.")
    if minutes >= 60 or seconds >= 60:
        raise ValueError("Minutes and seconds must be below 60.")

    return hours * 60 + minutes + seconds / 60


def parse_observation_value(value, metric_type):
    raw_value = str(value).strip().replace(",", ".")
    if not raw_value:
        raise ValueError("Value cannot be empty.")

    if metric_type == "time":
        if ":" in raw_value:
            return parse_time_to_minutes(raw_value)
        try:
            return float(raw_value)
        except ValueError as exc:
            raise ValueError("Send a time like 00:35:30 or a number of minutes.") from exc

    if metric_type == "number":
        if ":" in raw_value:
            raise ValueError("This optimization expects a number, not a time value.")
        try:
            return float(raw_value)
        except ValueError as exc:
            raise ValueError("Send a numeric value, for example 42 or 42.5.") from exc

    raise ValueError(f"Unknown metric type: {metric_type}")


def format_observation_value(value, metric_type):
    if metric_type == "time":
        total_seconds = int(round(float(value) * 60))
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    return f"{float(value):.3g}"
