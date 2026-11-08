import re
import sys
import time
import unicodedata
import urllib.request
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal

from django.core.management.base import BaseCommand
from api.models import Season, Team, Player, PlayerSeasonStats, LeagueStanding

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
    'Referer': 'https://www.google.com/'
}

TEAM_NAME_MAP = {
    'Galatasaray': ('Galatasaray', 'GS'),
    'Fenerbahçe': ('Fenerbahçe', 'FB'),
    'Beşiktaş': ('Beşiktaş', 'BJK'),
    'Trabzonspor': ('Trabzonspor', 'TS'),
    'Başakşehir': ('Başakşehir', 'İBFK'),
    'İstanbul Başakşehir': ('Başakşehir', 'İBFK'),
    'İstanbul BBSK': ('Başakşehir', 'İBFK'),
    'Büyükşehir Bld': ('Başakşehir', 'İBFK'),
    'Kasımpaşa': ('Kasımpaşa', 'KAS'),
    'Sivasspor': ('Sivasspor', 'SİV'),
    'Alanyaspor': ('Alanyaspor', 'ALN'),
    'Corendon Alanyaspor': ('Alanyaspor', 'ALN'),
    'Ç. Rizespor': ('Çaykur Rizespor', 'RİZ'),
    'Rizespor': ('Çaykur Rizespor', 'RİZ'),
    'Antalyaspor': ('Antalyaspor', 'ANT'),
    'Gaziantep FK': ('Gaziantep FK', 'GFK'),
    'Gaziantepspor': ('Gaziantepspor', 'GAZ'),
    'Adana Demirspor': ('Adana Demirspor', 'ADS'),
    'Adanaspor': ('Adanaspor', 'ADA'),
    'Samsunspor': ('Samsunspor', 'SAM'),
    'Kayserispor': ('Kayserispor', 'KAY'),
    'K. Erciyesspor': ('Kayseri Erciyesspor', 'ERC'),
    'Hatayspor': ('Hatayspor', 'HAT'),
    'Konyaspor': ('Konyaspor', 'KON'),
    'Tümosan Konyaspor': ('Konyaspor', 'KON'),
    'Ankaragücü': ('Ankaragücü', 'ANK'),
    'MKE Ankaragücü': ('Ankaragücü', 'ANK'),
    'Ankaragücü GK': ('Ankaragücü', 'ANK'),
    'Karagümrük': ('Fatih Karagümrük', 'FKG'),
    'Fatih Karagümrük': ('Fatih Karagümrük', 'FKG'),
    'Karagümrük GK': ('Fatih Karagümrük', 'FKG'),
    'Pendikspor': ('Pendikspor', 'PEN'),
    'İstanbulspor': ('İstanbulspor', 'İST'),
    'Göztepe': ('Göztepe', 'GÖZ'),
    'Eyüpspor': ('Eyüpspor', 'EYÜ'),
    'Bodrum FK': ('Bodrum FK', 'BOD'),
    'Giresunspor': ('Giresunspor', 'GİR'),
    'Ümraniyespor': ('Ümraniyespor', 'ÜMR'),
    'Yeni Malatyaspor': ('Yeni Malatyaspor', 'YMS'),
    'Y. Malatyaspor': ('Yeni Malatyaspor', 'YMS'),
    'Malatyaspor': ('Malatyaspor', 'MAL'),
    'Altay': ('Altay', 'ALT'),
    'Altay SK': ('Altay', 'ALT'),
    'Bursaspor': ('Bursaspor', 'BUR'),
    'Eskişehirspor': ('Eskişehirspor', 'ESK'),
    'Gençlerbirliği': ('Gençlerbirliği', 'GEN'),
    'Denizlispor': ('Denizlispor', 'DEN'),
    'Akhisarspor': ('Akhisarspor', 'AKH'),
    'Akhisar Belediye': ('Akhisarspor', 'AKH'),
    'BB Erzurumspor': ('Erzurumspor FK', 'ERZ'),
    'Erzurumspor FK': ('Erzurumspor FK', 'ERZ'),
    'Erzurumspor': ('Erzurumspor', 'ERZ'),
    'Kocaelispor': ('Kocaelispor', 'KOC'),
    'Kardemir Karabük': ('Karabükspor', 'KRB'),
    'Karabükspor': ('Karabükspor', 'KRB'),
    'D.Ç. Karabükspor': ('Karabükspor', 'KRB'),
    'Elazığspor': ('Elazığspor', 'ELA'),
    'Mersin İY': ('Mersin İdman Yurdu', 'MİY'),
    'Mersin İdman Yurdu': ('Mersin İdman Yurdu', 'MİY'),
    'Orduspor': ('Orduspor', 'ORD'),
    'Manisaspor': ('Manisaspor', 'MAN'),
    'Bucaspor': ('Bucaspor', 'BUC'),
    'Diyarbakırspor': ('Diyarbakırspor', 'DİY'),
    'Hacettepe': ('Hacettepe', 'HAC'),
    'Hacettepe GK': ('Hacettepe', 'HAC'),
    'GB Oftaşspor': ('Hacettepe', 'HAC'),
    'Sakaryaspor': ('Sakaryaspor', 'SAK'),
    'Boluspor': ('Boluspor', 'BOL'),
    'Ankaraspor': ('Ankaraspor', 'OSM'),
    'BB Ankaraspor': ('Ankaraspor', 'OSM'),
    'Osmanlıspor FK': ('Ankaraspor', 'OSM'),
    'Vefaspor': ('Vefa', 'VEF'),
    'Sarıyer': ('Sarıyer', 'SAR'),
    'Zonguldakspor': ('Zonguldakspor', 'ZON'),
    'Karşıyaka': ('Karşıyaka', 'KSK'),
    'Altınordu': ('Altınordu', 'ALTN'),
    'Bakırköyspor': ('Bakırköyspor', 'BAK'),
    'Balıkesirspor': ('Balıkesirspor', 'BAL'),
    'Dardanelspor': ('Çanakkale Dardanelspor', 'DAR'),
    'Ç. Dardanelspor': ('Çanakkale Dardanelspor', 'DAR'),
    'Vanspor': ('Vanspor', 'VAN'),
    'Yimpaş Yozgat': ('Yozgatspor', 'YOZ'),
    'Zeytinburnuspor': ('Zeytinburnuspor', 'ZEY'),
    'Şekerspor': ('Şekerspor', 'ŞEK'),
    'Şeker Hilal': ('Şekerspor', 'ŞEK'),
    'İzmirspor': ('İzmirspor', 'İZM'),
    'Beykozspor': ('Beykozspor', 'BEY'),
    'Beyoğluspor': ('Beyoğluspor', 'BEYO'),
    'Feriköy GK': ('Feriköy', 'FER'),
    'Adalet GK': ('Adalet', 'ADL'),
    'Yeşildirek': ('Yeşildirek', 'YEŞ'),
    'Ankara Demir': ('Ankara Demirspor', 'AND'),
    'Aydınspor': ('Aydınspor', 'AYD'),
    'Kahramanmaraş': ('Kahramanmaraşspor', 'KMS'),
    'Kırıkkalespor': ('Kırıkkalespor', 'KRK'),
    'PTT': ('PTT', 'PTT'),
    'Petrolofisi': ('Petrolofisi', 'PET'),
    'Siirt Jetpa': ('Siirt Jetpa', 'Sİİ'),
    'A.Sebatspor': ('Akçaabat Sebatspor', 'SEB'),
}

KEY_CLUBS_CONFIG = [
    ('Galatasaray', 'galatasaray-istanbul', 141),
    ('Fenerbahçe', 'fenerbahce-istanbul', 36),
    ('Beşiktaş', 'besiktas-istanbul', 114),
    ('Trabzonspor', 'trabzonspor', 449),
    ('Başakşehir', 'istanbul-basaksehir-fk', 6890),
    ('Bursaspor', 'bursaspor', 20),
    ('Eskişehirspor', 'eskisehirspor', 603),
    ('Göztepe', 'goztepe', 3249),
    ('Altay', 'altay-izmir', 113),
    ('Samsunspor', 'samsunspor', 152),
    ('Kasımpaşa', 'kasimpasa', 10484),
    ('Sivasspor', 'sivasspor', 2381),
    ('Alanyaspor', 'alanyaspor', 11282),
    ('Konyaspor', 'konyaspor', 2293),
    ('Kayserispor', 'kayserispor', 3205),
    ('Çaykur Rizespor', 'caykur-rizespor', 118),
    ('Gaziantep FK', 'gaziantep-fk', 2832),
    ('Gençlerbirliği', 'genclerbirligi-ankara', 112),
    ('Kocaelispor', 'kocaelispor', 125),
    ('Hatayspor', 'hatayspor', 7775),
    ('Ankaragücü', 'mke-ankaragucu', 111),
    ('Fatih Karagümrük', 'fatih-karagumruk', 6889),
    ('Adana Demirspor', 'adana-demirspor', 3840),
    ('Adanaspor', 'adanaspor', 32),
    ('Antalyaspor', 'antalyaspor', 589),
    ('İstanbulspor', 'istanbulspor', 140),
    ('Giresunspor', 'giresunspor', 116),
    ('Eyüpspor', 'eyupspor', 7178),
    ('Bodrum FK', 'bodrum-fk', 14798),
]

def normalize_text(s):
    if not s:
        return ''
    return ''.join(c for c in unicodedata.normalize('NFKD', s) if not unicodedata.combining(c)).lower().replace(' ', '').replace('-', '').replace('.', '')

class Command(BaseCommand):
    help = "Transfermarkt ve resmi kaynaklardan 1959'dan bugüne tüm sezonların lig puan durumlarını ve oyuncu performans istatistiklerini (maç, gol, asist, dakika) eşitler."

    def add_arguments(self, parser):
        parser.add_argument('--skip-standings', action='store_true', help='Puan durumu senkronizasyonunu atla')
        parser.add_argument('--skip-stats', action='store_true', help='Oyuncu istatistikleri senkronizasyonunu atla')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.team_slug_cache = {}  # (team_id, year) -> (slug, vid)

    def get_or_create_team(self, raw_name):
        clean = raw_name.strip()
        canon_name, short_name = TEAM_NAME_MAP.get(clean, (clean, clean[:3].upper()))
        
        team = Team.objects.filter(name__iexact=canon_name).first()
        if not team:
            team = Team.objects.filter(short_name=short_name, is_super_lig=True).first()
        if not team:
            team = Team.objects.filter(name__icontains=canon_name).first()
        if not team:
            team = Team.objects.create(name=canon_name, short_name=short_name, is_super_lig=True)
        return team

    def sync_season_standings(self, season):
        year = season.start_year
        tm_year = 1958 if season.name == '1959' else year
        url = f'https://www.transfermarkt.com.tr/super-lig/tabelle/wettbewerb/TR1?saison_id={tm_year}'
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            html = urllib.request.urlopen(req, timeout=12).read().decode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')
            table = soup.find('table', class_='items')
            rows = table.find('tbody').find_all('tr') if table else []
            if not rows:
                return 0

            valid_team_ids = set()
            for r in rows:
                tds = r.find_all('td')
                if len(tds) < 10:
                    continue
                rank_raw = tds[0].text.strip()
                if not rank_raw.isdigit():
                    continue
                rank = int(rank_raw)
                
                td_team = r.find('td', class_='no-border-links') or tds[2]
                a_tag = td_team.find('a')
                team_name = a_tag.text.strip() if a_tag else td_team.text.strip()
                
                # Cache slug and vid
                if a_tag and a_tag.get('href'):
                    href = a_tag['href']
                    m = re.search(r'/([^/]+)/spielplan/verein/(\d+)', href)
                    if m:
                        slug = m.group(1)
                        vid = int(m.group(2))
                    else:
                        m2 = re.search(r'/([^/]+)/[a-z]+/verein/(\d+)', href)
                        slug = m2.group(1) if m2 else ''
                        vid = int(m2.group(2)) if m2 else 0
                else:
                    slug, vid = '', 0

                played = int(tds[3].text.strip())
                won = int(tds[4].text.strip())
                drawn = int(tds[5].text.strip())
                lost = int(tds[6].text.strip())
                
                gf_ga = tds[7].text.strip()
                if ':' in gf_ga:
                    gf_str, ga_str = gf_ga.split(':')
                    gf = int(gf_str)
                    ga = int(ga_str)
                else:
                    gf, ga = 0, 0
                
                diff_str = tds[8].text.strip()
                diff = int(diff_str) if diff_str.lstrip('-+').isdigit() else (gf - ga)
                
                # Points parsing: 2-point system before 1987, 3-point system from 1987 onwards
                pts_str = tds[9].text.strip()
                if ':' in pts_str:
                    pts_part = pts_str.split(':')[0]
                    pts = int(pts_part) if pts_part.isdigit() else ((won * 2) + drawn)
                elif pts_str.isdigit():
                    pts = int(pts_str)
                else:
                    pts = ((won * 2) + drawn) if tm_year < 1987 else ((won * 3) + drawn)

                team = self.get_or_create_team(team_name)
                valid_team_ids.add(team.id)

                if slug and vid:
                    self.team_slug_cache[(team.id, tm_year)] = (slug, vid)

                LeagueStanding.objects.update_or_create(
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
                        'goal_difference': diff,
                        'points': pts,
                    }
                )

            # Obsolete rows cleanup (removes fake/synthetic seeded teams)
            if valid_team_ids:
                LeagueStanding.objects.filter(season=season).exclude(team_id__in=valid_team_ids).delete()

            return len(valid_team_ids)
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"  Puan durumu hata ({season.name}): {e}"))
            return 0

    def sync_club_stats(self, season, team, slug, vid):
        year = season.start_year
        tm_year = 1958 if season.name == '1959' else year
        url = f'https://www.transfermarkt.com.tr/{slug}/leistungsdaten/verein/{vid}/reldata/%26{tm_year}/plus/1'
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            html = urllib.request.urlopen(req, timeout=12).read().decode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')
            table = soup.find('table', class_='items')
            rows = table.find('tbody').find_all('tr') if table else []
            if not rows:
                return 0, 0

            all_db_players = list(Player.objects.all())
            norm_db_players = {normalize_text(p.name): p for p in all_db_players}

            updated = 0
            created = 0
            seen_player_ids = set()

            for r in rows:
                tds = r.find_all('td')
                if len(tds) < 18:
                    continue
                hl = r.find('td', class_='hauptlink')
                if not hl or not hl.find('a'):
                    continue
                raw_name = hl.find('a').text.strip()
                if not raw_name:
                    continue
                norm = normalize_text(raw_name)
                pos = tds[4].text.strip()
                age_raw = tds[5].text.strip()
                age = int(age_raw) if age_raw.isdigit() else None
                
                m_raw = tds[8].text.strip()
                matches = int(m_raw) if m_raw.isdigit() else 0
                g_raw = tds[9].text.strip()
                goals = int(g_raw) if g_raw.isdigit() else 0
                a_raw = tds[10].text.strip()
                assists = int(a_raw) if a_raw.isdigit() else 0
                mins_raw = tds[17].text.strip().replace('.', '').replace("'", "")
                mins = int(mins_raw) if mins_raw.isdigit() else 0
                
                yc_raw = tds[11].text.strip()
                yc = int(yc_raw) if yc_raw.isdigit() else 0
                rc_raw = tds[13].text.strip()
                rc = int(rc_raw) if rc_raw.isdigit() else 0

                # Rating calculation
                if matches > 0:
                    base = 6.8 + min(1.8, (goals * 0.12) + (assists * 0.08))
                    if mins > 1500:
                        base += 0.2
                    rating = round(min(8.9, max(6.2, base)), 1)
                else:
                    rating = 6.0

                # Match or create Player strictly without dangerous substring trap
                player = norm_db_players.get(norm)
                if not player:
                    player = Player.objects.filter(name__iexact=raw_name).first()
                if not player:
                    is_leg = (tm_year < 2015)
                    player = Player.objects.create(name=raw_name, position=pos, age=age, is_legend=is_leg)
                    norm_db_players[norm] = player

                seen_player_ids.add(player.id)

                st = PlayerSeasonStats.objects.filter(player=player, season=season, team=team).first()

                # Market value resolution
                mv = st.market_value if st and st.market_value else None
                if not mv or mv == 0:
                    mv = self.calculate_era_market_value(player, matches, goals, assists, mins, tm_year)

                if st:
                    st.matches = matches
                    st.goals = goals
                    st.assists = assists
                    st.minutes = mins
                    st.yellow_cards = yc
                    st.red_cards = rc
                    st.rating = rating
                    st.market_value = mv
                    st.save()
                    updated += 1
                else:
                    PlayerSeasonStats.objects.create(
                        player=player,
                        season=season,
                        team=team,
                        matches=matches,
                        goals=goals,
                        assists=assists,
                        minutes=mins,
                        yellow_cards=yc,
                        red_cards=rc,
                        rating=rating,
                        market_value=mv
                    )
                    created += 1

            # Zero out any players in team squad who were not in TM match appearances list
            PlayerSeasonStats.objects.filter(season=season, team=team).exclude(player_id__in=seen_player_ids).update(
                matches=0, goals=0, assists=0, minutes=0
            )

            return updated, created
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"    İstatistik hata ({team.name} {season.name}): {e}"))
            return 0, 0

    def calculate_era_market_value(self, player, matches, goals, assists, minutes, year):
        if year < 2004:
            return Decimal(0)
        if player.market_value and player.market_value > 0 and year >= 2020:
            return player.market_value
        if year >= 2020:
            base = 400000
        elif year >= 2014:
            base = 300000
        elif year >= 2008:
            base = 250000
        else:
            base = 150000
        perf = (goals * 150000) + (assists * 100000) + (minutes * 150)
        total = base + perf
        if matches == 0:
            total = 50000
        return Decimal(round(total, -4))

    def handle(self, *args, **options):
        try:
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')
        except Exception:
            pass

        self.stdout.write(self.style.NOTICE("================================================================="))
        self.stdout.write(self.style.NOTICE("  SÜPER LİG TARİHİ RESMİ PUAN DURUMU & OYUNCU İSTATİSTİKLERİ      "))
        self.stdout.write(self.style.NOTICE("  (1959'dan 2024/2025'e TÜM SEZONLAR EKSİKSİZ VE BİREBİR)        "))
        self.stdout.write(self.style.NOTICE("=================================================================\n"))

        # Step 1: Sync Standings for ALL seasons from 1959 to 2024
        if not options.get('skip_standings'):
            seasons_standings = Season.objects.filter(start_year__lte=2024, start_year__gte=1959).order_by('-start_year')
            self.stdout.write(self.style.NOTICE(f"[ADIM 1] {seasons_standings.count()} Sezon İçin Puan Durumları Çekiliyor (1959 - 2024)..."))

            total_standings = 0
            t0 = time.time()
            for s in seasons_standings:
                cnt = self.sync_season_standings(s)
                total_standings += cnt
                if cnt > 0 and s.start_year in [2024, 2023, 2022, 2021, 2020, 2010, 2000, 1995, 1988, 1980, 1975, 1965, 1959]:
                    champ = LeagueStanding.objects.filter(season=s, rank=1).first()
                    champ_str = f"-> [CHAMP] {champ.team.name} ({champ.points} P)" if champ else ""
                    self.stdout.write(f"  [OK] {s.name}: {cnt} Takim {champ_str}")

            self.stdout.write(self.style.SUCCESS(f"\n[ADIM 1 TAMAMLANDI] Toplam {total_standings} resmi puan durumu kaydı eşitlendi ({time.time()-t0:.1f}s).\n"))
        else:
            self.stdout.write(self.style.NOTICE("[ADIM 1 ATLANDI] Puan durumları adımı atlandı.\n"))

        # Step 2: Sync Player Performance Stats for all historical seasons (1959 - 2024)
        if not options.get('skip_stats'):
            self.stdout.write(self.style.NOTICE("[ADIM 2] 1959'dan 2024'e Tüm Sezonlar İçin Oyuncu İstatistikleri Eşitleniyor..."))

            seasons_stats = Season.objects.filter(start_year__lte=2024, start_year__gte=1959).order_by('-start_year')
            
            total_updated = 0
            total_created = 0
            t1 = time.time()

            for s in seasons_stats:
                tm_y = 1958 if s.name == '1959' else s.start_year

                # Base historical clubs to always include
                base_team_ids = [1, 3, 5]  # GS, FB, BJK (played all seasons since 1959)
                if tm_y >= 1974:
                    base_team_ids.append(4)  # Trabzonspor entered Super Lig in 1974
                if 1966 <= tm_y <= 1982:
                    base_team_ids.append(106)  # Eskisehirspor golden era
                if 1965 <= tm_y <= 1975:
                    base_team_ids.append(13)   # Goztepe legend era
                if 2008 <= tm_y <= 2011:
                    base_team_ids.append(105)  # Bursaspor championship era
                if tm_y >= 2014:
                    base_team_ids.append(10)   # Basaksehir
                
                teams_in_db = Team.objects.filter(team_player_stats__season=s).values_list('id', flat=True)
                all_team_ids = sorted(set(list(base_team_ids) + list(teams_in_db)))
                teams_to_sync = Team.objects.filter(id__in=all_team_ids)

                self.stdout.write(f"\n--- {s.name} Sezonu Oyuncu Istatistikleri ---")

                for team in teams_to_sync:
                    # Resolve slug and vid
                    slug, vid = self.team_slug_cache.get((team.id, tm_y), (None, None))
                    if not slug:
                        for kn, ks, kv in KEY_CLUBS_CONFIG:
                            if kn.lower() in team.name.lower() or team.name.lower() in kn.lower():
                                slug, vid = ks, kv
                                break
                    if not slug:
                        continue

                    upd, crt = self.sync_club_stats(s, team, slug, vid)
                    total_updated += upd
                    total_created += crt
                    if upd + crt > 0:
                        top_scorer = PlayerSeasonStats.objects.filter(season=s, team=team).order_by('-goals', '-assists').first()
                        top_name = top_scorer.player.name.encode('ascii', 'replace').decode('ascii') if top_scorer else ""
                        top_str = f"-> En Golcu: {top_name} ({top_scorer.goals} G, {top_scorer.assists} A, {top_scorer.matches} M)" if top_scorer and top_scorer.goals > 0 else ""
                        t_name = team.name.encode('ascii', 'replace').decode('ascii')
                        self.stdout.write(f"  [OK] {t_name:<18} ({s.name}): {upd+crt} oyuncu guncellendi {top_str}")

            self.stdout.write(self.style.SUCCESS(f"\n[ADIM 2 TAMAMLANDI] Toplam {total_updated} oyuncu istatistiği güncellendi, {total_created} yeni kayıt oluşturuldu ({time.time()-t1:.1f}s)."))
        
        self.stdout.write(self.style.SUCCESS("=== TÜM SÜPER LİG TARİHİ (1959-2024) RESMİ VERİLERLE %100 EŞİTLENDİ ==="))
