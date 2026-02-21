"""
Simple recursive text chunker.
Splits on paragraph boundaries first, falls back to sentences, then hard character limit.
"""

SEPARATORS = ["\n\n", "\n", ". ", " "]


def chunk_text(
    text: str,
    chunk_size: int = 512,
    chunk_overlap: int = 50,
) -> list[str]:
    """Split text into overlapping chunks, preserving natural boundaries."""
    if len(text) <= chunk_size:
        return [text.strip()] if text.strip() else []

    chunks = _recursive_split(text, chunk_size, separators=SEPARATORS)

    # Apply overlap: prepend tail of previous chunk to each subsequent chunk
    if chunk_overlap > 0 and len(chunks) > 1:
        overlapped = [chunks[0]]
        for i in range(1, len(chunks)):
            overlap_text = chunks[i - 1][-chunk_overlap:]
            overlapped.append(overlap_text + chunks[i])
        chunks = overlapped

    return [c.strip() for c in chunks if c.strip()]


def _recursive_split(text: str, chunk_size: int, separators: list[str]) -> list[str]:
    """Try each separator in order. Fall back to hard split if none work."""
    if len(text) <= chunk_size:
        return [text]

    for sep in separators:
        if sep in text:
            parts = text.split(sep)
            chunks: list[str] = []
            current = ""

            for part in parts:
                candidate = current + sep + part if current else part
                if len(candidate) <= chunk_size:
                    current = candidate
                else:
                    if current:
                        chunks.append(current)
                    # If a single part exceeds chunk_size, split it further
                    if len(part) > chunk_size:
                        remaining_seps = separators[separators.index(sep) + 1 :]
                        chunks.extend(_recursive_split(part, chunk_size, remaining_seps))
                        current = ""
                    else:
                        current = part

            if current:
                chunks.append(current)

            if len(chunks) > 1:
                return chunks

    # Hard split as last resort
    return [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]
