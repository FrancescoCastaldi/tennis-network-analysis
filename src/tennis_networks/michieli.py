"""Convert the four networks of Michieli (2018) from MATLAB files to CSV edge lists and check them.

Run:
    python -m tennis_networks.michieli

Input:  data/raw/networks/*.mat
Output: data/processed/michieli_<n>_<name>.csv with columns source,target[,weight]

File format:
* networks 1-3: dense matrix "A" (4245 x 4245) and player names in "names", a MATLAB
  string object that SciPy does not decode: it is read from __function_workspace__.
* network 4: sparse matrix "x" (22405 x 22405) and names in "ids" (cell array).
* In network 1, A[i, j] is the number of wins of player j over player i: an edge from the
  loser i to the winner j.
"""

import struct
import zlib

import numpy as np
import pandas as pd
import scipy.io
import scipy.sparse as sp

from tennis_networks.config import PROCESSED, RAW

NETWORKS_DIR = RAW / "networks"
NETWORKS = [
    ("1_direct_wins.mat", "michieli_1_wins.csv", True, True),
    ("2_direct_points.mat", "michieli_2_points.csv", True, True),
    ("3_undirect_unweighted.mat", "michieli_3_undirected.csv", False, False),
    ("4_extended_undirect_unweighted.mat", "michieli_4_extended.csv", False, False),
]

# Figures from the paper (Section II) and from the readme of the author's Drive folder.
EXPECTED_PLAYERS = {1: 4245, 2: 4245, 3: 4245, 4: 22405}
EXPECTED_MATCHES_NET1 = 151734


def _workspace_chunks(raw):
    """Elements of __function_workspace__ (MAT v5 format), decompressed when miCOMPRESSED."""
    pos, chunks = 8, []
    while pos + 8 <= len(raw):
        dtype, nbytes = struct.unpack_from("<II", raw, pos)
        body = raw[pos + 8 : pos + 8 + nbytes]
        chunks.append(zlib.decompress(body) if dtype == 15 else body)
        pos += 8 + nbytes + (0 if dtype == 15 else (8 - nbytes % 8) % 8)
    return chunks


def _matlab_strings(blob, n):
    """Decode an n x 1 MATLAB string array stored as uint64: [1, 2, n, 1, lengths..., UTF-16 text]."""
    for dims in ((n, 1), (1, n)):
        start = blob.find(struct.pack("<4Q", 1, 2, *dims))
        if start < 0:
            continue
        lens = np.frombuffer(blob, dtype="<u8", count=n, offset=start + 32).astype(int)
        chars = np.frombuffer(blob, dtype="<u2", count=int(lens.sum()), offset=start + 32 + 8 * n)
        text = chars.tobytes().decode("utf-16-le")
        cuts = np.concatenate([[0], np.cumsum(lens)])
        return [text[a:b] for a, b in zip(cuts[:-1], cuts[1:], strict=True)]
    return None


def load_mat(path):
    """Return (CSR adjacency matrix, list of player names)."""
    m = scipy.io.loadmat(path)
    if "x" in m:
        names = [str(np.ravel(e)[0]) for e in np.ravel(m["ids"])]
        return sp.csr_matrix(m["x"]), names
    a = sp.csr_matrix(m["A"].astype(float))
    raw = m["__function_workspace__"].tobytes()
    for chunk in _workspace_chunks(raw):
        names = _matlab_strings(chunk, a.shape[0])
        if names:
            return a, names
    raise ValueError(f"player names not found in {path.name}")


def to_edgelist(a, names, directed, weighted):
    a = a if directed else sp.triu(a, k=1)
    coo = sp.coo_matrix(a)
    df = pd.DataFrame({"source": np.asarray(names)[coo.row], "target": np.asarray(names)[coo.col]})
    if weighted:
        df["weight"] = coo.data
    return df


def main():
    PROCESSED.mkdir(parents=True, exist_ok=True)
    for k, (src, dst, directed, weighted) in enumerate(NETWORKS, start=1):
        a, names = load_mat(NETWORKS_DIR / src)
        if not a.shape[0] == len(names) == len(set(names)) == EXPECTED_PLAYERS[k]:
            raise ValueError(f"{src}: unexpected number of players")
        if a.diagonal().sum() != 0:
            raise ValueError(f"{src}: self-loops found")
        symmetric = abs(a - a.T).sum() == 0
        if not directed and not symmetric:
            raise ValueError(f"{src}: the matrix should be symmetric")
        if k == 1 and a.sum() != EXPECTED_MATCHES_NET1:
            raise ValueError("network 1: wins do not add up to the matches of the paper")
        df = to_edgelist(a, names, directed, weighted)
        df.to_csv(PROCESSED / dst, index=False, encoding="utf-8")
        print(f"{dst}: {len(names)} players, {len(df)} edges, {'symmetric' if symmetric else 'asymmetric'} matrix")


if __name__ == "__main__":
    main()
