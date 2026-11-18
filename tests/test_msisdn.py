import pytest

from tapis import db
from tapis.core import msisdn


@pytest.fixture(autouse=True)
def _db(tmp_path, monkeypatch):
    from tapis import config

    monkeypatch.setattr(config, "DB_PATH", tmp_path / "t.db")
    db.init_db()
    db.seed()


@pytest.mark.parametrize("raw", ["081234567890", "+6281234567890", "6281234567890", "81234567890"])
def test_normalisasi(raw):
    assert msisdn.normalisasi(raw).e164 == "+6281234567890"


def test_operator():
    assert msisdn.normalisasi("081234567890").operator == "Telkomsel"


def test_invalid():
    with pytest.raises(msisdn.NomorTidakValid):
        msisdn.normalisasi("021555")
