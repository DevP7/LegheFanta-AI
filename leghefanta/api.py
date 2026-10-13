"""Client minimale per l'API privata di Leghe Fantacalcio (apileague.fantacalcio.it).

L'API non è documentata: endpoint e campi vengono dal reverse engineering del
frontend Angular di leghe.fantacalcio.it. Ogni richiesta vuole due header:
`app_key` (statico, pubblico, presente nel bundle JS del sito) e un bearer token
**specifico per lega** (vedi `auth.py`).
"""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

BASE_URL = "https://apileague.fantacalcio.it"
APP_KEY = "ICiELOObd5DF5uJEATi77CRvHiiRuMU0"


class ApiError(RuntimeError):
    def __init__(self, status: int, path: str, body: str):
        self.status = status
        self.path = path
        self.body = body
        hint = ""
        if "ATH001" in body:
            hint = " (token non valido, scaduto o di un'altra lega: rifai il login)"
        elif "ATH007" in body:
            hint = " (app_key mancante o cambiata: va riletta dal bundle del sito)"
        super().__init__(f"HTTP {status} su {path}{hint}: {body[:200]}")


class LegaClient:
    """Client legato a una singola lega (il token vale per una lega sola)."""

    def __init__(self, token: str, base_url: str = BASE_URL, timeout: float = 30.0):
        self.token = token
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        url = self.base_url + path
        if params:
            url += "?" + urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
        req = urllib.request.Request(
            url,
            headers={
                "app_key": APP_KEY,
                "Authorization": f"Bearer {self.token}",
                "Accept": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return json.loads(resp.read().decode("utf-8") or "null")
        except urllib.error.HTTPError as e:
            raise ApiError(e.code, path, e.read().decode("utf-8", "replace")) from e

    # --- endpoint di lettura -------------------------------------------------

    def status(self) -> dict:
        """Giornata corrente (`mday`), scadenza formazione (`mstr`, UTC), `sto` = bloccata."""
        return self.get("/onboarding/v1/league/status")

    def competitions(self) -> list[dict]:
        return self.get("/onboarding/v1/league/competitions") or []

    def roster_settings(self) -> dict:
        """Regole rosa: `minrl`/`maxrl` per ruolo, `budg`, dimensione rosa."""
        return self.get("/onboarding/v1/league/settings/rosters")

    def players(self) -> list[dict]:
        """Listone della lega. La risposta è un oggetto con chiave `players`."""
        data = self.get("/onboarding/v1/league/players") or {}
        return data.get("players", [])

    def teams(self) -> list[dict]:
        """Tutte le squadre della lega, con la rosa in `cal` (id) e `cs` (costi)."""
        out: list[dict] = []
        page = 1
        while True:
            data = self.get("/onboarding/v1/league/teams", {"page": page})
            out.extend(data.get("data", []))
            if page >= int(data.get("pages") or 1):
                return out
            page += 1

