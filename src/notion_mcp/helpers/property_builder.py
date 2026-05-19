"""Build Notion property values from simple Python types."""

from typing import Any, Dict


def build_property(prop_type: str, value: Any) -> Dict:
    """Convert a simple Python value to Notion's property format."""
    if value is None:
        return {prop_type: None}

    if prop_type == "title":
        return {"title": [{"type": "text", "text": {"content": str(value)}}]}

    elif prop_type == "rich_text":
        return {"rich_text": [{"type": "text", "text": {"content": str(value)}}]}

    elif prop_type == "number":
        return {"number": float(value) if value is not None else None}

    elif prop_type == "select":
        return {"select": {"name": str(value)}}

    elif prop_type == "status":
        return {"status": {"name": str(value)}}

    elif prop_type == "multi_select":
        if isinstance(value, str):
            value = [v.strip() for v in value.split(",")]
        return {"multi_select": [{"name": str(v)} for v in value]}

    elif prop_type == "date":
        if isinstance(value, dict):
            return {"date": value}
        return {"date": {"start": str(value)}}

    elif prop_type == "checkbox":
        return {"checkbox": bool(value)}

    elif prop_type == "url":
        return {"url": str(value)}

    elif prop_type == "email":
        return {"email": str(value)}

    elif prop_type == "phone_number":
        return {"phone_number": str(value)}

    elif prop_type == "people":
        if isinstance(value, str):
            value = [value]
        return {"people": [{"object": "user", "id": uid} for uid in value]}

    elif prop_type == "relation":
        if isinstance(value, str):
            value = [value]
        return {"relation": [{"id": pid} for pid in value]}

    elif prop_type == "files":
        if isinstance(value, str):
            value = [value]
        return {
            "files": [
                {"name": f"file_{i}", "external": {"url": url}}
                for i, url in enumerate(value)
            ]
        }

    else:
        raise ValueError(f"Unsupported property type: {prop_type}")


def build_properties(
    schema: Dict[str, Dict],
    values: Dict[str, Any],
) -> Dict[str, Dict]:
    """Build a properties dict for Notion API based on schema and user values."""
    result = {}
    for prop_name, value in values.items():
        if prop_name not in schema:
            continue
        prop_type = schema[prop_name].get("type")
        try:
            result[prop_name] = build_property(prop_type, value)
        except Exception as e:
            raise ValueError(
                f"Failed to build property '{prop_name}' (type={prop_type}): {e}"
            )
    return result


def build_filter(filters: Dict[str, Any], schema: Dict[str, Dict]) -> Dict:
    """Build a Notion filter object from a simple dict."""
    if not filters:
        return None

    conditions = []
    for prop_name, value in filters.items():
        if prop_name not in schema:
            continue

        prop_type = schema[prop_name].get("type")
        condition = _build_single_filter(prop_name, prop_type, value)
        if condition:
            conditions.append(condition)

    if not conditions:
        return None
    if len(conditions) == 1:
        return conditions[0]
    return {"and": conditions}


def _build_single_filter(prop_name: str, prop_type: str, value: Any) -> Dict:
    """Build a single filter condition."""
    if isinstance(value, dict):
        operator, op_value = next(iter(value.items()))
        return {
            "property": prop_name,
            prop_type: {operator: op_value},
        }

    if prop_type in ("title", "rich_text"):
        return {
            "property": prop_name,
            prop_type: {"contains": str(value)},
        }
    elif prop_type == "select":
        return {
            "property": prop_name,
            "select": {"equals": str(value)},
        }
    elif prop_type == "status":
        return {
            "property": prop_name,
            "status": {"equals": str(value)},
        }
    elif prop_type == "multi_select":
        return {
            "property": prop_name,
            "multi_select": {"contains": str(value)},
        }
    elif prop_type == "number":
        return {
            "property": prop_name,
            "number": {"equals": float(value)},
        }
    elif prop_type == "checkbox":
        return {
            "property": prop_name,
            "checkbox": {"equals": bool(value)},
        }
    elif prop_type == "date":
        return {
            "property": prop_name,
            "date": {"equals": str(value)},
        }
    return None


def parse_property_value(prop: Dict) -> Any:
    """Convert a Notion property back to a simple Python value."""
    ptype = prop.get("type")
    val = prop.get(ptype)

    if val is None:
        return None
    if ptype in ("title", "rich_text"):
        return "".join(t.get("plain_text", "") for t in val)
    if ptype == "number":
        return val
    if ptype == "select":
        return val.get("name") if val else None
    if ptype == "status":
        return val.get("name") if val else None
    if ptype == "multi_select":
        return [s.get("name") for s in val]
    if ptype == "date":
        return val.get("start") if val else None
    if ptype == "checkbox":
        return val
    if ptype in ("url", "email", "phone_number"):
        return val
    if ptype == "people":
        return [p.get("name", "Unknown") for p in val]
    if ptype == "relation":
        return [r.get("id") for r in val]
    if ptype == "formula":
        return val.get(val.get("type"))
    if ptype == "rollup":
        return str(val)
    return str(val)