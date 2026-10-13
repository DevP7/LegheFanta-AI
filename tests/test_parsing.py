import base64
import json
import unittest

from leghefanta.auth import leagues_from_localstorage
from leghefanta.rose import build_rose, parse_team_roster


def fake_jwt(claims: dict) -> str:
    enc = lambda d: base64.urlsafe_b64encode(json.dumps(d).encode()).decode().rstrip("=")
    return f"{enc({'alg': 'RS256'})}.{enc(claims)}.firma"


class TestAuth(unittest.TestCase):
    def test_estrae_token_per_lega(self):
        blob = {
            "current-user": 1,
            "current-user-1": {
                "jwt": "account-level",
                "leagues": [
                    {"id": 42, "alias": "lega-a", "name": "Lega A", "type": 1,
                     "token": fake_jwt({"l_id": "42", "t_id": "100"})},
                    {"id": 43, "alias": "lega-b", "name": "Lega B", "type": 2,
                     "token": fake_jwt({"l_id": "43", "t_id": "200"})},
                ],
            },
        }
        leagues = leagues_from_localstorage(json.dumps(blob))
        self.assertEqual([lg.alias for lg in leagues], ["lega-a", "lega-b"])
        self.assertEqual(leagues[1].team_id, 200)

    def test_rifiuta_token_di_altra_lega(self):
        blob = {"current-user": 1, "current-user-1": {"leagues": [
            {"id": 42, "alias": "x", "token": fake_jwt({"l_id": "99"})}]}}
        with self.assertRaises(ValueError):
            leagues_from_localstorage(blob)


class TestRose(unittest.TestCase):
    def test_accoppia_id_e_costi(self):
        self.assertEqual(parse_team_roster("7071;6966", "72;47"), [(7071, 72), (6966, 47)])

    def test_rifiuta_lunghezze_diverse(self):
        with self.assertRaises(ValueError):
            parse_team_roster("1;2;3", "10;20")

    def test_build_rose(self):
        teams = [{"id": 100, "n": "Mia", "nu": "Giuseppe", "cr": 12, "crs": 488,
                  "cal": "5585;1", "cs": "80;1"}]
        players = [{"id": 5585, "name": "Malen", "tname": "Roma", "marle": [16], "quotd": 20}]
        rose = build_rose(teams, players, my_team_id=100)
        self.assertTrue(rose[0]["mia"])
        malen, ignoto = rose[0]["giocatori"]
        self.assertEqual((malen["nome"], malen["ruolo"], malen["ruoli_mantra"], malen["costo"]),
                         ("Malen", "A", ["Pc"], 80))
        self.assertIsNone(ignoto["nome"])


if __name__ == "__main__":
    unittest.main()
