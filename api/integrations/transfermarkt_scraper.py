import logging
import re
import time
import unicodedata
from decimal import Decimal
from difflib import SequenceMatcher

import requests
from bs4 import BeautifulSoup
from django.db import transaction
from django.db.models import Count, Max, Q

from api.integrations.player_analytics import PlayerAnalyticsService
from api.models import LeagueStanding, Player, PlayerAttribute, PlayerSeasonStats, Season, Team

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
    def _tm_vid_to_team_map(cls) -> dict[int, Team]:
        """Veritabanındaki 18 Süper Lig takımını Transfermarkt kulüp ID'siyle eşler."""
        vid_map: dict[int, Team] = {}
        for team in Team.objects.filter(is_super_lig=True):
            cfg = cls._resolve_club_source(team)
            if cfg:
                vid_map[int(cfg[1])] = team
        return vid_map

    @classmethod
    def discover_tm_clubs_and_values(
        cls, session: requests.Session, season_year: int
    ) -> tuple[dict[str, tuple[str, int]], dict[int, float], dict[str, float]]:
        """
        Transfermarkt lig ana sayfasından ilgili sezonun kulüp ID, slug ve toplam piyasa
        değerlerini tek HTTP isteğiyle keşfeder.
        """
        url = f"{cls.BASE_URL}/super-lig/startseite/wettbewerb/TR1/saison_id/{season_year}"
        html = cls._fetch_html(session, url)
        discovered: dict[str, tuple[str, int]] = {}
        mv_by_vid: dict[int, float] = {}
        mv_by_norm: dict[str, float] = {}
        if not html:
            return discovered, mv_by_vid, mv_by_norm
        soup = BeautifulSoup(html, "html.parser")
        table = soup.find("table", class_="items")
        tbody = table.find("tbody") if table else None
        if not tbody:
            return discovered, mv_by_vid, mv_by_norm
        for row in tbody.find_all("tr", class_=["odd", "even"]):
            td_name = row.find("td", class_="hauptlink")
            a = td_name.find("a", href=re.compile(r"/verein/\d+")) if td_name else None
            if not a:
                continue
            href = a.get("href", "")
            m = re.search(r"^/([^/]+)/startseite/verein/(\d+)", href)
            if not m:
                continue
            slug, vid = m.group(1), int(m.group(2))
            norm_name = cls._norm_text(a.get_text(strip=True))
            discovered[norm_name] = (slug, vid)
            tds = row.find_all("td", recursive=False)
            if tds:
                club_mv = cls.parse_market_value(tds[-1].get_text(strip=True))
                if club_mv > 0:
                    mv_by_vid[vid] = club_mv
                    mv_by_norm[norm_name] = club_mv
        return discovered, mv_by_vid, mv_by_norm

    @classmethod
    def discover_tm_clubs(cls, session: requests.Session, season_year: int) -> dict[str, tuple[str, int]]:
        """Transfermarkt lig ana sayfasından ilgili sezonun kulüp ID ve slug'larını keşfeder."""
        discovered, _mv_vid, _mv_norm = cls.discover_tm_clubs_and_values(session, season_year)
        return discovered

    @classmethod
    def _scrape_tm_clean_sheets(cls, session: requests.Session, season_year: int) -> dict[str, dict]:
        """Transfermarkt 'Beyaz Sayfa' tablosundan kalecilerin gol yemediği maç ve yediği golleri çeker."""
        by_tm_id: dict[str, dict] = {}
        by_norm: dict[str, dict] = {}
        for page in range(1, 5):
            url = f"{cls.BASE_URL}/super-lig/weisseweste/wettbewerb/TR1/saison_id/{season_year}/plus/1/page/{page}"
            html = cls._fetch_html(session, url, min_len=2500)
            if not html:
                break
            soup = BeautifulSoup(html, "html.parser")
            table = soup.find("table", class_="items")
            tbody = table.find("tbody") if table else None
            rows = tbody.find_all("tr", class_=["odd", "even"]) if tbody else []
            if not rows:
                break
            for row in rows:
                a_tag = row.find("a", href=re.compile(r"/spieler/\d+"))
                if not a_tag:
                    continue
                tm_m = re.search(r"/spieler/(\d+)", a_tag.get("href", ""))
                tm_id = tm_m.group(1) if tm_m else None
                name = cls._clean_display_name(a_tag.get_text(strip=True))
                tds = [td.get_text(strip=True) for td in row.find_all("td", recursive=False)]
                if len(tds) < 6:
                    continue
                entry = {
                    "clean_sheets": cls._parse_int(tds[4]),
                    "goals_conceded": cls._parse_int(tds[5]),
                }
                if tm_id and tm_id not in by_tm_id:
                    by_tm_id[tm_id] = entry
                norm = cls._norm_text(name)
                if norm and norm not in by_norm:
                    by_norm[norm] = entry
            if len(rows) < 25:
                break
        return {"by_tm_id": by_tm_id, "by_norm": by_norm}

    @classmethod
    def _scrape_tm_standings(cls, session: requests.Session, season_year: int) -> list[dict]:
        """Transfermarkt canlı puan durumu tablosunu (O, G, B, M, AG, YG, AV, P) çeker."""
        url = f"{cls.BASE_URL}/super-lig/tabelle/wettbewerb/TR1/saison_id/{season_year}"
        html = cls._fetch_html(session, url, min_len=3000)
        if not html:
            return []
        soup = BeautifulSoup(html, "html.parser")
        table = soup.find("table", class_="items")
        tbody = table.find("tbody") if table else None
        if not tbody:
            return []
        rows_out: list[dict] = []
        for tr in tbody.find_all("tr"):
            a_tag = tr.find("a", href=re.compile(r"/verein/\d+"))
            if not a_tag:
                continue
            vid_m = re.search(r"/verein/(\d+)", a_tag.get("href", ""))
            tm_vid = int(vid_m.group(1)) if vid_m else None
            tds = [td.get_text(strip=True) for td in tr.find_all("td", recursive=False)]
            if len(tds) < 10 or ":" not in tds[7]:
                continue
            gf_s, ga_s = tds[7].split(":", 1)
            rows_out.append(
                {
                    "tm_vid": tm_vid,
                    "name": a_tag.get_text(strip=True),
                    "rank": cls._parse_int(tds[0]),
                    "played": cls._parse_int(tds[3]),
                    "won": cls._parse_int(tds[4]),
                    "drawn": cls._parse_int(tds[5]),
                    "lost": cls._parse_int(tds[6]),
                    "goals_for": cls._parse_int(gf_s),
                    "goals_against": cls._parse_int(ga_s),
                    "points": cls._parse_int(tds[9]),
                }
            )
        return rows_out

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
    def _espn_pos_group(pos_abbr: str) -> str:
        p = (pos_abbr or "").upper()
        if p == "G":
            return "GK"
        if p == "D":
            return "DEF"
        if p == "F":
            return "FWD"
        if p == "M":
            return "MID"
        return ""

    @classmethod
    def _match_espn_entry(
        cls,
        p_name: str,
        p_jersey: int | None,
        p_pos: str,
        espn_entries: list[dict],
        used_indices: set[int] | None = None,
    ) -> tuple[int, dict] | None:
        """Transfermarkt/DB oyuncusunu aynı kulübün ESPN kadro listesinde tekil olarak eşler."""
        used = used_indices if used_indices is not None else set()
        p_norm = cls._norm_text(p_name)
        p_trans = cls._translit_text(p_name)
        p_nospace = p_norm.replace(" ", "")
        p_pg = cls._pos_group(p_pos)
        p_is_gk = p_pg == "GK"
        p_toks = p_trans.split()

        # 1. Tam normalize / transliterasyon / boşluksuz eşleşme
        for idx, entry in enumerate(espn_entries):
            if idx in used:
                continue
            e_norm = cls._norm_text(entry["name"])
            e_trans = cls._translit_text(entry["name"])
            e_pg = cls._espn_pos_group(entry.get("pos_abbr", ""))
            if e_pg and (e_pg == "GK") != p_is_gk:
                continue
            if p_norm == e_norm or p_trans == e_trans or (p_nospace and p_nospace == e_norm.replace(" ", "")):
                return idx, entry

        # 2. Forma numarası + aynı pozisyon grubu + kısmi ad örtüşmesi
        if p_jersey:
            for idx, entry in enumerate(espn_entries):
                if idx in used or entry.get("jersey") != p_jersey:
                    continue
                e_pg = cls._espn_pos_group(entry.get("pos_abbr", ""))
                if e_pg and e_pg != p_pg:
                    continue
                e_trans = cls._translit_text(entry["name"])
                e_toks = e_trans.split()
                token_overlap = bool(set(p_toks) & set(e_toks))
                ratio = SequenceMatcher(None, p_trans, e_trans).ratio()
                if token_overlap or ratio >= 0.50:
                    return idx, entry

        # 3. Yakın soyad / modern yazım eşleşmesi
        for idx, entry in enumerate(espn_entries):
            if idx in used:
                continue
            e_pg = cls._espn_pos_group(entry.get("pos_abbr", ""))
            if e_pg and (e_pg == "GK") != p_is_gk:
                continue
            e_trans = cls._translit_text(entry["name"])
            e_toks = e_trans.split()
            if SequenceMatcher(None, p_trans, e_trans).ratio() >= 0.85:
                return idx, entry
            if len(p_toks) >= 2 and len(e_toks) >= 2 and p_toks[-1] == e_toks[-1]:
                if SequenceMatcher(None, p_toks[0], e_toks[0]).ratio() >= 0.80:
                    return idx, entry
        return None

    @classmethod
    def compute_season_metrics(
        cls,
        matches: int,
        minutes: int,
        goals: int,
        assists: int,
        yellow_cards: int = 0,
        red_cards: int = 0,
        clean_sheets: int = 0,
        position: str = "",
        market_value: float = 0.0,
        total_shots: int = 0,
        saves: int = 0,
        goals_conceded: int = 0,
        has_espn_shots: bool = False,
    ) -> dict:
        """
        Gerçek maç, dakika, gol, asist, kart, kaleci temiz sayfa ve ESPN şut verisinden
        oyuncu sezonu metriklerini ve reytingini deterministik ve tutarlı hesaplar.
        """
        matches = int(matches or 0)
        if matches <= 0:
            return {
                "shots_per_game": 0.0,
                "pass_accuracy": 0.0,
                "key_passes": 0,
                "key_passes_per_game": 0.0,
                "dribbles_per_game": 0.0,
                "clean_sheets": 0,
                "rating": 0.0,
            }

        m = max(matches, 1)
        minutes = int(minutes or 0)
        goals = int(goals or 0)
        assists = int(assists or 0)
        yellow_cards = int(yellow_cards or 0)
        red_cards = int(red_cards or 0)
        total_shots = int(total_shots or 0)
        saves = int(saves or 0)
        goals_conceded = int(goals_conceded or 0)

        pg = cls._pos_group(position)
        mins_pg = (minutes / m) if minutes > 0 else 65.0
        clean_sheets_val = int(clean_sheets or 0) if pg == "GK" else 0

        if has_espn_shots:
            shots_pg = round(max(0, total_shots) / m, 2)
        elif pg == "GK":
            shots_pg = 0.0
        else:
            pos_shot_base = 0.90 if pg == "FWD" else (0.65 if pg == "MID" else 0.35)
            shots_pg = round(((goals * 1.45 + assists * 0.40) / m) + pos_shot_base * min(1.0, max(0.25, mins_pg / 85.0)), 2)

        if pg == "GK":
            key_passes = 0
            key_passes_pg = 0.0
        else:
            base_kp = {"MID": 0.85, "FWD": 0.65, "DEF": 0.38}.get(pg, 0.65)
            kp_est = ((assists * 3.2) / m) + base_kp * min(1.15, max(0.25, mins_pg / 82.0)) + min(0.55, shots_pg * 0.12)
            key_passes = max(assists, int(round(kp_est * m)))
            key_passes_pg = round(key_passes / m, 2)

        base_pa = {"GK": 74.5, "DEF": 84.5, "MID": 82.5, "FWD": 75.5}.get(pg, 79.0)
        mv_m = float(market_value or 0) / 1_000_000.0
        pa_raw = base_pa + min(4.0, mv_m * 0.15) + (1.5 if mins_pg >= 75 else -1.5) + min(3.0, (assists / m) * 3.0)
        pass_accuracy = round(min(92.5, max(64.0, pa_raw)), 1)

        if pg == "GK":
            dribbles_pg = 0.0
        else:
            base_dr = {"FWD": 0.95, "MID": 0.78, "DEF": 0.42}.get(pg, 0.70)
            dr_raw = base_dr * min(1.1, max(0.2, mins_pg / 80.0)) + (goals * 0.25 + assists * 0.35) / m
            dribbles_pg = round(min(3.8, max(0.1, dr_raw)), 2)

        play_factor = min(1.0, mins_pg / 85.0)
        disc_pen = (yellow_cards * 0.04 + red_cards * 0.22) / m
        if pg == "GK":
            cs_rate = clean_sheets_val / m
            ga_rate = (goals_conceded / m) if goals_conceded > 0 else max(0.0, 1.3 - cs_rate)
            save_bonus = (saves / m) * 0.08
            rat_raw = 6.35 + play_factor * 0.35 + cs_rate * 1.15 - ga_rate * 0.22 + save_bonus - disc_pen
        else:
            gw, aw = (1.05, 0.70) if pg == "FWD" else ((1.20, 0.85) if pg == "MID" else (1.35, 0.95))
            contrib = (goals * gw + assists * aw) / m
            shot_bonus = min(0.25, shots_pg * 0.045)
            rat_raw = 6.28 + play_factor * 0.42 + contrib * 1.10 + shot_bonus - disc_pen
        rating = round(min(8.60, max(6.05, rat_raw)), 2)

        return {
            "shots_per_game": shots_pg,
            "pass_accuracy": pass_accuracy,
            "key_passes": key_passes,
            "key_passes_per_game": key_passes_pg,
            "dribbles_per_game": dribbles_pg,
            "clean_sheets": clean_sheets_val,
            "rating": rating,
        }

    @classmethod
    def fetch_live_league_rosters(
        cls, teams: list[Team] | None = None, season: Season | None = None
    ) -> tuple[list[tuple[Team, list[dict]]], dict]:
        """Transfermarkt, Mackolik ve ESPN'den 18 takımın canlı aktif kadrolarını ve tüm sezon istatistiklerini çeker."""
        if season is None:
            season = Season.get_active_season()
        season_year = season.start_year
        target_teams = list(teams) if teams is not None else list(Team.objects.filter(is_super_lig=True).order_by("id"))

        from api.integrations.api_football import APIFootballService

        session = cls._build_session()
        sofa_status = cls._check_sofascore_status(session)
        discovered_tm, mv_by_vid, mv_by_norm = cls.discover_tm_clubs_and_values(session, season_year)
        clean_sheets_map = cls._scrape_tm_clean_sheets(session, season_year)
        standings_rows = cls._scrape_tm_standings(session, season_year) if len(target_teams) >= 18 else []

        payload: list[tuple[Team, list[dict]]] = []
        skipped: list[str] = []
        club_market_values: dict[int, float] = {}

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

            espn_entries = APIFootballService.fetch_espn_club_roster_stats(team, session=session)
            used_espn: set[int] = set()
            for pdata in merged:
                if cls._is_goalkeeper(pdata.get("position", "")):
                    cs_hit = clean_sheets_map["by_tm_id"].get(pdata.get("tm_id")) or clean_sheets_map["by_norm"].get(
                        cls._norm_text(pdata["name"])
                    )
                    if cs_hit:
                        pdata["clean_sheets"] = cs_hit["clean_sheets"]
                        pdata["gk_goals_conceded"] = cs_hit["goals_conceded"]

                if espn_entries:
                    espn_match = cls._match_espn_entry(
                        pdata["name"], pdata.get("jersey_number"), pdata.get("position", ""), espn_entries, used_espn
                    )
                    if espn_match:
                        e_idx, e_val = espn_match
                        used_espn.add(e_idx)
                        pdata["total_shots"] = e_val["total_shots"]
                        pdata["espn_saves"] = e_val["saves"]
                        pdata["espn_goals_conceded"] = e_val["goals_conceded"]
                        pdata["has_espn_shots"] = True
                        if "espn" not in pdata.get("sources", []):
                            pdata.setdefault("sources", []).append("espn")

            club_mv = mv_by_vid.get(int(tm_id)) or mv_by_norm.get(t_norm, 0.0)
            if club_mv > 0:
                club_market_values[team.id] = club_mv

            payload.append((team, merged))
            if idx < len(target_teams) - 1:
                time.sleep(0.8)

        return payload, {
            "sofascore_status": sofa_status,
            "skipped_teams": skipped,
            "club_market_values": club_market_values,
            "standings_rows": standings_rows,
        }

    @classmethod
    def _sync_live_standings_rows(cls, season: Season, standings_rows: list[dict]) -> int:
        """Transfermarkt puan durumu tablosunu veritabanıyla eşitler."""
        vid_to_team = cls._tm_vid_to_team_map()
        norm_to_team = {cls._norm_text(t.name): t for t in Team.objects.filter(is_super_lig=True)}
        updated = 0
        for row in standings_rows:
            team = None
            if row.get("tm_vid") and row["tm_vid"] in vid_to_team:
                team = vid_to_team[row["tm_vid"]]
            if not team:
                team = norm_to_team.get(cls._norm_text(row.get("name", "")))
            if not team:
                continue
            LeagueStanding.objects.update_or_create(
                season=season,
                team=team,
                defaults={
                    "rank": row["rank"],
                    "played": row["played"],
                    "won": row["won"],
                    "drawn": row["drawn"],
                    "lost": row["lost"],
                    "goals_for": row["goals_for"],
                    "goals_against": row["goals_against"],
                    "goal_difference": row["goals_for"] - row["goals_against"],
                    "points": row["points"],
                },
            )
            updated += 1
        return updated

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
            meta_info = {
                "sofascore_status": "cached_input",
                "skipped_teams": skipped,
                "club_market_values": {},
                "standings_rows": [],
            }
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
            "teams_mv_updated": 0,
            "standings_synced": 0,
            **meta_info,
        }

        with transaction.atomic():
            active_target_by_pid: dict[int, Team] = {}
            team_live_pids: dict[int, set[int]] = {}
            club_mv_overrides = meta_info.get("club_market_values", {})

            # 1. Tüm takımlar için canlı aktif kadroları yaz ve global aktif indeks çıkar
            for team, _roster in clubs_payload:
                team_pids: set[int] = set()
                squad_mv_sum = 0.0
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
                    squad_mv_sum += float(player.market_value or 0)

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

                    metrics = cls.compute_season_metrics(
                        matches=stat_obj.matches,
                        minutes=stat_obj.minutes,
                        goals=stat_obj.goals,
                        assists=stat_obj.assists,
                        yellow_cards=stat_obj.yellow_cards,
                        red_cards=stat_obj.red_cards,
                        clean_sheets=pdata.get("clean_sheets", 0),
                        position=player.position,
                        market_value=float(player.market_value or 0),
                        total_shots=pdata.get("total_shots", 0),
                        saves=pdata.get("espn_saves", 0),
                        goals_conceded=pdata.get("espn_goals_conceded", pdata.get("gk_goals_conceded", 0)),
                        has_espn_shots=bool(pdata.get("has_espn_shots", False)),
                    )
                    stat_obj.shots_per_game = metrics["shots_per_game"]
                    stat_obj.pass_accuracy = metrics["pass_accuracy"]
                    stat_obj.key_passes = metrics["key_passes"]
                    stat_obj.key_passes_per_game = metrics["key_passes_per_game"]
                    stat_obj.dribbles_per_game = metrics["dribbles_per_game"]
                    stat_obj.clean_sheets = metrics["clean_sheets"]
                    stat_obj.rating = metrics["rating"]
                    stat_obj.save()

                    cls._ensure_player_attributes(player)

                    active_target_by_pid[player.id] = team
                    team_pids.add(player.id)
                    summary["active_players_upserted"] += 1

                team_live_pids[team.id] = team_pids
                target_mv = club_mv_overrides.get(team.id) or squad_mv_sum
                if target_mv > 0:
                    team.market_value = Decimal(f"{float(target_mv):.2f}")
                    team.save(update_fields=["market_value"])
                    summary["teams_mv_updated"] += 1

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

                standings_rows = meta_info.get("standings_rows") or []
                if pre_fetched is None and len(standings_rows) >= 18:
                    summary["standings_synced"] = cls._sync_live_standings_rows(season, standings_rows)

        summary.pop("standings_rows", None)
        summary.pop("club_market_values", None)
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
