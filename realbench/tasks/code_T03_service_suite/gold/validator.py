"""Reference: validator.py"""
def validate_event(event: dict, rules: dict) -> bool:
    if not isinstance(event, dict) or not isinstance(rules, dict):
        return False
    if "allowed_types" in rules and event.get("type") not in rules["allowed_types"]:
        return False
    if "min_ts" in rules and event.get("ts", float("-inf")) < rules["min_ts"]:
        return False
    if "max_val" in rules and event.get("val", float("inf")) > rules["max_val"]:
        return False
    return True
