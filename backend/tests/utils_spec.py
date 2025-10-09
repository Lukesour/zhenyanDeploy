def todo_spec(message: str) -> None:
    """Mark a requirement gap that needs specification update.

    Usage in tests when encountering undefined behavior:
        todo_spec("When no similar cases and model unavailable, expected http code?")
    """
    # Intentionally simple: raise AssertionError to fail fast with TODO-SPEC tag
    raise AssertionError(f"TODO-SPEC: {message}")

















