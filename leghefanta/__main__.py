"""Uso:

    python -m leghefanta leghe                 # elenca le leghe dell'account
    python -m leghefanta rose [--lega ALIAS]   # scarica le rose in data/<alias>/rose.json
    python -m leghefanta login [--headed]      # forza un nuovo login
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from .api import LegaClient
from .auth import get_leagues
from .rose import build_rose


def cmd_leghe(args) -> None:
    for lg in get_leagues():
        tipo = {1: "Classic", 2: "Mantra"}.get(lg.type, f"tipo {lg.type}")
        print(f"{lg.alias:30} {lg.name:30} {tipo:8} lega={lg.id} squadra={lg.team_id}")


def cmd_rose(args) -> None:
    leagues = get_leagues()
    if args.lega:
        leagues = [lg for lg in leagues if args.lega in (lg.alias, str(lg.id))]
        if not leagues:
            raise SystemExit(f"Lega {args.lega!r} non trovata. Usa `python -m leghefanta leghe`.")
    for lg in leagues:
        client = LegaClient(lg.token)
        rose = build_rose(client.teams(), client.players(), my_team_id=lg.team_id)
        out = {
            "lega": {"id": lg.id, "alias": lg.alias, "nome": lg.name, "tipo": lg.type},
            "scaricato_il": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "stato": client.status(),
            "regole_rosa": client.roster_settings(),
            "rose": rose,
        }
        dest = Path(args.out) / lg.alias / "rose.json"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(json.dumps(out, indent=2, ensure_ascii=False))
        n = sum(len(r["giocatori"]) for r in rose)
        print(f"{lg.alias}: {len(rose)} squadre, {n} giocatori -> {dest}")


def cmd_login(args) -> None:
    leagues = get_leagues(force_login=True, headless=not args.headed)
    print(f"Login riuscito: {len(leagues)} leghe salvate.")


def main() -> None:
    ap = argparse.ArgumentParser(prog="leghefanta")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("leghe").set_defaults(func=cmd_leghe)
    p = sub.add_parser("rose")
    p.add_argument("--lega", help="alias o id della lega (default: tutte)")
    p.add_argument("--out", default="data")
    p.set_defaults(func=cmd_rose)
    p = sub.add_parser("login")
    p.add_argument("--headed", action="store_true", help="mostra il browser")
    p.set_defaults(func=cmd_login)
    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
