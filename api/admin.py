from django.contrib import admin
from .models import (
    Season, Team, LeagueStanding, Player, PlayerAttribute,
    PlayerSeasonStats, Transfer, ScoutList, Fixture
)


@admin.register(Season)
class SeasonAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_year', 'end_year', 'is_current')
    list_filter = ('is_current',)
    search_fields = ('name',)


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'short_name', 'city', 'stadium', 'manager', 'market_value', 'is_super_lig')
    list_filter = ('is_super_lig', 'city')
    search_fields = ('name', 'short_name', 'manager')


@admin.register(LeagueStanding)
class LeagueStandingAdmin(admin.ModelAdmin):
    list_display = ('season', 'rank', 'team', 'points', 'played', 'won', 'drawn', 'lost', 'goals_for', 'goals_against', 'goal_difference')
    list_filter = ('season', 'team')
    search_fields = ('team__name', 'season__name')
    ordering = ('season', 'rank')


class PlayerAttributeInline(admin.StackedInline):
    model = PlayerAttribute
    can_delete = False


class PlayerSeasonStatsInline(admin.TabularInline):
    model = PlayerSeasonStats
    extra = 1


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ('name', 'current_team', 'position', 'age', 'nationality', 'market_value', 'is_active', 'is_legend')
    list_filter = ('current_team', 'position', 'is_active', 'is_legend')
    search_fields = ('name', 'nationality')
    inlines = [PlayerAttributeInline, PlayerSeasonStatsInline]


@admin.register(PlayerSeasonStats)
class PlayerSeasonStatsAdmin(admin.ModelAdmin):
    list_display = ('player', 'season', 'team', 'matches', 'goals', 'assists', 'rating', 'shots_per_game', 'key_passes')
    list_filter = ('season', 'team')
    search_fields = ('player__name', 'team__name')


@admin.register(Transfer)
class TransferAdmin(admin.ModelAdmin):
    list_display = ('player', 'from_team', 'to_team', 'transfer_type', 'contract_type', 'transfer_fee', 'transfer_date', 'is_new')
    list_filter = ('transfer_type', 'contract_type', 'season', 'is_new')
    search_fields = ('player__name', 'from_team__name', 'to_team__name')


@admin.register(ScoutList)
class ScoutListAdmin(admin.ModelAdmin):
    list_display = ('user', 'player', 'rating', 'created_at')
    list_filter = ('rating', 'user')
    search_fields = ('player__name', 'user__username', 'note')


@admin.register(Fixture)
class FixtureAdmin(admin.ModelAdmin):
    list_display = ('round_name', 'home_team', 'home_score', 'away_score', 'away_team', 'status_display', 'match_date', 'is_live')
    list_filter = ('season', 'round_number', 'status', 'is_live')
    search_fields = ('home_team__name', 'away_team__name', 'venue')

