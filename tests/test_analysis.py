import networkx as nx
import pandas as pd
import pytest

from tennis_networks import analysis


def test_refresh_centralization_preserves_other_global_results(tmp_path, monkeypatch):
    tables = tmp_path / "tables"
    tables.mkdir()
    table_path = tables / "global_measures.csv"
    pd.DataFrame([{"network": "one_way_star", "degree_centralization": 0.25, "modularity": 0.7}]).to_csv(
        table_path, index=False
    )
    graph = nx.DiGraph((0, leaf) for leaf in range(1, 5))

    monkeypatch.setattr(analysis, "TABLES", tables)
    monkeypatch.setattr(analysis, "PROCESSED", tmp_path)
    monkeypatch.setattr(analysis, "load_network", lambda spec: graph)
    monkeypatch.setattr(analysis, "write_run_manifest", lambda *args, **kwargs: None)

    analysis.refresh_centralization({"seed": 20261115, "networks": [{"id": "one_way_star"}]})

    result = pd.read_csv(table_path).iloc[0]
    assert result["degree_centralization"] == pytest.approx(0.5)
    assert result["modularity"] == pytest.approx(0.7)
    assert table_path.read_text(encoding="utf-8").splitlines()[1].endswith(",0.7")


def test_refresh_centralization_requires_existing_global_table(tmp_path, monkeypatch):
    monkeypatch.setattr(analysis, "TABLES", tmp_path)

    with pytest.raises(FileNotFoundError, match="Run the full analysis"):
        analysis.refresh_centralization({"seed": 20261115, "networks": []})
