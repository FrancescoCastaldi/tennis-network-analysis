# Data provenance

## Michieli (2018) networks: `data/raw/networks/`

Downloaded on 2026-10-16 from the author's public Google Drive folder
(<https://drive.google.com/drive/folders/1mCxZfkkpIC9o-nxZ1yW3GBBdvBOPW6mQ>, subfolder `networks`).
The folder readme (`readme_michieli.docx`) asks to cite the paper: U. Michieli, *Complex Network
Analysis of Men Single ATP Tennis Matches*, arXiv:1804.08138, 2018.

| File | Bytes | SHA-256 | Content |
|---|---:|---|---|
| `1_direct_wins.mat` | 249,654 | `327b1fcd...1623f` | `A` dense 4,245 x 4,245, `names` (MATLAB string) |
| `2_direct_points.mat` | 1,104,607 | `eb2104aa...efbb4d` | `A`, `names` |
| `3_undirect_unweighted.mat` | 299,251 | `8e56e1a1...cb978` | `A`, `names` |
| `4_extended_undirect_unweighted.mat` | 2,400,323 | `071cbcc0...def36` | `x` sparse 22,405 x 22,405, `ids` (cell array) |

Full digests are checked by `tests/test_data.py`.

- Networks 1 to 3: ATP main draw, 1968 to August 2017, the same 4,245 players in the same order.
  In network 1, `A[i, j]` is the number of wins of player `j` over player `i` (edge from loser to
  winner); the weights add up to 151,734 matches, as in the paper.
- Network 2 links every pair of opponents in both directions with the ATP points of their matches.
  Contrary to the readme, the two directions carry the same weight in 97% of the pairs, so it holds
  no information on who won. It is converted but not analysed.
- Network 4 extends network 3 to March 2018 and adds Davis Cup, Challenger and Futures matches
  from 1991. Its player order differs from networks 1 to 3. It has 499,057 undirected pairs.
- SciPy cannot decode the MATLAB `string` object holding the names of networks 1 to 3:
  `tennis_networks.michieli` reads it from `__function_workspace__`.
- The four matrices carry no dates, so eras and surfaces are built from tennis-data.co.uk.

## tennis-data.co.uk: `data/raw/tennisdata/`

One spreadsheet per season from <https://www.tennis-data.co.uk/alldata.php>: ATP 2000-2025
(26 files) and WTA 2007-2025 (19 files), downloaded on 2026-10-16 with
`python -m tennis_networks.download`. URL, size and SHA-256 of each file are in
`data/raw/tennisdata/manifest.csv`. The 2026 season is left out because it is incomplete.
The site does not state a licence; it is cited as the source, as the reference paper does.

Cleaning (`tennis_networks.tennisdata`):

- matches ended by walkover are dropped (no tennis was played); retirements are kept;
- white space in names is normalised; names already follow the `Surname I.` format of Michieli;
- Greenset is merged into hard courts; the 1,685 ATP carpet matches (surface abandoned in 2009)
  stay out of the surface networks;
- the season is the year of the file, so the first matches of a season may fall in late December.

Result: 114,084 played matches (68,972 ATP, 45,112 WTA) and nine networks, summarised in
`results/tables/td_networks_summary.csv`.

## Consistency between the two sources

For ATP matches from 2000 to August 2017, 97.6% of the loser-winner pairs and 99.3% of the players
of tennis-data.co.uk are also in Michieli network 1 (`results/tables/td_validity_michieli.csv`).
The ten missing players differ only in the spelling of their names (for example `Del Potro J.M.`).

## Not used

Jeff Sackmann's `tennis_atp` and `tennis_wta` repositories, the source of the reference paper,
are no longer public.
