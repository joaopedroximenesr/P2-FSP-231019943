"""Leitor mínimo de JSON-stat 2.0 (formato da API do Eurostat) -> lista de dicts."""
import itertools


def jsonstat_to_rows(js):
    ids = js["id"]
    sizes = js["size"]
    dims = js["dimension"]
    cats = []
    for d in ids:
        idx = dims[d]["category"]["index"]
        # index pode ser dict {code: pos} ou lista
        if isinstance(idx, dict):
            order = sorted(idx, key=lambda k: idx[k])
        else:
            order = list(idx)
        cats.append(order)
    values = js.get("value", {})
    status = js.get("status", {})
    rows = []
    for pos, combo in enumerate(itertools.product(*cats)):
        key = str(pos)
        v = values.get(key) if isinstance(values, dict) else (values[pos] if pos < len(values) else None)
        if v is None:
            continue
        r = dict(zip(ids, combo))
        r["value"] = v
        st = status.get(key) if isinstance(status, dict) else None
        r["flag"] = st
        rows.append(r)
    return rows


def labels(js, dim):
    return js["dimension"][dim]["category"].get("label", {})
