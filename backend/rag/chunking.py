"""Text chunking with metadata preservation."""


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """Split text into overlapping chunks by sentences."""
    if not text:
        return []

    # Split by sentence-ending punctuation
    import re
    sentences = re.split(r'(?<=[.!?])\s+', text)

    chunks = []
    current_chunk = []
    current_length = 0

    for sentence in sentences:
        sentence_len = len(sentence.split())
        if current_length + sentence_len > chunk_size and current_chunk:
            chunks.append(" ".join(current_chunk))
            # Keep overlap
            overlap_words = " ".join(current_chunk).split()[-overlap:]
            current_chunk = overlap_words + [sentence]
            current_length = len(current_chunk)
        else:
            current_chunk.append(sentence)
            current_length += sentence_len

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks


def chunk_document(pages: list[dict], chunk_size: int = 500, overlap: int = 50) -> list[dict]:
    """Chunk parsed document pages into indexed chunks with metadata."""
    all_chunks = []
    chunk_index = 0

    for page_data in pages:
        text = page_data.get("content", "")
        page_num = page_data.get("page", 0)
        section = page_data.get("style", "")

        text_chunks = chunk_text(text, chunk_size, overlap)
        for chunk_text_item in text_chunks:
            all_chunks.append({
                "chunk_index": chunk_index,
                "content": chunk_text_item,
                "page_number": page_num,
                "section": section,
                "token_count": len(chunk_text_item.split()),
                "metadata": {"page": page_num, "section": section},
            })
            chunk_index += 1

    return all_chunks
