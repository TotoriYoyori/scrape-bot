import re


def to_snake_case(name: str) -> str:
    """Convert category name to clean snake_case suitable for file names."""
    name = name.strip().lower()
    name = re.sub(r"[^a-z0-9]+", "_", name)
    name = name.strip("_")
    return name
