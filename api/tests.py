from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from django.utils import timezone
from datetime import date
from decimal import Decimal

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

