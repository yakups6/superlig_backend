from decimal import Decimal
from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from drf_spectacular.utils import extend_schema_field
from django.db import models
from django.db.models import Q, Sum
from .models import (
    Season, Team, LeagueStanding, Player, PlayerAttribute,
    PlayerSeasonStats, Transfer, ScoutList, Fixture,
    FavoriteTeam, UserDevice, NotificationLog
)


# ==========================================
# 1. KULLANICI & KİMLİK DOĞRULAMA (AUTH)
# ==========================================

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'date_joined']
        read_only_fields = ['id', 'date_joined']


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password', 'password2']

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Şifreler birbiriyle eşleşmiyor."})
        email_val = (attrs.get('email') or '').strip()
        if email_val and User.objects.filter(email__iexact=email_val).exists():
            raise serializers.ValidationError({"email": "Bu e-posta adresi zaten kullanımda."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            password=validated_data['password']
        )
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True, help_text="Kullanıcı adı")
    password = serializers.CharField(required=True, write_only=True, help_text="Şifre")


class TokenPairSerializer(serializers.Serializer):
    refresh = serializers.CharField(read_only=True)
    access = serializers.CharField(read_only=True)


class AuthResponseSerializer(serializers.Serializer):
    message = serializers.CharField(read_only=True)
    user = UserSerializer(read_only=True)
    tokens = TokenPairSerializer(read_only=True)


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])


# ==========================================
# 2. SEZON SERIALIZER
# ==========================================

class SeasonSerializer(serializers.ModelSerializer):
    short_code = serializers.CharField(read_only=True)

    class Meta:
        model = Season
        fields = ['id', 'name', 'short_code', 'start_year', 'end_year', 'start_date', 'end_date', 'is_current']


# ==========================================
# 3. OYUNCU ÖZELLİKLERİ & RADAR
# ==========================================

class PlayerAttributeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlayerAttribute
        fields = ['id', 'player', 'pace', 'shooting', 'passing', 'dribbling', 'defending', 'physical', 'strengths', 'weaknesses']
        extra_kwargs = {'player': {'required': False}}


# ==========================================
# 4. OYUNCU İSTATİSTİKLERİ & KADRO
# ==========================================

class PlayerSeasonStatsSerializer(serializers.ModelSerializer):
    season_name = serializers.CharField(source='season.name', read_only=True)
    team_name = serializers.CharField(source='team.name', read_only=True)
    team_short_name = serializers.CharField(source='team.short_name', read_only=True)
    team_logo = serializers.CharField(source='team.logo_url', read_only=True)
    player_name = serializers.CharField(source='player.name', read_only=True)
    player_age = serializers.IntegerField(source='player.age', read_only=True)
    player_nationality = serializers.CharField(source='player.nationality', read_only=True)
    player_image = serializers.CharField(source='player.image_url', read_only=True)
    player_position = serializers.CharField(source='player.position', read_only=True)
    market_value = serializers.SerializerMethodField()

    @extend_schema_field(serializers.DecimalField(max_digits=12, decimal_places=2))
    def get_market_value(self, obj):
        if obj.market_value is not None:
            return obj.market_value
        return obj.player.market_value

    class Meta:
        model = PlayerSeasonStats
        fields = [
            'id', 'player', 'player_name', 'player_age', 'player_nationality', 'player_image',
            'player_position', 'market_value', 'season', 'season_name', 'team', 'team_name',
            'team_short_name', 'team_logo', 'matches', 'minutes', 'goals', 'assists',
            'shots_per_game', 'pass_accuracy', 'key_passes', 'key_passes_per_game',
            'dribbles_per_game', 'yellow_cards', 'red_cards', 'rating', 'clean_sheets',
            'transfer_note'
        ]


class PlayerSimpleSerializer(serializers.ModelSerializer):
    team_name = serializers.CharField(source='current_team.name', read_only=True)
    team_short_name = serializers.CharField(source='current_team.short_name', read_only=True)
    team_logo = serializers.CharField(source='current_team.logo_url', read_only=True)

    class Meta:
        model = Player
        fields = [
            'id', 'name', 'current_team', 'team_name', 'team_short_name', 'team_logo',
            'position', 'age', 'nationality', 'jersey_number', 'market_value',
            'image_url', 'is_active', 'is_legend'
        ]


class PlayerDetailSerializer(serializers.ModelSerializer):
    team_name = serializers.CharField(source='current_team.name', read_only=True)
    team_short_name = serializers.CharField(source='current_team.short_name', read_only=True)
    team_logo = serializers.CharField(source='current_team.logo_url', read_only=True)
    attributes = PlayerAttributeSerializer(read_only=True)
    season_stats = PlayerSeasonStatsSerializer(many=True, read_only=True)

    class Meta:
        model = Player
        fields = [
            'id', 'name', 'current_team', 'team_name', 'team_short_name', 'team_logo',
            'position', 'age', 'nationality', 'jersey_number', 'market_value',
            'image_url', 'is_active', 'is_legend', 'attributes', 'season_stats'
        ]


# ==========================================
# 5. PUAN DURUMU & TAKIM
# ==========================================

class LeagueStandingSerializer(serializers.ModelSerializer):
    team_name = serializers.CharField(source='team.name', read_only=True)
    team_short_name = serializers.CharField(source='team.short_name', read_only=True)
    team_logo = serializers.CharField(source='team.logo_url', read_only=True)
    season_name = serializers.CharField(source='season.name', read_only=True)

    class Meta:
        model = LeagueStanding
        fields = [
            'id', 'season', 'season_name', 'team', 'team_name', 'team_short_name', 'team_logo',
            'rank', 'played', 'won', 'drawn', 'lost', 'goals_for', 'goals_against',
            'goal_difference', 'points'
        ]


class TeamListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = '__all__'


class TeamDetailSerializer(serializers.ModelSerializer):
    players = serializers.SerializerMethodField()
    standing = serializers.SerializerMethodField()
    season = serializers.SerializerMethodField()
    market_value = serializers.SerializerMethodField()

    class Meta:
        model = Team
        fields = [
            'id', 'name', 'short_name', 'city', 'stadium', 'manager',
            'market_value', 'logo_url', 'is_super_lig', 'league_name',
            'standing', 'players', 'season'
        ]

    def _get_target_season(self):
        request = self.context.get('request')
        if request:
            qp = getattr(request, 'query_params', getattr(request, 'GET', {}))
            season_param = qp.get('season')
            if season_param:
                target_season = Season.objects.filter(name=season_param).first()
                if not target_season and '/' in str(season_param):
                    parts = str(season_param).split('/')
                    if parts[0].isdigit():
                        target_season = Season.objects.filter(start_year=int(parts[0])).first()
                if not target_season and str(season_param).isdigit():
                    target_season = Season.objects.filter(id=int(season_param)).first()
                if not target_season and str(season_param).isdigit():
                    target_season = Season.objects.filter(start_year=int(season_param)).first()
                if target_season:
                    return target_season
        return Season.get_active_season()

    @extend_schema_field(serializers.DecimalField(max_digits=14, decimal_places=2, allow_null=True))
    def get_market_value(self, obj):
        target_season = self._get_target_season()
        if not target_season:
            return obj.market_value

        # Pre-2004 historical seasons had no Transfermarkt market valuations
        if target_season.start_year < 2004:
            return None

        # Modern active / current season (2024/2025+) uses authentic club valuation
        if target_season.start_year >= 2024 or target_season.is_current:
            return obj.market_value

        # For historical seasons between 2004 and 2023, calculate from player stats or standing
        stats_sum = PlayerSeasonStats.objects.filter(
            team=obj, season=target_season, market_value__gt=0
        ).aggregate(s=Sum('market_value'))['s']
        if stats_sum and stats_sum > 0:
            return stats_sum

        standing = LeagueStanding.objects.filter(team=obj, season=target_season).first()
        if standing:
            rank = standing.rank or 5
            year = target_season.start_year
            era_factor = max(0.2, min(1.0, (year - 2000) / 24.0))
            if rank == 1:
                base = 90000000 * era_factor
            elif rank <= 3:
                base = 65000000 * era_factor
            elif rank <= 6:
                base = 35000000 * era_factor
            elif rank <= 12:
                base = 20000000 * era_factor
            else:
                base = 10000000 * era_factor
            return Decimal(round(base, -5))
        return obj.market_value

    @extend_schema_field(SeasonSerializer)
    def get_season(self, obj):
        target_season = self._get_target_season()
        if target_season:
            return SeasonSerializer(target_season).data
        return None

    @extend_schema_field(LeagueStandingSerializer)
    def get_standing(self, obj):
        target_season = self._get_target_season()
        if target_season:
            standing = LeagueStanding.objects.filter(team=obj, season=target_season).first()
            if standing:
                return LeagueStandingSerializer(standing).data
        return None

    @extend_schema_field(PlayerSimpleSerializer(many=True))
    def get_players(self, obj):
        target_season = self._get_target_season()

        def _get_mv(item):
            try:
                return Decimal(str(item.get('market_value') or 0))
            except Exception:
                return Decimal(0)
        
        # O sezondaki mevcut PlayerSeasonStats kayıtlarını getir
        data = []
        seen_names = set()
        if target_season:
            qs = PlayerSeasonStats.objects.filter(team=obj, season=target_season).select_related('player')
            active_stats = qs.filter(Q(matches__gt=0) | ~Q(transfer_note=''))
            season_stats = active_stats if active_stats.count() >= 12 else qs
            
            is_historical = (target_season.start_year < 2004)
            if is_historical:
                sorted_stats = sorted(season_stats, key=lambda x: (x.goals or 0, x.assists or 0, x.matches or 0), reverse=True)
            else:
                sorted_stats = sorted(
                    season_stats,
                    key=lambda x: (Decimal(str(x.market_value if x.market_value is not None else (x.player.market_value or 0))), x.matches or 0),
                    reverse=True
                )
            for st in sorted_stats:
                norm_name = "".join(c for c in st.player.name.lower() if c.isalnum())
                for k, v in [('ı', 'i'), ('ğ', 'g'), ('ü', 'u'), ('ş', 's'), ('ö', 'o'), ('ç', 'c')]:
                    norm_name = norm_name.replace(k, v)
                if norm_name in seen_names:
                    continue
                seen_names.add(norm_name)

                p_dict = PlayerSimpleSerializer(st.player).data
                if st.transfer_note:
                    p_dict['transfer_note'] = st.transfer_note
                    p_dict['name'] = f"{st.player.name} {st.transfer_note}"
                    p_dict['display_name'] = f"{st.player.name} {st.transfer_note}"
                else:
                    p_dict['transfer_note'] = ''
                    p_dict['display_name'] = st.player.name

                p_dict['season_matches'] = st.matches
                p_dict['season_goals'] = st.goals
                p_dict['season_assists'] = st.assists
                p_dict['season_rating'] = st.rating
                p_dict['matches'] = st.matches
                p_dict['goals'] = st.goals
                p_dict['assists'] = st.assists
                p_dict['rating'] = st.rating
                # Sezonun gerçek piyasa değeri (tarihi sezonlar için None/0, modern için gerçek)
                if is_historical:
                    val = 0
                else:
                    val = st.market_value if st.market_value is not None else (st.player.market_value or 0)
                p_dict['market_value'] = str(val)
                data.append(p_dict)

        if target_season and target_season.start_year < 2004:
            data.sort(key=lambda x: (int(x.get('goals') or 0), int(x.get('assists') or 0), int(x.get('matches') or 0)), reverse=True)
        else:
            data.sort(key=_get_mv, reverse=True)
        return data


# ==========================================
# 6. TRANSFER SERIALIZER
# ==========================================

class TransferSerializer(serializers.ModelSerializer):
    player_name = serializers.CharField(source='player.name', read_only=True)
    player_image = serializers.CharField(source='player.image_url', read_only=True)
    player_position = serializers.CharField(source='player.position', read_only=True)
    from_team_name = serializers.SerializerMethodField()
    from_team_short_name = serializers.SerializerMethodField()
    from_team_logo = serializers.SerializerMethodField()
    to_team_name = serializers.SerializerMethodField()
    to_team_short_name = serializers.SerializerMethodField()
    to_team_logo = serializers.SerializerMethodField()
    transfer_type_display = serializers.CharField(source='get_transfer_type_display', read_only=True)
    contract_type_display = serializers.CharField(source='get_contract_type_display', read_only=True)
    season_name = serializers.CharField(source='season.name', read_only=True)

    def get_from_team_name(self, obj):
        return obj.from_team.name if obj.from_team else "Serbest"

    def get_from_team_short_name(self, obj):
        return obj.from_team.short_name if obj.from_team else "SER"

    def get_from_team_logo(self, obj):
        return obj.from_team.logo_url if obj.from_team else ""

    def get_to_team_name(self, obj):
        return obj.to_team.name if obj.to_team else "Serbest"

    def get_to_team_short_name(self, obj):
        return obj.to_team.short_name if obj.to_team else "SER"

    def get_to_team_logo(self, obj):
        return obj.to_team.logo_url if obj.to_team else ""

    class Meta:
        model = Transfer
        fields = [
            'id', 'player', 'player_name', 'player_image', 'player_position',
            'from_team', 'from_team_name', 'from_team_short_name', 'from_team_logo',
            'to_team', 'to_team_name', 'to_team_short_name', 'to_team_logo',
            'transfer_type', 'transfer_type_display', 'contract_type', 'contract_type_display',
            'transfer_fee', 'season', 'season_name', 'transfer_date', 'is_new', 'details'
        ]


# ==========================================
# 7. KULLANICI SCOUT / FAVORİ TAKİP LİSTESİ
# ==========================================

class ScoutListSerializer(serializers.ModelSerializer):
    player_details = PlayerSimpleSerializer(source='player', read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)
    note = serializers.CharField(required=False, allow_blank=True, default='Favori oyuncu')

    class Meta:
        model = ScoutList
        fields = [
            'id', 'user', 'user_username', 'player', 'player_details', 'note', 'rating',
            'notify_starting_11', 'notify_goals', 'notify_assists', 'notify_cards',
            'created_at'
        ]
        read_only_fields = ['id', 'user', 'user_username', 'created_at']


class FavoriteTeamSerializer(serializers.ModelSerializer):
    team_name = serializers.CharField(source='team.name', read_only=True)
    team_short_name = serializers.CharField(source='team.short_name', read_only=True)
    team_logo = serializers.CharField(source='team.logo_url', read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = FavoriteTeam
        fields = [
            'id', 'user', 'user_username', 'team', 'team_name', 'team_short_name',
            'team_logo', 'notify_match_start', 'notify_goals', 'notify_cards',
            'notify_lineups', 'created_at'
        ]
        read_only_fields = ['id', 'user', 'user_username', 'created_at']


class UserDeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserDevice
        fields = ['id', 'expo_push_token', 'platform', 'device_name', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


class NotificationLogSerializer(serializers.ModelSerializer):
    fixture_info = serializers.SerializerMethodField()

    def get_fixture_info(self, obj):
        if not obj.related_fixture:
            return None
        f = obj.related_fixture
        return {
            'id': f.id,
            'home': f.home_team.name if f.home_team else '',
            'away': f.away_team.name if f.away_team else '',
            'home_score': f.home_score,
            'away_score': f.away_score,
            'status': f.status,
            'round_name': f.round_name
        }

    class Meta:
        model = NotificationLog
        fields = [
            'id', 'user', 'title', 'body', 'notification_type',
            'related_fixture', 'related_team', 'related_player',
            'fixture_info', 'data_payload', 'is_read', 'created_at'
        ]
        read_only_fields = ['id', 'user', 'created_at']


# ==========================================
# 8. FİKSTÜR, MAÇLAR & CANLI SKOR SERIALIZER (API-FOOTBALL)
# ==========================================

class FixtureSerializer(serializers.ModelSerializer):
    home_team_name = serializers.CharField(source='home_team.name', read_only=True)
    home_team_short_name = serializers.CharField(source='home_team.short_name', read_only=True)
    home_team_logo = serializers.CharField(source='home_team.logo_url', read_only=True)
    away_team_name = serializers.CharField(source='away_team.name', read_only=True)
    away_team_short_name = serializers.CharField(source='away_team.short_name', read_only=True)
    away_team_logo = serializers.CharField(source='away_team.logo_url', read_only=True)
    season_name = serializers.CharField(source='season.name', read_only=True)
    status_display = serializers.SerializerMethodField()
    live_clock = serializers.SerializerMethodField()
    events = serializers.SerializerMethodField()

    def get_status_display(self, obj):
        import re
        from .integrations import APIFootballService

        if obj.status == 'FT':
            return 'MS'
        if obj.status == 'HT':
            return 'İY'
        if obj.is_live:
            raw = (obj.status_display or '').strip()
            if raw.upper() in ('DEVRE ARASI', 'HT', 'İY'):
                return 'İY'
            m_wrap = re.match(r'^CANLI\s*\((.+)\)$', raw, flags=re.IGNORECASE)
            if m_wrap:
                raw = m_wrap.group(1).strip()
            cleaned = APIFootballService.normalize_clock_label(raw)
            if cleaned:
                return cleaned
            return f"{obj.elapsed_minute or 1}'"
        if obj.status == 'NS':
            return APIFootballService.format_dynamic_ns_label(obj.match_date)
        return obj.status_display or 'Başlamadı'

    def get_live_clock(self, obj):
        if not obj.is_live:
            return None
        from .integrations import APIFootballService
        clk = APIFootballService.get_live_clock(obj.id)
        if clk:
            return clk
        if obj.status == 'HT':
            return {
                'phase': 'HT',
                'period': 1,
                'clock_seconds': 2700,
                'display_clock': 'İY',
            }
        elap = obj.elapsed_minute or (1 if obj.status == '1H' else 46)
        return {
            'phase': '2H' if obj.status == '2H' or elap > 45 else '1H',
            'period': 2 if obj.status == '2H' or elap > 45 else 1,
            'clock_seconds': max(0, (elap - 1) * 60),
            'display_clock': self.get_status_display(obj),
        }

    def get_events(self, obj):
        from .integrations import APIFootballService
        return APIFootballService.get_cached_events(obj.id)

    class Meta:
        model = Fixture
        fields = [
            'id', 'api_id', 'season', 'season_name', 'round_name', 'round_number',
            'home_team', 'home_team_name', 'home_team_short_name', 'home_team_logo',
            'away_team', 'away_team_name', 'away_team_short_name', 'away_team_logo',
            'home_score', 'away_score', 'match_date', 'status', 'status_display',
            'venue', 'referee', 'is_live', 'elapsed_minute', 'live_clock', 'events'
        ]


# ==========================================
# 9. VERİ ENTEGRASYON & SENKRONİZASYON YANIT SERIALIZER
# ==========================================

class SyncResponseSerializer(serializers.Serializer):
    status = serializers.CharField(help_text="İşlem durumu (success / error)")
    message = serializers.CharField(help_text="Açıklama mesajı")
    count = serializers.IntegerField(required=False, help_text="İşlenen / güncellenen kayıt sayısı")
    source = serializers.CharField(help_text="Veri kaynağı (Transfermarkt, SofaScore/WhoScored, API-Football)")
    timestamp = serializers.DateTimeField(help_text="Senkronizasyon zamanı")

