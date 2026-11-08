from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    SeasonViewSet, TeamViewSet, PlayerViewSet,
    PlayerSeasonStatsViewSet, TransferViewSet,
    LeagueStandingViewSet, ScoutListViewSet, FixtureViewSet,
    LeaderboardsView, PlayerComparisonView, HomeSummaryView, LegendsView,
    RegisterView, LoginView, CustomTokenRefreshView, UserProfileView, ChangePasswordView,
    SyncTransfersView, SyncSquadsView, SyncAttributesView,
    SyncFixturesView, SyncAllView,
    FavoriteTeamViewSet, DeviceRegistrationView, NotificationInboxViewSet, TestNotificationView
)

router = DefaultRouter()
router.register(r'seasons', SeasonViewSet, basename='season')
router.register(r'teams', TeamViewSet, basename='team')
router.register(r'players', PlayerViewSet, basename='player')
router.register(r'player-stats', PlayerSeasonStatsViewSet, basename='player-stats')
router.register(r'transfers', TransferViewSet, basename='transfer')
router.register(r'standings', LeagueStandingViewSet, basename='standing')
router.register(r'fixtures', FixtureViewSet, basename='fixture')
router.register(r'scout-notes', ScoutListViewSet, basename='scout-notes')
router.register(r'favorite-teams', FavoriteTeamViewSet, basename='favorite-team')
router.register(r'notifications/inbox', NotificationInboxViewSet, basename='notification-inbox')

urlpatterns = [
    # Auth Endpoints (Kullanıcı Kayıt & Giriş & Profil)
    path('auth/register/', RegisterView.as_view(), name='auth-register'),
    path('auth/login/', LoginView.as_view(), name='auth-login'),
    path('auth/refresh/', CustomTokenRefreshView.as_view(), name='auth-refresh'),
    path('auth/me/', UserProfileView.as_view(), name='auth-me'),
    path('auth/change-password/', ChangePasswordView.as_view(), name='auth-change-password'),

    # Bildirim Servisi & Cihaz Kayıt Endpoints
    path('notifications/register-device/', DeviceRegistrationView.as_view(), name='device-register'),
    path('notifications/test-event/', TestNotificationView.as_view(), name='notification-test-event'),

    # Özel İş Mantığı ve Analiz Endpoints
    path('leaderboards/', LeaderboardsView.as_view(), name='leaderboards'),
    path('compare/', PlayerComparisonView.as_view(), name='player-compare'),
    path('home-summary/', HomeSummaryView.as_view(), name='home-summary'),
    path('legends/', LegendsView.as_view(), name='legends-list'),

    # Veri Entegrasyonu & Otomasyon Endpoints (Transfermarkt, SofaScore/WhoScored, API-Football)
    path('sync/transfers/', SyncTransfersView.as_view(), name='sync-transfers'),
    path('sync/squads/', SyncSquadsView.as_view(), name='sync-squads'),
    path('sync/attributes/', SyncAttributesView.as_view(), name='sync-attributes'),
    path('sync/fixtures/', SyncFixturesView.as_view(), name='sync-fixtures'),
    path('sync/all/', SyncAllView.as_view(), name='sync-all'),

    # CRUD Router Endpoints (Teams, Players, Transfers, Standings, Fixtures, ScoutNotes, etc.)
    path('', include(router.urls)),
]
