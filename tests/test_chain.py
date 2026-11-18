from tapis import chain


def test_chain_utuh(tmp_path, monkeypatch):
    from tapis import config, db

    monkeypatch.setattr(config, "DB_PATH", tmp_path / "t.db")
    db.init_db()
    with db.connect() as conn:
        conn.execute(
            "INSERT INTO warrant VALUES ('w','p',NULL,'ITE_PP71','1','X','a','b',NULL,'AKTIF',NULL)"
        )
        conn.execute("INSERT INTO target(id, warrant_id, msisdn, created_at) VALUES ('t','w','+62811','x')")
    for i in range(3):
        chain.append("event", "t", {"n": i})
    assert chain.verify("t")["valid"] is True
