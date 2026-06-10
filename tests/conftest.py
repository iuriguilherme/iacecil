import pytest

@pytest.fixture(autouse=True)
def isolated_zodb(tmp_path, monkeypatch):
    """Redirect neutral persistence to a temp dir so tests never touch
    the real instance/zodb data."""
    import iacecil.controllers.persistence.neutral as neutral
    monkeypatch.setattr(neutral, 'zodb_path', str(tmp_path / 'zodb'))
    neutral._people_db = None
    neutral._messages_db = None
    yield
    for attr in ('_people_db', '_messages_db'):
        db = getattr(neutral, attr)
        if db is not None:
            db.close()
            setattr(neutral, attr, None)
