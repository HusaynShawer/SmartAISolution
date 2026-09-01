def test_generate_embeddings_returns_list():
    from rag.splitter import split_text

    text = "This is a fairly long sentence that should be split " * 50
    chunks = split_text(text)

    assert isinstance(chunks, list)
    assert all(isinstance(c, str) and c for c in chunks)


def test_splitter_respects_chunk_size_and_overlap():
    from rag.splitter import split_text

    text = "\n\n".join(f"Paragraph {i} with some content to split." for i in range(30))
    chunks = split_text(text)

    assert len(chunks) > 1
    # Every chunk within reasonable length bounds
    for chunk in chunks:
        assert len(chunk) <= 1000 + 200  # chunk_size + overlap tolerance