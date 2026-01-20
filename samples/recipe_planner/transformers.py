"""Text transformations for exports."""


def format_line(parts):
    joined = ",".join(str(p) for p in parts)
    return joined.strip()


def parse_line(text):
    items = [p.strip() for p in text.split(",")]
    return [p for p in items if p]


def merge_rows(rows):
    merged = []
    for row in rows:
        merged.extend(row)
    return merged


def normalize_block(lines):
    cleaned = [line.strip().lower() for line in lines]
    return [line for line in cleaned if line]
