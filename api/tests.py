from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from django.utils import timezone
from datetime import date
from decimal import Decimal
from unittest.mock import patch

from .models import (
    Season, Team, LeagueStanding, Player, PlayerAttribute,
    PlayerSeasonStats, Transfer, ScoutList, Fixture
)


class SuperLigAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

        # 1. Sezon
        self.season = Season.objects.create(
            name="2026/2027",
            start_year=2026,
            end_year=2027,
            start_date=date(2026, 8, 1),
            end_date=date(2027, 6, 30),
            is_current=True
        )

        # 2. Takımlar
        self.gs = Team.objects.create(
            name="Galatasaray", short_name="GS", city="İstanbul",
            market_value=Decimal("261000000"), is_super_lig=True
        )
        self.fb = Team.objects.create(
            name="Fenerbahçe", short_name="FB", city="İstanbul",
            market_value=Decimal("230000000"), is_super_lig=True
        )
        self.napoli = Team.objects.create(
            name="SSC Napoli", short_name="NAP", city="Napoli",
            is_super_lig=False, league_name="Serie A"
        )

        # 3. Puan Durumu
        LeagueStanding.objects.create(
            season=self.season, team=self.gs, rank=1,
            won=10, drawn=2, lost=1, goals_for=30, goals_against=10
        )

        # 4. Oyuncular
        self.osimhen = Player.objects.create(
            name="Victor Osimhen", current_team=self.gs, position="Santrafor",
            market_value=Decimal("100000000"), is_active=True
        )
        PlayerAttribute.objects.create(
            player=self.osimhen, pace=91, shooting=88, passing=72, dribbling=83, defending=42, physical=89
        )
        PlayerSeasonStats.objects.create(
            player=self.osimhen, season=self.season, team=self.gs,
            matches=15, minutes=1280, goals=12, assists=4,
            shots_per_game=3.5, pass_accuracy=78.0, key_passes=33,
            key_passes_per_game=2.2, rating=7.92
        )

        self.en_nesyri = Player.objects.create(
            name="Youssef En-Nesyri", current_team=self.fb, position="Santrafor",
            market_value=Decimal("20000000"), is_active=True
        )
        PlayerAttribute.objects.create(
            player=self.en_nesyri, pace=82, shooting=80, passing=68, dribbling=74, defending=48, physical=84
        )
        PlayerSeasonStats.objects.create(
            player=self.en_nesyri, season=self.season, team=self.fb,
            matches=16, minutes=1190, goals=8, assists=3,
            shots_per_game=2.1, pass_accuracy=74.0, key_passes=18,
            key_passes_per_game=1.1, rating=7.35
        )

        # 5. Transfer
        self.transfer = Transfer.objects.create(
            player=self.osimhen, from_team=self.napoli, to_team=self.gs,
            transfer_type='INCOMING', contract_type='LOAN',
            transfer_fee=Decimal("0"), season=self.season,
            transfer_date=date(2026, 9, 2), is_new=True
        )

        # 6. Test Kullanıcısı
        self.user = User.objects.create_user(
            username="testscout", email="scout@test.com", password="SecurePassword123!"
        )

    def test_user_registration_and_login(self):
        """Kayıt ve giriş uç noktaları test edilir"""
        reg_payload = {
            "username": "newuser",
            "email": "newuser@test.com",
            "first_name": "Ali",
            "last_name": "Can",
            "password": "Password123!",
            "password2": "Password123!"
        }
        res_reg = self.client.post('/api/auth/register/', reg_payload)
        self.assertEqual(res_reg.status_code, status.HTTP_201_CREATED)
        self.assertIn("tokens", res_reg.data)

        # Giriş
        login_payload = {"username": "newuser", "password": "Password123!"}
        res_login = self.client.post('/api/auth/login/', login_payload)
        self.assertEqual(res_login.status_code, status.HTTP_200_OK)
        self.assertIn("access", res_login.data["tokens"])

    def test_automatic_season_resolution(self):
        """Otomatik güncel sezon çözümlenmesi test edilir"""
        current_season = Season.get_active_season()
        self.assertIsNotNone(current_season)
        self.assertEqual(current_season.name, "2026/2027")

        res = self.client.get('/api/seasons/current/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['name'], "2026/2027")

    def test_team_detail_with_standing_and_roster(self):
        """Takım analiz ekranı (puan durumu + kadro) test edilir"""
        res = self.client.get(f'/api/teams/{self.gs.id}/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['name'], "Galatasaray")
        self.assertIsNotNone(res.data['standing'])
        self.assertEqual(res.data['standing']['rank'], 1)
        self.assertTrue(len(res.data['players']) >= 1)

    def test_player_comparison_and_algorithmic_analysis(self):
        """2. Fotoğraftaki Oyuncu Karşılaştırma ve Algoritmik Analiz motoru test edilir"""
        url = f'/api/compare/?player1={self.osimhen.id}&player2={self.en_nesyri.id}'
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("bars", res.data)
        self.assertIn("radar", res.data)
        self.assertIn("algorithmic_analysis", res.data)
        self.assertTrue(len(res.data['algorithmic_analysis']['headline']) > 0)
        self.assertEqual(res.data['bars']['goals']['val1'], 12)
        self.assertEqual(res.data['bars']['goals']['val2'], 8)

    def test_transfers_filtering(self):
        """Transferler filtresi (Gelenler / Gidenler) test edilir"""
        res = self.client.get('/api/transfers/?type=INCOMING')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['player_name'], "Victor Osimhen")

    def test_leaderboards(self):
        """Lig istatistik liderleri test edilir"""
        res = self.client.get('/api/leaderboards/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("leaders", res.data)
        top_scorers = res.data['leaders']['top_scorers']
        self.assertTrue(len(top_scorers) > 0)
        self.assertEqual(top_scorers[0]['player_name'], "Victor Osimhen")
        self.assertEqual(top_scorers[0]['goals'], 12)

    def test_authenticated_scout_notes_crud(self):
        """Scout notları yetkilendirme ve CRUD test edilir"""
        # Giriş yapmadan istek -> 401 Unauthorized
        res_unauth = self.client.post('/api/scout-notes/', {"player": self.osimhen.id, "note": "Harika", "rating": 9})
        self.assertEqual(res_unauth.status_code, status.HTTP_401_UNAUTHORIZED)

        # Giriş yaparak istek -> 201 Created
        self.client.force_authenticate(user=self.user)
        res_create = self.client.post('/api/scout-notes/', {"player": self.osimhen.id, "note": "Hızlı ve bitirici", "rating": 9})
        self.assertEqual(res_create.status_code, status.HTTP_201_CREATED)
        note_id = res_create.data['id']

        # Güncelleme -> 200 OK
        res_update = self.client.patch(f'/api/scout-notes/{note_id}/', {"rating": 10})
        self.assertEqual(res_update.status_code, status.HTTP_200_OK)
        self.assertEqual(res_update.data['rating'], 10)

        # Silme -> 204 No Content
        res_delete = self.client.delete(f'/api/scout-notes/{note_id}/')
        self.assertEqual(res_delete.status_code, status.HTTP_204_NO_CONTENT)

    def test_fixtures_and_live_scores(self):
        """API-Football Fikstür ve Canlı Maç endpointleri test edilir"""
        # Test maçı oluştur
        fixture = Fixture.objects.create(
            season=self.season,
            round_name="10. Hafta",
            round_number=10,
            home_team=self.gs,
            away_team=self.fb,
            home_score=2,
            away_score=1,
            match_date=timezone.now(),
            status="FT",
            status_display="MS",
            venue="RAMS Park"
        )

        # Fikstür listeleme
        res_fix = self.client.get('/api/fixtures/?round_number=10')
        self.assertEqual(res_fix.status_code, status.HTTP_200_OK)
        self.assertTrue(len(res_fix.data) >= 1)
        self.assertEqual(res_fix.data[0]['home_team_name'], "Galatasaray")
        self.assertEqual(res_fix.data[0]['away_team_name'], "Fenerbahçe")

        # Canlı maçlar
        res_live = self.client.get('/api/fixtures/live/')
        self.assertEqual(res_live.status_code, status.HTTP_200_OK)

        # Güncel hafta
        res_round = self.client.get('/api/fixtures/current_round/')
        self.assertEqual(res_round.status_code, status.HTTP_200_OK)
        self.assertIn("fixtures", res_round.data)

    def test_data_sync_endpoints(self):
        """Transfermarkt, SofaScore ve API-Football senkronizasyon uç noktaları test edilir"""
        # 1. Transfer Takip '🔄 API ile Güncelle' butonu (Transfermarkt)
        res_tr = self.client.post('/api/sync/transfers/')
        self.assertEqual(res_tr.status_code, status.HTTP_200_OK)
        self.assertEqual(res_tr.data['status'], 'success')
        self.assertIn("Transfermarkt", res_tr.data['source'])

        # 2. SofaScore / WhoScored Oyuncu Radar & Yetenek Senkronizasyonu
        res_attr = self.client.post('/api/sync/attributes/')
        self.assertEqual(res_attr.status_code, status.HTTP_200_OK)
        self.assertEqual(res_attr.data['status'], 'success')

        # 3. API-Football Fikstür Senkronizasyonu
        res_fix_sync = self.client.post('/api/sync/fixtures/')
        self.assertEqual(res_fix_sync.status_code, status.HTTP_200_OK)
        self.assertEqual(res_fix_sync.data['status'], 'success')

    def test_sofascore_whoscored_enrichment(self):
        """SofaScore/WhoScored analitik motorunun oyuncu özelliklerini zenginleştirmesi test edilir"""
        from api.integrations import PlayerAnalyticsService
        attr = PlayerAnalyticsService.enrich_player(self.osimhen)
        self.assertIsNotNone(attr)
        self.assertEqual(attr.pace, 89)
        self.assertEqual(attr.shooting, 88)
        self.assertIn("Ceza sahası bitiriciliği", attr.strengths)

    def test_squad_diff_preserves_history_and_handles_intra_league(self):
        """Kadro farkı algoritması ayrılanları arşive taşır, geçmiş veriyi korur ve lig içi transferi tek kulübe alır"""
        from api.integrations import TransfermarktScraper

        old_season = Season.objects.create(
            name="2024/2025",
            start_year=2024,
            end_year=2025,
            start_date=date(2024, 8, 1),
            end_date=date(2025, 6, 30),
            is_current=False,
        )
        departing = Player.objects.create(
            name="Fernando Muslera", current_team=self.gs, position="Kaleci", is_active=True
        )
        PlayerSeasonStats.objects.create(
            player=departing, season=old_season, team=self.gs, matches=34, minutes=3060, goals=0
        )
        PlayerSeasonStats.objects.create(
            player=departing, season=self.season, team=self.gs, matches=0, minutes=0, goals=0
        )

        # Sahte canlı veri oluştur (En-Nesyri GS'ye geçsin, Muslera kadroda olmasın, Ederson MK+TM tekilleşsin)
        def make_filler(prefix, count):
            return [
                {
                    "tm_id": f"{prefix}{i}",
                    "name": f"{prefix} Player {i}",
                    "jersey_number": 50 + i,
                    "position": "Stoper",
                    "age": 24,
                    "nationality": "Türkiye",
                    "market_value": 1000000.0,
                    "image_url": None,
                    "matches": 1,
                    "goals": 0,
                    "assists": 0,
                    "minutes": 90,
                    "yellow_cards": 0,
                    "red_cards": 0,
                    "sources": ["transfermarkt"],
                }
                for i in range(count)
            ]

        pre_fetched = {
            self.gs.id: {
                "tm_players": [
                    {
                        "tm_id": "1",
                        "name": "Victor Osimhen",
                        "jersey_number": 45,
                        "position": "Santrafor",
                        "age": 27,
                        "nationality": "Nijerya",
                        "market_value": 65000000.0,
                        "image_url": None,
                        "matches": 8,
                        "goals": 9,
                        "assists": 3,
                        "minutes": 700,
                        "yellow_cards": 1,
                        "red_cards": 0,
                        "sources": ["transfermarkt"],
                    },
                    {
                        "tm_id": "2",
                        "name": "Youssef En-Nesyri",
                        "jersey_number": 19,
                        "position": "Santrafor",
                        "age": 29,
                        "nationality": "Fas",
                        "market_value": 20000000.0,
                        "image_url": None,
                        "matches": 5,
                        "goals": 4,
                        "assists": 1,
                        "minutes": 400,
                        "yellow_cards": 0,
                        "red_cards": 0,
                        "sources": ["transfermarkt"],
                    },
                    *make_filler("GS", 15),
                ],
                "mk_players": [],
            },
            self.fb.id: {
                "tm_players": [
                    {
                        "tm_id": "31",
                        "name": "Ederson",
                        "jersey_number": 31,
                        "position": "Kaleci",
                        "age": 33,
                        "nationality": "Brezilya",
                        "market_value": 15000000.0,
                        "image_url": None,
                        "matches": 10,
                        "goals": 0,
                        "assists": 0,
                        "minutes": 900,
                        "yellow_cards": 0,
                        "red_cards": 0,
                        "sources": ["transfermarkt"],
                    },
                    *make_filler("FB", 15),
                ],
                "mk_players": [
                    {
                        "name": "Ederson Santana de Moraes",
                        "jersey_number": 31,
                        "position": "Kaleci",
                        "age": 33,
                        "matches_all_comp": 10,
                        "goals_all_comp": 0,
                        "assists_all_comp": 0,
                    }
                ],
            },
        }

        summary = TransfermarktScraper.sync_live_squads_with_diff(
            teams=[self.gs, self.fb], season=self.season, pre_fetched=pre_fetched
        )
        self.assertEqual(summary["teams_synced"], 2)

        # Ayrılan Muslera silinmemeli, geçmişi korunmalı ve Eski Oyunculara geçmeli
        departing.refresh_from_db()
        self.assertIsNone(departing.current_team)
        self.assertFalse(departing.is_active)
        self.assertTrue(departing.is_legend)
        self.assertTrue(PlayerSeasonStats.objects.filter(player=departing, season=old_season, team=self.gs).exists())
        self.assertFalse(PlayerSeasonStats.objects.filter(player=departing, season=self.season, team=self.gs).exists())

        # Lig içi transfer En-Nesyri sadece GS aktif kadrosunda olmalı
        self.en_nesyri.refresh_from_db()
        self.assertEqual(self.en_nesyri.current_team_id, self.gs.id)
        self.assertFalse(PlayerSeasonStats.objects.filter(player=self.en_nesyri, season=self.season, team=self.fb).exists())
        self.assertTrue(PlayerSeasonStats.objects.filter(player=self.en_nesyri, season=self.season, team=self.gs).exists())

        # Ederson + Ederson Santana de Moraes tekilleşmiş olmalı (1 kaleci)
        self.assertEqual(Player.objects.filter(current_team=self.fb, jersey_number=31).count(), 1)

        # Takım piyasa değeri ve dinamik oyuncu metrikleri/reytingleri güncellenmeli
        self.gs.refresh_from_db()
        self.assertGreater(self.gs.market_value, Decimal("0"))
        osimhen_st = PlayerSeasonStats.objects.get(player=self.osimhen, season=self.season, team=self.gs)
        self.assertGreater(osimhen_st.rating, 7.5)
        self.assertGreater(osimhen_st.shots_per_game, 0.0)
        self.assertEqual(osimhen_st.clean_sheets, 0)

    def test_stats_reconciliation_and_fixture_finalization_no_double_count(self):
        """Maç bitiminde istatistik uzlaştırma idempotent olmalı, çift sayım ve yedek enflasyonu yapmamalı"""
        from api.integrations import APIFootballService

        bench_gk = Player.objects.create(
            name="Günay Güvenç", current_team=self.gs, position="Kaleci", jersey_number=19, is_active=True
        )
        PlayerSeasonStats.objects.create(
            player=bench_gk, season=self.season, team=self.gs,
            matches=2, minutes=180, goals=0, assists=0, clean_sheets=1
        )
        LeagueStanding.objects.create(
            season=self.season, team=self.fb, rank=2,
            won=9, drawn=2, lost=2, goals_for=25, goals_against=12
        )

        pending_fix = Fixture.objects.create(
            season=self.season,
            round_name="12. Hafta",
            round_number=12,
            home_team=self.gs,
            away_team=self.fb,
            match_date=timezone.now(),
            status="NS",
            status_display="19:00",
        )

        # _finalize_finished_fixture_atomically aynı maçı iki kez işlese bile puan durumu/oyuncu çift sayılmamalı
        with patch.object(APIFootballService, "fetch_espn_club_roster_stats", return_value=[]):
            first = APIFootballService._finalize_finished_fixture_atomically(
                pending_fix.id, 2, 0, [{"side": "home", "scorer": "Victor Osimhen", "assist": None}]
            )
            second = APIFootballService._finalize_finished_fixture_atomically(
                pending_fix.id, 2, 0, [{"side": "home", "scorer": "Victor Osimhen", "assist": None}]
            )
        self.assertTrue(first)
        self.assertFalse(second)

        gs_standing = LeagueStanding.objects.get(season=self.season, team=self.gs)
        self.assertEqual(gs_standing.won, 11)
        self.assertEqual(gs_standing.played, 14)

        # Kümülatif ESPN toplamları idempotent uygulanmalı; yedekte kalan oyuncuya +1 eklenmemeli
        espn_roster = [
            {
                "name": "Victor Osimhen",
                "jersey": 45,
                "pos_abbr": "F",
                "matches": 15,
                "goals": 13,
                "assists": 4,
                "total_shots": 60,
                "shots_on_target": 28,
                "yellow_cards": 1,
                "red_cards": 0,
                "saves": 0,
                "goals_conceded": 0,
            },
            {
                "name": "Günay Güvenç",
                "jersey": 19,
                "pos_abbr": "G",
                "matches": 2,
                "goals": 0,
                "assists": 0,
                "total_shots": 0,
                "shots_on_target": 0,
                "yellow_cards": 0,
                "red_cards": 0,
                "saves": 5,
                "goals_conceded": 1,
            },
        ]
        APIFootballService.sync_team_espn_player_stats(self.season, self.gs, espn_entries=espn_roster)
        APIFootballService.sync_team_espn_player_stats(self.season, self.gs, espn_entries=espn_roster)

        osimhen_st = PlayerSeasonStats.objects.get(player=self.osimhen, season=self.season, team=self.gs)
        bench_st = PlayerSeasonStats.objects.get(player=bench_gk, season=self.season, team=self.gs)
        self.assertEqual(osimhen_st.matches, 15)
        self.assertEqual(osimhen_st.goals, 13)
        self.assertAlmostEqual(osimhen_st.shots_per_game, 4.0, places=2)
        self.assertEqual(bench_st.matches, 2)
        self.assertEqual(bench_st.clean_sheets, 1)

    def test_transfer_sync_deduplicates_domestic_and_preserves_history(self):
        """Canlı transfer senkronizasyonu geçmiş sezonları korur ve lig içi/dış takımları tekilleştirir"""
        from api.integrations import TransfermarktScraper

        old_season = Season.objects.create(
            name="2025/2026",
            start_year=2025,
            end_year=2026,
            start_date=date(2025, 8, 1),
            end_date=date(2026, 6, 30),
            is_current=False,
        )
        old_transfer = Transfer.objects.create(
            player=self.osimhen,
            from_team=self.napoli,
            to_team=self.gs,
            transfer_type="INCOMING",
            contract_type="PERMANENT",
            transfer_fee=Decimal("75000000"),
            season=old_season,
            transfer_date=date(2025, 8, 5),
            is_new=False,
        )

        # Sentetik canlı veri:
        # 1. GS -> FB lig içi transfer (DOMESTIC)
        # 2. Yabancı kulüpten geliş (is_super_lig=False oluşturmalı)
        pre_fetched = [
            {
                "tm_id": "2",
                "player_name": "Youssef En-Nesyri",
                "position": "Santrafor",
                "age": 29,
                "market_value": 15000000.0,
                "portrait_url": None,
                "from_sl_vid": 36,  # Fenerbahçe
                "from_ext_name": "",
                "from_logo": None,
                "to_sl_vid": 141,  # Galatasaray
                "to_ext_name": "",
                "to_logo": None,
                "contract_type": "PERMANENT",
                "transfer_fee": 12000000.0,
                "fee_note": "12.00M € Bonservis",
                "transfer_date": date(2026, 8, 28),
            },
            {
                "tm_id": "99",
                "player_name": "Rafael Leão",
                "position": "Sol Kanat",
                "age": 27,
                "market_value": 50000000.0,
                "portrait_url": None,
                "from_sl_vid": None,
                "from_ext_name": "AC Milan",
                "from_logo": None,
                "to_sl_vid": 141,
                "to_ext_name": "",
                "to_logo": None,
                "contract_type": "PERMANENT",
                "transfer_fee": 38000000.0,
                "fee_note": "38.00M € Bonservis",
                "transfer_date": date(2026, 8, 29),
            },
        ]

        synced = TransfermarktScraper.scrape_super_lig_transfers(season=self.season, pre_fetched=pre_fetched)
        self.assertEqual(len(synced), 2)
        self.assertTrue(Transfer.objects.filter(id=old_transfer.id, season=old_season).exists())
        self.assertEqual(Transfer.objects.filter(season=self.season, transfer_type="DOMESTIC").count(), 1)
        milan = Team.objects.get(name="AC Milan")
        self.assertFalse(milan.is_super_lig)
        # Mevcut oyuncu için oluşturulmuş yeni transfer oyuncusu pasif arşive atanmalı (aktif SL kadroyu bozmamalı)
        leao = Player.objects.get(name="Rafael Leão")
        self.assertFalse(leao.is_active)
        self.assertIsNone(leao.current_team)


