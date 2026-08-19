from feedscan.cli import main


def test_list_on_empty_db_prints_nothing(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("FEEDSCAN_DB", str(tmp_path / "db.sqlite"))
    import importlib

    import feedscan.cli as cli

    importlib.reload(cli)
    assert cli.main(["list"]) == 0
    assert capsys.readouterr().out == ""
