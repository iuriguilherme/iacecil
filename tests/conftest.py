import pytest

@pytest.fixture(autouse=True)
def isolated_zodb(tmp_path, monkeypatch):
    """Redirect every persistence surface to a temp dir so tests never
    touch real instance/ data: neutral records, the per-chat store, and
    matrix sync tokens."""
    import iacecil.controllers.persistence.neutral as neutral
    import iacecil.controllers.persistence.chat_store as chat_store
    import iacecil.connectors.matrix as matrix_mod
    monkeypatch.setattr(neutral, 'zodb_path', str(tmp_path / 'zodb'))
    monkeypatch.setattr(chat_store, 'zodb_path', str(tmp_path / 'zodb'))
    monkeypatch.setattr(matrix_mod, 'TOKEN_DIR', str(tmp_path / 'matrix'))
    neutral._people_db = None
    neutral._messages_db = None
    yield
    chat_store.close_all()
    for attr in ('_people_db', '_messages_db'):
        db = getattr(neutral, attr)
        if db is not None:
            db.close()
            setattr(neutral, attr, None)
