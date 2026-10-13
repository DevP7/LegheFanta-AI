"""Costruzione delle rose a partire dalle risposte dell'API."""

from __future__ import annotations

# Codici ruolo Mantra usati nel campo `marle` di /league/players.
MARLE_TO_CODE = {
    6: "Por", 7: "Dd", 8: "Ds", 9: "Dc", 10: "E", 11: "M",
    12: "C", 13: "T", 14: "W", 15: "A", 16: "Pc", 19: "B",
}

# Ruolo Classic (P/D/C/A) ricavato dal ruolo Mantra principale.
MANTRA_TO_CLASSIC = {
    "Por": "P", "Dd": "D", "Ds": "D", "Dc": "D", "B": "D",
    "E": "C", "M": "C", "C": "C", "T": "C", "W": "C",
    "A": "A", "Pc": "A",
}


def parse_team_roster(cal: str, cs: str) -> list[tuple[int, int]]:
    """Accoppia gli id giocatore (`cal`) ai costi pagati (`cs`).

    Sono due stringhe separate da `;` legate solo dalla posizione: se le lunghezze
    differiscono il risultato sarebbe sbagliato ma plausibile, quindi si rifiuta.
    """
    ids = [x for x in (cal or "").split(";") if x]
    costs = [x for x in (cs or "").split(";") if x]
    if len(ids) != len(costs):
        raise ValueError(f"Rosa incoerente: {len(ids)} giocatori ma {len(costs)} costi")
    return [(int(i), int(c)) for i, c in zip(ids, costs)]


def player_info(p: dict) -> dict:
    mantra = [MARLE_TO_CODE.get(r, str(r)) for r in (p.get("marle") or [])]
    classic = MANTRA_TO_CLASSIC.get(mantra[0]) if mantra else None
    return {
        "id": p["id"],
        "nome": p.get("name"),
        "squadra": p.get("tname"),
        "ruolo": classic,
        "ruoli_mantra": mantra,
        "quotazione": p.get("quotd"),
        "fvm_classic": p.get("fvmfc"),
        "fvm_mantra": p.get("fvmma"),
        "eta": p.get("age"),
    }


def build_rose(teams: list[dict], players: list[dict], my_team_id: int | None = None) -> list[dict]:
    """Unisce squadre e listone in una lista di rose leggibili."""
    by_id = {p["id"]: player_info(p) for p in players}
    rose = []
    for t in teams:
        giocatori = []
        for pid, costo in parse_team_roster(t.get("cal", ""), t.get("cs", "")):
            info = dict(by_id.get(pid) or {"id": pid, "nome": None})
            info["costo"] = costo
            giocatori.append(info)
        rose.append(
            {
                "id": t["id"],
                "nome": t.get("n"),
                "allenatore": t.get("nu"),
                "mia": t["id"] == my_team_id,
                "crediti_residui": t.get("cr"),
                "crediti_spesi": t.get("crs"),
                "giocatori": giocatori,
            }
        )
    return rose
