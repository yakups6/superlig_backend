import re
from datetime import date
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from django.db import transaction
from django.db.models import Q

from api.integrations.transfermarkt_scraper import TransfermarktScraper
from api.models import Fixture, RivalryMatch, Team

TR_MONTHS = {
    "oca": 1,
    "sub": 2,
    "şub": 2,
    "mar": 3,
    "nis": 4,
    "may": 5,
    "haz": 6,
    "tem": 7,
    "agu": 8,
    "ağu": 8,
    "eyl": 9,
    "eki": 10,
    "kas": 11,
    "ara": 12,
}

# 1959'dan günümüze tüm Süper Lig kulüplerinin resmi Transfermarkt verein ID eşlemesi
SUPER_LIG_CLUB_TM_IDS = {
    "galatasaray": 141,
    "fenerbahce": 36,
    "besiktas": 114,
    "trabzonspor": 449,
    "bursaspor": 20,
    "ankaragucu": 868,
    "mke ankaragucu": 868,
    "genclerbirligi": 820,
    "altay": 2375,
    "samsunspor": 152,
    "gaziantepspor": 524,
    "eskisehirspor": 825,
    "goztepe": 1467,
    "antalyaspor": 589,
    "konyaspor": 2293,
    "basaksehir": 6890,
    "istanbul basaksehir": 6890,
    "caykur rizespor": 126,
    "rizespor": 126,
    "istanbulspor": 924,
    "kasimpasa": 10484,
    "sivasspor": 2381,
    "kocaelispor": 120,
    "kayserispor": 3205,
    "denizlispor": 833,
    "adanaspor": 6,
    "boluspor": 3207,
    "adana demirspor": 3840,
    "karsiyaka": 2330,
    "sariyer": 518,
    "mersin idman yurdu": 3216,
    "mersin talimyurdu": 3216,
    "malatyaspor": 1264,
    "ankara demirspor": 12524,
    "alanyaspor": 11282,
    "vefa": 39974,
    "fatih karagumruk": 6646,
    "karagumruk": 6646,
    "sakaryaspor": 2463,
    "kayseri erciyesspor": 6894,
    "erciyesspor": 6894,
    "turk telekom": 1518,
    "ptt": 1518,
    "orduspor": 2323,
    "izmirspor": 3842,
    "diyarbakirspor": 845,
    "karabukspor": 1506,
    "dc karabukspor": 1506,
    "kardemir karabukspor": 1506,
    "ferikoy": 50726,
    "ankaraspor": 2944,
    "osmanlispor": 2944,
    "altinordu": 12374,
    "sekerhilal": 5743,
    "sekerspor": 5743,
    "beykozspor": 13451,
    "gaziantep fk": 2832,
    "akhisarspor": 19771,
    "giresunspor": 11688,
    "keciorengucu": 12388,
    "manisaspor": 1267,
    "hatayspor": 7775,
    "yeni malatyaspor": 19789,
    "vanspor": 40181,
    "zeytinburnuspor": 5745,
    "elazigspor": 2292,
    "canakkale dardanelspor": 1507,
    "dardanelspor": 1507,
    "bakirkoyspor": 3202,
    "aydinspor": 45468,
    "erzurumspor": 1766,
    "erzurumspor fk": 39722,
    "eyupspor": 7160,
    "yozgatspor": 740,
    "hacettepe": 10483,
    "balikesirspor": 20698,
    "akcaabat sebatspor": 1511,
    "beyogluspor": 31261,
    "yesildirek": 77165,
    "alibeykoyspor": 3208,
    "adalet": 3208,
    "bodrum fk": 44006,
    "pendikspor": 3209,
    "umraniyespor": 24245,
    "petrolofisi": 23766,
    "bucaspor": 2750,
    "siirt jetpa": 1291,
    "siirtspor": 1291,
    "amed sk": 12382,
    "kirikkalespor": 12390,
    "mke kirikkalespor": 12390,
    "kahramanmarasspor": 12452,
    "arca corum fk": 37951,
    "corum fk": 37951,
    "zonguldakspor": 45132,
}


class RivalryService:
    BILANZ_URL = (
        "https://www.transfermarkt.com.tr/verein/bilanzdetail/verein/{tm_id1}"
        "/saison_id/0/wettbewerb_id//datum_von/0000-00-00/datum_bis/0000-00-00"
        "/day/0/gegner_id/{tm_id2}/plus/1"
    )
    SPIELBERICHT_URL = "https://www.transfermarkt.com.tr/spielbericht/index/spielbericht/{match_id}"

    @classmethod
    def resolve_team_tm_id(cls, team: Team):
        if not team:
            return None
        norm = TransfermarktScraper._norm_text(team.name)
        if norm in SUPER_LIG_CLUB_TM_IDS:
            return SUPER_LIG_CLUB_TM_IDS[norm]
        for key, tm_id in SUPER_LIG_CLUB_TM_IDS.items():
            if key in norm or norm in key:
                return tm_id
        m = re.search(r"/head/(\d+)\.", team.logo_url or "")
        if m:
            return int(m.group(1))
        return None

    @staticmethod
    def parse_tr_date(date_str: str):
        """'26 Eki 2026' veya '10 Haz 1959' formatındaki Türkçe tarihi date nesnesine çevirir."""
        if not date_str:
            return None
        cleaned = re.sub(r"\s+", " ", date_str.strip())
        m = re.match(r"^(\d{1,2})\s+([A-Za-zÇĞİÖŞÜçğıöşü]+)\s+(\d{4})$", cleaned)
        if not m:
            return None
        day = int(m.group(1))
        mon_key = m.group(2).lower()
        mon_norm = TransfermarktScraper._norm_text(mon_key)
        month = TR_MONTHS.get(mon_key) or TR_MONTHS.get(mon_norm)
        year = int(m.group(3))
        if not month:
            return None
        try:
            return date(year, month, day)
        except ValueError:
            return None

    @staticmethod
    def normalize_season_label(raw_season: str, href: str = "", match_dt: date = None):
        m_href = re.search(r"saison_id/(\d{4})", href or "")
        if m_href:
            sy = int(m_href.group(1))
            return f"{sy}/{sy + 1}", sy

        raw = (raw_season or "").strip()
        m_full = re.match(r"^(\d{4})/(\d{4})$", raw)
        if m_full:
            sy = int(m_full.group(1))
            return raw, sy

        m_short = re.match(r"^(\d{2})/(\d{2})$", raw)
        if m_short:
            y1 = int(m_short.group(1))
            sy = 1900 + y1 if y1 >= 50 else 2000 + y1
            return f"{sy}/{sy + 1}", sy

        if raw.isdigit() and len(raw) == 4:
            ey = int(raw)
            sy = ey - 1
            return f"{sy}/{ey}", sy

        if match_dt:
            sy = match_dt.year if match_dt.month >= 7 else match_dt.year - 1
            return f"{sy}/{sy + 1}", sy

        return "2026/2027", 2026

    @staticmethod
    def normalize_competition_name(comp_raw: str) -> str:
        c = (comp_raw or "").strip()
        if not c:
            return "Süper Lig"
        low = TransfermarktScraper._norm_text(c)
        if (
            "super lig" in low
            or "milli lig" in low
            or "1. lig" == low
            or "sampiyonluk final" in low
            or "super final" in low
            or "final grubu" in low
        ):
            return "Süper Lig"
        if "turkiye kupasi" in low or "federasyon kupasi" in low:
            return "Türkiye Kupası"
        if "super kupa" in low or "cumhurbaskanligi" in low:
            return "TFF Süper Kupa"
        if "basbakanlik" in low:
            return "Başbakanlık Kupası"
        return c

    @staticmethod
    def normalize_round_label(round_raw: str) -> str:
        r = (round_raw or "").strip()
        if not r:
            return ""
        if r.isdigit():
            return f"{r}. Hafta"
        return r

    @classmethod
    def fetch_transfermarkt_pair_matches(cls, team1: Team, team2: Team, session=None):
        """
        Transfermarkt bilanzdetail sayfalarından iki takım arasındaki 1959'dan günümüze
        tüm resmi maçları (Süper Lig, Türkiye Kupası, Süper Kupa vb.) çeker.
        """
        tm_id1 = cls.resolve_team_tm_id(team1)
        tm_id2 = cls.resolve_team_tm_id(team2)
        if not tm_id1 or not tm_id2 or tm_id1 == tm_id2:
            return []

        http = session or requests
        first_url = cls.BILANZ_URL.format(tm_id1=tm_id1, tm_id2=tm_id2)
        try:
            resp = http.get(first_url, headers=TransfermarktScraper.HEADERS, timeout=15)
            if resp.status_code != 200:
                return []
        except Exception:
            return []

        soups = [BeautifulSoup(resp.text, "html.parser")]
        page_urls = []
        seen_pages = {1}
        for a in soups[0].select("ul.tm-pagination a[href]"):
            href = a.get("href", "")
            m_pg = re.search(r"/page/(\d+)", href)
            if m_pg:
                pg_num = int(m_pg.group(1))
                if pg_num not in seen_pages and pg_num <= 6:
                    seen_pages.add(pg_num)
                    page_urls.append((pg_num, urljoin(TransfermarktScraper.BASE_URL, href)))

        for _, pg_url in sorted(page_urls, key=lambda x: x[0]):
            try:
                r_pg = http.get(pg_url, headers=TransfermarktScraper.HEADERS, timeout=15)
                if r_pg.status_code == 200:
                    soups.append(BeautifulSoup(r_pg.text, "html.parser"))
            except Exception:
                continue

        t1_norm = TransfermarktScraper._norm_text(team1.name)
        parsed = []
        seen_match_ids = set()

        for soup in soups:
            for tr in soup.select("table.items > tbody > tr"):
                tds = tr.find_all("td", recursive=False)
                if len(tds) < 11:
                    continue

                score_a = tds[7].find("a")
                score_href = score_a.get("href", "") if score_a else ""
                m_mid = re.search(r"/spielbericht/(\d+)", score_href)
                tm_mid = f"TM_{m_mid.group(1)}" if m_mid else None

                date_disp = tds[3].get_text(" ", strip=True)
                match_dt = cls.parse_tr_date(date_disp)
                time_disp = tds[4].get_text(" ", strip=True)

                season_a = tds[0].find("a")
                home_a = tds[5].find("a")
                away_a = tds[9].find("a")
                season_href = (
                    (season_a.get("href", "") if season_a else "")
                    or (home_a.get("href", "") if home_a else "")
                )
                season_label, start_year = cls.normalize_season_label(
                    tds[0].get_text(strip=True), season_href, match_dt
                )

                comp_a = tds[1].find("a")
                comp_img = tds[1].find("img")
                comp_raw = (
                    (comp_a.get("title") if comp_a else "")
                    or (comp_img.get("title") if comp_img else "")
                    or tds[1].get_text(" ", strip=True)
                )
                competition = cls.normalize_competition_name(comp_raw)
                round_label = cls.normalize_round_label(tds[2].get_text(" ", strip=True))

                home_href = home_a.get("href", "") if home_a else ""
                away_href = away_a.get("href", "") if away_a else ""
                m_h_id = re.search(r"/verein/(\d+)", home_href)
                m_a_id = re.search(r"/verein/(\d+)", away_href)
                h_tm_id = int(m_h_id.group(1)) if m_h_id else None
                a_tm_id = int(m_a_id.group(1)) if m_a_id else None

                if h_tm_id == tm_id1 or a_tm_id == tm_id2:
                    home_team, away_team = team1, team2
                elif h_tm_id == tm_id2 or a_tm_id == tm_id1:
                    home_team, away_team = team2, team1
                else:
                    h_txt = TransfermarktScraper._norm_text(tds[5].get_text(" ", strip=True))
                    if t1_norm and t1_norm in h_txt:
                        home_team, away_team = team1, team2
                    else:
                        home_team, away_team = team2, team1

                h_rank_el = tds[5].select_one(".tabellenplatz")
                a_rank_el = tds[9].select_one(".tabellenplatz")
                home_rank = h_rank_el.get_text(strip=True) if h_rank_el else ""
                away_rank = a_rank_el.get_text(strip=True) if a_rank_el else ""

                score_raw = tds[7].get_text(" ", strip=True)
                m_sc = re.search(r"(\d+)\s*:\s*(\d+)(?:\s*(UZT|PEN|Hükmen))?", score_raw, re.I)
                if m_sc:
                    home_score = int(m_sc.group(1))
                    away_score = int(m_sc.group(2))
                    score_note = (m_sc.group(3) or "").upper()
                    status = "FT"
                else:
                    home_score = None
                    away_score = None
                    score_note = ""
                    status = "NS"

                att_raw = tds[10].get_text(strip=True)
                attendance = "" if att_raw in ("-", "") else att_raw

                if not tm_mid:
                    tm_mid = f"TM_{min(tm_id1, tm_id2)}_{max(tm_id1, tm_id2)}_{date_disp}_{round_label}"
                if tm_mid in seen_match_ids:
                    continue
                seen_match_ids.add(tm_mid)

                parsed.append(
                    {
                        "tm_match_id": tm_mid[:50],
                        "season_label": season_label,
                        "start_year": start_year,
                        "competition": competition,
                        "round_label": round_label,
                        "match_date": match_dt,
                        "match_date_display": date_disp,
                        "match_time": time_disp,
                        "home_team": home_team,
                        "away_team": away_team,
                        "home_rank": home_rank,
                        "away_rank": away_rank,
                        "home_score": home_score,
                        "away_score": away_score,
                        "score_note": score_note,
                        "status": status,
                        "attendance": attendance,
                    }
                )

        return parsed

    @classmethod
    def sync_pair_rivalry_matches(cls, team1: Team, team2: Team, session=None, fetch_remote=True):
        """
        İki takım arasındaki tüm maçları (Transfermarkt arşivi + yerel Fixture tablosu)
        RivalryMatch veritabanı tablosuna idempotent olarak senkronize eder.
        """
        if not team1 or not team2 or team1.id == team2.id:
            return 0

        tm_rows = cls.fetch_transfermarkt_pair_matches(team1, team2, session=session) if fetch_remote else []

        with transaction.atomic():
            for row in tm_rows:
                # Aynı sezon/ev/deplasman için sentetik FIX_ kaydı varsa sil, gerçek TM_ kaydı kalsın
                if row["competition"] == "Süper Lig":
                    RivalryMatch.objects.filter(
                        tm_match_id__startswith="FIX_",
                        season_label=row["season_label"],
                        competition="Süper Lig",
                        home_team=row["home_team"],
                        away_team=row["away_team"],
                    ).delete()
                RivalryMatch.objects.update_or_create(
                    tm_match_id=row["tm_match_id"],
                    defaults={
                        "season_label": row["season_label"],
                        "start_year": row["start_year"],
                        "competition": row["competition"],
                        "round_label": row["round_label"],
                        "match_date": row["match_date"],
                        "match_date_display": row["match_date_display"],
                        "match_time": row["match_time"],
                        "home_team": row["home_team"],
                        "away_team": row["away_team"],
                        "home_rank": row["home_rank"],
                        "away_rank": row["away_rank"],
                        "home_score": row["home_score"],
                        "away_score": row["away_score"],
                        "score_note": row["score_note"],
                        "status": row["status"],
                        "attendance": row["attendance"],
                    },
                )

            # Yerel Fixture tablosundaki (2026/2027 ve 2024/2025) güncel maçları senkronize et
            db_fixtures = list(
                Fixture.objects.filter(
                    home_team__in=[team1, team2],
                    away_team__in=[team1, team2],
                ).select_related("season", "home_team", "away_team")
            )
            TR_MON_NAMES = ["", "Oca", "Şub", "Mar", "Nis", "May", "Haz", "Tem", "Ağu", "Eyl", "Eki", "Kas", "Ara"]
            for fix in db_fixtures:
                s_name = fix.season.name if fix.season else "2026/2027"
                s_year = fix.season.start_year if fix.season else 2026
                f_date = fix.match_date.date() if fix.match_date else None
                f_date_disp = (
                    f"{f_date.day} {TR_MON_NAMES[f_date.month]} {f_date.year}"
                    if f_date
                    else ""
                )
                f_status = "FT" if (fix.status == "FT" and fix.home_score is not None and fix.away_score is not None) else "NS"

                existing = RivalryMatch.objects.filter(
                    season_label=s_name,
                    competition="Süper Lig",
                    home_team=fix.home_team,
                    away_team=fix.away_team,
                ).first()

                if existing:
                    # Eğer Fixture tablosunda maç bitmişse skoru yerel veritabanıyla birebir tut
                    if f_status == "FT" and (existing.status != "FT" or existing.home_score != fix.home_score or existing.away_score != fix.away_score):
                        existing.home_score = fix.home_score
                        existing.away_score = fix.away_score
                        existing.status = "FT"
                        existing.details_fetched = False
                        if f_date:
                            existing.match_date = f_date
                            existing.match_date_display = f_date_disp
                        existing.save()
                else:
                    RivalryMatch.objects.update_or_create(
                        tm_match_id=f"FIX_{fix.id}",
                        defaults={
                            "season_label": s_name,
                            "start_year": s_year,
                            "competition": "Süper Lig",
                            "round_label": fix.round_name or f"{fix.round_number}. Hafta",
                            "match_date": f_date,
                            "match_date_display": f_date_disp,
                            "match_time": fix.match_date.strftime("%H:%M") if fix.match_date else "",
                            "home_team": fix.home_team,
                            "away_team": fix.away_team,
                            "home_score": fix.home_score if f_status == "FT" else None,
                            "away_score": fix.away_score if f_status == "FT" else None,
                            "status": f_status,
                        },
                    )

        return RivalryMatch.objects.filter(
            home_team__in=[team1, team2], away_team__in=[team1, team2]
        ).count()

    @classmethod
    def get_rivalry_data(cls, team1: Team, team2: Team, competition_filter: str = "ALL", force_sync: bool = False):
        qs = RivalryMatch.objects.filter(
            home_team__in=[team1, team2],
            away_team__in=[team1, team2],
        )
        has_tm_rows = qs.filter(tm_match_id__startswith="TM_").exists()

        if force_sync or not has_tm_rows:
            cls.sync_pair_rivalry_matches(team1, team2, fetch_remote=True)
        else:
            cls.sync_pair_rivalry_matches(team1, team2, fetch_remote=False)

        all_matches = list(
            RivalryMatch.objects.filter(
                home_team__in=[team1, team2],
                away_team__in=[team1, team2],
            )
            .select_related("home_team", "away_team")
            .order_by("-match_date", "-start_year", "-id")
        )

        # Turnuva kırılımlarını hesapla
        comp_counts = {"ALL": len(all_matches)}
        for m in all_matches:
            c = m.competition or "Süper Lig"
            comp_counts[c] = comp_counts.get(c, 0) + 1

        comp_norm = (competition_filter or "ALL").strip()
        if comp_norm and comp_norm.upper() != "ALL":
            filtered_matches = [
                m for m in all_matches
                if (m.competition or "").lower() == comp_norm.lower()
                or (comp_norm.upper() == "SUPER_LIG" and m.competition == "Süper Lig")
            ]
        else:
            filtered_matches = all_matches

        t1_wins = 0
        t2_wins = 0
        draws = 0
        t1_goals = 0
        t2_goals = 0
        played_count = 0
        upcoming_count = 0

        t1_home = {"played": 0, "wins": 0, "draws": 0, "losses": 0, "goals_for": 0, "goals_against": 0}
        t2_home = {"played": 0, "wins": 0, "draws": 0, "losses": 0, "goals_for": 0, "goals_against": 0}

        biggest_t1 = None  # (goal_diff, total_goals, match_dict)
        biggest_t2 = None
        highest_scoring = None  # (total_goals, match_dict)
        last_5 = []
        serialized_matches = []

        for m in filtered_matches:
            is_t1_home = m.home_team_id == team1.id
            hs = m.home_score
            as_ = m.away_score
            is_ft = m.status == "FT" and hs is not None and as_ is not None

            winner_id = None
            if is_ft:
                played_count += 1
                g1 = hs if is_t1_home else as_
                g2 = as_ if is_t1_home else hs
                t1_goals += g1
                t2_goals += g2

                if is_t1_home:
                    t1_home["played"] += 1
                    t1_home["goals_for"] += g1
                    t1_home["goals_against"] += g2
                else:
                    t2_home["played"] += 1
                    t2_home["goals_for"] += g2
                    t2_home["goals_against"] += g1

                if g1 > g2:
                    t1_wins += 1
                    winner_id = team1.id
                    if is_t1_home:
                        t1_home["wins"] += 1
                    else:
                        t2_home["losses"] += 1
                elif g2 > g1:
                    t2_wins += 1
                    winner_id = team2.id
                    if is_t1_home:
                        t1_home["losses"] += 1
                    else:
                        t2_home["wins"] += 1
                else:
                    draws += 1
                    if is_t1_home:
                        t1_home["draws"] += 1
                    else:
                        t2_home["draws"] += 1
            else:
                upcoming_count += 1

            m_dict = {
                "id": m.id,
                "tm_match_id": m.tm_match_id,
                "season_label": m.season_label,
                "start_year": m.start_year,
                "competition": m.competition,
                "round_label": m.round_label,
                "match_date": m.match_date.isoformat() if m.match_date else None,
                "match_date_display": m.match_date_display or (m.match_date.isoformat() if m.match_date else ""),
                "match_time": m.match_time,
                "home_team": {
                    "id": m.home_team.id,
                    "name": m.home_team.name,
                    "short_name": m.home_team.short_name or m.home_team.name[:3].upper(),
                    "logo_url": m.home_team.logo_url,
                    "rank": m.home_rank,
                },
                "away_team": {
                    "id": m.away_team.id,
                    "name": m.away_team.name,
                    "short_name": m.away_team.short_name or m.away_team.name[:3].upper(),
                    "logo_url": m.away_team.logo_url,
                    "rank": m.away_rank,
                },
                "home_score": hs,
                "away_score": as_,
                "score_note": m.score_note,
                "status": "FT" if is_ft else "NS",
                "winner_team_id": winner_id,
                "attendance": m.attendance,
            }
            serialized_matches.append(m_dict)

            if is_ft:
                if len(last_5) < 5:
                    last_5.append(
                        {
                            "id": m.id,
                            "season_label": m.season_label,
                            "date": m_dict["match_date_display"],
                            "home_short": m_dict["home_team"]["short_name"],
                            "away_short": m_dict["away_team"]["short_name"],
                            "home_score": hs,
                            "away_score": as_,
                            "winner_team_id": winner_id,
                        }
                    )

                if m.score_note != "PEN":
                    tot_g = hs + as_
                    if highest_scoring is None or tot_g > highest_scoring[0]:
                        highest_scoring = (tot_g, m_dict)

                    g1 = hs if is_t1_home else as_
                    g2 = as_ if is_t1_home else hs
                    if g1 > g2:
                        cand = (g1 - g2, g1, m_dict)
                        if biggest_t1 is None or (cand[0], cand[1]) > (biggest_t1[0], biggest_t1[1]):
                            biggest_t1 = cand
                    elif g2 > g1:
                        cand = (g2 - g1, g2, m_dict)
                        if biggest_t2 is None or (cand[0], cand[1]) > (biggest_t2[0], biggest_t2[1]):
                            biggest_t2 = cand

        if played_count > 0:
            t1_pct = round((t1_wins / played_count) * 100, 1)
            d_pct = round((draws / played_count) * 100, 1)
            t2_pct = round(max(0.0, 100.0 - t1_pct - d_pct), 1)
            avg_goals = round((t1_goals + t2_goals) / played_count, 2)
        else:
            t1_pct, d_pct, t2_pct = 33.3, 33.4, 33.3
            avg_goals = 0.0

        if played_count == 0:
            analysis = f"{team1.name} ile {team2.name} arasında bu kategoride henüz tamamlanmış maç kaydı bulunmuyor."
        else:
            leader_str = (
                f"{team1.name} {t1_wins}-{t2_wins} üstün"
                if t1_wins > t2_wins
                else (
                    f"{team2.name} {t2_wins}-{t1_wins} üstün"
                    if t2_wins > t1_wins
                    else f"{t1_wins}-{t2_wins} tam eşitlik var"
                )
            )
            analysis = (
                f"{team1.name} ile {team2.name} arasında oynanan {played_count} maçta {leader_str} "
                f"({draws} beraberlik). Bu karşılaşmalarda {team1.name} {t1_goals} gol, "
                f"{team2.name} ise {t2_goals} gol kaydetti (maç başı {avg_goals} gol)."
            )

        competitions_list = [
            {"key": "ALL", "label": "Tüm Maçlar", "count": comp_counts.get("ALL", 0)}
        ]
        for comp_name, cnt in sorted(
            ((k, v) for k, v in comp_counts.items() if k != "ALL"),
            key=lambda x: (-x[1], x[0]),
        ):
            competitions_list.append({"key": comp_name, "label": comp_name, "count": cnt})

        def _team_dict(t: Team):
            return {
                "id": t.id,
                "name": t.name,
                "short_name": t.short_name or t.name[:3].upper(),
                "logo_url": t.logo_url,
                "city": t.city,
                "stadium": t.stadium,
                "manager": t.manager,
                "market_value": float(t.market_value or 0),
                "is_super_lig": t.is_super_lig,
            }

        return {
            "team1": _team_dict(team1),
            "team2": _team_dict(team2),
            "competition_filter": comp_norm or "ALL",
            "competitions": competitions_list,
            "summary": {
                "total_matches": played_count,
                "upcoming_matches": upcoming_count,
                "team1_wins": t1_wins,
                "draws": draws,
                "team2_wins": t2_wins,
                "team1_win_pct": t1_pct,
                "draw_pct": d_pct,
                "team2_win_pct": t2_pct,
                "team1_goals": t1_goals,
                "team2_goals": t2_goals,
                "total_goals": t1_goals + t2_goals,
                "avg_goals_per_match": avg_goals,
                "team1_home": t1_home,
                "team2_home": t2_home,
                "biggest_team1_win": biggest_t1[2] if biggest_t1 else None,
                "biggest_team2_win": biggest_t2[2] if biggest_t2 else None,
                "highest_scoring_match": highest_scoring[1] if highest_scoring else None,
                "last_5": last_5,
                "analysis": analysis,
            },
            "matches": serialized_matches,
        }

    @staticmethod
    def _parse_tm_clock_minute(uhr_el) -> str:
        """Transfermarkt .sb-aktion-uhr sprite konumundan maç dakikasını (örn: 29', 45+2') çözer."""
        if not uhr_el:
            return ""
        sprite = uhr_el.select_one(".sb-sprite-uhr-klein")
        if not sprite:
            raw = uhr_el.get_text(strip=True)
            return f"{raw}'" if raw and not raw.endswith("'") else raw
        style = sprite.get("style", "")
        m_pos = re.search(r"background-position:\s*(-?\d+)px\s+(-?\d+)px", style)
        if not m_pos:
            return ""
        x_val = abs(int(m_pos.group(1)))
        y_val = abs(int(m_pos.group(2)))
        col = x_val // 36
        row = y_val // 36
        base_min = row * 10 + col + 1
        # sb-sprite-uhr-k.png yalnızca 1..120 dakikaları (satır 0..11, y < 432) kapsar; y >= 432 bilinmeyen/maç sonu ikonu
        if col < 0 or col > 9 or y_val >= 432 or base_min < 1 or base_min > 120:
            return ""
        extra_txt = sprite.get_text(" ", strip=True)
        m_extra = re.search(r"\+\s*(\d+)", extra_txt)
        if m_extra:
            return f"{base_min}+{m_extra.group(1)}'"
        return f"{base_min}'"

    @classmethod
    def fetch_transfermarkt_match_detail(cls, match: RivalryMatch, session=None):
        """Transfermarkt maç raporu (spielbericht) sayfasından stadyum, hakem, ilk yarı, goller ve kartları çeker."""
        raw_id = str(match.tm_match_id or "")
        m_id = re.match(r"^TM_(\d+)$", raw_id)
        if not m_id:
            return None

        url = cls.SPIELBERICHT_URL.format(match_id=m_id.group(1))
        http = session or requests
        try:
            resp = http.get(url, headers=TransfermarktScraper.HEADERS, timeout=15)
            if resp.status_code != 200:
                return None
        except Exception:
            return None

        soup = BeautifulSoup(resp.text, "html.parser")

        tm_header_ids = []
        for a in soup.select(".sb-team a.sb-vereinslink"):
            m_v = re.search(r"/verein/(\d+)", a.get("href", ""))
            if m_v:
                tm_header_ids.append(int(m_v.group(1)))
        db_home_tm_id = cls.resolve_team_tm_id(match.home_team)
        db_away_tm_id = cls.resolve_team_tm_id(match.away_team)
        is_swapped = (
            len(tm_header_ids) >= 2
            and db_home_tm_id is not None
            and db_away_tm_id is not None
            and tm_header_ids[0] == db_away_tm_id
            and tm_header_ids[1] == db_home_tm_id
        )

        venue = ""
        referee = ""
        attendance = ""

        zusatz = soup.select_one(".sb-zusatzinfos")
        if zusatz:
            venue_a = zusatz.select_one('a[href*="/stadion/"]')
            if venue_a:
                venue = venue_a.get_text(" ", strip=True)
            ref_a = zusatz.select_one('a[href*="/schiedsrichter/"]')
            if ref_a:
                referee = ref_a.get_text(" ", strip=True)
            z_txt = zusatz.get_text(" ", strip=True)
            m_att = re.search(r"([\d\.]+)\s*seyirci", z_txt, re.I)
            if m_att:
                attendance = m_att.group(1)

        halftime_score = ""
        ht_el = soup.select_one(".sb-halbzeit")
        if ht_el:
            ht_raw = ht_el.get_text(" ", strip=True)
            m_ht = re.search(r"(\d+)\s*:\s*(\d+)", ht_raw)
            if m_ht:
                if is_swapped:
                    halftime_score = f"{m_ht.group(2)} - {m_ht.group(1)}"
                else:
                    halftime_score = f"{m_ht.group(1)} - {m_ht.group(2)}"

        home_short = match.home_team.short_name or match.home_team.name[:3].upper()
        away_short = match.away_team.short_name or match.away_team.name[:3].upper()

        def _resolve_side(li_classes):
            is_tm_home = "sb-aktion-heim" in (li_classes or [])
            if is_swapped:
                return "away" if is_tm_home else "home"
            return "home" if is_tm_home else "away"

        events = []
        for li in soup.select("#sb-tore li"):
            side = _resolve_side(li.get("class") or [])
            team_obj = match.home_team if side == "home" else match.away_team
            t_short = home_short if side == "home" else away_short

            minute = cls._parse_tm_clock_minute(li.select_one(".sb-aktion-uhr"))
            stand_el = li.select_one(".sb-aktion-spielstand")
            score_after = stand_el.get_text(" ", strip=True) if stand_el else ""

            aktion = li.select_one(".sb-aktion-aktion")
            aktion_text = aktion.get_text(" ", strip=True) if aktion else ""
            players_a = aktion.select("a.wichtig") if aktion else []
            scorer = players_a[0].get_text(" ", strip=True) if len(players_a) >= 1 else ""

            parts = re.split(r"\basist\s*:", aktion_text, maxsplit=1, flags=re.I)
            goal_part = parts[0]
            assist_part = parts[1] if len(parts) > 1 else ""

            goal_meta = goal_part.lower()
            if scorer:
                goal_meta = goal_meta.replace(scorer.lower(), "", 1)

            is_own_goal = ("kendi kalesine" in goal_meta) or bool(re.search(r"\(\s*kk\s*\)", goal_meta))
            is_penalty = "penalt" in goal_meta

            assist = ""
            if (
                len(players_a) >= 2
                and assist_part
                and not is_own_goal
                and not is_penalty
                and "penalt" not in assist_part.lower()
            ):
                assist = players_a[1].get_text(" ", strip=True)

            if scorer:
                events.append(
                    {
                        "side": side,
                        "team_short": t_short,
                        "team_name": team_obj.name,
                        "minute": minute,
                        "score_after": score_after,
                        "scorer": scorer,
                        "assist": assist,
                        "is_penalty": is_penalty,
                        "is_own_goal": is_own_goal,
                    }
                )

        cards = []
        for li in soup.select("#sb-karten li"):
            aktion = li.select_one(".sb-aktion-aktion")
            aktion_text = aktion.get_text(" ", strip=True) if aktion else ""
            players_a = aktion.select("a.wichtig") if aktion else []
            player_name = players_a[0].get_text(" ", strip=True) if players_a else ""

            sprite_el = li.select_one(".sb-aktion-spielstand .sb-sprite")
            sprite_classes = set(sprite_el.get("class") or []) if sprite_el else set()

            if "sb-rot" in sprite_classes:
                card_type = "Kırmızı Kart"
            elif "sb-gelbrot" in sprite_classes:
                card_type = "2. Sarıdan Kırmızı"
            elif "sb-gelb" in sprite_classes:
                continue
            else:
                low_txt = aktion_text.lower()
                action_only = low_txt.replace(player_name.lower(), "", 1) if player_name else low_txt
                if (
                    "sarı-kırmızı" in action_only
                    or "sarı karttan kırmızı" in action_only
                    or "ikinci sarıdan kırmızı" in action_only
                ):
                    card_type = "2. Sarıdan Kırmızı"
                elif "kırmızı kart" in action_only:
                    card_type = "Kırmızı Kart"
                else:
                    continue

            side = _resolve_side(li.get("class") or [])
            team_obj = match.home_team if side == "home" else match.away_team
            t_short = home_short if side == "home" else away_short
            minute = cls._parse_tm_clock_minute(li.select_one(".sb-aktion-uhr"))
            if player_name:
                cards.append(
                    {
                        "side": side,
                        "team_short": t_short,
                        "team_name": team_obj.name,
                        "minute": minute,
                        "player": player_name,
                        "card_type": card_type,
                    }
                )

        return {
            "venue": venue,
            "referee": referee,
            "attendance": attendance,
            "halftime_score": halftime_score,
            "events": events,
            "cards": cards,
        }

    @classmethod
    def get_match_detail(cls, match_id: int, force_refresh: bool = False):
        """Rekabet maçının tüm detaylarını (stadyum, hakem, İY skoru, goller, kırmızı kartlar) döner."""
        match = (
            RivalryMatch.objects.select_related("home_team", "away_team")
            .filter(id=match_id)
            .first()
        )
        if not match:
            return None

        if force_refresh or not match.details_fetched:
            local_fix = None
            if match.competition == "Süper Lig":
                local_fix = Fixture.objects.filter(
                    season__name=match.season_label,
                    home_team=match.home_team,
                    away_team=match.away_team,
                ).first()

            tm_detail = cls.fetch_transfermarkt_match_detail(match) if match.status == "FT" else None

            venue = (
                (tm_detail.get("venue") if tm_detail else "")
                or match.venue
                or (local_fix.venue if local_fix else "")
                or (match.home_team.stadium or "")
            )
            referee = (
                (tm_detail.get("referee") if tm_detail else "")
                or match.referee
                or (local_fix.referee if local_fix else "")
            )
            attendance = (
                (tm_detail.get("attendance") if tm_detail else "")
                or match.attendance
            )
            halftime_score = (
                (tm_detail.get("halftime_score") if tm_detail else "")
                or match.halftime_score
            )
            events = tm_detail.get("events", []) if tm_detail else list(match.events_json or [])
            if not events and local_fix:
                from api.integrations.api_football import APIFootballService
                events = list(APIFootballService.get_cached_events(local_fix.id) or [])
            cards = tm_detail.get("cards", []) if tm_detail else list(match.cards_json or [])

            match.venue = venue[:150]
            match.referee = referee[:100]
            match.attendance = attendance[:30]
            match.halftime_score = halftime_score[:30]
            match.events_json = events
            match.cards_json = cards
            # Oynanacak (NS) veya dış erişim başarısız olduğunda sabit önbelleğe kitleme
            if match.status == "FT" and (
                tm_detail is not None or not str(match.tm_match_id or "").startswith("TM_")
            ):
                match.details_fetched = True
            match.save(
                update_fields=[
                    "venue",
                    "referee",
                    "attendance",
                    "halftime_score",
                    "events_json",
                    "cards_json",
                    "details_fetched",
                ]
            )

        is_ft = match.status == "FT" and match.home_score is not None and match.away_score is not None
        if is_ft:
            status_display = f"Maç Bitti (MS) • {match.score_note}" if match.score_note else "Maç Bitti (MS)"
        else:
            status_display = f"Oynanacak ({match.match_date_display} {match.match_time})".strip()

        return {
            "id": match.id,
            "tm_match_id": match.tm_match_id,
            "season_label": match.season_label,
            "competition": match.competition,
            "round_label": match.round_label,
            "match_date": match.match_date.isoformat() if match.match_date else None,
            "match_date_display": match.match_date_display or (match.match_date.isoformat() if match.match_date else ""),
            "match_time": match.match_time,
            "status": "FT" if is_ft else "NS",
            "status_display": status_display,
            "home_team": {
                "id": match.home_team.id,
                "name": match.home_team.name,
                "short_name": match.home_team.short_name or match.home_team.name[:3].upper(),
                "logo_url": match.home_team.logo_url,
                "rank": match.home_rank,
            },
            "away_team": {
                "id": match.away_team.id,
                "name": match.away_team.name,
                "short_name": match.away_team.short_name or match.away_team.name[:3].upper(),
                "logo_url": match.away_team.logo_url,
                "rank": match.away_rank,
            },
            "home_score": match.home_score,
            "away_score": match.away_score,
            "score_note": match.score_note,
            "halftime_score": match.halftime_score,
            "venue": match.venue or match.home_team.stadium or "",
            "referee": match.referee or "",
            "attendance": match.attendance or "",
            "events": list(match.events_json or []),
            "cards": list(match.cards_json or []),
        }

