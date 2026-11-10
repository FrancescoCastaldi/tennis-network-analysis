from tennis_networks import tennisdata as td


def test_played_drops_walkovers(matches):
    assert len(td.played(matches)) == 5


def test_edge_list_goes_from_loser_to_winner(matches):
    edges = td.edge_list(td.played(matches)).set_index(["source", "target"])["weight"]
    assert edges[("Nadal R.", "Federer R.")] == 1
    assert edges[("Ferrer D.", "Nadal R.")] == 1
    assert ("Ferrer D.", "Lopez F.") not in edges.index
    assert edges.sum() == 5


def test_player_rank_is_median(matches):
    ranks = td.player_rank(matches)
    assert ranks["Federer R."] == 1
    assert ranks["Ferrer D."] == 5


def test_subsets_split_by_surface(matches):
    nets = td.subsets(td.played(matches))
    assert len(nets["td_atp_grass"]) == 1
    assert len(nets["td_atp_clay"]) == 2
    assert len(nets["td_atp_hard"]) == 2


def test_clean_name_collapses_spaces():
    assert td.clean_name("  Del  Potro J.M. ") == "Del Potro J.M."


def test_clean_name_normalizes_source_name_aliases():
    assert td.clean_name("Raducànu E.") == "Raducanu E."


def test_spreadsheet_files_skip_appledouble(tmp_path):
    for name in ["2007.xlsx", "._2007.xlsx", "2008.xls"]:
        (tmp_path / name).write_bytes(b"")
    assert [p.name for p in td.spreadsheet_files(tmp_path)] == ["2007.xlsx", "2008.xls"]
