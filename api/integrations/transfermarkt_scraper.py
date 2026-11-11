import logging
import re
import time
import unicodedata
from difflib import SequenceMatcher

import requests
from bs4 import BeautifulSoup
from django.db import transaction
from django.db.models import Count, Max, Q

from api.integrations.player_analytics import PlayerAnalyticsService
from api.models import Player, PlayerAttribute, PlayerSeasonStats, Season, Team

logger = logging.getLogger(__name__)


class TransfermarktScraper:
    """
    2026/2027 (ve güncel aktif sezon) Süper Lig kadro ve istatistik senkronizasyonu.

    - Transfermarkt (/kader + /leistungsdaten TR1) ana canlı kaynak,
      Mackolik (/takim/.../kadro) çapraz doğrulama,
      Sofascore erişilebildiğinde ek kontrol (403 engeli aşımı yapılmadan) olarak kullanılır.
    - Kadro farkı (diff) algoritması ile sadece güncel aktif kadroda bulunanlar
      o takımda bırakılır; ayrılanlar silinmeden tarihsel istatistikleri korunarak
      otomatik 'Eski Oyuncular' statüsüne geçirilir, lig içi transferler ise
      yalnızca yeni kulübün güncel kadrosunda gösterilir.
    """

    BASE_URL = "https://www.transfermarkt.com.tr"
    MACKOLIK_BASE = "https://www.mackolik.com"
    MIN_VALID_SQUAD_SIZE = 15

    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
    }

    # DB takım adı/kısa adı -> (tm_slug, tm_verein_id, mk_slug, mk_id)
    CLUB_SOURCES = {
        "galatasaray": ("galatasaray-istanbul", 141, "galatasaray", "esa748l653sss1wurz5ps3228"),
        "fenerbahce": ("fenerbahce-istanbul", 36, "fenerbah%C3%A7e", "8lroq0cbhdxj8124qtxwrhvmm"),
        "besiktas": ("besiktas-istanbul", 114, "be%C5%9Fikta%C5%9F", "2ez9cvam9lp9jyhng3eh3znb4"),
        "trabzonspor": ("trabzonspor", 449, "trabzonspor", "2yab38jdfl0gk2tei1mq40o06"),
        "basaksehir": ("istanbul-basaksehir-fk", 6890, "ba%C5%9Fak%C5%9Fehir", "47njg6cmlx5q3fvdsupd2n6qu"),
        "goztepe": ("goztepe", 1467, "g%C3%B6ztepe", "cjbaf8s09qoa1n11r33gc560x"),
        "arca corum fk": ("corum-fk", 37951, "%C3%A7orum-fk", "eg0cqg1u8zz85ma9nzk0cijv"),
        "corum fk": ("corum-fk", 37951, "%C3%A7orum-fk", "eg0cqg1u8zz85ma9nzk0cijv"),
        "samsunspor": ("samsunspor", 152, "samsunspor", "dpsnqu7pd2b0shfzjyn5j1znf"),
        "caykur rizespor": ("caykur-rizespor", 126, "%C3%A7-rizespor", "1lbrlj3uu8wi2h9j79snuoae4"),
        "kasimpasa": ("kasimpasa", 10484, "kas%C4%B1mpa%C5%9Fa", "4idg23egrrvtrbgrg7p5x7bwf"),
        "alanyaspor": ("alanyaspor", 11282, "alanyaspor", "84fpe0iynjdghwysyo5tizdkk"),
        "konyaspor": ("konyaspor", 2293, "konyaspor", "cw4lbdzlqqdvbkdkz00c9ye49"),
        "amed sk": ("amed-sk", 12382, "amed-sk", "2154uhyeun0lm781iiiijqhwo"),
        "gaziantep fk": ("gaziantep-fk", 2832, "gaziantep-fk", "2agzb2h4ppg7lfz9hn7eg1rqo"),
        "genclerbirligi": ("genclerbirligi-ankara", 820, "gen%C3%A7lerbirli%C4%9Fi", "embqktr41hfzczc8uav1scmcn"),
        "kocaelispor": ("kocaelispor", 120, "kocaelispor", "b703zecenioz21dnj3p63v3f7"),
        "erzurumspor fk": ("buyuksehir-belediye-erzurumspor", 39722, "erzurumspor-fk", "ea2gyhkv6vwmxbxevdb4u3796"),
        "eyupspor": ("eyupspor", 7160, "ey%C3%BCpspor", "bmgtxgipsznlb1j20zwjti3xh"),
    }

    MACKOLIK_POS_MAP = {
        "K": "Kaleci",
        "D": "Defans",
        "O": "Orta Saha",
        "F": "Forvet",
    }

    @staticmethod
    def _clean_display_name(name: str) -> str:
        """Birleşik Unicode aksanlarını temizler (örn. Mackolik Yi̇ği̇t -> Yiğit)."""
        if not name:
            return ""
        return re.sub(r"\s+", " ", unicodedata.normalize("NFC", name)).strip()

    @staticmethod
    def _norm_text(text: str) -> str:
        """Türkçe/Azerice/Avrupa karakterlerini sadeleştirilmiş küçük harfe çevirir."""
        if not text:
            return ""
        s = unicodedata.normalize("NFKD", text)
        s = "".join(ch for ch in s if not unicodedata.combining(ch))
        s = (
            s.replace("İ", "I")
            .replace("ı", "i")
            .replace("Ə", "E")
            .replace("ə", "e")
            .replace("ß", "ss")
            .replace("Ø", "O")
            .replace("ø", "o")
            .replace("Ł", "L")
            .replace("ł", "l")
        )
        s = re.sub(r"[^a-z0-9\s]", " ", s.lower())
        return re.sub(r"\s+", " ", s).strip()

    @classmethod
    def _translit_text(cls, text: str) -> str:
        """Transliterasyon varyasyonlarını (x->kh, q->g vb.) tek forma indirger."""
        s = cls._norm_text(text)
        return s.replace("x", "kh").replace("q", "g").replace("yev", "ev")

    @staticmethod
    def _is_goalkeeper(pos: str) -> bool:
        p = (pos or "").lower()
        return "kaleci" in p or "gk" in p or "goalkeeper" in p

    @classmethod
    def _pos_group(cls, pos: str) -> str:
        p = (pos or "").lower()
        if "kaleci" in p or "gk" in p:
            return "GK"
        if any(k in p for k in ("defans", "stoper", "bek")):
            return "DEF"
        if any(k in p for k in ("forvet", "santrafor", "kanat")):
            return "FWD"
        return "MID"

    @classmethod
    def _build_session(cls) -> requests.Session:
        session = requests.Session()
        session.headers.update(cls.HEADERS)
        return session

    @classmethod
    def _fetch_html(cls, session: requests.Session, url: str, min_len: int = 4000) -> str:
        """Ortak HTTP GET + rate-limit retry yardımcı fonksiyonu."""
        for attempt in range(3):
            try:
                resp = session.get(url, timeout=18)
                if resp.status_code == 200 and len(resp.text) >= min_len:
                    return resp.text
                if resp.status_code in (429, 500, 502, 503, 504):
                    time.sleep(2.0 * (attempt + 1))
                    continue
                logger.warning("URL HTTP %s (%d byte): %s", resp.status_code, len(resp.text), url)
            except requests.RequestException as exc:
                logger.warning("İstek hatası (%s): %s", url, exc)
            time.sleep(1.2 * (attempt + 1))
        return ""

    @classmethod
    def parse_market_value(cls, val_str: str) -> float:
        """Transfermarkt piyasa değeri metnini Euro sayısal değerine çevirir."""
        if not val_str or "-" in val_str:
            return 0.0
        clean = val_str.replace("\xa0", " ").replace("€", "").strip()
        m_mil = re.search(r"([\d\.,]+)\s*(?:mn|mil|milyon|m)\b", clean, re.I)
        if m_mil:
            try:
                return float(m_mil.group(1).replace(",", ".")) * 1_000_000
            except ValueError:
                return 0.0
        m_bin = re.search(r"([\d\.,]+)\s*(?:bin|k)\b", clean, re.I)
        if m_bin:
            try:
                return float(m_bin.group(1).replace(",", ".")) * 1_000
            except ValueError:
                return 0.0
        return 0.0

    @staticmethod
    def _parse_int(text: str) -> int:
        if not text:
            return 0
        t = text.replace("'", "").replace(".", "").strip()
        return int(t) if t.isdigit() else 0

    @classmethod
    def _resolve_club_source(cls, team: Team) -> tuple[str, int, str, str] | None:
        key = cls._norm_text(team.name)
        if key in cls.CLUB_SOURCES:
            return cls.CLUB_SOURCES[key]
        for alias, cfg in cls.CLUB_SOURCES.items():
            if alias in key or key in alias:
                return cfg
        return None

    @classmethod
    def discover_tm_clubs(cls, session: requests.Session, season_year: int) -> dict[str, tuple[str, int]]:
        """Transfermarkt lig ana sayfasından ilgili sezonun kulüp ID ve slug'larını keşfeder."""
        url = f"{cls.BASE_URL}/super-lig/startseite/wettbewerb/TR1/saison_id/{season_year}"
        html = cls._fetch_html(session, url)
        discovered: dict[str, tuple[str, int]] = {}
        if not html:
            return discovered
        soup = BeautifulSoup(html, "html.parser")
        table = soup.find("table", class_="items")
        if not table:
            return discovered
        for a in table.select("td.hauptlink a[href*='/verein/']"):
            href = a.get("href", "")
            m = re.search(r"^/([^/]+)/startseite/verein/(\d+)", href)
            if not m:
                continue
            slug, vid = m.group(1), int(m.group(2))
            discovered[cls._norm_text(a.get_text(strip=True))] = (slug, vid)
        return discovered

    @classmethod
    def _check_sofascore_status(cls, session: requests.Session) -> str:
        """Sofascore uç noktasını kibarca kontrol eder (403 alırsa bypass etmeden atlar)."""
        url = "https://api.sofascore.com/api/v1/unique-tournament/52/seasons"
        try:
            resp = session.get(url, timeout=6)
            if resp.status_code == 200:
                return "ok_200"
            return f"http_{resp.status_code}_skipped"
        except requests.RequestException:
            return "unreachable_skipped"

    @classmethod
    def _scrape_tm_club_live(
        cls, session: requests.Session, tm_slug: str, tm_id: int, season_year: int
    ) -> list[dict]:
        """Transfermarkt /kader (aktif kadro) + /leistungsdaten (Süper Lig istatistikleri) verisini çeker."""
        kader_url = f"{cls.BASE_URL}/{tm_slug}/kader/verein/{tm_id}/saison_id/{season_year}/plus/1"
        perf_url = f"{cls.BASE_URL}/{tm_slug}/leistungsdaten/verein/{tm_id}/reldata/TR1%26{season_year}/plus/1"

        kader_html = cls._fetch_html(session, kader_url)
        if not kader_html:
            return []

        soup_k = BeautifulSoup(kader_html, "html.parser")
        table_k = soup_k.find("table", class_="items")
        if not table_k or not table_k.find("tbody"):
            return []

        players: dict[str, dict] = {}
        for row in table_k.find("tbody").find_all("tr", class_=["odd", "even"]):
            td_name = row.find("td", class_="hauptlink")
            if not td_name or not td_name.find("a"):
                continue
            a_tag = td_name.find("a")
            name = cls._clean_display_name(a_tag.get_text(strip=True))
            if not name:
                continue
            tm_id_m = re.search(r"/spieler/(\d+)", a_tag.get("href", ""))
            tm_player_id = tm_id_m.group(1) if tm_id_m else None

            num_div = row.find("div", class_="rn_nummer")
            num_txt = num_div.get_text(strip=True) if num_div else ""
            jersey = int(num_txt) if num_txt.isdigit() else None

            position = "Futbolcu"
            inline_tbl = row.find("table", class_="inline-table")
            if inline_tbl:
                trs = inline_tbl.find_all("tr")
                if len(trs) >= 2:
                    position = trs[1].get_text(strip=True) or "Futbolcu"

            img = row.find("img", class_="bilderrahmen-fixed") or (inline_tbl.find("img") if inline_tbl else None)
            img_url = None
            if img:
                cand = img.get("data-src") or img.get("src")
                if cand and "default" not in cand:
                    img_url = cand

            tds = row.find_all("td", recursive=False)
            age = None
            for td in tds:
                txt = td.get_text(strip=True)
                m_age = re.search(r"\((\d{2})\)", txt)
                if m_age:
                    age = int(m_age.group(1))
                    break
                if txt.isdigit() and 15 <= int(txt) <= 45:
                    age = int(txt)

            flag = row.find("img", class_="flaggenrahmen")
            nationality = flag.get("title", "").strip() if flag else ""
            market_value = cls.parse_market_value(tds[-1].get_text(strip=True)) if tds else 0.0

            key = tm_player_id or cls._norm_text(name)
            players[key] = {
                "tm_id": tm_player_id,
                "name": name,
                "aliases": [],
                "jersey_number": jersey,
                "position": position,
                "age": age,
                "nationality": nationality,
                "market_value": market_value,
                "image_url": img_url,
                "matches": 0,
                "goals": 0,
                "assists": 0,
                "minutes": 0,
                "yellow_cards": 0,
                "red_cards": 0,
                "sources": ["transfermarkt"],
            }

        # Yalnızca aktif kadrodaki oyuncuların Süper Lig maç istatistiklerini ekle (ayrılanları geri ekleme!)
        perf_html = cls._fetch_html(session, perf_url)
        if perf_html:
            soup_p = BeautifulSoup(perf_html, "html.parser")
            table_p = soup_p.find("table", class_="items")
            if table_p and table_p.find("tbody"):
                for row in table_p.find("tbody").find_all("tr", class_=["odd", "even"]):
                    td_name = row.find("td", class_="hauptlink")
                    if not td_name or not td_name.find("a"):
                        continue
                    a_tag = td_name.find("a")
                    tm_id_m = re.search(r"/spieler/(\d+)", a_tag.get("href", ""))
                    key = tm_id_m.group(1) if tm_id_m else cls._norm_text(a_tag.get_text(strip=True))
                    if key not in players:
                        continue
                    tds = [td.get_text(strip=True) for td in row.find_all("td", recursive=False)]
                    if len(tds) >= 15:
                        players[key]["matches"] = cls._parse_int(tds[5])
                        players[key]["goals"] = cls._parse_int(tds[6])
                        players[key]["assists"] = cls._parse_int(tds[7])
                        players[key]["yellow_cards"] = cls._parse_int(tds[8])
                        players[key]["red_cards"] = cls._parse_int(tds[9]) + cls._parse_int(tds[10])
                        players[key]["minutes"] = cls._parse_int(tds[14])

        return list(players.values())

    @classmethod
    def _scrape_mackolik_club_live(cls, session: requests.Session, mk_slug: str, mk_id: str) -> list[dict]:
        """Mackolik kulüp kadro sayfasını çapraz doğrulama amacıyla çeker."""
        url = f"{cls.MACKOLIK_BASE}/takim/{mk_slug}/kadro/{mk_id}"
        html = cls._fetch_html(session, url, min_len=2000)
        if not html:
            return []

        soup = BeautifulSoup(html, "html.parser")
        table = soup.find("table")
        if not table:
            return []

        mk_players = []
        for tr in table.find_all("tr")[1:]:
            tds = tr.find_all("td")
            if len(tds) < 6:
                continue
            a = tr.find("a", href=True)
            raw_name = a.get_text(strip=True) if a else tds[2].get_text(strip=True)
            name = cls._clean_display_name(raw_name)
            if not name:
                continue
            jersey = cls._parse_int(tds[1].get_text(strip=True)) or None
            pos_code = tds[4].get_text(strip=True)
            pos = cls.MACKOLIK_POS_MAP.get(pos_code, pos_code or "Futbolcu")
            age = cls._parse_int(tds[5].get_text(strip=True)) or None
            matches_all = cls._parse_int(tds[6].get_text(strip=True)) if len(tds) > 6 else 0
            goals_all = cls._parse_int(tds[8].get_text(strip=True)) if len(tds) > 8 else 0
            assists_all = cls._parse_int(tds[9].get_text(strip=True)) if len(tds) > 9 else 0
            mk_players.append(
                {
                    "name": name,
                    "jersey_number": jersey,
                    "position": pos,
                    "age": age,
                    "matches_all_comp": matches_all,
                    "goals_all_comp": goals_all,
                    "assists_all_comp": assists_all,
                }
            )
        return mk_players

    @classmethod
    def _mk_matches_tm(cls, mk_name: str, tm_name: str) -> bool:
        na, nb = cls._translit_text(mk_name), cls._translit_text(tm_name)
        if not na or not nb:
            return False
        if na == nb or na.replace(" ", "") == nb.replace(" ", ""):
            return True
        ta, tb = na.split(), nb.split()
        if min(len(ta), len(tb)) >= 2:
            shorter, longer = (ta, tb) if len(ta) <= len(tb) else (tb, ta)
            if all(t in longer for t in shorter):
                return True
        if len(ta) >= 2 and len(tb) >= 2 and ta[0] == tb[0] and ta[-1] == tb[-1]:
            return True
        return SequenceMatcher(None, na, nb).ratio() >= 0.86

    @classmethod
    def merge_club_sources(cls, tm_players: list[dict], mk_players: list[dict]) -> list[dict]:
        """
        Transfermarkt ana kadrosu ile Mackolik kadrosunu birleştirir:
        - Tam isim/numara+mevki grubu eşleşenlere Mackolik tam adını takma ad olarak ekler (tekrar oluşturmaz).
        - Transfermarkt'ta yer almayan ancak Mackolik'te bu sezon resmi maça çıkmış genç oyuncuları ekler.
        """
        if not tm_players and mk_players:
            return [
                {
                    "tm_id": None,
                    "name": mk["name"],
                    "aliases": [],
                    "jersey_number": mk.get("jersey_number"),
                    "position": mk.get("position") or "Futbolcu",
                    "age": mk.get("age"),
                    "nationality": "Türkiye",
                    "market_value": 0.0,
                    "image_url": None,
                    "matches": 0,
                    "goals": 0,
                    "assists": 0,
                    "minutes": 0,
                    "yellow_cards": 0,
                    "red_cards": 0,
                    "sources": ["mackolik"],
                }
                for mk in mk_players
            ]

        merged = [dict(p, aliases=list(p.get("aliases", [])), sources=list(p.get("sources", ["transfermarkt"]))) for p in tm_players]
        by_jersey: dict[int, list[dict]] = {}
        for tm in merged:
            if tm.get("jersey_number"):
                by_jersey.setdefault(tm["jersey_number"], []).append(tm)

        for mk in mk_players:
            mk_name = cls._clean_display_name(mk["name"])
            matched = next((tm for tm in merged if cls._mk_matches_tm(mk_name, tm["name"])), None)
            if not matched and mk.get("jersey_number") in by_jersey:
                mk_pos = cls._pos_group(mk.get("position", ""))
                for cand in by_jersey[mk["jersey_number"]]:
                    if cls._pos_group(cand.get("position", "")) == mk_pos:
                        matched = cand
                        break
            if matched:
                if "mackolik" not in matched["sources"]:
                    matched["sources"].append("mackolik")
                if cls._norm_text(mk_name) != cls._norm_text(matched["name"]) and mk_name not in matched["aliases"]:
                    matched["aliases"].append(mk_name)
                if not matched.get("jersey_number") and mk.get("jersey_number"):
                    matched["jersey_number"] = mk["jersey_number"]
                continue

            if mk.get("matches_all_comp", 0) > 0:
                merged.append(
                    {
                        "tm_id": None,
                        "name": mk_name,
                        "aliases": [],
                        "jersey_number": mk.get("jersey_number"),
                        "position": mk.get("position") or "Futbolcu",
                        "age": mk.get("age"),
                        "nationality": "Türkiye",
                        "market_value": 0.0,
                        "image_url": None,
                        "matches": 0,
                        "goals": 0,
                        "assists": 0,
                        "minutes": 0,
                        "yellow_cards": 0,
                        "red_cards": 0,
                        "sources": ["mackolik"],
                    }
                )
        return merged

    @classmethod
    def _build_db_index(cls, active_season: Season):
        """Veritabanı oyuncularını tek sorguda bellek indeksine alır."""
        players_meta = list(
            Player.objects.annotate(
                last_year=Max("season_stats__season__start_year"),
                stats_count=Count("season_stats"),
            ).values(
                "id", "name", "current_team_id", "is_active", "is_legend", "position", "last_year", "stats_count"
            )
        )
        season_team_pairs = set(
            PlayerSeasonStats.objects.filter(season=active_season).values_list("player_id", "team_id")
        )
        by_norm: dict[str, list[dict]] = {}
        by_translit: dict[str, list[dict]] = {}
        by_nospace: dict[str, list[dict]] = {}
        by_last_tok: dict[str, list[dict]] = {}

        for meta in players_meta:
            norm = cls._norm_text(meta["name"])
            trans = cls._translit_text(meta["name"])
            meta["norm"] = norm
            meta["trans"] = trans
            meta["nospace"] = norm.replace(" ", "")
            meta["tokens"] = norm.split()
            meta["is_gk"] = cls._is_goalkeeper(meta.get("position", ""))
            by_norm.setdefault(norm, []).append(meta)
            by_translit.setdefault(trans, []).append(meta)
            if meta["nospace"]:
                by_nospace.setdefault(meta["nospace"], []).append(meta)
            if meta["tokens"]:
                by_last_tok.setdefault(meta["tokens"][-1], []).append(meta)

        return {
            "by_norm": by_norm,
            "by_translit": by_translit,
            "by_nospace": by_nospace,
            "by_last_tok": by_last_tok,
            "season_team_pairs": season_team_pairs,
        }

    @classmethod
    def _rank_candidate(cls, meta: dict, team_id: int, season_team_pairs: set[tuple[int, int]]) -> tuple:
        return (
            1 if (meta["id"], team_id) in season_team_pairs else 0,
            1 if meta["current_team_id"] == team_id else 0,
            1 if meta["is_active"] else 0,
            meta["last_year"] or 0,
            meta["stats_count"] or 0,
            -meta["id"],
        )

    @classmethod
    def _is_plausible_exact_hit(cls, meta: dict, team_id: int) -> bool:
        last_yr = meta["last_year"]
        if meta["current_team_id"] == team_id or meta["stats_count"] == 0:
            return True
        # 2012 öncesi emekli adaş efsanelerle modern gençleri karıştırma
        return last_yr is None or last_yr >= 2012

    @classmethod
    def _is_plausible_modern_fuzzy(cls, meta: dict, live_name: str, live_pos: str, team_id: int) -> bool:
        last_yr = meta["last_year"]
        if (last_yr is None or last_yr < 2020) and meta["current_team_id"] != team_id:
            return False
        if meta["is_gk"] != cls._is_goalkeeper(live_pos):
            return False
        na, nb = cls._translit_text(live_name), meta["trans"]
        if na.replace(" ", "") == nb.replace(" ", ""):
            return True
        ta, tb = na.split(), nb.split()
        if len(ta) < 2 or len(tb) < 2 or len(ta) != len(tb):
            return False
        surname_ratio = SequenceMatcher(None, ta[-1], tb[-1]).ratio()
        if ta[-1] != tb[-1] and not (min(len(ta[-1]), len(tb[-1])) >= 5 and surname_ratio >= 0.92):
            return False
        first_ratio = SequenceMatcher(None, ta[0], tb[0]).ratio()
        return ta[0] == tb[0] or first_ratio >= 0.85 or SequenceMatcher(None, na, nb).ratio() >= 0.92

    @classmethod
    def _resolve_live_players(cls, clubs_payload: list[tuple[Team, list[dict]]], active_season: Season) -> dict[int, list[tuple[dict, int | None]]]:
        """
        Tüm takımların canlı oyuncularını iki turlu (1: Tam Eşleşme, 2: Modern Varyant)
        küresel çözümleyici ile tekil DB Player ID'lerine eşler; iki canlı oyuncu aynı ID'yi alamaz.
        """
        idx = cls._build_db_index(active_season)
        used_ids: set[int] = set()
        assignments: dict[tuple[int, int], int] = {}

        # Tur 1: Tam normalize isim / transliterasyon eşleşmesi
        for team, roster in clubs_payload:
            for i, pdata in enumerate(roster):
                norm = cls._norm_text(pdata["name"])
                trans = cls._translit_text(pdata["name"])
                cands = [
                    m for m in (idx["by_norm"].get(norm, []) + idx["by_translit"].get(trans, []))
                    if m["id"] not in used_ids and cls._is_plausible_exact_hit(m, team.id)
                ]
                if not cands:
                    continue
                best = max(cands, key=lambda m: cls._rank_candidate(m, team.id, idx["season_team_pairs"]))
                used_ids.add(best["id"])
                assignments[(team.id, i)] = best["id"]

        # Tur 2: Bitişik isim (Hasanege / Hasan Ege) veya modern transliterasyon / Mackolik takma ad
        for team, roster in clubs_payload:
            for i, pdata in enumerate(roster):
                if (team.id, i) in assignments:
                    continue
                nospace = cls._norm_text(pdata["name"]).replace(" ", "")
                last_tok = cls._translit_text(pdata["name"]).split()[-1] if cls._translit_text(pdata["name"]) else ""
                pool = idx["by_nospace"].get(nospace, []) + idx["by_last_tok"].get(last_tok, [])
                for alias in pdata.get("aliases", []):
                    pool = pool + idx["by_norm"].get(cls._norm_text(alias), [])

                cands = []
                seen_cid = set()
                for m in pool:
                    if m["id"] in used_ids or m["id"] in seen_cid:
                        continue
                    seen_cid.add(m["id"])
                    if cls._is_plausible_modern_fuzzy(m, pdata["name"], pdata.get("position", ""), team.id):
                        cands.append(m)
                if not cands:
                    continue
                best = max(cands, key=lambda m: cls._rank_candidate(m, team.id, idx["season_team_pairs"]))
                used_ids.add(best["id"])
                assignments[(team.id, i)] = best["id"]

        resolved: dict[int, list[tuple[dict, int | None]]] = {}
        for team, roster in clubs_payload:
            resolved[team.id] = [(pdata, assignments.get((team.id, i))) for i, pdata in enumerate(roster)]
        return resolved

    @classmethod
    def _ensure_player_attributes(cls, player: Player):
        if PlayerAttribute.objects.filter(player=player).exists():
            return
        name_lower = player.name.lower()
        matched = None
        for key, prof in PlayerAnalyticsService.VERIFIED_ANALYTICS.items():
            if key in name_lower:
                matched = prof
                break
        if not matched:
            matched = PlayerAnalyticsService._generate_algorithmic_profile(player)
        PlayerAttribute.objects.create(
            player=player,
            pace=matched["pace"],
            shooting=matched["shooting"],
            passing=matched["passing"],
            dribbling=matched["dribbling"],
            defending=matched["defending"],
            physical=matched["physical"],
            strengths=matched["strengths"],
            weaknesses=matched["weaknesses"],
        )

    @staticmethod
    def _compute_baseline_rating(matches: int, goals: int, assists: int, minutes: int, existing_rating: float) -> float:
        if existing_rating and existing_rating > 0:
            return round(existing_rating, 2)
        if matches <= 0:
            return 0.0
        contrib = (goals * 0.14 + assists * 0.10) / max(matches, 1)
        min_bonus = 0.25 if minutes >= matches * 60 else 0.05
        return round(min(8.6, 6.45 + min_bonus + contrib * 2.5), 2)

    @classmethod
    def fetch_live_league_rosters(
        cls, teams: list[Team] | None = None, season: Season | None = None
    ) -> tuple[list[tuple[Team, list[dict]]], dict]:
        """Transfermarkt ve Mackolik'ten 18 takımın canlı aktif kadrolarını ve istatistiklerini çeker."""
        if season is None:
            season = Season.get_active_season()
        season_year = season.start_year
        target_teams = list(teams) if teams is not None else list(Team.objects.filter(is_super_lig=True).order_by("id"))

        session = cls._build_session()
        sofa_status = cls._check_sofascore_status(session)
        discovered_tm = cls.discover_tm_clubs(session, season_year)

        payload: list[tuple[Team, list[dict]]] = []
        skipped: list[str] = []

        for idx, team in enumerate(target_teams):
            cfg = cls._resolve_club_source(team)
            if not cfg:
                logger.warning("Kulüp kaynağı eşleştirilemedi: %s", team.name)
                skipped.append(team.name)
                continue
            tm_slug, tm_id, mk_slug, mk_id = cfg
            # Lig sayfasından güncel slug/id keşfedildiyse onu önceliklendir
            t_norm = cls._norm_text(team.name)
            if t_norm in discovered_tm:
                tm_slug, tm_id = discovered_tm[t_norm]

            tm_players = cls._scrape_tm_club_live(session, tm_slug, tm_id, season_year)
            mk_players = cls._scrape_mackolik_club_live(session, mk_slug, mk_id)
            merged = cls.merge_club_sources(tm_players, mk_players)

            if len(merged) < cls.MIN_VALID_SQUAD_SIZE:
                logger.error(
                    "%s için geçerli canlı kadro çekilemedi (%d oyuncu), veri bozulmaması için atlandı.",
                    team.name,
                    len(merged),
                )
                skipped.append(team.name)
                continue

            payload.append((team, merged))
            if idx < len(target_teams) - 1:
                time.sleep(0.8)

        return payload, {"sofascore_status": sofa_status, "skipped_teams": skipped}

    @classmethod
    def sync_live_squads_with_diff(
        cls,
        teams: list[Team] | None = None,
        season: Season | None = None,
        pre_fetched: dict[int, dict] | None = None,
    ) -> dict:
        """
        Canlı 2026/2027 kadrolarını çeker ve Kadro Farkı (Diff) algoritması uygular:
        - Aktif kadrodakileri günceller / oluşturur ve canlı istatistiklerini işler.
        - Takımdan ayrılanları veritabanından SİLMEZ; eski takım bağını koparıp
          geçmiş sezon istatistiklerini koruyarak Eski Oyuncular statüsüne geçirir.
        - Başka bir Süper Lig takımına transfer olanların yalnızca yeni takımındaki
          güncel kadro kaydını aktif bırakır.
        """
        if season is None:
            season = Season.get_active_season()

        full_league_mode = teams is None
        target_teams = list(teams) if teams is not None else list(Team.objects.filter(is_super_lig=True).order_by("id"))

        if pre_fetched is not None:
            clubs_payload: list[tuple[Team, list[dict]]] = []
            skipped = []
            for team in target_teams:
                entry = pre_fetched.get(team.id) or pre_fetched.get(str(team.id))
                if not entry:
                    skipped.append(team.name)
                    continue
                merged = cls.merge_club_sources(entry.get("tm_players", []), entry.get("mk_players", []))
                if len(merged) < cls.MIN_VALID_SQUAD_SIZE:
                    skipped.append(team.name)
                    continue
                clubs_payload.append((team, merged))
            meta_info = {"sofascore_status": "cached_input", "skipped_teams": skipped}
        else:
            clubs_payload, meta_info = cls.fetch_live_league_rosters(teams=target_teams, season=season)

        if not clubs_payload:
            return {"teams_synced": 0, **meta_info}

        resolved = cls._resolve_live_players(clubs_payload, season)

        summary = {
            "season": season.name,
            "teams_synced": len(clubs_payload),
            "active_players_upserted": 0,
            "new_players_created": 0,
            "intra_league_transfers": [],
            "detached_to_legends": 0,
            "non_sl_swept": 0,
            **meta_info,
        }

        with transaction.atomic():
            active_target_by_pid: dict[int, Team] = {}
            team_live_pids: dict[int, set[int]] = {}

            # 1. Tüm takımlar için canlı aktif kadroları yaz ve global aktif indeks çıkar
            for team, _roster in clubs_payload:
                team_pids: set[int] = set()
                for pdata, existing_pid in resolved[team.id]:
                    if existing_pid:
                        player = Player.objects.get(id=existing_pid)
                    else:
                        player = Player(name=pdata["name"])
                        summary["new_players_created"] += 1

                    prev_team_id = player.current_team_id
                    player.current_team = team
                    player.is_active = True
                    player.is_legend = False
                    if pdata.get("position") and pdata["position"] != "Futbolcu":
                        player.position = pdata["position"]
                    elif not player.position:
                        player.position = "Futbolcu"
                    if pdata.get("age"):
                        player.age = pdata["age"]
                    if pdata.get("nationality"):
                        player.nationality = pdata["nationality"]
                    if pdata.get("jersey_number") is not None:
                        player.jersey_number = pdata["jersey_number"]
                    if pdata.get("market_value") is not None:
                        player.market_value = pdata["market_value"]
                    if pdata.get("image_url"):
                        player.image_url = pdata["image_url"]
                    player.save()

                    if prev_team_id and prev_team_id != team.id:
                        summary["intra_league_transfers"].append(
                            {"player": player.name, "from_team_id": prev_team_id, "to_team": team.name}
                        )

                    stat_obj, _ = PlayerSeasonStats.objects.get_or_create(
                        player=player,
                        season=season,
                        team=team,
                    )
                    stat_obj.matches = pdata.get("matches", 0)
                    stat_obj.minutes = pdata.get("minutes", 0)
                    stat_obj.goals = pdata.get("goals", 0)
                    stat_obj.assists = pdata.get("assists", 0)
                    stat_obj.yellow_cards = pdata.get("yellow_cards", 0)
                    stat_obj.red_cards = pdata.get("red_cards", 0)
                    stat_obj.market_value = pdata.get("market_value", player.market_value or 0.0)
                    stat_obj.transfer_note = ""
                    stat_obj.rating = cls._compute_baseline_rating(
                        stat_obj.matches,
                        stat_obj.goals,
                        stat_obj.assists,
                        stat_obj.minutes,
                        stat_obj.rating,
                    )
                    stat_obj.save()

                    cls._ensure_player_attributes(player)

                    active_target_by_pid[player.id] = team
                    team_pids.add(player.id)
                    summary["active_players_upserted"] += 1

                team_live_pids[team.id] = team_pids

            # 2. Kadro Farkı (Diff): Her kulüpten ayrılan veya lig içi transfer olan eski kayıtları temizle
            for team, _roster in clubs_payload:
                live_pids = team_live_pids[team.id]
                db_attached_pids = set(
                    Player.objects.filter(current_team=team).values_list("id", flat=True)
                ) | set(
                    PlayerSeasonStats.objects.filter(season=season, team=team).values_list("player_id", flat=True)
                )
                departed_pids = db_attached_pids - live_pids
                if not departed_pids:
                    continue

                # Güncel sezon altından eski takım bağını kaldır; <2026 geçmiş istatistiklere dokunma!
                PlayerSeasonStats.objects.filter(
                    season=season, team=team, player_id__in=departed_pids
                ).delete()

                # Lig içi başka SL kulübüne gitmeyenleri Eski Oyuncular (is_legend=True) yap
                to_legend_ids = [pid for pid in departed_pids if pid not in active_target_by_pid]
                if to_legend_ids:
                    qs_detach = Player.objects.filter(id__in=to_legend_ids)
                    if not full_league_mode:
                        qs_detach = qs_detach.filter(Q(current_team=team) | Q(current_team__isnull=True))
                    updated = qs_detach.update(current_team=None, is_active=False, is_legend=True)
                    summary["detached_to_legends"] += updated

            # 3. Tam lig senkronizasyonunda Süper Lig dışı kulüplerdeki/boştaki bayat aktif kayıtları da arşive geçir
            if full_league_mode and not meta_info["skipped_teams"]:
                active_ids = set(active_target_by_pid.keys())
                PlayerSeasonStats.objects.filter(season=season).exclude(player_id__in=active_ids).delete()
                swept = (
                    Player.objects.exclude(id__in=active_ids)
                    .filter(Q(is_active=True) | Q(current_team__isnull=False))
                    .update(current_team=None, is_active=False, is_legend=True)
                )
                summary["non_sl_swept"] = swept

        return summary

    @classmethod
    def scrape_super_lig_teams(cls):
        """Geriye dönük uyumluluk: mevcut Süper Lig takımlarını döndürür."""
        return list(Team.objects.filter(is_super_lig=True).order_by("id"))

    @classmethod
    def scrape_super_lig_transfers(cls, season: Season | None = None):
        """Geriye dönük uyumluluk: mevcut transfer kayıtlarını koruyarak ilgili sezon transferlerini döndürür."""
        from api.models import Transfer

        if season is None:
            season = Season.get_active_season()
        return list(Transfer.objects.filter(season=season))

    @classmethod
    def scrape_team_squad(cls, team: Team, season: Season | None = None):
        """Tek takım için de canlı kadro + diff senkronizasyonu çalıştırır."""
        if season is None:
            season = Season.get_active_season()
        cls.sync_live_squads_with_diff(teams=[team], season=season)
        return list(Player.objects.filter(current_team=team, is_active=True))
