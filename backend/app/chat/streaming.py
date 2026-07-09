"""Helper functions for Vercel AI SDK-compatible data streaming."""

import json


def format_text_delta(delta: str) -> str:
    """Format a text delta to Vercel AI SDK Data Stream Protocol format.

    Format: 0:"<json_escaped_text>"\n
    """
    return f"0:{json.dumps(delta)}\n"


def format_error(error_message: str) -> str:
    """Format an error string to Vercel AI SDK Data Stream Protocol format.

    Format: e:"<json_escaped_error_message>"\n
    """
    return f"e:{json.dumps(error_message)}\n"


def format_data(data: list[dict] | dict) -> str:
    """Format data/annotations to Vercel AI SDK Data Stream Protocol format.

    Format: 2:[<json_escaped_data>]\n
    """
    payload = [data] if isinstance(data, dict) else data
    return f"2:{json.dumps(payload)}\n"

