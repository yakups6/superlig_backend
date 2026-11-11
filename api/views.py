from decimal import Decimal
from django.shortcuts import render
from rest_framework import viewsets, filters, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.db.models import Q, Sum, Count, Max, F
from collections import Counter
from drf_spectacular.utils import (
    extend_schema, extend_schema_view, OpenApiParameter, OpenApiTypes
)

from datetime import timedelta
from zoneinfo import ZoneInfo
from django.utils import timezone
from .models import (
    Season, Team, LeagueStanding, Player, PlayerAttribute,
    PlayerSeasonStats, Transfer, ScoutList, Fixture,
    FavoriteTeam, UserDevice, NotificationLog
)
from .serializers import (
    SeasonSerializer, TeamListSerializer, TeamDetailSerializer,
    LeagueStandingSerializer, PlayerSimpleSerializer, PlayerDetailSerializer,
    PlayerSeasonStatsSerializer, TransferSerializer, ScoutListSerializer,
    RegisterSerializer, LoginSerializer, AuthResponseSerializer,
    UserSerializer, ChangePasswordSerializer, PlayerAttributeSerializer,
    FixtureSerializer, SyncResponseSerializer,
    FavoriteTeamSerializer, UserDeviceSerializer, NotificationLogSerializer
)
from .services import compare_players
from .integrations import (
    TransfermarktScraper, PlayerAnalyticsService, APIFootballService
)
from .notifications import (
    dispatch_match_goal_notification, dispatch_lineup_notification, send_expo_push_notification
)


# ==========================================
# 1. KULLANICI KİMLİK DOĞRULAMA (AUTH) VIEWS
# ==========================================

class RegisterView(APIView):
    """
    Kullanıcı Kayıt Sistemi (POST /api/auth/register/)
    Başarılı kayıtta kullanıcı bilgileri ve JWT token'ları döner.
    """
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        tags=['1. Kimlik Doğrulama (Auth)'],
        summary="Yeni Kullanıcı Kaydı",
        description="Sisteme yeni bir kullanıcı kaydeder ve otomatik JWT token üretir.",
        request=RegisterSerializer,
        responses={201: AuthResponseSerializer, 400: OpenApiTypes.OBJECT}
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            return Response({
                "message": "Kullanıcı başarıyla kaydedildi.",
                "user": UserSerializer(user).data,
                "tokens": {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                }
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    """
    Kullanıcı Giriş Sistemi (POST /api/auth/login/)
    Giriş başarılı olduğunda JWT erişim ve yenileme token'ları döner.
    """
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        tags=['1. Kimlik Doğrulama (Auth)'],
        summary="Kullanıcı Girişi (JWT Token Al)",
        description="Kullanıcı adı ve şifre ile giriş yaparak API çağrılarında kullanılacak JWT token'ları alır.",
        request=LoginSerializer,
        responses={200: AuthResponseSerializer, 400: OpenApiTypes.OBJECT, 401: OpenApiTypes.OBJECT}
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        username = serializer.validated_data['username'].strip()
        password = serializer.validated_data['password']

        user = authenticate(username=username, password=password)
        if not user and '@' in username:
            email_user = User.objects.filter(email__iexact=username).first()
            if email_user:
                user = authenticate(username=email_user.username, password=password)
        if not user:
            ci_user = User.objects.filter(username__iexact=username).first()
            if ci_user and ci_user.username != username:
                user = authenticate(username=ci_user.username, password=password)

        if not user:
            return Response(
                {"error": "Geçersiz kullanıcı adı/e-posta veya şifre."},
                status=status.HTTP_401_UNAUTHORIZED
            )

        refresh = RefreshToken.for_user(user)
        return Response({
            "message": "Giriş başarılı.",
            "user": UserSerializer(user).data,
            "tokens": {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            }
        }, status=status.HTTP_200_OK)


class CustomTokenRefreshView(TokenRefreshView):
    """
    JWT Token Yenileme (POST /api/auth/refresh/)
    """
    @extend_schema(
        tags=['1. Kimlik Doğrulama (Auth)'],
        summary="JWT Token Yenile (Refresh)",
        description="Refresh token göndererek süresi dolan access token'ı yeniler."
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class UserProfileView(APIView):
    """
    Kullanıcı Profil ve Oturum Bilgisi (GET, PUT, PATCH /api/auth/me/)
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=['1. Kimlik Doğrulama (Auth)'],
        summary="Giriş Yapan Kullanıcı Profili",
        description="Giriş yapmış olan kullanıcının profil detaylarını döner.",
        responses={200: UserSerializer}
    )
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        tags=['1. Kimlik Doğrulama (Auth)'],
        summary="Kullanıcı Profilini Güncelle",
        request=UserSerializer,
        responses={200: UserSerializer}
    )
    def put(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(APIView):
    """
    Şifre Değiştirme (POST /api/auth/change-password/)
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=['1. Kimlik Doğrulama (Auth)'],
        summary="Kullanıcı Şifresi Değiştir",
        request=ChangePasswordSerializer,
        responses={200: OpenApiTypes.OBJECT, 400: OpenApiTypes.OBJECT}
    )
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            if not request.user.check_password(serializer.validated_data['old_password']):
                return Response({"old_password": ["Mevcut şifreniz hatalı."]}, status=status.HTTP_400_BAD_REQUEST)
            request.user.set_password(serializer.validated_data['new_password'])
            request.user.save()
            return Response({"message": "Şifreniz başarıyla değiştirildi."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ==========================================
# 2. TAM CRUD İŞLEMLERİ OLAN MODEL VIEWSET'LER
# ==========================================

@extend_schema_view(
    list=extend_schema(tags=['2. Sezonlar'], summary="Sezonları Listele"),
    retrieve=extend_schema(tags=['2. Sezonlar'], summary="Sezon Detayı"),
    create=extend_schema(tags=['2. Sezonlar'], summary="Yeni Sezon Ekle"),
    update=extend_schema(tags=['2. Sezonlar'], summary="Sezonu Güncelle"),
    partial_update=extend_schema(tags=['2. Sezonlar'], summary="Sezonu Kısmi Güncelle"),
    destroy=extend_schema(tags=['2. Sezonlar'], summary="Sezonu Sil"),
)
class SeasonViewSet(viewsets.ModelViewSet):
    """
    Sezon CRUD (GET, POST, PUT, PATCH, DELETE)
    """
    queryset = Season.objects.all()
    serializer_class = SeasonSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    @extend_schema(
        tags=['2. Sezonlar'],
        summary="Aktif / Güncel Sezon Bilgisi",
        description="Günün tarihine göre otomatik olarak aktif sezonu döner. Sezonda takılı kalmaz.",
        responses={200: SeasonSerializer}
    )
    @action(detail=False, methods=['get'], url_path='current')
    def current(self, request):
        active_season = Season.get_active_season()
        if not active_season:
            return Response({"error": "Kayıtlı sezon bulunamadı."}, status=status.HTTP_404_NOT_FOUND)
        return Response(SeasonSerializer(active_season).data)

    @extend_schema(
        tags=['2. Sezonlar'],
        summary="Otomatik Sezon Geçişini Tetikle",
        description="Takvim gününe göre sistemin aktif sezonunu anında senkronize eder.",
        responses={200: OpenApiTypes.OBJECT}
    )
    @action(detail=False, methods=['post'], url_path='auto-switch')
    def auto_switch(self, request):
        active_season = Season.get_active_season()
        return Response({
            "message": f"Aktif sezon başarıyla güncellendi: {active_season.name}",
            "current_season": SeasonSerializer(active_season).data
        })


@extend_schema_view(
    list=extend_schema(
        tags=['3. Takım Analizi'],
        summary="Takımları Listele",
        parameters=[
            OpenApiParameter(name='is_super_lig', type=bool, required=False, description='Sadece Süper Lig takımlarını filtrele (true/false)'),
            OpenApiParameter(name='search', type=str, required=False, description='Takım adı, şehir veya stadyum ara')
        ]
    ),
    retrieve=extend_schema(tags=['3. Takım Analizi'], summary="Takım Analiz Detayı (Puan, Sıra, Kadro Değeri ve Oyuncu Listesi)"),
    create=extend_schema(tags=['3. Takım Analizi'], summary="Yeni Takım Ekle"),
    update=extend_schema(tags=['3. Takım Analizi'], summary="Takımı Güncelle"),
    partial_update=extend_schema(tags=['3. Takım Analizi'], summary="Takımı Kısmi Güncelle"),
    destroy=extend_schema(tags=['3. Takım Analizi'], summary="Takımı Sil"),
)
class TeamViewSet(viewsets.ModelViewSet):
    """
    Takım CRUD (GET, POST, PUT, PATCH, DELETE)
    """
    queryset = Team.objects.all()
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'city', 'stadium']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return TeamDetailSerializer
        return TeamListSerializer

    def get_queryset(self):
        qs = Team.objects.all()
        is_super_lig = self.request.query_params.get('is_super_lig')
        if is_super_lig is not None:
            qs = qs.filter(is_super_lig=(is_super_lig.lower() in ['true', '1']))
        return qs


@extend_schema_view(
    list=extend_schema(
        tags=['4. Oyuncular & Efsaneler'],
        summary="Oyuncuları Listele",
        parameters=[
            OpenApiParameter(name='season', type=str, required=False, description='Sezon Adı (örn: 2024/2025) veya ID ile o sezonun oyuncularını ve istatistiklerini getir'),
            OpenApiParameter(name='team', type=int, required=False, description='Takım ID filtreleme'),
            OpenApiParameter(name='is_legend', type=bool, required=False, description='Eski / Efsane oyuncular (true/false)'),
            OpenApiParameter(name='is_active', type=bool, required=False, description='Aktif oyuncular (true/false)'),
            OpenApiParameter(name='position', type=str, required=False, description='Mevki arama (Santrafor, Kanat, vb.)'),
            OpenApiParameter(name='search', type=str, required=False, description='Oyuncu adı arama')
        ]
    ),
    retrieve=extend_schema(tags=['4. Oyuncular & Efsaneler'], summary="Oyuncu Detayı (Radar Nitelikleri ve Sezon Sezon İstatistikleri)"),
    create=extend_schema(tags=['4. Oyuncular & Efsaneler'], summary="Yeni Oyuncu Ekle"),
    update=extend_schema(tags=['4. Oyuncular & Efsaneler'], summary="Oyuncu Güncelle"),
    partial_update=extend_schema(tags=['4. Oyuncular & Efsaneler'], summary="Oyuncu Kısmi Güncelle"),
    destroy=extend_schema(tags=['4. Oyuncular & Efsaneler'], summary="Oyuncu Sil"),
)
class PlayerViewSet(viewsets.ModelViewSet):
    """
    Oyuncu CRUD (GET, POST, PUT, PATCH, DELETE)
    """
    queryset = Player.objects.select_related('current_team').prefetch_related('attributes', 'season_stats__season', 'season_stats__team')
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'nationality', 'position']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return PlayerDetailSerializer
        if self.action in ['create', 'update', 'partial_update']:
            return PlayerSimpleSerializer
        return PlayerSimpleSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        team_id = self.request.query_params.get('team')
        is_legend = self.request.query_params.get('is_legend')
        is_active = self.request.query_params.get('is_active')
        position = self.request.query_params.get('position')

        if team_id:
            if team_id.isdigit():
                qs = qs.filter(current_team_id=team_id)
            else:
                qs = qs.filter(
                    Q(current_team__short_name__iexact=team_id) |
                    Q(current_team__name__icontains=team_id)
                )
        if is_legend is not None:
            qs = qs.filter(is_legend=(is_legend.lower() in ['true', '1']))
        if is_active is not None:
            qs = qs.filter(is_active=(is_active.lower() in ['true', '1']))
        if position:
            qs = qs.filter(position__icontains=position)

        return qs.order_by('-market_value', 'name')

    def list(self, request, *args, **kwargs):
        season_param = request.query_params.get('season')
        if not season_param:
            return super().list(request, *args, **kwargs)

        season = Season.objects.filter(name=season_param).first()
        if not season and str(season_param).isdigit():
            season = Season.objects.filter(id=int(season_param)).first()
        if not season and str(season_param).isdigit():
            season = Season.objects.filter(start_year=int(season_param)).first()

        if not season:
            return Response([])

        stats_qs = PlayerSeasonStats.objects.filter(season=season).select_related('player', 'team')

        team_param = request.query_params.get('team')
        if team_param and team_param != 'ALL':
            if str(team_param).isdigit():
                stats_qs = stats_qs.filter(team_id=int(team_param))
            else:
                stats_qs = stats_qs.filter(
                    Q(team__short_name__iexact=team_param) |
                    Q(team__name__icontains=team_param)
                )

        position_param = request.query_params.get('position')
        if position_param and position_param != 'ALL':
            pos_up = position_param.upper()
            if pos_up == 'FORVET':
                stats_qs = stats_qs.filter(
                    Q(player__position__icontains='forvet') |
                    Q(player__position__icontains='santr') |
                    Q(player__position__icontains='kanat')
                )
            elif pos_up == 'ORTA':
                stats_qs = stats_qs.filter(
                    Q(player__position__icontains='orta') |
                    Q(player__position__icontains='on numara') |
                    Q(player__position__icontains='önlibero')
                )
            elif pos_up == 'DEFANS':
                stats_qs = stats_qs.filter(
                    Q(player__position__icontains='stoper') |
                    Q(player__position__icontains='bek') |
                    Q(player__position__icontains='defans')
                )
            elif pos_up == 'KALECI':
                stats_qs = stats_qs.filter(player__position__icontains='kaleci')
            else:
                stats_qs = stats_qs.filter(player__position__icontains=position_param)

        search_query = request.query_params.get('search')
        if search_query:
            stats_qs = stats_qs.filter(
                Q(player__name__icontains=search_query) |
                Q(player__position__icontains=search_query) |
                Q(team__name__icontains=search_query) |
                Q(team__short_name__icontains=search_query)
            )

        is_historical = (season.start_year < 2004)
        if is_historical:
            sorted_stats = sorted(
                stats_qs,
                key=lambda x: (x.goals or 0, x.assists or 0, x.matches or 0),
                reverse=True
            )
        else:
            sorted_stats = sorted(
                stats_qs,
                key=lambda x: (
                    Decimal(str(x.market_value if x.market_value is not None else (x.player.market_value or 0))),
                    x.matches or 0,
                    x.goals or 0,
                    x.assists or 0
                ),
                reverse=True
            )

        data = []
        seen = set()
        for st in sorted_stats:
            key = (st.player_id, st.team_id)
            if key in seen:
                continue
            seen.add(key)
            p = st.player

            name_display = f"{p.name} {st.transfer_note}".strip() if st.transfer_note else p.name

            item = {
                'id': p.id,
                'name': name_display,
                'display_name': name_display,
                'transfer_note': st.transfer_note or '',
                'current_team': st.team_id,
                'current_team_short_name': st.team.short_name,
                'team_id': st.team_id,
                'team_name': st.team.name,
                'team_short_name': st.team.short_name,
                'team_logo': st.team.logo_url,
                'position': p.position,
                'age': p.age,
                'nationality': p.nationality,
                'jersey_number': p.jersey_number,
                'market_value': str(st.market_value if st.market_value is not None else (p.market_value or 0)),
                'image_url': p.image_url,
                'is_active': p.is_active,
                'is_legend': p.is_legend,
                'season_matches': st.matches,
                'season_goals': st.goals,
                'season_assists': st.assists,
                'season_rating': st.rating,
                'matches': st.matches,
                'goals': st.goals,
                'assists': st.assists,
                'rating': st.rating,
            }
            data.append(item)

        return Response(data)

    @extend_schema(
        tags=['4.1 Eski Oyuncular (Geçmiş Sezonlar & Efsaneler)'],
        summary="Eski ve Efsanevi Oyuncuları Listele (Hagi, Alex, Sneijder, Quaresma, Drogba, Gomez, Sørloth, Carlos vb.)",
        description="Süper Lig tarihine damga vurmuş 20+ efsane oyuncunun radar özellikleri, sezonluk maç/gol/asist istatistikleri ve şampiyonluk başarıları.",
        responses={200: PlayerDetailSerializer(many=True)}
    )
    @action(detail=False, methods=['get'], url_path='legends', permission_classes=[permissions.AllowAny])
    def legends(self, request):
        legends = Player.objects.filter(is_legend=True).prefetch_related('attributes', 'season_stats__season', 'season_stats__team')
        serializer = PlayerDetailSerializer(legends, many=True)
        return Response(serializer.data)


@extend_schema(
    tags=['4.1 Eski Oyuncular (Geçmiş Sezonlar & Efsaneler)'],
    summary="Eski Oyuncular: Geçmiş Sezonlar & Efsaneler",
    description="Mobil tasarımdaki 'Eski Oyuncular: Geçmiş Sezonlar & Efsaneler' menüsü için özel endpoint. Alex, Hagi, Sneijder, Gomez, Quaresma, Drogba, Carlos, Sørloth, Talisca vb. efsane futbolcuları döner.",
    responses={200: PlayerDetailSerializer(many=True)}
)
class LegendsView(APIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        season_param = request.query_params.get('season')
        team_param = request.query_params.get('team')
        position_param = request.query_params.get('position')
        search_query = request.query_params.get('search')

        # 1. SPECIFIC SEASON SELECTED
        if season_param and season_param.upper() != 'ALL':
            season = Season.objects.filter(name=season_param).first()
            if not season and str(season_param).isdigit():
                season = Season.objects.filter(id=int(season_param)).first()
            if not season and str(season_param).isdigit():
                season = Season.objects.filter(start_year=int(season_param)).first()

            if not season:
                return Response([])

            stats_qs = PlayerSeasonStats.objects.filter(season=season).select_related('player', 'team')

            if team_param and team_param != 'ALL':
                if str(team_param).isdigit():
                    stats_qs = stats_qs.filter(team_id=int(team_param))
                else:
                    stats_qs = stats_qs.filter(
                        Q(team__short_name__iexact=team_param) |
                        Q(team__name__icontains=team_param)
                    )

            if position_param and position_param != 'ALL':
                pos_up = position_param.upper()
                if pos_up == 'FORVET':
                    stats_qs = stats_qs.filter(
                        Q(player__position__icontains='forvet') |
                        Q(player__position__icontains='santr') |
                        Q(player__position__icontains='kanat')
                    )
                elif pos_up == 'ORTA':
                    stats_qs = stats_qs.filter(
                        Q(player__position__icontains='orta') |
                        Q(player__position__icontains='on numara') |
                        Q(player__position__icontains='önlibero')
                    )
                elif pos_up == 'DEFANS':
                    stats_qs = stats_qs.filter(
                        Q(player__position__icontains='stoper') |
                        Q(player__position__icontains='bek') |
                        Q(player__position__icontains='defans')
                    )
                elif pos_up == 'KALECI':
                    stats_qs = stats_qs.filter(player__position__icontains='kaleci')
                else:
                    stats_qs = stats_qs.filter(player__position__icontains=position_param)

            if search_query:
                stats_qs = stats_qs.filter(
                    Q(player__name__icontains=search_query) |
                    Q(player__position__icontains=search_query) |
                    Q(team__name__icontains=search_query) |
                    Q(team__short_name__icontains=search_query)
                )

            sorted_stats = sorted(
                stats_qs,
                key=lambda x: (
                    1 if x.player.is_legend else 0,
                    x.goals or 0,
                    x.assists or 0,
                    x.matches or 0,
                    float(x.rating or 7.5),
                    float(x.market_value or 0)
                ),
                reverse=True
            )

            data = []
            seen = set()
            for st in sorted_stats:
                key = (st.player_id, st.team_id)
                if key in seen:
                    continue
                seen.add(key)
                p = st.player
                name_display = f"{p.name} {st.transfer_note}".strip() if st.transfer_note else p.name

                data.append({
                    'id': p.id,
                    'name': name_display,
                    'display_name': name_display,
                    'transfer_note': st.transfer_note or '',
                    'position': p.position,
                    'age': p.age,
                    'nationality': p.nationality,
                    'jersey_number': p.jersey_number,
                    'market_value': st.market_value or p.market_value,
                    'image_url': p.image_url or 'https://img.a.transfermarkt.technology/portrait/header/default.jpg',
                    'is_active': p.is_active,
                    'is_legend': p.is_legend,
                    'team_id': st.team_id,
                    'team_name': st.team.name,
                    'team_short_name': st.team.short_name,
                    'team_logo': st.team.logo_url,
                    'season_name': season.name,
                    'season_matches': st.matches,
                    'season_goals': st.goals,
                    'season_assists': st.assists,
                    'season_rating': float(st.rating) if st.rating else 8.2,
                    'rating': float(st.rating) if st.rating else 8.2,
                    'era_badge': f'{season.name} Dönemi',
                })

            return Response(data)

        # 2. ALL SEASONS / ALL-TIME LEGENDS
        legends_qs = Player.objects.filter(is_legend=True).annotate(
            total_matches=Sum('season_stats__matches'),
            total_goals=Sum('season_stats__goals'),
            total_assists=Sum('season_stats__assists'),
            best_rating=Max('season_stats__rating'),
            seasons_count=Count('season_stats__season', distinct=True)
        ).prefetch_related('season_stats__team')

        if position_param and position_param != 'ALL':
            pos_up = position_param.upper()
            if pos_up == 'FORVET':
                legends_qs = legends_qs.filter(
                    Q(position__icontains='forvet') |
                    Q(position__icontains='santr') |
                    Q(position__icontains='kanat')
                )
            elif pos_up == 'ORTA':
                legends_qs = legends_qs.filter(
                    Q(position__icontains='orta') |
                    Q(position__icontains='on numara') |
                    Q(position__icontains='önlibero')
                )
            elif pos_up == 'DEFANS':
                legends_qs = legends_qs.filter(
                    Q(position__icontains='stoper') |
                    Q(position__icontains='bek') |
                    Q(position__icontains='defans')
                )
            elif pos_up == 'KALECI':
                legends_qs = legends_qs.filter(position__icontains='kaleci')
            else:
                legends_qs = legends_qs.filter(position__icontains=position_param)

        if search_query:
            legends_qs = legends_qs.filter(
                Q(name__icontains=search_query) |
                Q(position__icontains=search_query) |
                Q(nationality__icontains=search_query)
            )

        sorted_legends = sorted(
            legends_qs,
            key=lambda x: (
                x.total_goals or 0,
                x.total_matches or 0,
                x.seasons_count or 0,
                float(x.best_rating or 8.0)
            ),
            reverse=True
        )

        data = []
        for p in sorted_legends[:150]:
            prominent_team = None
            if p.season_stats.exists():
                team_counts = Counter(st.team for st in p.season_stats.all() if st.team)
                if team_counts:
                    prominent_team = team_counts.most_common(1)[0][0]
            if not prominent_team:
                prominent_team = p.current_team

            data.append({
                'id': p.id,
                'name': p.name,
                'display_name': p.name,
                'position': p.position,
                'age': p.age,
                'nationality': p.nationality,
                'jersey_number': p.jersey_number,
                'market_value': p.market_value,
                'image_url': p.image_url or 'https://img.a.transfermarkt.technology/portrait/header/default.jpg',
                'is_active': p.is_active,
                'is_legend': True,
                'team_id': prominent_team.id if prominent_team else None,
                'team_name': prominent_team.name if prominent_team else 'Süper Lig Efsanesi',
                'team_short_name': prominent_team.short_name if prominent_team else 'EFS',
                'team_logo': prominent_team.logo_url if prominent_team else '',
                'season_name': 'Tüm Zamanlar',
                'career_matches': p.total_matches or 0,
                'career_goals': p.total_goals or 0,
                'career_assists': p.total_assists or 0,
                'season_matches': p.total_matches or 0,
                'season_goals': p.total_goals or 0,
                'season_assists': p.total_assists or 0,
                'season_rating': float(p.best_rating) if p.best_rating else 8.5,
                'rating': float(p.best_rating) if p.best_rating else 8.5,
                'era_badge': 'Tüm Zamanlar',
            })

        return Response(data)


@extend_schema_view(
    list=extend_schema(
        tags=['5. Oyuncu Sezon İstatistikleri'],
        summary="Oyuncu Sezon İstatistiklerini Listele",
        parameters=[
            OpenApiParameter(name='player', type=int, required=False, description='Oyuncu ID'),
            OpenApiParameter(name='season', type=int, required=False, description='Sezon ID'),
            OpenApiParameter(name='team', type=int, required=False, description='Takım ID'),
        ]
    ),
    retrieve=extend_schema(tags=['5. Oyuncu Sezon İstatistikleri'], summary="İstatistik Detayı"),
    create=extend_schema(tags=['5. Oyuncu Sezon İstatistikleri'], summary="Yeni Sezon İstatistiği Ekle"),
    update=extend_schema(tags=['5. Oyuncu Sezon İstatistikleri'], summary="İstatistik Güncelle"),
    partial_update=extend_schema(tags=['5. Oyuncu Sezon İstatistikleri'], summary="İstatistik Kısmi Güncelle"),
    destroy=extend_schema(tags=['5. Oyuncu Sezon İstatistikleri'], summary="İstatistik Sil"),
)
class PlayerSeasonStatsViewSet(viewsets.ModelViewSet):
    """
    Oyuncu Sezon İstatistikleri CRUD (GET, POST, PUT, PATCH, DELETE)
    """
    queryset = PlayerSeasonStats.objects.select_related('player', 'season', 'team')
    serializer_class = PlayerSeasonStatsSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        qs = super().get_queryset()
        player_id = self.request.query_params.get('player')
        season_id = self.request.query_params.get('season')
        team_id = self.request.query_params.get('team')

        if player_id:
            qs = qs.filter(player_id=player_id)
        if season_id:
            qs = qs.filter(season_id=season_id)
        if team_id:
            if team_id.isdigit():
                qs = qs.filter(team_id=team_id)
            else:
                qs = qs.filter(
                    Q(team__short_name__iexact=team_id) |
                    Q(team__name__icontains=team_id)
                )
        return qs


@extend_schema_view(
    list=extend_schema(
        tags=['6. Transfer Takip'],
        summary="Transferleri Listele (Gelen / Giden / Lig İçi)",
        parameters=[
            OpenApiParameter(name='type', type=str, required=False, description='Transfer Türü: INCOMING (Gelen), OUTGOING (Giden), DOMESTIC (Lig İçi)'),
            OpenApiParameter(name='team', type=str, required=False, description='Takım ID veya Kısa Adı (Örn: 1 veya GS)'),
            OpenApiParameter(name='season', type=int, required=False, description='Sezon ID'),
            OpenApiParameter(name='search', type=str, required=False, description='Oyuncu veya takım adı arama')
        ]
    ),
    retrieve=extend_schema(tags=['6. Transfer Takip'], summary="Transfer Detayı"),
    create=extend_schema(tags=['6. Transfer Takip'], summary="Yeni Transfer Ekle"),
    update=extend_schema(tags=['6. Transfer Takip'], summary="Transfer Güncelle"),
    partial_update=extend_schema(tags=['6. Transfer Takip'], summary="Transfer Kısmi Güncelle"),
    destroy=extend_schema(tags=['6. Transfer Takip'], summary="Transfer Sil"),
)
class TransferViewSet(viewsets.ModelViewSet):
    """
    Transfer CRUD (GET, POST, PUT, PATCH, DELETE)
    """
    queryset = Transfer.objects.select_related('player', 'from_team', 'to_team', 'season')
    serializer_class = TransferSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ['player__name', 'from_team__name', 'to_team__name', 'details']

    def get_queryset(self):
        qs = super().get_queryset()
        transfer_type = self.request.query_params.get('type')
        season_id = self.request.query_params.get('season')
        team_param = self.request.query_params.get('team')

        if transfer_type:
            qs = qs.filter(transfer_type__iexact=transfer_type)

        if season_id:
            if str(season_id).lower() != 'all':
                s_obj = Season.objects.filter(name=season_id).first()
                if not s_obj and str(season_id).isdigit():
                    s_obj = Season.objects.filter(id=int(season_id)).first() or Season.objects.filter(start_year=int(season_id)).first()
                if not s_obj:
                    norm = str(season_id).replace('-', '/')
                    s_obj = Season.objects.filter(name__icontains=norm).first()
                if s_obj:
                    qs = qs.filter(season=s_obj)
                else:
                    qs = qs.filter(Q(season__name__icontains=season_id) | Q(season__start_year__icontains=season_id))
        else:
            current_season = Season.get_active_season()
            if current_season:
                qs = qs.filter(season=current_season)
        if team_param:
            if team_param.isdigit():
                qs = qs.filter(Q(to_team_id=team_param) | Q(from_team_id=team_param))
            else:
                team_obj = Team.objects.filter(Q(short_name__iexact=team_param) | Q(name__iexact=team_param)).first()
                if team_obj:
                    qs = qs.filter(Q(to_team=team_obj) | Q(from_team=team_obj))
                else:
                    qs = qs.filter(
                        Q(to_team__short_name__iexact=team_param) |
                        Q(from_team__short_name__iexact=team_param) |
                        Q(to_team__name__icontains=team_param) |
                        Q(from_team__name__icontains=team_param)
                    )

        return qs.order_by('-is_new', '-transfer_date', '-transfer_fee', 'id')


@extend_schema_view(
    list=extend_schema(
        tags=['7. Puan Durumu'],
        summary="Puan Durumunu Listele",
        parameters=[
            OpenApiParameter(name='season', type=int, required=False, description='Sezon ID (Varsayılan: Aktif Sezon)')
        ]
    ),
    retrieve=extend_schema(tags=['7. Puan Durumu'], summary="Puan Durumu Satır Detayı"),
    create=extend_schema(tags=['7. Puan Durumu'], summary="Puan Durumuna Takım Ekle"),
    update=extend_schema(tags=['7. Puan Durumu'], summary="Puan Durumu Güncelle"),
    partial_update=extend_schema(tags=['7. Puan Durumu'], summary="Puan Durumu Kısmi Güncelle"),
    destroy=extend_schema(tags=['7. Puan Durumu'], summary="Puan Durumundan Sil"),
)
class LeagueStandingViewSet(viewsets.ModelViewSet):
    """
    Puan Durumu CRUD (GET, POST, PUT, PATCH, DELETE)
    """
    queryset = LeagueStanding.objects.select_related('team', 'season').order_by('rank', '-points', '-goal_difference')
    serializer_class = LeagueStandingSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        qs = super().get_queryset()
        season_param = self.request.query_params.get('season')
        if season_param:
            season_match = Season.objects.filter(name=season_param).first()
            if not season_match and str(season_param).isdigit():
                season_match = Season.objects.filter(id=int(season_param)).first()
            if not season_match and str(season_param).isdigit():
                season_match = Season.objects.filter(start_year=int(season_param)).first()
            if season_match:
                return qs.filter(season=season_match)
            return qs.none()
        
        current_season = Season.get_active_season()
        if current_season:
            return qs.filter(season=current_season)
        return qs


@extend_schema_view(
    list=extend_schema(tags=['13. Scout / Favoriler'], summary="Giriş Yapan Kullanıcının Scout Listesi"),
    retrieve=extend_schema(tags=['13. Scout / Favoriler'], summary="Scout Notu Detayı"),
    create=extend_schema(tags=['13. Scout / Favoriler'], summary="Oyuncuyu Scout / Favori Listesine Ekle"),
    update=extend_schema(tags=['13. Scout / Favoriler'], summary="Scout Notu / Puanını Güncelle"),
    partial_update=extend_schema(tags=['13. Scout / Favoriler'], summary="Scout Notu / Puanını Kısmi Güncelle"),
    destroy=extend_schema(tags=['13. Scout / Favoriler'], summary="Oyuncuyu Scout Listesinden Çıkar"),
)
class ScoutListViewSet(viewsets.ModelViewSet):
    """
    Kullanıcı Scout / Favori Oyuncu Listesi CRUD (GET, POST, PUT, PATCH, DELETE)
    Giriş yapan kullanıcı kendi scout listesini tam yönetir.
    """
    queryset = ScoutList.objects.all()
    serializer_class = ScoutListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return ScoutList.objects.none()
        return ScoutList.objects.filter(user=self.request.user).select_related('player__current_team').order_by('-created_at')

    def perform_create(self, serializer):
        player = serializer.validated_data.get('player')
        ScoutList.objects.filter(user=self.request.user, player=player).delete()
        serializer.save(user=self.request.user)

    @extend_schema(
        tags=['13. Scout / Favoriler'],
        summary="Oyuncuyu Favorilere Ekle / Çıkar (Toggle)",
        description="Giriş yapan kullanıcının favori listesinde oyuncu varsa çıkarır, yoksa ekler."
    )
    @action(detail=False, methods=['post'])
    def toggle(self, request):
        player_id = request.data.get('player')
        if not player_id:
            return Response({"error": "Oyuncu ID (player) zorunludur."}, status=status.HTTP_400_BAD_REQUEST)
        player = Player.objects.filter(id=player_id).first()
        if not player:
            return Response({"error": "Oyuncu bulunamadı."}, status=status.HTTP_404_NOT_FOUND)

        existing = ScoutList.objects.filter(user=request.user, player=player)
        if existing.exists():
            existing.delete()
            return Response({
                "action": "removed",
                "player_id": player.id,
                "message": f"{player.name} favorilerinizden çıkarıldı."
            }, status=status.HTTP_200_OK)

        note = request.data.get('note') or f"{player.name} favorilere eklendi."
        rating = int(request.data.get('rating') or 9)
        created_item = ScoutList.objects.create(
            user=request.user,
            player=player,
            note=note,
            rating=rating
        )
        return Response({
            "action": "added",
            "player_id": player.id,
            "item": ScoutListSerializer(created_item).data,
            "message": f"{player.name} başarıyla favorilerinize eklendi!"
        }, status=status.HTTP_201_CREATED)

    @extend_schema(
        tags=['13. Scout / Favoriler'],
        summary="Oyuncu Bildirim Tercihlerini Güncelle",
        description="Favori oyuncunun ilk 11, gol, asist ve kart bildirim izinlerini günceller."
    )
    @action(detail=False, methods=['patch'])
    def preferences(self, request):
        player_id = request.data.get('player')
        if not player_id:
            return Response({"error": "player ID zorunludur."}, status=status.HTTP_400_BAD_REQUEST)
        scout_item = ScoutList.objects.filter(user=request.user, player_id=player_id).first()
        if not scout_item:
            return Response({"error": "Oyuncu favori listenizde bulunamadı."}, status=status.HTTP_404_NOT_FOUND)

        for field in ['notify_starting_11', 'notify_goals', 'notify_assists', 'notify_cards']:
            if field in request.data:
                setattr(scout_item, field, bool(request.data[field]))
        scout_item.save()
        return Response({
            "status": "updated",
            "item": ScoutListSerializer(scout_item).data,
            "message": f"{scout_item.player.name} bildirim tercihleri güncellendi."
        })


# ==========================================
# 2.B FAVORİ TAKIMLAR & BİLDİRİM YÖNETİMİ
# ==========================================

@extend_schema_view(
    list=extend_schema(tags=['13. Scout / Favoriler'], summary="Favori Takım Listesi"),
    create=extend_schema(tags=['13. Scout / Favoriler'], summary="Takımı Favorilere Ekle"),
    retrieve=extend_schema(tags=['13. Scout / Favoriler'], summary="Favori Takım Detayı"),
    partial_update=extend_schema(tags=['13. Scout / Favoriler'], summary="Takım Bildirim Tercihlerini Güncelle"),
    destroy=extend_schema(tags=['13. Scout / Favoriler'], summary="Takımı Favorilerden Çıkar"),
)
class FavoriteTeamViewSet(viewsets.ModelViewSet):
    """
    Kullanıcının favori takım listesi ve Maçkolik tarzı bildirim tercihleri.
    """
    queryset = FavoriteTeam.objects.all()
    serializer_class = FavoriteTeamSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return FavoriteTeam.objects.none()
        return FavoriteTeam.objects.filter(user=self.request.user).select_related('team').order_by('-created_at')

    def perform_create(self, serializer):
        team = serializer.validated_data.get('team')
        FavoriteTeam.objects.filter(user=self.request.user, team=team).delete()
        serializer.save(user=self.request.user)

    @extend_schema(
        tags=['13. Scout / Favoriler'],
        summary="Takımı Favorilere Ekle / Çıkar (Toggle)",
        description="Giriş yapan kullanıcının favori listesinde takım varsa çıkarır, yoksa ekler."
    )
    @action(detail=False, methods=['post'])
    def toggle(self, request):
        team_id = request.data.get('team')
        if not team_id:
            return Response({"error": "Takım ID (team) zorunludur."}, status=status.HTTP_400_BAD_REQUEST)
        team = Team.objects.filter(id=team_id).first()
        if not team:
            return Response({"error": "Takım bulunamadı."}, status=status.HTTP_404_NOT_FOUND)

        existing = FavoriteTeam.objects.filter(user=request.user, team=team)
        if existing.exists():
            existing.delete()
            return Response({
                "action": "removed",
                "team_id": team.id,
                "message": f"{team.name} favori takımlarınızdan çıkarıldı."
            }, status=status.HTTP_200_OK)

        item = FavoriteTeam.objects.create(
            user=request.user,
            team=team,
            notify_match_start=bool(request.data.get('notify_match_start', True)),
            notify_goals=bool(request.data.get('notify_goals', True)),
            notify_cards=bool(request.data.get('notify_cards', False)),
            notify_lineups=bool(request.data.get('notify_lineups', True)),
        )
        return Response({
            "action": "added",
            "team_id": team.id,
            "item": FavoriteTeamSerializer(item).data,
            "message": f"{team.name} favori takımlarınıza eklendi!"
        }, status=status.HTTP_201_CREATED)

    @extend_schema(
        tags=['13. Scout / Favoriler'],
        summary="Takım Bildirim Tercihlerini Güncelle",
        description="Favori takımın gol, maç başlangıcı, ilk 11 ve kırmızı kart bildirim izinlerini günceller."
    )
    @action(detail=False, methods=['patch'])
    def preferences(self, request):
        team_id = request.data.get('team')
        if not team_id:
            return Response({"error": "team ID zorunludur."}, status=status.HTTP_400_BAD_REQUEST)
        fav = FavoriteTeam.objects.filter(user=request.user, team_id=team_id).first()
        if not fav:
            return Response({"error": "Takım favori listenizde bulunamadı."}, status=status.HTTP_404_NOT_FOUND)

        for field in ['notify_match_start', 'notify_goals', 'notify_cards', 'notify_lineups']:
            if field in request.data:
                setattr(fav, field, bool(request.data[field]))
        fav.save()
        return Response({
            "status": "updated",
            "item": FavoriteTeamSerializer(fav).data,
            "message": f"{fav.team.name} bildirim tercihleri güncellendi."
        })


# ==========================================
# 2.C PUSH TOKEN CİHAZ KAYIT & BİLDİRİM KUTUSU
# ==========================================

class DeviceRegistrationView(APIView):
    """
    Mobil uygulamanın Expo Push Token'ını kaydettiği endpoint.
    Giriş yapmış kullanıcıya bağlar (veya misafir cihaz olarak kaydeder).
    """
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        token = request.data.get('expo_push_token')
        if not token:
            return Response({"error": "expo_push_token zorunludur."}, status=status.HTTP_400_BAD_REQUEST)

        platform = request.data.get('platform', 'android')
        device_name = request.data.get('device_name', '')
        user = request.user if request.user and request.user.is_authenticated else None

        dev, created = UserDevice.objects.update_or_create(
            expo_push_token=token,
            defaults={
                'user': user,
                'platform': platform,
                'device_name': device_name,
                'is_active': True,
                'updated_at': timezone.now()
            }
        )
        return Response({
            "status": "registered",
            "device_id": dev.id,
            "created": created,
            "message": "Cihaz push bildirim servisine başarıyla kaydedildi."
        }, status=status.HTTP_200_OK)


class NotificationInboxViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Kullanıcının geçmiş bildirim kutusu (Notification Center).
    Giriş yapan kullanıcının kendi bildirimlerini ve genel maç duyurularını getirir.
    """
    serializer_class = NotificationLogSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return NotificationLog.objects.none()
        u = self.request.user
        if u and u.is_authenticated:
            return NotificationLog.objects.filter(Q(user=u) | Q(user__isnull=True)).order_by('-created_at')[:50]
        return NotificationLog.objects.filter(user__isnull=True).order_by('-created_at')[:30]

    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def mark_all_read(self, request):
        NotificationLog.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return Response({"status": "ok", "message": "Tüm bildirimler okundu olarak işaretlendi."})

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        notif = self.get_object()
        notif.is_read = True
        notif.save(update_fields=['is_read'])
        return Response({"status": "ok", "message": "Bildirim okundu."})

    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        u = request.user
        if u and u.is_authenticated:
            cnt = NotificationLog.objects.filter(user=u, is_read=False).count()
        else:
            cnt = 0
        return Response({"unread_count": cnt})


class TestNotificationView(APIView):
    """
    Maçkolik bildirim simülatörü.
    Test amaçlı canlı gol, asist veya ilk 11 bildirimi oluşturup telefonunuza basar.
    """
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        evt_type = request.data.get('type', 'GOAL').upper()
        player_name = request.data.get('player_name', 'Victor Osimhen')
        assist_name = request.data.get('assist_name', 'Barış Alper Yılmaz')
        minute = request.data.get('minute', 34)

        # Aktif veya ilk fikstürü bul
        fix = Fixture.objects.filter(is_live=True).first() or Fixture.objects.first()
        if not fix:
            return Response({"error": "Sistemde test edilecek fikstür bulunamadı."}, status=status.HTTP_404_NOT_FOUND)

        if evt_type == 'GOAL':
            event_data = {
                'scorer': player_name,
                'assist': assist_name,
                'minute': minute,
                'is_penalty': request.data.get('is_penalty', False),
                'is_own_goal': False,
                'team_short': fix.home_team.short_name or 'GS'
            }
            res = dispatch_match_goal_notification(fix, event_data, target_user=request.user if request.user.is_authenticated else None)
            return Response({
                "status": "success",
                "message": f"⚽ {player_name} için test gol bildirimi fırlatıldı!",
                "data": res
            })
        elif evt_type == 'LINEUP':
            pl = Player.objects.filter(name__icontains=player_name.split()[-1]).first() or Player.objects.first()
            team = pl.current_team if pl and pl.current_team else fix.home_team
            res = dispatch_lineup_notification(fix, pl, team, target_user=request.user if request.user.is_authenticated else None)
            return Response({
                "status": "success",
                "message": f"📋 {pl.name} için test ilk 11 bildirimi fırlatıldı!",
                "data": res
            })
        else:
            return Response({"error": "Geçersiz event_type (GOAL veya LINEUP desteklenir)"}, status=status.HTTP_400_BAD_REQUEST)


# ==========================================
# 3. ÖZEL İŞ MANTIĞI & ANALİZ SERVİSLERİ
# ==========================================

class LeaderboardsView(APIView):
    """
    Lig İstatistikleri (İçinde bulunulan sezonda gol, asist, kilit pas vb. sıralama)
    Her yeni sezonda otomatik olarak güncel sezonun istatistik liderlerini listeler.
    """
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        tags=['9. Lig İstatistikleri & Liderler'],
        summary="Sezon İstatistik Liderleri (Gol, Asist, Kilit Pas)",
        description="İçinde bulunulan veya seçilen sezondaki gol, asist, kilit pas, şut, pas isabeti, maç puanı liderlerini döner.",
        parameters=[
            OpenApiParameter(name='season', type=int, required=False, description='Sezon ID (Varsayılan: Aktif Sezon)'),
            OpenApiParameter(name='limit', type=int, required=False, description='Her kategorideki oyuncu limiti (Varsayılan: 10)'),
        ],
        responses={200: OpenApiTypes.OBJECT}
    )
    def get(self, request):
        season_id = request.query_params.get('season')
        if not season_id:
            active_season = Season.get_active_season()
            season_id = active_season.name if active_season else '2026/2027'
        limit = int(request.query_params.get('limit', 10))

        if season_id:
            season = Season.objects.filter(name=season_id).first()
            if not season and str(season_id).isdigit():
                season = Season.objects.filter(id=int(season_id)).first()
            if not season and str(season_id).isdigit():
                season = Season.objects.filter(start_year=int(season_id)).first()
        else:
            season = Season.get_active_season()

        if not season:
            return Response({"error": "Henüz kayıtlı sezon bulunmuyor."}, status=status.HTTP_404_NOT_FOUND)

        qs = PlayerSeasonStats.objects.filter(season=season).select_related('player', 'team')

        top_scorers = qs.filter(goals__gt=0).order_by('-goals', '-assists')[:limit]
        top_assists = qs.filter(assists__gt=0).order_by('-assists', '-goals')[:limit]
        top_key_passes = qs.filter(key_passes__gt=0).order_by('-key_passes', '-key_passes_per_game')[:limit]
        top_shots = qs.filter(shots_per_game__gt=0).order_by('-shots_per_game')[:limit]
        top_pass_accuracy = qs.filter(pass_accuracy__gt=0, matches__gte=3).order_by('-pass_accuracy')[:limit]
        top_ratings = qs.filter(rating__gt=0, matches__gte=3).order_by('-rating')[:limit]
        top_dribbles = qs.filter(dribbles_per_game__gt=0).order_by('-dribbles_per_game')[:limit]

        return Response({
            "season": {
                "id": season.id,
                "name": season.name,
                "is_current": season.is_current,
                "start_year": season.start_year,
                "end_year": season.end_year
            },
            "leaders": {
                "top_scorers": PlayerSeasonStatsSerializer(top_scorers, many=True).data,
                "top_assists": PlayerSeasonStatsSerializer(top_assists, many=True).data,
                "top_key_passes": PlayerSeasonStatsSerializer(top_key_passes, many=True).data,
                "top_shots": PlayerSeasonStatsSerializer(top_shots, many=True).data,
                "top_pass_accuracy": PlayerSeasonStatsSerializer(top_pass_accuracy, many=True).data,
                "top_ratings": PlayerSeasonStatsSerializer(top_ratings, many=True).data,
                "top_dribbles": PlayerSeasonStatsSerializer(top_dribbles, many=True).data,
            }
        })


class PlayerComparisonView(APIView):
    """
    2. Fotoğraftaki Oyuncu Karşılaştırma ve Algoritmik Analiz Servisi
    Örnek: /api/compare/?player1=1&player2=2&season=1
    """
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        tags=['10. Oyuncu Karşılaştırma & Algoritmik Analiz'],
        summary="2 Oyuncuyu Karşılaştır ve Algoritmik Analiz Üret",
        description="Seçilen iki oyuncunun (güncel veya efsane) istatistik barlarını, radar niteliklerini ve dinamik algoritmik analiz cümlesini döner.",
        parameters=[
            OpenApiParameter(name='player1', type=int, required=False, description='1. Oyuncu ID (Boş bırakılırsa ilk aktif oyuncu seçilir)'),
            OpenApiParameter(name='player2', type=int, required=False, description='2. Oyuncu ID (Boş bırakılırsa ikinci aktif oyuncu seçilir)'),
            OpenApiParameter(name='season', type=int, required=False, description='Sezon ID (Opsiyonel, varsayılan: aktif/en son sezon)'),
        ],
        responses={200: OpenApiTypes.OBJECT}
    )
    def get(self, request):
        p1_id = request.query_params.get('player1')
        p2_id = request.query_params.get('player2')
        season_id = request.query_params.get('season')
        if not season_id:
            active_season = Season.get_active_season()
            season_id = active_season.name if active_season else '2026/2027'

        # 1. Oyuncuyu çözümle (Girilen ID yoksa varsayılan olarak Osimhen veya ilk aktif forvete geç)
        p1 = None
        if p1_id:
            try:
                p1 = Player.objects.filter(id=int(p1_id)).first()
            except (ValueError, TypeError):
                p1 = None

        if not p1:
            p1 = Player.objects.filter(name__icontains='Osimhen').first() or Player.objects.filter(is_active=True).first()

        # 2. Oyuncuyu çözümle (Girilen ID yoksa varsayılan olarak ligin golcü santraforuna geç)
        p2 = None
        if p2_id:
            try:
                p2 = Player.objects.filter(id=int(p2_id)).first()
            except (ValueError, TypeError):
                p2 = None

        if not p2 or (p1 and p2.id == p1.id):
            p2 = Player.objects.filter(is_active=True, name__icontains='Muriqi').first()
            if not p2:
                p2 = Player.objects.filter(is_active=True, name__icontains='Vlahovic').first()
            if not p2 and p1:
                p2 = Player.objects.exclude(id=p1.id).filter(is_active=True, position='Santrafor').first()
            if not p2 and p1:
                p2 = Player.objects.exclude(id=p1.id).filter(is_active=True).first()

        if not p1 or not p2:
            return Response(
                {"error": "Karşılaştırılacak oyuncular sistemde bulunamadı."},
                status=status.HTTP_404_NOT_FOUND
            )

        result = compare_players(p1.id, p2.id, season_id)
        if not result:
            return Response(
                {"error": "Karşılaştırma analizi üretilemedi."},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response(result)


class HomeSummaryView(APIView):
    """
    1. Fotoğraftaki Ana Sayfa menüleri ve özet sayaçları
    """
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        tags=['11. Ana Sayfa Gösterge Paneli'],
        summary="Ana Sayfa Sayaçları ve Özet Verisi",
        description="1. fotoğraftaki menülerin sayaçları, güncel sezon ve lig lideri takım özeti.",
        responses={200: OpenApiTypes.OBJECT}
    )
    def get(self, request):
        current_season = Season.get_active_season()
        super_lig_teams = Team.objects.filter(is_super_lig=True)
        active_players_count = Player.objects.filter(is_active=True, is_legend=False).count()
        legend_players_count = Player.objects.filter(is_legend=True).count()
        if current_season:
            incoming_transfers_count = Transfer.objects.filter(season=current_season, transfer_type='INCOMING').count()
            outgoing_transfers_count = Transfer.objects.filter(season=current_season, transfer_type='OUTGOING').count()
        else:
            incoming_transfers_count = Transfer.objects.filter(transfer_type='INCOMING').count()
            outgoing_transfers_count = Transfer.objects.filter(transfer_type='OUTGOING').count()

        leader = None
        if current_season:
            top_team_standing = LeagueStanding.objects.filter(season=current_season, rank=1).select_related('team').first()
            if top_team_standing:
                leader = {
                    "team_name": top_team_standing.team.name,
                    "points": top_team_standing.points,
                    "logo": top_team_standing.team.logo_url
                }

        return Response({
            "season": current_season.name if current_season else "Belirtilmemiş",
            "super_lig_teams_count": super_lig_teams.count(),
            "active_players_count": active_players_count,
            "legend_players_count": legend_players_count,
            "incoming_transfers_count": incoming_transfers_count,
            "outgoing_transfers_count": outgoing_transfers_count,
            "league_leader": leader
        })


def recalculate_season_standings(season):
    """
    Belirli bir sezonun tüm puan cetvelini kurallara göre (Puan, Averaj, Atılan Gol)
    yeniden sıralar ve rank sütununu 1'den N'ye günceller.
    """
    standings = list(LeagueStanding.objects.filter(season=season).order_by('-points', '-goal_difference', '-goals_for', 'team__name'))
    for idx, standing in enumerate(standings, start=1):
        if standing.rank != idx:
            standing.rank = idx
            standing.save(update_fields=['rank'])
    return standings


# ==========================================
# 8. MAÇLAR & FİKSTÜR & CANLI SKOR VIEWSET (API-FOOTBALL)
# ==========================================

@extend_schema_view(
    list=extend_schema(
        tags=['8. Maçlar & Fikstür & Canlı Skor (API-Football)'],
        summary="Fikstür ve Maçları Listele",
        description="Süper Lig maçlarını haftaya, takıma veya duruma göre filtreleyerek listeler.",
        parameters=[
            OpenApiParameter('round_number', OpenApiTypes.INT, description="Hafta Numarası (örn: 10)"),
            OpenApiParameter('team', OpenApiTypes.INT, description="Takım ID"),
            OpenApiParameter('is_live', OpenApiTypes.BOOL, description="Sadece canlı maçlar (true/false)"),
            OpenApiParameter('status', OpenApiTypes.STR, description="Durum kodu (NS, FT, LIVE)")
        ]
    ),
    retrieve=extend_schema(
        tags=['8. Maçlar & Fikstür & Canlı Skor (API-Football)'],
        summary="Maç Detayı",
        description="Belirli bir maçın skor, stadyum, hakem ve durum detaylarını getirir."
    ),
    create=extend_schema(tags=['8. Maçlar & Fikstür & Canlı Skor (API-Football)'], summary="Yeni Maç Ekle"),
    update=extend_schema(tags=['8. Maçlar & Fikstür & Canlı Skor (API-Football)'], summary="Maç Güncelle"),
    partial_update=extend_schema(tags=['8. Maçlar & Fikstür & Canlı Skor (API-Football)'], summary="Maç Kısmi Güncelle"),
    destroy=extend_schema(tags=['8. Maçlar & Fikstür & Canlı Skor (API-Football)'], summary="Maç Sil")
)
class FixtureViewSet(viewsets.ModelViewSet):
    queryset = Fixture.objects.select_related('home_team', 'away_team', 'season').all()
    serializer_class = FixtureSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['home_team__name', 'away_team__name', 'venue', 'referee']
    ordering_fields = ['match_date', 'round_number']
    ordering = ['match_date', 'round_number']

    def get_queryset(self):
        qs = super().get_queryset()
        
        season_param = self.request.query_params.get('season')
        if season_param:
            if season_param.isdigit():
                qs = qs.filter(season_id=season_param)
            else:
                qs = qs.filter(season__name=season_param)
        else:
            active_season = Season.get_active_season()
            if active_season and qs.filter(season=active_season).exists():
                qs = qs.filter(season=active_season)

        round_num = self.request.query_params.get('round_number')
        if round_num:
            qs = qs.filter(round_number=round_num)

        team_id = self.request.query_params.get('team')
        if team_id:
            if team_id.isdigit():
                qs = qs.filter(Q(home_team_id=team_id) | Q(away_team_id=team_id))
            else:
                team_obj = Team.objects.filter(Q(short_name__iexact=team_id) | Q(name__iexact=team_id)).first()
                if team_obj:
                    qs = qs.filter(Q(home_team=team_obj) | Q(away_team=team_obj))
                else:
                    qs = qs.filter(
                        Q(home_team__short_name__iexact=team_id) |
                        Q(away_team__short_name__iexact=team_id) |
                        Q(home_team__name__icontains=team_id) |
                        Q(away_team__name__icontains=team_id)
                    )

        is_live = self.request.query_params.get('is_live')
        if is_live is not None:
            qs = qs.filter(is_live=is_live.lower() in ('true', '1'))

        status_param = self.request.query_params.get('status')
        if status_param:
            qs = qs.filter(status=status_param.upper())

        return qs

    @extend_schema(
        tags=['8. Maçlar & Fikstür & Canlı Skor (API-Football)'],
        summary="Şu Anda Oynanan Canlı Maçlar",
        description="Canlı skor, anlık dakika ve maç durumunu API-Football üzerinden döner.",
        responses={200: FixtureSerializer(many=True)}
    )
    @action(detail=False, methods=['get'])
    def live(self, request):
        APIFootballService.ensure_background_poller()
        APIFootballService.fetch_and_sync_live_scores()
        live_matches = self.get_queryset().filter(is_live=True)
        serializer = self.get_serializer(live_matches, many=True)
        resp = Response(serializer.data)
        resp['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        resp['Pragma'] = 'no-cache'
        resp['Expires'] = '0'
        return resp

    @extend_schema(
        tags=['8. Maçlar & Fikstür & Canlı Skor (API-Football)'],
        summary="Güncel Haftanın Maçları",
        description="İçinde bulunulan aktif haftanın (örn: 10. Hafta) tüm fikstürünü döner.",
        responses={200: FixtureSerializer(many=True)}
    )
    @action(detail=False, methods=['get'])
    def current_round(self, request):
        latest_fixture = self.get_queryset().filter(status__in=['1H', '2H', 'HT', 'FT']).order_by('-round_number', '-match_date').first()
        active_round = latest_fixture.round_number if latest_fixture else 10
        round_matches = self.get_queryset().filter(round_number=active_round)
        serializer = self.get_serializer(round_matches, many=True)
        return Response({
            "round_number": active_round,
            "round_name": f"{active_round}. Hafta",
            "fixtures": serializer.data
        })

    @extend_schema(
        tags=['8. Maçlar & Fikstür & Canlı Skor (API-Football)'],
        summary="Maçı Bitir (MS) ve İstatistikleri Anında Güncelle",
        description="Maçı MS (Maç Sonu) olarak tamamlar; Puan Durumu (LeagueStanding) tablosunu ve oyuncu sezon istatistiklerini derhal günceller."
    )
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def finish_match(self, request, pk=None):
        fixture = self.get_object()
        force = request.data.get('force', False)
        
        home_score = request.data.get('home_score')
        away_score = request.data.get('away_score')
        
        if home_score is not None:
            fixture.home_score = int(home_score)
        elif fixture.home_score is None:
            fixture.home_score = 0
            
        if away_score is not None:
            fixture.away_score = int(away_score)
        elif fixture.away_score is None:
            fixture.away_score = 0

        was_already_ft = (fixture.status == 'FT')
        
        fixture.status = 'FT'
        fixture.status_display = 'MS'
        fixture.is_live = False
        fixture.elapsed_minute = 90
        fixture.save()
        
        season = fixture.season
        home_team = fixture.home_team
        away_team = fixture.away_team
        
        # Puan durumu güncelleme
        if not was_already_ft or force:
            home_standing, _ = LeagueStanding.objects.get_or_create(
                season=season, team=home_team,
                defaults={'rank': 1, 'played': 0, 'won': 0, 'drawn': 0, 'lost': 0, 'goals_for': 0, 'goals_against': 0, 'points': 0}
            )
            away_standing, _ = LeagueStanding.objects.get_or_create(
                season=season, team=away_team,
                defaults={'rank': 2, 'played': 0, 'won': 0, 'drawn': 0, 'lost': 0, 'goals_for': 0, 'goals_against': 0, 'points': 0}
            )
            
            home_standing.played += 1
            away_standing.played += 1
            home_standing.goals_for += fixture.home_score
            home_standing.goals_against += fixture.away_score
            away_standing.goals_for += fixture.away_score
            away_standing.goals_against += fixture.home_score
            
            if fixture.home_score > fixture.away_score:
                home_standing.won += 1
                home_standing.points += 3
                away_standing.lost += 1
            elif fixture.home_score < fixture.away_score:
                away_standing.won += 1
                away_standing.points += 3
                home_standing.lost += 1
            else:
                home_standing.drawn += 1
                home_standing.points += 1
                away_standing.drawn += 1
                away_standing.points += 1
                
            home_standing.save()
            away_standing.save()
            
            # Puan cetveli sıralamasını güncelle
            recalculate_season_standings(season)
            
            # Oyuncuların maç sayılarını artır
            PlayerSeasonStats.objects.filter(season=season, team=home_team).update(matches=F('matches') + 1)
            PlayerSeasonStats.objects.filter(season=season, team=away_team).update(matches=F('matches') + 1)
            
            # Özel golcüler veya asistçiler gönderildiyse güncelle
            scorers_data = request.data.get('scorers', [])
            for s in scorers_data:
                p_id = s.get('player_id')
                goals_to_add = s.get('goals', 0)
                assists_to_add = s.get('assists', 0)
                if p_id:
                    stat = PlayerSeasonStats.objects.filter(season=season, player_id=p_id).first()
                    if stat:
                        if goals_to_add:
                            stat.goals += int(goals_to_add)
                        if assists_to_add:
                            stat.assists += int(assists_to_add)
                        stat.save()

        updated_standings = LeagueStanding.objects.filter(season=season).order_by('rank', '-points', '-goal_difference')
        standings_data = LeagueStandingSerializer(updated_standings, many=True).data

        return Response({
            "status": "success",
            "message": f"{fixture.home_team.name} {fixture.home_score} - {fixture.away_score} {fixture.away_team.name} maçı tamamlandı (MS)! Puan tablosu ve oyuncu istatistikleri başarıyla güncellendi.",
            "fixture": FixtureSerializer(fixture).data,
            "standings": standings_data
        }, status=status.HTTP_200_OK)

    @extend_schema(
        tags=['8. Maçlar & Fikstür & Canlı Skor (API-Football)'],
        summary="Canlı Skor / Maç Olayı Simülasyonu",
        description="Canlı maça gol ekler, dakikayı ilerletir veya maç durumunu değiştirir."
    )
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def update_live(self, request, pk=None):
        fixture = self.get_object()
        action_type = request.data.get('action')
        minute = request.data.get('minute')
        
        if minute is not None:
            fixture.elapsed_minute = int(minute)
            fixture.status_display = f"CANLI ({fixture.elapsed_minute}')"
            
        if action_type == 'goal_home':
            fixture.home_score = (fixture.home_score or 0) + 1
            fixture.is_live = True
            fixture.status = 'LIVE'
            fixture.status_display = f"CANLI ({fixture.elapsed_minute or 75}')"
        elif action_type == 'goal_away':
            fixture.away_score = (fixture.away_score or 0) + 1
            fixture.is_live = True
            fixture.status = 'LIVE'
            fixture.status_display = f"CANLI ({fixture.elapsed_minute or 75}')"
        elif action_type == 'advance_minute':
            current_min = fixture.elapsed_minute or 74
            new_min = min(current_min + 5, 90)
            fixture.elapsed_minute = new_min
            if new_min >= 90:
                fixture.status_display = "90+3' (Son Anlar)"
            else:
                fixture.status_display = f"CANLI ({new_min}')"
        elif action_type == 'start_live':
            fixture.is_live = True
            fixture.status = '1H'
            fixture.elapsed_minute = 1
            fixture.home_score = fixture.home_score or 0
            fixture.away_score = fixture.away_score or 0
            fixture.status_display = "CANLI (1')"
            
        fixture.save()
        return Response({
            "status": "success",
            "fixture": FixtureSerializer(fixture).data
        })

    @extend_schema(
        tags=['8. Maçlar & Fikstür & Canlı Skor (API-Football)'],
        summary="Maçkolik Canlı Skor ve Hafta Özeti",
        description="Maçkolik tarzı canlı maçlar, biten maçlar ve fikstür özetini tek ekranda döner."
    )
    @action(detail=False, methods=['get'])
    def live_summary(self, request):
        import time as _time
        APIFootballService.ensure_background_poller()

        season_param = request.query_params.get('season')
        season = None
        if season_param:
            season = Season.objects.filter(name=season_param).first()
        if not season:
            season = Season.get_active_season() or Season.objects.first()

        force_sync = request.query_params.get('force') in ('1', 'true')
        synced_live = APIFootballService.sync_real_espn_live_scoreboard(season, force=force_sync)

        qs = Fixture.objects.filter(season=season).select_related('home_team', 'away_team')
        if not synced_live:
            APIFootballService._refresh_clock_based_live_states(qs)

        round_param = request.query_params.get('round')
        if round_param == 'ALL':
            current_round = 'ALL'
        elif round_param and round_param.isdigit():
            current_round = int(round_param)
        else:
            live_first = qs.filter(is_live=True).order_by('match_date').first()
            if live_first:
                current_round = live_first.round_number
            else:
                ist_tz = ZoneInfo('Europe/Istanbul')
                now_ist = timezone.now().astimezone(ist_tz)
                next_ns = qs.filter(status='NS', match_date__gte=now_ist - timedelta(hours=3)).order_by('match_date').first()
                if next_ns:
                    current_round = next_ns.round_number
                else:
                    latest = qs.filter(status__in=['1H', '2H', 'HT', 'FT', 'LIVE']).order_by('-round_number').first()
                    current_round = latest.round_number if latest else 11

        ist_tz = ZoneInfo('Europe/Istanbul')
        now_ist = timezone.now().astimezone(ist_tz)
        active_fixture = qs.filter(is_live=True).order_by('match_date').first()
        if not active_fixture:
            active_fixture = qs.filter(status='NS', match_date__gte=now_ist - timedelta(hours=3)).order_by('match_date').first()
        active_round = active_fixture.round_number if active_fixture else 11

        all_rounds = list(qs.values_list('round_number', flat=True).distinct().order_by('round_number'))
        if not all_rounds:
            all_rounds = list(range(1, 39))

        max_round_num = max(all_rounds) if all_rounds else 38
        if current_round == 'ALL':
            round_fixtures = qs.order_by('round_number', 'match_date')
            round_name = f"Tüm Sezon Fikstürü (1-{max_round_num}. Hafta)"
        else:
            round_fixtures = qs.filter(round_number=current_round).order_by('match_date')
            round_name = f"{current_round}. Hafta"

        live_fixtures = qs.filter(is_live=True).order_by('match_date')

        resp = Response({
            "season_name": season.name if season else "2026/2027",
            "current_round": current_round,
            "active_round": active_round,
            "round_name": round_name,
            "all_rounds": all_rounds,
            "server_time_ms": int(_time.time() * 1000),
            "live_fixtures": FixtureSerializer(live_fixtures, many=True).data,
            "round_fixtures": FixtureSerializer(round_fixtures, many=True).data
        })
        resp['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        resp['Pragma'] = 'no-cache'
        resp['Expires'] = '0'
        return resp


# ==========================================
# 12. VERİ ENTEGRASYONU & OTOMASYON (API SYNC)
# ==========================================

class SyncTransfersView(APIView):
    """
    Transfer Takip ekranındaki '🔄 API ile Güncelle' butonu için endpoint.
    Transfermarkt web scraping yaparak Süper Lig'in yeni transferlerini veritabanına aktarır.
    """
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        tags=['12. Veri Entegrasyonu & Otomasyon'],
        summary="Transferleri Transfermarkt'tan Güncelle (Scraping)",
        description="Mobil uygulamadaki '🔄 API ile Güncelle' butonu için Transfermarkt web scraping servisini çalıştırarak en güncel transferleri sisteme kaydeder.",
        request=None,
        responses={200: SyncResponseSerializer}
    )
    def post(self, request):
        transfers = TransfermarktScraper.scrape_super_lig_transfers()
        return Response({
            "status": "success",
            "message": f"Transfermarkt üzerinden {len(transfers)} transfer başarıyla senkronize edildi.",
            "count": len(transfers),
            "source": "Transfermarkt (Web Scraping)",
            "timestamp": timezone.now()
        }, status=status.HTTP_200_OK)


class SyncSquadsView(APIView):
    """
    Transfermarkt üzerinden kulüplerin resmi kadrolarını ve piyasa değerlerini günceller.
    """
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        tags=['12. Veri Entegrasyonu & Otomasyon'],
        summary="Kulüp Kadrolarını Transfermarkt'tan Güncelle",
        description="Süper Lig takımlarının oyuncularını, forma numaralarını, piyasa değerlerini ve fotoğraflarını çeker.",
        parameters=[
            OpenApiParameter('team_id', OpenApiTypes.INT, description="Tek bir takımın kadrosunu güncellemek için takım ID (opsiyonel)")
        ],
        request=None,
        responses={200: SyncResponseSerializer}
    )
    def post(self, request):
        team_id = request.query_params.get('team_id')
        if team_id:
            team = Team.objects.filter(id=team_id).first()
            if not team:
                return Response({"error": "Takım bulunamadı."}, status=status.HTTP_404_NOT_FOUND)
            players = TransfermarktScraper.scrape_team_squad(team)
            return Response({
                "status": "success",
                "message": f"{team.name} için {len(players)} aktif oyuncu kadrosu güncellendi.",
                "count": len(players),
                "source": "Transfermarkt + Mackolik (Canlı Kadro Farkı)",
                "timestamp": timezone.now()
            }, status=status.HTTP_200_OK)

        summary = TransfermarktScraper.sync_live_squads_with_diff()
        total_players = summary.get('active_players_upserted', 0)
        return Response({
            "status": "success",
            "message": f"Canlı kadro farkı ile {total_players} aktif oyuncu güncellendi.",
            "count": total_players,
            "summary": summary,
            "source": "Transfermarkt + Mackolik (Canlı Kadro Farkı)",
            "timestamp": timezone.now()
        }, status=status.HTTP_200_OK)


class SyncAttributesView(APIView):
    """
    WhoScored ve SofaScore analitiği ile oyuncuların güçlü/zayıf yönlerini ve radar grafiklerini günceller.
    """
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        tags=['12. Veri Entegrasyonu & Otomasyon'],
        summary="Radar ve Güçlü/Zayıf Yönleri Güncelle (SofaScore / WhoScored)",
        description="Oyuncuların hız, şut, pas, teknik, defans, fizik değerlerini ve güçlü/zayıf özelliklerini SofaScore/WhoScored standartlarında günceller.",
        request=None,
        responses={200: SyncResponseSerializer}
    )
    def post(self, request):
        count = PlayerAnalyticsService.sync_all_players_attributes()
        return Response({
            "status": "success",
            "message": f"SofaScore ve WhoScored analitiği ile {count} oyuncunun radar ve yetenek özellikleri güncellendi.",
            "count": count,
            "source": "SofaScore / WhoScored Analytics",
            "timestamp": timezone.now()
        }, status=status.HTTP_200_OK)


class SyncFixturesView(APIView):
    """
    API-Football (RapidAPI) üzerinden Süper Lig fikstürü, canlı skorları ve puan durumunu günceller.
    """
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        tags=['12. Veri Entegrasyonu & Otomasyon'],
        summary="Fikstür ve Canlı Skorları Güncelle (API-Football RapidAPI)",
        description="API-Football (RapidAPI) servisine bağlanarak Süper Lig maç fikstürünü, maç sonuçlarını ve canlı skorları senkronize eder.",
        request=None,
        responses={200: SyncResponseSerializer}
    )
    def post(self, request):
        fixtures = APIFootballService.fetch_and_sync_fixtures()
        return Response({
            "status": "success",
            "message": f"API-Football (RapidAPI) üzerinden {len(fixtures)} maç fikstürü senkronize edildi.",
            "count": len(fixtures),
            "source": "API-Football (RapidAPI)",
            "timestamp": timezone.now()
        }, status=status.HTTP_200_OK)


class SyncAllView(APIView):
    """
    Tek tıkla tüm entegrasyonları (Transfermarkt, SofaScore/WhoScored, API-Football) sırayla çalıştırır.
    """
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        tags=['12. Veri Entegrasyonu & Otomasyon'],
        summary="Tüm Veri Kaynaklarını Tek Tıkla Senkronize Et",
        description="1. Transfermarkt (Kulüpler, Kadrolar, Transferler) -> 2. SofaScore/WhoScored (Radar ve Yetenekler) -> 3. API-Football (Fikstür ve Canlı Skor) zincirini otomatik çalıştırır.",
        request=None,
        responses={200: SyncResponseSerializer}
    )
    def post(self, request):
        TransfermarktScraper.scrape_super_lig_teams()
        squad_summary = TransfermarktScraper.sync_live_squads_with_diff()
        transfers = TransfermarktScraper.scrape_super_lig_transfers()
        attr_count = PlayerAnalyticsService.sync_all_players_attributes()
        fixtures = APIFootballService.fetch_and_sync_fixtures()

        return Response({
            "status": "success",
            "message": "Tüm entegrasyonlar (Transfermarkt, Mackolik, Analitik, API-Football) başarıyla tamamlandı.",
            "summary": {
                "squads_synced": squad_summary.get("active_players_upserted", 0),
                "detached_to_legends": squad_summary.get("detached_to_legends", 0),
                "transfers_synced": len(transfers),
                "player_attributes_synced": attr_count,
                "fixtures_synced": len(fixtures)
            },
            "source": "Transfermarkt + Mackolik + Analitik + API-Football",
            "timestamp": timezone.now()
        }, status=status.HTTP_200_OK)


def app_view(request):
    """
    Süper Lig Analiz & Scout Mobil Uygulama Canlı Arayüzü (Web SPA & Mobile Emulator)
    """
    return render(request, 'index.html')


