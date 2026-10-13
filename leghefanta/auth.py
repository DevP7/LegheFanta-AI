"""Recupero dei token per lega.

Dopo il login, il sito salva in `localStorage["LEAGUES2024_LOCAL"]` un JSON con,
per l'utente corrente, l'elenco `leagues[]`: ogni voce ha il proprio `token`
(JWT valido ~365 giorni, uno per lega). Il `jwt` a livello account NON funziona
con l'API.

Tre modi per ottenerli, in ordine di preferenza:
1. `LEGHE_TOKENS_FILE` (default `.leghe_tokens.json`): file già salvato da un login precedente.
2. `LEGHE_LOCALSTORAGE`: il valore di `LEAGUES2024_LOCAL` incollato dal browser
   (DevTools > Application > Local Storage > leghe.fantacalcio.it).
3. Login automatico con Playwright usando `LEGHE_USERNAME` / `LEGHE_PASSWORD`.
"""

from __future__ import annotations

import base64
import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path

LOGIN_URL = "https://leghe.fantacalcio.it/login"
STORAGE_KEY = "LEAGUES2024_LOCAL"
DEFAULT_TOKENS_FILE = ".leghe_tokens.json"


@dataclass
class League:
    id: int
    alias: str
    name: str
    type: int  # 1 = Classic, 2 = Mantra (dedotto, non confermato dall'API)
    token: str
    team_id: int | None = None


def decode_jwt_payload(token: str) -> dict:
    """Decodifica il payload di un JWT senza verificarne la firma."""
    payload = token.split(".")[1]
    payload += "=" * (-len(payload) % 4)
    return json.loads(base64.urlsafe_b64decode(payload))


def leagues_from_localstorage(blob: str | dict) -> list[League]:
    """Estrae le leghe (con token) dal JSON di `LEAGUES2024_LOCAL`."""
    data = json.loads(blob) if isinstance(blob, str) else blob
    user_id = data.get("current-user")
    user = data.get(f"current-user-{user_id}")
    if not user:
        raise ValueError("LEAGUES2024_LOCAL non contiene l'utente corrente: login non completato?")
    out: list[League] = []
    for entry in user.get("leagues") or []:
        token = entry.get("token")
        if not token:
            continue
        claims = decode_jwt_payload(token)
        # Il token è valido per una sola lega: se l_id non coincide, la voce è etichettata male.
        if str(claims.get("l_id")) != str(entry.get("id")):
            raise ValueError(f"Token della lega {entry.get('alias')} punta a l_id={claims.get('l_id')}")
        out.append(
            League(
                id=int(entry["id"]),
                alias=entry.get("alias", ""),
                name=entry.get("name", ""),
                type=int(entry.get("type") or 0),
                token=token,
                team_id=int(claims["t_id"]) if claims.get("t_id") else None,
            )
        )
    if not out:
        raise ValueError("Nessuna lega trovata nell'account")
    return out


def save_tokens(leagues: list[League], path: str | Path) -> None:
    p = Path(path)
    p.write_text(json.dumps([asdict(lg) for lg in leagues], indent=2))
    p.chmod(0o600)


def load_tokens(path: str | Path) -> list[League]:
    return [League(**d) for d in json.loads(Path(path).read_text())]


def login_with_playwright(username: str, password: str, headless: bool = True) -> list[League]:
    """Login sul sito con un browser automatizzato e lettura del localStorage.

    I selettori del form sono generici perché la pagina può cambiare: se fallisce,
    usa `--headed` per vedere cosa succede o incolla `LEGHE_LOCALSTORAGE`.
    """
    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        launch = {"headless": headless}
        if os.path.exists("/opt/pw-browsers/chromium"):
            launch["executable_path"] = "/opt/pw-browsers/chromium"
        browser = pw.chromium.launch(**launch)
        page = browser.new_page()
        page.goto(LOGIN_URL, wait_until="domcontentloaded")
        # Banner cookie (Didomi) se presente.
        for sel in ("#didomi-notice-agree-button", "button:has-text('Accetta')"):
            try:
                page.locator(sel).first.click(timeout=3000)
                break
            except Exception:
                pass
        page.locator(
            "input[type=email], input[name=username], input[formcontrolname=username], input[name=email]"
        ).first.fill(username)
        page.locator("input[type=password]").first.fill(password)
        page.locator("button[type=submit], button:has-text('Accedi'), button:has-text('Login')").first.click()
        page.wait_for_function(
            f"""() => {{
                const raw = localStorage.getItem('{STORAGE_KEY}');
                if (!raw) return false;
                const d = JSON.parse(raw);
                const u = d['current-user-' + d['current-user']];
                return !!(u && u.leagues && u.leagues.some(l => l.token));
            }}""",
            timeout=60000,
        )
        blob = page.evaluate(f"() => localStorage.getItem('{STORAGE_KEY}')")
        browser.close()
    return leagues_from_localstorage(blob)


def get_leagues(force_login: bool = False, headless: bool = True) -> list[League]:
    tokens_file = os.environ.get("LEGHE_TOKENS_FILE", DEFAULT_TOKENS_FILE)
    if not force_login and Path(tokens_file).exists():
        return load_tokens(tokens_file)
    if not force_login and os.environ.get("LEGHE_LOCALSTORAGE"):
        leagues = leagues_from_localstorage(os.environ["LEGHE_LOCALSTORAGE"])
    else:
        user, pwd = os.environ.get("LEGHE_USERNAME"), os.environ.get("LEGHE_PASSWORD")
        if not (user and pwd):
            raise SystemExit(
                "Credenziali mancanti: imposta LEGHE_USERNAME e LEGHE_PASSWORD "
                "(oppure LEGHE_LOCALSTORAGE) come variabili d'ambiente."
            )
        leagues = login_with_playwright(user, pwd, headless=headless)
    save_tokens(leagues, tokens_file)
    return leagues
