import os
import re
import time
import threading
import requests
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from django.db import close_old_connections, transaction
from django.db.models import F, Q
from django.utils import timezone
from api.models import Fixture, Team, Season, LeagueStanding, Player, PlayerSeasonStats


class APIFootballService:
    """
    Canlı Skor & Fikstür Senkronizasyon Servisi:
    - Birincil Canlı Kaynak: ESPN Gerçek Zamanlı Süper Lig API (tur.1/scoreboard)
    - İkincil Kaynak: API-Football (RapidAPI - League ID: 203)
    - Maçkolik standardında canlı dakika akışı (1'..45+2' -> İY -> 46'..90+4' -> MS).
    - Maç bittiği anda (MS) Puan Durumu (LeagueStanding) ve Oyuncu Sezon İstatistiklerini (PlayerSeasonStats) otomatik günceller.
    """

    BASE_URL = "https://v3.football.api-sports.io"
    RAPIDAPI_URL = "https://api-football-v1.p.rapidapi.com/v3"
    ESPN_SCOREBOARD_URL = "https://site.api.espn.com/apis/site/v2/sports/soccer/tur.1/scoreboard"
    ESPN_ROSTER_URL = "https://site.api.espn.com/apis/site/v2/sports/soccer/tur.1/teams/{espn_id}/roster"
    ESPN_SUMMARY_URL = "https://site.api.espn.com/apis/site/v2/sports/soccer/tur.1/summary?event={event_id}"
    SUPER_LIG_LEAGUE_ID = 203

    ESPN_CLUB_IDS = {
        'alanyaspor': 9078,
        'amed': 132335,
        'besiktas': 1895,
        'rize': 7656,
        'erzurum': 19267,
        'eyup': 20729,
        'fenerbahce': 436,
        'galatasaray': 432,
        'gaziantep': 20070,
        'genclerbirligi': 996,
        'goztepe': 789,
        'basaksehir': 7914,
        'kasimpasa': 6870,
        'kocaeli': 995,
        'konya': 7648,
        'samsun': 11429,
        'trabzon': 997,
        'corum': 132334,
    }

    _LIVE_EVENTS_CACHE = {}
    _LIVE_CLOCK_CACHE = {}
    _last_espn_sync_ts = 0.0
    _initial_events_warmed = False
    _sync_lock = threading.Lock()
    _poller_started = False
    _poller_lock = threading.Lock()

    TR_MONTHS = {
        1: 'Oca', 2: 'Şub', 3: 'Mar', 4: 'Nis', 5: 'May', 6: 'Haz',
        7: 'Tem', 8: 'Ağu', 9: 'Eyl', 10: 'Eki', 11: 'Kas', 12: 'Ara'
    }

    @classmethod
    def get_cached_events(cls, fixture_id):
        return cls._LIVE_EVENTS_CACHE.get(fixture_id, [])

    @classmethod
    def get_live_clock(cls, fixture_id):
        return cls._LIVE_CLOCK_CACHE.get(fixture_id)

    @staticmethod
    def normalize_clock_label(raw_clk):
        if not raw_clk:
            return ''
        s = str(raw_clk).strip()
        # ESPN "45'+2'" -> Maçkolik "45+2'"
        s = re.sub(r"'\s*\+\s*(\d+)'?", r"+\1'", s)
        return s

    @classmethod
    def format_dynamic_ns_label(cls, match_dt, now_ist=None):
        ist = ZoneInfo('Europe/Istanbul')
        if not now_ist:
            now_ist = timezone.now().astimezone(ist)
        if not match_dt:
            return 'Başlamadı'
        m_ist = match_dt.astimezone(ist)
        hm = m_ist.strftime('%H:%M')
        diff_days = (m_ist.date() - now_ist.date()).days
        if diff_days == 0:
            return f"Bugün {hm}"
        if diff_days == 1:
            return f"Yarın {hm}"
        if diff_days == -1:
            return f"Dün {hm}"
        return f"{m_ist.day:02d} {cls.TR_MONTHS.get(m_ist.month, '')} {hm}"

    @classmethod
    def ensure_background_poller(cls):
        """
        Arka planda her 8 saniyede bir canlı skorları, dakikaları (1' -> İY -> 46' -> MS)
        ve biten maçların puan tablosu etkilerini kesintisiz senkronize eder.
        """
        if cls._poller_started:
            return
        with cls._poller_lock:
            if cls._poller_started:
                return
            cls._poller_started = True

            def _poller_loop():
                # İlk açılışta geçmişten kalan tamamlanmamış maçları hemen yakala
                time.sleep(1.0)
                while True:
                    try:
                        close_old_connections()
                        cls.sync_real_espn_live_scoreboard(force=True)
                    except Exception as exc:
                        print(f"[LivePoller] Senkronizasyon uyarısı: {exc}")
                    finally:
                        try:
                            close_old_connections()
                        except Exception:
                            pass
                    time.sleep(8.0)

            t = threading.Thread(target=_poller_loop, name="superlig-espn-live-poller", daemon=True)
            t.start()

    @staticmethod
    def _norm_text(val):
        if not val:
            return ''
        s = str(val).replace('İ', 'i').replace('I', 'i').lower()
        for src, dst in [('ı', 'i'), ('ğ', 'g'), ('ü', 'u'), ('ş', 's'), ('ö', 'o'), ('ç', 'c'), ('á', 'a'), ('é', 'e'), ('ó', 'o'), ('ć', 'c'), ('š', 's'), ('ž', 'z')]:
            s = s.replace(src, dst)
        return re.sub(r'[^a-z0-9 ]+', ' ', s).strip()

    @classmethod
    def _match_super_lig_team(cls, raw_name):
        norm = cls._norm_text(raw_name)
        if not norm:
            return None
        keyword_to_exact_name = [
            ('galatasaray', 'Galatasaray'),
            ('amed', 'Amed SK'),
            ('trabzon', 'Trabzonspor'),
            ('besiktas', 'Beşiktaş'),
            ('fenerbahce', 'Fenerbahçe'),
            ('kasimpasa', 'Kasımpaşa'),
            ('kocaeli', 'Kocaelispor'),
            ('erzurum', 'Erzurumspor FK'),
            ('corum', 'Arca Çorum FK'),
            ('goztepe', 'Göztepe'),
            ('alanya', 'Alanyaspor'),
            ('basaksehir', 'Başakşehir'),
            ('rize', 'Çaykur Rizespor'),
            ('gaziantep', 'Gaziantep FK'),
            ('konya', 'Konyaspor'),
            ('genclerbirligi', 'Gençlerbirliği'),
            ('gencler', 'Gençlerbirliği'),
            ('samsun', 'Samsunspor'),
            ('eyup', 'Eyüpspor'),
        ]
        for kw, exact_db_name in keyword_to_exact_name:
            if kw in norm:
                team = Team.objects.filter(is_super_lig=True, name=exact_db_name).first()
                if team:
                    return team
        return Team.objects.exclude(name__icontains='Birleşik').filter(name__icontains=raw_name.split()[0]).first()

    @classmethod
    def _match_player_for_team(cls, raw_player_name, team, season):
        norm_target = cls._norm_text(raw_player_name)
        if not norm_target:
            return None
        target_tokens = [t for t in norm_target.split() if len(t) >= 2]
        if not target_tokens:
            return None
        surname = target_tokens[-1]

        # 1. Önce bu sezonda o takımda istatistik kaydı olan oyunculara bak
        stats_qs = list(PlayerSeasonStats.objects.filter(season=season, team=team).select_related('player'))
        for st in stats_qs:
            p_norm = cls._norm_text(st.player.name)
            if p_norm == norm_target:
                return st.player
        for st in stats_qs:
            p_tokens = cls._norm_text(st.player.name).split()
            if len(surname) >= 3 and p_tokens and p_tokens[-1] == surname:
                return st.player

        # 2. current_team üzerinden bak
        team_players = list(Player.objects.filter(current_team=team))
        for p in team_players:
            p_norm = cls._norm_text(p.name)
            if p_norm == norm_target:
                return p
        for p in team_players:
            p_tokens = cls._norm_text(p.name).split()
            if len(surname) >= 3 and p_tokens and p_tokens[-1] == surname:
                return p
        return None

    @classmethod
    def resolve_espn_club_id(cls, team_name):
        norm = cls._norm_text(team_name)
        if not norm:
            return None
        for kw, eid in cls.ESPN_CLUB_IDS.items():
            if kw in norm:
                return eid
        return None

    @classmethod
    def fetch_espn_club_roster_stats(cls, team_or_name, session=None):
        """ESPN tur.1/teams/{id}/roster uç noktasından kulübün kümülatif sezon oyuncu istatistiklerini çeker."""
        if isinstance(team_or_name, int):
            espn_id = team_or_name
        else:
            raw_name = getattr(team_or_name, 'name', team_or_name)
            espn_id = cls.resolve_espn_club_id(raw_name)
        if not espn_id:
            return []
        url = cls.ESPN_ROSTER_URL.format(espn_id=espn_id)
        try:
            http = session or requests
            resp = http.get(url, timeout=12)
            if resp.status_code != 200:
                return []
            data = resp.json()
        except Exception as exc:
            print(f"[ESPN Roster] {team_or_name} çekilemedi: {exc}")
            return []

        entries = []
        for ath in data.get("athletes", []) or []:
            name = ath.get("displayName") or ath.get("fullName") or ""
            if not name:
                continue
            jersey_raw = ath.get("jersey")
            jersey = int(jersey_raw) if str(jersey_raw).isdigit() else None
            pos_abbr = ((ath.get("position") or {}).get("abbreviation") or "").upper()
            stat_map = {}
            for cat in ((ath.get("statistics") or {}).get("splits") or {}).get("categories", []) or []:
                for st in cat.get("stats", []) or []:
                    stat_map[st.get("name")] = st.get("value", 0.0)
            entries.append(cls._build_espn_player_entry(name, jersey, pos_abbr, stat_map))
        return entries

    @staticmethod
    def _build_espn_player_entry(name, jersey, pos_abbr, stat_map, extra=None):
        """ESPN oyuncu istatistik sözlüğünü standart dahili formata dönüştürür."""
        entry = {
            "name": name,
            "jersey": jersey,
            "pos_abbr": pos_abbr,
            "matches": int(round(float(stat_map.get("appearances", 0) or 0))),
            "goals": int(round(float(stat_map.get("totalGoals", 0) or 0))),
            "assists": int(round(float(stat_map.get("goalAssists", 0) or 0))),
            "total_shots": int(round(float(stat_map.get("totalShots", 0) or 0))),
            "shots_on_target": int(round(float(stat_map.get("shotsOnTarget", 0) or 0))),
            "yellow_cards": int(round(float(stat_map.get("yellowCards", 0) or 0))),
            "red_cards": int(round(float(stat_map.get("redCards", 0) or 0))),
            "saves": int(round(float(stat_map.get("saves", 0) or 0))),
            "goals_conceded": int(round(float(stat_map.get("goalsConceded", 0) or 0))),
        }
        if extra:
            entry.update(extra)
        return entry

    @classmethod
    def fetch_espn_match_summary_players(cls, event_id, home_team=None, away_team=None, session=None):
        """
        ESPN /summary?event={id} uç noktasından biten maçta gerçekten sahaya çıkan (ilk 11 + sonradan giren)
        oyuncuların o maça özel gol, asist, şut, kart, kurtarış ve yedikleri gol istatistiklerini çeker.
        """
        result = {"home": [], "away": []}
        if not event_id:
            return result
        url = cls.ESPN_SUMMARY_URL.format(event_id=event_id)
        try:
            http = session or requests
            resp = http.get(url, timeout=10)
            if resp.status_code != 200:
                return result
            data = resp.json()
        except Exception as exc:
            print(f"[ESPN Summary] event={event_id} çekilemedi: {exc}")
            return result

        home_norm = cls._norm_text(getattr(home_team, "name", "") or "")
        away_norm = cls._norm_text(getattr(away_team, "name", "") or "")

        for roster_block in data.get("rosters") or []:
            side = roster_block.get("homeAway")
            if side not in ("home", "away"):
                t_norm = cls._norm_text(((roster_block.get("team") or {}).get("displayName")) or "")
                if home_norm and t_norm and (home_norm in t_norm or t_norm in home_norm):
                    side = "home"
                elif away_norm and t_norm and (away_norm in t_norm or t_norm in away_norm):
                    side = "away"
                else:
                    continue

            for item in roster_block.get("roster") or []:
                ath = item.get("athlete") or {}
                name = ath.get("displayName") or ath.get("fullName") or ""
                if not name:
                    continue
                stat_map = {
                    st.get("name"): st.get("value", 0.0)
                    for st in (item.get("stats") or [])
                    if st.get("name")
                }
                appearances = int(round(float(stat_map.get("appearances", 0) or 0)))
                sub_ins = int(round(float(stat_map.get("subIns", 0) or 0)))
                is_starter = bool(item.get("starter"))
                is_sub = bool(item.get("subbedIn")) or sub_ins > 0
                did_not_play = bool(item.get("didNotPlay"))
                played = (not did_not_play) and (appearances > 0 or is_starter or is_sub)
                if not played:
                    continue

                jersey_raw = item.get("jersey")
                jersey = int(jersey_raw) if str(jersey_raw).isdigit() else None
                pos_abbr = ((item.get("position") or {}).get("abbreviation") or "").upper()
                result[side].append(
                    cls._build_espn_player_entry(
                        name,
                        jersey,
                        pos_abbr,
                        stat_map,
                        extra={
                            "matches": 1,
                            "minutes": 90 if is_starter else 25,
                            "is_starter": is_starter,
                        },
                    )
                )
        return result

    @classmethod
    def _aggregate_goal_event_deltas(cls, goal_events_for_team):
        """Maç özeti kadrosu alınamadığında skorboard gol/asist olaylarından oyuncu katkı listesi üretir."""
        by_norm = {}
        for ev in goal_events_for_team or []:
            if not ev.get("is_own_goal"):
                scorer = (ev.get("scorer") or "").strip()
                if scorer and scorer.lower() not in ("gol", "goal"):
                    key = cls._norm_text(scorer)
                    slot = by_norm.setdefault(key, cls._build_espn_player_entry(
                        scorer, None, "", {}, extra={"matches": 1, "minutes": 90}
                    ))
                    slot["goals"] += 1
            assist = (ev.get("assist") or "").strip()
            if assist and not ev.get("is_own_goal"):
                key = cls._norm_text(assist)
                slot = by_norm.setdefault(key, cls._build_espn_player_entry(
                    assist, None, "", {}, extra={"matches": 1, "minutes": 90}
                ))
                slot["assists"] += 1
        return list(by_norm.values())

    @classmethod
    def sync_team_espn_player_stats(
        cls,
        season,
        team,
        espn_entries=None,
        match_delta_entries=None,
        goal_events_for_team=None,
        opp_conceded=None,
        team_played=None,
    ):
        """
        Maç bittiğinde (MS) kadrodaki oyuncuların sezon istatistiklerini idempotent uzlaştırır:
        - ESPN /roster kümülatif toplamı bu maçı içeriyorsa (max >= team_played) doğrudan onu baz alır.
        - ESPN /roster henüz gecikmeli ise (eski haftada kaldıysa veya boşsa) maç özeti (/summary)
          veya gol olaylarından yalnızca gerçekten oynayan/katkı veren oyunculara bu maçın farkını ekler.
        - Yedek bekleyen oyunculara körü körüne +1 eklemez, çift sayım yapmaz; oynayan kalecinin
          gol yemediği maçta (opp_conceded == 0) clean_sheets değerini +1 artırır.
        """
        if not season or not team:
            return 0
        if espn_entries is None:
            espn_entries = cls.fetch_espn_club_roster_stats(team)

        espn_max_matches = max((e.get("matches", 0) for e in (espn_entries or [])), default=0)
        roster_caught_up = bool(espn_entries) and (not team_played or espn_max_matches >= team_played)
        delta_source = list(match_delta_entries or [])
        if not delta_source and not roster_caught_up and goal_events_for_team:
            delta_source = cls._aggregate_goal_event_deltas(goal_events_for_team)
        apply_match_delta = (not roster_caught_up) and bool(delta_source)

        if not espn_entries and not apply_match_delta:
            return 0

        from api.integrations.transfermarkt_scraper import TransfermarktScraper

        active_players = list(Player.objects.filter(current_team=team, is_active=True))
        if not active_players:
            return 0

        existing_stats = {
            st.player_id: st
            for st in PlayerSeasonStats.objects.filter(season=season, team=team)
        }
        used_espn_indices = set()
        used_delta_indices = set()
        updated = 0

        for player in active_players:
            espn = None
            if espn_entries:
                matched = TransfermarktScraper._match_espn_entry(
                    player.name, player.jersey_number, player.position, espn_entries, used_espn_indices
                )
                if matched:
                    idx, espn = matched
                    used_espn_indices.add(idx)

            delta = None
            if apply_match_delta:
                d_matched = TransfermarktScraper._match_espn_entry(
                    player.name, player.jersey_number, player.position, delta_source, used_delta_indices
                )
                if d_matched:
                    d_idx, delta = d_matched
                    used_delta_indices.add(d_idx)

            if not espn and not delta:
                continue

            st_obj = existing_stats.get(player.id)
            prev_matches = (st_obj.matches or 0) if st_obj else 0
            prev_goals = (st_obj.goals or 0) if st_obj else 0
            prev_assists = (st_obj.assists or 0) if st_obj else 0
            prev_minutes = (st_obj.minutes or 0) if st_obj else 0
            prev_yc = (st_obj.yellow_cards or 0) if st_obj else 0
            prev_rc = (st_obj.red_cards or 0) if st_obj else 0
            prev_cs = (st_obj.clean_sheets or 0) if st_obj else 0

            base_matches = max(prev_matches, espn["matches"] if espn else 0)
            base_goals = max(prev_goals, espn["goals"] if espn else 0)
            base_assists = max(prev_assists, espn["assists"] if espn else 0)
            base_yc = max(prev_yc, espn["yellow_cards"] if espn else 0)
            base_rc = max(prev_rc, espn["red_cards"] if espn else 0)

            if base_matches <= 0 and not delta:
                continue

            if not st_obj:
                st_obj, _ = PlayerSeasonStats.objects.get_or_create(
                    player=player,
                    season=season,
                    team=team,
                    defaults={"market_value": player.market_value or 0},
                )

            is_gk = TransfermarktScraper._is_goalkeeper(player.position)
            new_matches = base_matches
            new_goals = base_goals
            new_assists = base_assists
            new_yc = base_yc
            new_rc = base_rc
            new_cs = prev_cs
            new_minutes = prev_minutes

            if delta:
                already_at_week = bool(team_played and base_matches >= team_played)
                if not already_at_week:
                    new_matches = base_matches + (delta.get("matches") or 1)
                    new_goals = base_goals + delta.get("goals", 0)
                    new_assists = base_assists + delta.get("assists", 0)
                    new_yc = base_yc + delta.get("yellow_cards", 0)
                    new_rc = base_rc + delta.get("red_cards", 0)
                    new_minutes = prev_minutes + delta.get("minutes", 90)
                    if is_gk and opp_conceded == 0:
                        new_cs = prev_cs + 1
            else:
                if is_gk and opp_conceded == 0 and new_matches > prev_matches:
                    new_cs = prev_cs + 1
                if new_matches > prev_matches:
                    added_m = new_matches - prev_matches
                    per_match_min = 90 if is_gk else (
                        max(25, min(90, int(round(prev_minutes / prev_matches)))) if prev_matches > 0 else 75
                    )
                    new_minutes = prev_minutes + added_m * per_match_min

            base_shots = (
                espn["total_shots"]
                if espn
                else (int(round((st_obj.shots_per_game or 0.0) * base_matches)) if base_matches > 0 else 0)
            )
            delta_shots = delta.get("total_shots", 0) if delta and not (team_played and base_matches >= team_played) else 0
            total_shots = base_shots + delta_shots

            base_saves = espn["saves"] if espn else 0
            delta_saves = delta.get("saves", 0) if delta and not (team_played and base_matches >= team_played) else 0
            total_saves = base_saves + delta_saves

            base_conceded = espn["goals_conceded"] if espn else 0
            delta_conceded = delta.get("goals_conceded", 0) if delta and not (team_played and base_matches >= team_played) else 0
            total_conceded = base_conceded + delta_conceded

            has_shots = bool(espn) or (delta is not None and (base_shots > 0 or delta_shots > 0))

            st_obj.matches = new_matches
            st_obj.minutes = new_minutes
            st_obj.goals = new_goals
            st_obj.assists = new_assists
            st_obj.yellow_cards = new_yc
            st_obj.red_cards = new_rc

            metrics = TransfermarktScraper.compute_season_metrics(
                matches=st_obj.matches,
                minutes=st_obj.minutes,
                goals=st_obj.goals,
                assists=st_obj.assists,
                yellow_cards=st_obj.yellow_cards,
                red_cards=st_obj.red_cards,
                clean_sheets=new_cs,
                position=player.position,
                market_value=float(player.market_value or 0),
                total_shots=total_shots,
                saves=total_saves,
                goals_conceded=total_conceded,
                has_espn_shots=has_shots,
            )
            st_obj.shots_per_game = metrics["shots_per_game"]
            st_obj.pass_accuracy = metrics["pass_accuracy"]
            st_obj.key_passes = metrics["key_passes"]
            st_obj.key_passes_per_game = metrics["key_passes_per_game"]
            st_obj.dribbles_per_game = metrics["dribbles_per_game"]
            st_obj.clean_sheets = metrics["clean_sheets"]
            st_obj.rating = metrics["rating"]
            st_obj.save()
            updated += 1

        return updated

    @classmethod
    def _finalize_finished_fixture_atomically(cls, fixture_id, h_score, a_score, goal_events, espn_event_id=None):
        """
        Gerçek hayatta maç bittiğinde (ESPN state == 'post') yalnızca BİR KEZ çalışır:
        - Maçı FT (MS) olarak işaretler.
        - Ev sahibi ve deplasman takımlarının puan durumunu (O, G, B, M, AG, YG, AV, P) ve lig sıralamasını günceller.
        - Kilit dışında ESPN kümülatif sezon toplamlarıyla oyuncu istatistiklerini idempotent günceller.
        """
        season = None
        home_team = None
        away_team = None
        home_played = 0
        away_played = 0

        with transaction.atomic():
            fix = Fixture.objects.select_for_update().select_related('season', 'home_team', 'away_team').get(id=fixture_id)
            if fix.status == 'FT':
                # Zaten daha önce işlenmiş, sadece skor farkı varsa düzelt
                if fix.home_score != h_score or fix.away_score != a_score or fix.is_live:
                    fix.home_score = h_score
                    fix.away_score = a_score
                    fix.is_live = False
                    fix.status_display = 'MS'
                    fix.save(update_fields=['home_score', 'away_score', 'is_live', 'status_display'])
                return False

            fix.home_score = h_score
            fix.away_score = a_score
            fix.status = 'FT'
            fix.status_display = 'MS'
            fix.is_live = False
            fix.elapsed_minute = 90
            fix.save()

            season = fix.season
            home_team = fix.home_team
            away_team = fix.away_team

            home_st, _ = LeagueStanding.objects.get_or_create(
                season=season, team=home_team,
                defaults={'rank': 1, 'played': 0, 'won': 0, 'drawn': 0, 'lost': 0, 'goals_for': 0, 'goals_against': 0, 'points': 0}
            )
            away_st, _ = LeagueStanding.objects.get_or_create(
                season=season, team=away_team,
                defaults={'rank': 2, 'played': 0, 'won': 0, 'drawn': 0, 'lost': 0, 'goals_for': 0, 'goals_against': 0, 'points': 0}
            )

            home_st.played += 1
            away_st.played += 1
            home_st.goals_for += h_score
            home_st.goals_against += a_score
            away_st.goals_for += a_score
            away_st.goals_against += h_score

            if h_score > a_score:
                home_st.won += 1
                home_st.points += 3
                away_st.lost += 1
            elif h_score < a_score:
                away_st.won += 1
                away_st.points += 3
                home_st.lost += 1
            else:
                home_st.drawn += 1
                home_st.points += 1
                away_st.drawn += 1
                away_st.points += 1

            home_st.save()
            away_st.save()
            home_played = home_st.played
            away_played = away_st.played

            # Puan tablosu sıralamasını (rank) yeniden hesapla
            all_st = list(LeagueStanding.objects.filter(season=season).order_by('-points', '-goal_difference', '-goals_for', 'team__name'))
            for idx, st_row in enumerate(all_st, start=1):
                if st_row.rank != idx:
                    st_row.rank = idx
                    st_row.save(update_fields=['rank'])

        # Kümülatif ESPN sezon toplamları ile oyuncu istatistiklerini uzlaştır; /roster henüz geciktiyse
        # ESPN maç özeti (/summary) + gol olaylarıyla yalnızca oynayan oyunculara anlık farkı uygula
        home_espn = cls.fetch_espn_club_roster_stats(home_team) if home_team else []
        away_espn = cls.fetch_espn_club_roster_stats(away_team) if away_team else []

        home_max = max((e.get("matches", 0) for e in home_espn), default=0)
        away_max = max((e.get("matches", 0) for e in away_espn), default=0)
        needs_summary = bool(espn_event_id) and (
            (home_team and home_max < home_played) or (away_team and away_max < away_played)
        )
        summary_map = (
            cls.fetch_espn_match_summary_players(espn_event_id, home_team, away_team)
            if needs_summary
            else {}
        )

        home_goal_events = [ev for ev in (goal_events or []) if ev.get("side") == "home"]
        away_goal_events = [ev for ev in (goal_events or []) if ev.get("side") == "away"]

        if home_team:
            cls.sync_team_espn_player_stats(
                season,
                home_team,
                espn_entries=home_espn,
                match_delta_entries=summary_map.get("home"),
                goal_events_for_team=home_goal_events,
                opp_conceded=a_score,
                team_played=home_played,
            )
        if away_team:
            cls.sync_team_espn_player_stats(
                season,
                away_team,
                espn_entries=away_espn,
                match_delta_entries=summary_map.get("away"),
                goal_events_for_team=away_goal_events,
                opp_conceded=h_score,
                team_played=away_played,
            )
        return True

    @classmethod
    def sync_real_espn_live_scoreboard(cls, season=None, force=False):
        """
        ESPN Süper Lig canlı skor servisinden gerçek zamanlı skorları, saniye bazlı dakikaları,
        devre arası (İY) / ikinci yarı / maç sonucu (MS) geçişlerini, golcüleri ve
        önceki günlerden açık kalmış maçları eksiksiz senkronize eder.
        """
        if not season:
            season = Season.get_active_season() or Season.objects.first()
        if not season:
            return False

        now_mono = time.monotonic()
        if not force and (now_mono - cls._last_espn_sync_ts) < 6.0:
            return True

        with cls._sync_lock:
            now_mono = time.monotonic()
            if not force and (now_mono - cls._last_espn_sync_ts) < 6.0:
                return True

            ist = ZoneInfo('Europe/Istanbul')
            now_ist = timezone.now().astimezone(ist)

            # 1. Çekilecek tarihleri dinamik belirle:
            # - Bugün (ve gece yarısı sonrası ise dün)
            # - Geçmiş günlerden FT (MS) olmamış veya hala is_live=True kalmış TÜM maçların tarihleri!
            dates_to_fetch = []
            def _add_date_str(d_val):
                if d_val and d_val not in dates_to_fetch:
                    dates_to_fetch.append(d_val)

            if now_ist.hour < 5:
                _add_date_str((now_ist - timedelta(days=1)).strftime('%Y%m%d'))
            _add_date_str(now_ist.strftime('%Y%m%d'))

            pending_qs = Fixture.objects.filter(season=season).filter(
                Q(is_live=True) |
                (
                    ~Q(status='FT') &
                    Q(match_date__lte=now_ist + timedelta(hours=3)) &
                    Q(match_date__gte=now_ist - timedelta(days=21))
                )
            ).order_by('match_date')

            for p_fix in pending_qs:
                if p_fix.match_date:
                    _add_date_str(p_fix.match_date.astimezone(ist).strftime('%Y%m%d'))

            # Sunucu ilk açıldığında güncel haftanın oynanmış maçlarının golcü detaylarını da önbelleğe ısıt
            warming_now = not cls._initial_events_warmed
            if warming_now:
                recent_ft_qs = Fixture.objects.filter(
                    season=season,
                    match_date__gte=now_ist - timedelta(days=5),
                    match_date__lte=now_ist + timedelta(hours=3)
                ).order_by('match_date')
                for r_fix in recent_ft_qs:
                    if r_fix.match_date:
                        _add_date_str(r_fix.match_date.astimezone(ist).strftime('%Y%m%d'))

            req_headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Cache-Control': 'no-cache, no-store, max-age=0',
                'Pragma': 'no-cache',
            }
            fetched_any = False
            all_dates_ok = True
            cb_bucket = int(time.time() // 6)

            for d_str in dates_to_fetch:
                try:
                    resp = requests.get(
                        cls.ESPN_SCOREBOARD_URL,
                        params={'dates': d_str, '_cb': cb_bucket},
                        headers=req_headers,
                        timeout=4
                    )
                    if resp.status_code != 200:
                        all_dates_ok = False
                        continue
                    payload = resp.json()
                    fetched_any = True
                except Exception as exc:
                    all_dates_ok = False
                    print(f"[LiveScoreSync] ESPN erişim uyarısı ({d_str}): {exc}")
                    continue

                for ev in payload.get('events', []):
                    comps = ev.get('competitions') or []
                    if not comps:
                        continue
                    comp = comps[0]
                    competitors = comp.get('competitors') or []
                    home_comp = next((c for c in competitors if c.get('homeAway') == 'home'), None)
                    away_comp = next((c for c in competitors if c.get('homeAway') == 'away'), None)
                    if not home_comp or not away_comp:
                        continue

                    home_team = cls._match_super_lig_team(home_comp.get('team', {}).get('displayName', ''))
                    away_team = cls._match_super_lig_team(away_comp.get('team', {}).get('displayName', ''))
                    if not home_team or not away_team:
                        continue

                    ev_dt = None
                    raw_dt = comp.get('date') or ev.get('date')
                    if raw_dt:
                        try:
                            ev_dt = datetime.fromisoformat(raw_dt.replace('Z', '+00:00'))
                        except Exception:
                            ev_dt = None

                    qs_match = Fixture.objects.filter(season=season, home_team=home_team, away_team=away_team)
                    fix = None
                    if ev_dt:
                        fix = qs_match.filter(
                            match_date__gte=ev_dt - timedelta(days=5),
                            match_date__lte=ev_dt + timedelta(days=5)
                        ).first()
                    if not fix:
                        fix = qs_match.order_by('round_number').first()
                    if not fix:
                        continue

                    # Gerçek gol olaylarını ayrıştır
                    goal_events = []
                    for det in comp.get('details', []):
                        if det.get('scoringPlay'):
                            clk_disp = cls.normalize_clock_label(det.get('clock', {}).get('displayValue', ''))
                            athletes = det.get('athletesInvolved') or []
                            scorer_name = athletes[0].get('displayName', '') if len(athletes) >= 1 else 'Gol'
                            assist_name = athletes[1].get('displayName', '') if len(athletes) >= 2 else ''
                            det_team_id = str(det.get('team', {}).get('id', ''))
                            side = 'home' if det_team_id == str(home_comp.get('team', {}).get('id', '')) else 'away'
                            is_pen = bool(det.get('penaltyKick'))
                            is_og = bool(det.get('ownGoal'))
                            suffix = ' (P)' if is_pen else (' (KK)' if is_og else '')
                            t_short = home_team.short_name if side == 'home' else away_team.short_name
                            goal_events.append({
                                'minute': clk_disp,
                                'scorer': scorer_name,
                                'assist': assist_name,
                                'side': side,
                                'team_short': t_short or (home_team.name[:3].upper() if side == 'home' else away_team.name[:3].upper()),
                                'team_name': home_team.name if side == 'home' else away_team.name,
                                'is_penalty': is_pen,
                                'is_own_goal': is_og,
                                'text': f"{clk_disp} {scorer_name}{suffix}" + (f" (Asist: {assist_name})" if assist_name and not is_og else "")
                            })
                    if fix.id in cls._LIVE_EVENTS_CACHE:
                        prev_events = cls._LIVE_EVENTS_CACHE[fix.id]
                        if len(goal_events) > len(prev_events):
                            for new_ev in goal_events[len(prev_events):]:
                                try:
                                    from ..notifications import dispatch_match_goal_notification
                                    dispatch_match_goal_notification(fix, new_ev)
                                except Exception as n_err:
                                    logger.error(f"[LiveNotification] Hata: {n_err}")
                    cls._LIVE_EVENTS_CACHE[fix.id] = goal_events

                    st_info = comp.get('status') or {}
                    st_type = st_info.get('type') or {}
                    state = st_type.get('state', 'pre')  # 'pre', 'in', 'post'
                    st_name = (st_type.get('name') or '').upper()
                    short_detail = (st_type.get('shortDetail') or '').strip()
                    display_clock = cls.normalize_clock_label(st_info.get('displayClock') or '')
                    try:
                        period = int(st_info.get('period') or 0)
                    except (ValueError, TypeError):
                        period = 0
                    try:
                        raw_clock_sec = float(st_info.get('clock') or 0.0)
                    except (ValueError, TypeError):
                        raw_clock_sec = 0.0

                    try:
                        h_score = int(home_comp.get('score', 0) or 0)
                        a_score = int(away_comp.get('score', 0) or 0)
                    except (ValueError, TypeError):
                        h_score, a_score = 0, 0

                    if state == 'in':
                        # Maçkolik standardında canlı devre ve dakika hesaplaması
                        if st_name == 'STATUS_HALFTIME' or short_detail.upper() in ('HT', 'HALFTIME', 'İY'):
                            new_status = 'HT'
                            new_disp = 'İY'
                            elap = 45
                            cls._LIVE_CLOCK_CACHE[fix.id] = {
                                'phase': 'HT',
                                'period': 1,
                                'clock_seconds': 2700,
                                'display_clock': 'İY',
                                'synced_at_ms': int(time.time() * 1000),
                            }
                        elif period == 1 or 'FIRST' in st_name:
                            new_status = '1H'
                            clock_sec = max(0, int(raw_clock_sec))
                            m_match = re.match(r'^(\d+)', display_clock)
                            if clock_sec < 60 and m_match and int(m_match.group(1)) > 1:
                                clock_sec = (int(m_match.group(1)) - 1) * 60

                            is_stoppage = ('+' in display_clock) or (clock_sec >= 2700)
                            if is_stoppage:
                                elap = 45
                                if '+' in display_clock:
                                    new_disp = display_clock
                                else:
                                    extra_m = max(1, ((clock_sec - 2700) // 60) + 1)
                                    new_disp = f"45+{extra_m}'"
                                phase = '1H_STOPPAGE'
                            else:
                                calc_min = max(1, min(45, (clock_sec // 60) + 1))
                                elap = calc_min
                                new_disp = f"{calc_min}'"
                                phase = '1H'

                            cls._LIVE_CLOCK_CACHE[fix.id] = {
                                'phase': phase,
                                'period': 1,
                                'clock_seconds': clock_sec,
                                'display_clock': new_disp,
                                'synced_at_ms': int(time.time() * 1000),
                            }
                        else:
                            # 2. Yarı (2H) veya uzatma devresi
                            new_status = '2H' if (period in (0, 2) or 'SECOND' in st_name) else 'LIVE'
                            clock_sec = max(0, int(raw_clock_sec))
                            if new_status == '2H' and clock_sec < 2700:
                                clock_sec += 2700
                            m_match = re.match(r'^(\d+)', display_clock)
                            if clock_sec <= 2760 and m_match and int(m_match.group(1)) > 46:
                                clock_sec = (int(m_match.group(1)) - 1) * 60

                            is_stoppage = ('+' in display_clock) or (clock_sec >= 5400)
                            if is_stoppage:
                                elap = 90
                                if '+' in display_clock:
                                    new_disp = display_clock
                                else:
                                    extra_m = max(1, ((clock_sec - 5400) // 60) + 1)
                                    new_disp = f"90+{extra_m}'"
                                phase = '2H_STOPPAGE'
                            else:
                                calc_min = max(46, min(90, (clock_sec // 60) + 1))
                                elap = calc_min
                                new_disp = f"{calc_min}'"
                                phase = '2H'

                            cls._LIVE_CLOCK_CACHE[fix.id] = {
                                'phase': phase,
                                'period': max(2, period),
                                'clock_seconds': clock_sec,
                                'display_clock': new_disp,
                                'synced_at_ms': int(time.time() * 1000),
                            }

                        if (
                            fix.home_score != h_score or
                            fix.away_score != a_score or
                            fix.status != new_status or
                            fix.status_display != new_disp or
                            not fix.is_live or
                            fix.elapsed_minute != elap
                        ):
                            fix.home_score = h_score
                            fix.away_score = a_score
                            fix.status = new_status
                            fix.status_display = new_disp
                            fix.is_live = True
                            fix.elapsed_minute = elap
                            fix.save(update_fields=['home_score', 'away_score', 'status', 'status_display', 'is_live', 'elapsed_minute'])

                    elif state == 'post':
                        cls._LIVE_CLOCK_CACHE.pop(fix.id, None)
                        cls._finalize_finished_fixture_atomically(
                            fix.id, h_score, a_score, goal_events, espn_event_id=ev.get('id')
                        )

                    elif state == 'pre' and fix.status != 'FT':
                        cls._LIVE_CLOCK_CACHE.pop(fix.id, None)
                        target_dt = ev_dt or fix.match_date
                        dyn_disp = cls.format_dynamic_ns_label(target_dt, now_ist)
                        update_cols = []
                        if ev_dt and fix.match_date and abs((fix.match_date - ev_dt).total_seconds()) > 60:
                            fix.match_date = ev_dt
                            update_cols.append('match_date')
                        if fix.is_live or fix.home_score is not None or fix.status != 'NS':
                            fix.is_live = False
                            fix.status = 'NS'
                            fix.home_score = None
                            fix.away_score = None
                            fix.elapsed_minute = None
                            update_cols.extend(['is_live', 'status', 'home_score', 'away_score', 'elapsed_minute'])
                        if fix.status_display != dyn_disp:
                            fix.status_display = dyn_disp
                            update_cols.append('status_display')
                        if update_cols:
                            fix.save(update_fields=list(set(update_cols)))

            if warming_now and fetched_any and all_dates_ok:
                cls._initial_events_warmed = True
            if fetched_any:
                cls._last_espn_sync_ts = time.monotonic()
            return fetched_any

    @classmethod
    def get_headers(cls):
        """
        RapidAPI anahtarını ortam değişkenlerinden alır.
        """
        api_key = os.getenv('RAPIDAPI_KEY', '').strip()
        if not api_key:
            return None

        return {
            'x-rapidapi-host': 'api-football-v1.p.rapidapi.com',
            'x-rapidapi-key': api_key
        }

    @classmethod
    def fetch_and_sync_fixtures(cls, season=None, round_num=None):
        """
        API-Football'dan Süper Lig maç fikstürünü çeker ve Fixture tablosuna kaydeder.
        Eğer API anahtarı girilmemişse veya kota dolmuşsa güvenli gerçek veri yedeklemesini kullanır.
        """
        if not season:
            season = Season.get_active_season() or Season.objects.first()

        headers = cls.get_headers()
        year = season.start_year if season else 2024

        # Eğer API anahtarı varsa canlı istek yap
        if headers:
            try:
                url = f"{cls.RAPIDAPI_URL}/fixtures"
                params = {'league': cls.SUPER_LIG_LEAGUE_ID, 'season': year}
                if round_num:
                    params['round'] = f"Regular Season - {round_num}"

                resp = requests.get(url, headers=headers, params=params, timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    response_fixtures = data.get('response', [])
                    if response_fixtures:
                        return cls._save_api_fixtures(response_fixtures, season)
                print(f"[APIFootballService] RapidAPI Yanıtı: {resp.status_code} - {resp.text[:120]}")
            except Exception as e:
                print(f"[APIFootballService] RapidAPI bağlantı hatası: {e}")

        # Yedekleme: API key yoksa veya kota bittiyse gerçek Süper Lig fikstürünü sağla
        return cls._get_fallback_fixtures(season)

    @classmethod
    def fetch_and_sync_live_scores(cls):
        """
        Şu an canlı oynanmakta olan Süper Lig maçlarını API-Football'dan günceller.
        """
        headers = cls.get_headers()
        active_season = Season.get_active_season() or Season.objects.first()

        if headers:
            try:
                url = f"{cls.RAPIDAPI_URL}/fixtures"
                params = {'live': 'all', 'league': cls.SUPER_LIG_LEAGUE_ID}
                resp = requests.get(url, headers=headers, params=params, timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    live_list = data.get('response', [])
                    if live_list:
                        return cls._save_api_fixtures(live_list, active_season)
            except Exception as e:
                print(f"[APIFootballService] Canlı skor hatası: {e}")

        # Gerçek zamanlı ESPN Süper Lig canlı skor servisini çalıştır
        if cls.sync_real_espn_live_scoreboard(active_season):
            return list(Fixture.objects.filter(season=active_season, is_live=True))

        # İnternet erişimi yoksa saat bazlı yedeklemeyi döndür
        return cls._get_fallback_live_match(active_season)

    @classmethod
    def fetch_and_sync_standings(cls, season=None):
        """
        API-Football'dan Süper Lig güncel puan durumunu çeker ve LeagueStanding tablosunu günceller.
        """
        if not season:
            season = Season.get_active_season() or Season.objects.first()

        headers = cls.get_headers()
        year = season.start_year if season else 2024

        if headers:
            try:
                url = f"{cls.RAPIDAPI_URL}/standings"
                params = {'league': cls.SUPER_LIG_LEAGUE_ID, 'season': year}
                resp = requests.get(url, headers=headers, params=params, timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    league_data = data.get('response', [{}])[0].get('league', {})
                    standings_groups = league_data.get('standings', [])
                    if standings_groups:
                        table = standings_groups[0]
                        synced = []
                        for item in table:
                            t_name = item.get('team', {}).get('name', '')
                            team = Team.objects.filter(name__icontains=t_name.split()[0]).first()
                            if not team:
                                continue

                            rank = item.get('rank', 1)
                            points = item.get('points', 0)
                            all_stats = item.get('all', {})
                            played = all_stats.get('played', 0)
                            won = all_stats.get('win', 0)
                            drawn = all_stats.get('draw', 0)
                            lost = all_stats.get('lose', 0)
                            gf = all_stats.get('goals', {}).get('for', 0)
                            ga = all_stats.get('goals', {}).get('against', 0)

                            st_obj, _ = LeagueStanding.objects.update_or_create(
                                season=season,
                                team=team,
                                defaults={
                                    'rank': rank,
                                    'played': played,
                                    'won': won,
                                    'drawn': drawn,
                                    'lost': lost,
                                    'goals_for': gf,
                                    'goals_against': ga,
                                    'goal_difference': gf - ga,
                                    'points': points
                                }
                            )
                            synced.append(st_obj)
                        return synced
            except Exception as e:
                print(f"[APIFootballService] Puan durumu senkronizasyon hatası: {e}")

        return list(LeagueStanding.objects.filter(season=season))

    @classmethod
    def _save_api_fixtures(cls, fixtures_list, season):
        """
        API-Football JSON yanıtını Fixture modeline kaydeder.
        """
        saved = []
        for item in fixtures_list:
            fixture_info = item.get('fixture', {})
            league_info = item.get('league', {})
            teams_info = item.get('teams', {})
            goals_info = item.get('goals', {})

            api_id = fixture_info.get('id')
            raw_date = fixture_info.get('date')
            venue_name = fixture_info.get('venue', {}).get('name', '')
            referee = fixture_info.get('referee', '')
            status_short = fixture_info.get('status', {}).get('short', 'NS')
            elapsed = fixture_info.get('status', {}).get('elapsed')

            # Hafta
            round_raw = league_info.get('round', '1. Hafta')
            round_num = 1
            num_match = re.search(r'(\d+)', round_raw)
            if num_match:
                round_num = int(num_match.group(1))
            round_display = f"{round_num}. Hafta"

            # Takımlar
            home_raw = teams_info.get('home', {}).get('name', '')
            away_raw = teams_info.get('away', {}).get('name', '')

            home_team = Team.objects.filter(name__icontains=home_raw.split()[0]).first()
            if not home_team:
                home_team = Team.objects.create(name=home_raw, is_super_lig=True)

            away_team = Team.objects.filter(name__icontains=away_raw.split()[0]).first()
            if not away_team:
                away_team = Team.objects.create(name=away_raw, is_super_lig=True)

            home_score = goals_info.get('home')
            away_score = goals_info.get('away')

            # Durum formatlama
            is_live = status_short in ['1H', 'HT', '2H', 'ET', 'P', 'LIVE']
            if status_short == 'FT':
                status_disp = "MS"
            elif is_live:
                status_disp = f"Canlı ({elapsed}')" if elapsed else "Canlı"
            elif status_short == 'HT':
                status_disp = "Devre Arası"
            elif status_short == 'PST':
                status_disp = "Ertelendi"
            else:
                try:
                    dt = datetime.fromisoformat(raw_date.replace('Z', '+00:00'))
                    status_disp = dt.strftime('%H:%M')
                except Exception:
                    status_disp = "Başlamadı"

            dt_val = timezone.now()
            if raw_date:
                try:
                    dt_val = datetime.fromisoformat(raw_date.replace('Z', '+00:00'))
                except Exception:
                    pass

            fix_obj, _ = Fixture.objects.update_or_create(
                api_id=api_id,
                defaults={
                    'season': season,
                    'round_name': round_display,
                    'round_number': round_num,
                    'home_team': home_team,
                    'away_team': away_team,
                    'home_score': home_score,
                    'away_score': away_score,
                    'match_date': dt_val,
                    'status': status_short,
                    'status_display': status_disp,
                    'venue': venue_name or (home_team.stadium or "Süper Lig Stadyumu"),
                    'referee': referee or "Süper Lig Hakemi",
                    'is_live': is_live,
                    'elapsed_minute': elapsed
                }
            )
            saved.append(fix_obj)
        return saved

    @classmethod
    def _get_fallback_fixtures(cls, season):
        """
        API key olmadan veya kota aşıldığında mevcut sezon fikstürünü korur;
        yalnızca veritabanında hiç maç yoksa örnek fikstür oluşturur.
        """
        existing_qs = Fixture.objects.filter(season=season).order_by('match_date')
        if existing_qs.exists():
            cls._refresh_clock_based_live_states(existing_qs)
            return list(existing_qs)

        # Takımları al (yalnızca DB tamamen boşsa çalışır)
        def get_t(name):
            t = Team.objects.exclude(name__icontains='Birleşik').filter(name__icontains=name).first()
            if not t:
                t = Team.objects.create(name=name, is_super_lig=True, league_name='Trendyol Süper Lig')
            return t

        now = timezone.now()
        fixtures_data = [
            # 8. Hafta (Oynanmış Maçlar)
            (8, "8. Hafta", "Galatasaray", "Beşiktaş", 2, 1, "FT", "MS", now - timedelta(days=2), "RAMS Park", "Arda Kardeşler", False, None),
            (8, "8. Hafta", "Amed SK", "Arca Çorum FK", 3, 1, "FT", "MS", now - timedelta(days=2), "Diyarbakır Stadyumu", "Mehmet Türkmen", False, None),
            (8, "8. Hafta", "Fenerbahçe", "Kocaelispor", 2, 0, "FT", "MS", now - timedelta(days=2), "Şükrü Saracoğlu", "Cihan Aydın", False, None),
            (8, "8. Hafta", "Göztepe", "Trabzonspor", 1, 2, "FT", "MS", now - timedelta(days=3), "Gürsel Aksel Stadyumu", "Ali Şansalan", False, None),
            (8, "8. Hafta", "Kasımpaşa", "Samsunspor", 2, 1, "FT", "MS", now - timedelta(days=3), "Recep Tayyip Erdoğan Stadyumu", "Çağdaş Altay", False, None),
            (8, "8. Hafta", "Başakşehir", "Eyüpspor", 1, 1, "1H", "Canlı (42')", now, "Fatih Terim Stadyumu", "Abdulkadir Bitigen", True, 42),
            (8, "8. Hafta", "Corendon Alanyaspor", "Erzurumspor FK", 1, 0, "FT", "MS", now - timedelta(days=3), "Gain Park Stadyumu", "Yasin Kol", False, None),
            (8, "8. Hafta", "Gaziantep FK", "Tümosan Konyaspor", 2, 1, "FT", "MS", now - timedelta(days=3), "Kalyon Stadyumu", "Atilla Karaoğlan", False, None),
            (8, "8. Hafta", "Çaykur Rizespor", "Gençlerbirliği", 1, 1, "FT", "MS", now - timedelta(days=4), "Çaykur Didi Stadyumu", "Direnc Tonusluoğlu", False, None),

            # 9. Hafta (Gelecek Hafta)
            (9, "9. Hafta", "Amed SK", "Galatasaray", None, None, "NS", "Paz 19:00", now + timedelta(days=5), "Diyarbakır Stadyumu", "Halil Umut Meler", False, None),
            (9, "9. Hafta", "Trabzonspor", "Fenerbahçe", None, None, "NS", "Paz 19:00", now + timedelta(days=5), "Papara Park", "Oğuzhan Çakır", False, None),
            (9, "9. Hafta", "Beşiktaş", "Kasımpaşa", None, None, "NS", "Cmt 19:00", now + timedelta(days=4), "Tüpraş Stadyumu", "Zorbay Küçük", False, None),
            (9, "9. Hafta", "Samsunspor", "Başakşehir", None, None, "NS", "Pzt 20:00", now + timedelta(days=6), "19 Mayıs Stadyumu", "Direnc Tonusluoğlu", False, None),
            (9, "9. Hafta", "Eyüpspor", "Arca Çorum FK", None, None, "NS", "Paz 16:00", now + timedelta(days=5), "Recep Tayyip Erdoğan Stadyumu", "Kadir Sağlam", False, None),
            (9, "9. Hafta", "Tümosan Konyaspor", "Kocaelispor", None, None, "NS", "Paz 13:30", now + timedelta(days=5), "Medaş Konya Büyükşehir Stadyumu", "Emre Kargın", False, None),
        ]

        saved = []
        for r_num, r_name, h_name, a_name, h_sc, a_sc, stat, stat_disp, m_date, ven, ref, is_l, elap in fixtures_data:
            h_team = get_t(h_name)
            a_team = get_t(a_name)
            fix, _ = Fixture.objects.update_or_create(
                season=season,
                round_number=r_num,
                home_team=h_team,
                away_team=a_team,
                defaults={
                    'round_name': r_name,
                    'home_score': h_sc,
                    'away_score': a_sc,
                    'status': stat,
                    'status_display': stat_disp,
                    'match_date': m_date,
                    'venue': ven or (h_team.stadium or "Süper Lig Stadyumu"),
                    'referee': ref,
                    'is_live': is_l,
                    'elapsed_minute': elap
                }
            )
            saved.append(fix)
        return saved

    @classmethod
    def _refresh_clock_based_live_states(cls, qs):
        """
        Çevrimdışı (offline) yedekleme: Gerçek başlama saatine (match_date) göre
        dakika ve canlı durumunu (NS -> 1H -> İY -> 2H) Maçkolik formatında günceller.
        """
        now = timezone.now()
        for fix in qs.exclude(status='FT'):
            if not fix.match_date:
                continue
            diff_sec = int((now - fix.match_date).total_seconds())
            diff_min = diff_sec // 60
            if 0 <= diff_min <= 115:
                if diff_min < 45:
                    calc_status = '1H'
                    calc_min = max(1, diff_min + 1)
                    calc_disp = f"{calc_min}'"
                    cls._LIVE_CLOCK_CACHE[fix.id] = {
                        'phase': '1H',
                        'period': 1,
                        'clock_seconds': max(0, min(2699, diff_sec)),
                        'display_clock': calc_disp,
                        'synced_at_ms': int(time.time() * 1000),
                    }
                elif diff_min < 60:
                    calc_status = 'HT'
                    calc_min = 45
                    calc_disp = 'İY'
                    cls._LIVE_CLOCK_CACHE[fix.id] = {
                        'phase': 'HT',
                        'period': 1,
                        'clock_seconds': 2700,
                        'display_clock': 'İY',
                        'synced_at_ms': int(time.time() * 1000),
                    }
                else:
                    calc_status = '2H'
                    sec_in_2h = max(0, diff_sec - 3600)
                    calc_min = min(90, 46 + (sec_in_2h // 60))
                    calc_disp = f"{calc_min}'" if sec_in_2h < 2700 else f"90+{max(1, ((sec_in_2h - 2700) // 60) + 1)}'"
                    cls._LIVE_CLOCK_CACHE[fix.id] = {
                        'phase': '2H' if sec_in_2h < 2700 else '2H_STOPPAGE',
                        'period': 2,
                        'clock_seconds': 2700 + sec_in_2h,
                        'display_clock': calc_disp,
                        'synced_at_ms': int(time.time() * 1000),
                    }

                updated_fields = []
                if not fix.is_live:
                    fix.is_live = True
                    updated_fields.append('is_live')
                if fix.home_score is None:
                    fix.home_score = 0
                    updated_fields.append('home_score')
                if fix.away_score is None:
                    fix.away_score = 0
                    updated_fields.append('away_score')
                if fix.elapsed_minute != calc_min or fix.status != calc_status or fix.status_display != calc_disp:
                    fix.elapsed_minute = calc_min
                    fix.status = calc_status
                    fix.status_display = calc_disp
                    updated_fields.extend(['elapsed_minute', 'status', 'status_display'])
                if updated_fields:
                    fix.save(update_fields=list(set(updated_fields)))
            elif diff_min > 115 and (fix.is_live or fix.status in ('1H', '2H', 'HT')):
                # Süresi dolan maçın canlıda takılı kalmasını engelle, MS (Maç Bitti) olarak tamamla
                cls._LIVE_CLOCK_CACHE.pop(fix.id, None)
                fix.is_live = False
                fix.status = 'FT'
                fix.status_display = 'MS'
                fix.elapsed_minute = 90
                fix.save(update_fields=['is_live', 'status', 'status_display', 'elapsed_minute'])

    @classmethod
    def _get_fallback_live_match(cls, season):
        """
        Canlı maçları gerçek saat kontrolüyle filtreler ve döner.
        """
        season_qs = Fixture.objects.filter(season=season)
        if season_qs.exists():
            cls._refresh_clock_based_live_states(season_qs)
            return list(season_qs.filter(is_live=True))

        cls._get_fallback_fixtures(season)
        return list(Fixture.objects.filter(season=season, is_live=True))
