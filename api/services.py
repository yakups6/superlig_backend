from decimal import Decimal
from django.db.models import F, Q
from .models import Player, PlayerSeasonStats, PlayerAttribute, Season


def get_player_stats_for_season(player, season_id=None):
    """
    Oyuncunun belirtilen sezondaki veya en son/aktif sezondaki istatistiğini döner.
    """
    stats_qs = PlayerSeasonStats.objects.filter(player=player)
    if season_id:
        if str(season_id).isdigit():
            stats = stats_qs.filter(season_id=int(season_id)).first()
        else:
            stats = stats_qs.filter(season__name=str(season_id)).first()
        if stats:
            return stats
        return None

    # Önce dinamik aktif sezonu dene
    active_season = Season.get_active_season()
    if active_season:
        active_stat = stats_qs.filter(season=active_season).first()
        if active_stat:
            return active_stat

    # Aktif sezonda yoksa en son sezonu al
    return stats_qs.order_by('-season__start_year').first()


def generate_algorithmic_analysis(p1, s1, a1, p2, s2, a2):
    """
    İki oyuncunun istatistikleri ve radar özelliklerine göre
    2. fotoğraftaki gibi algoritmik analiz cümlesi ve içgörüler üretir.
    Örn: "Algoritmik Analiz: Osimhen ceza sahası etkinliğinde %24 daha verimli."
    """
    insights = []
    headline = ""

    # 1. Gol ve Bitiricilik / Ceza Sahası Etkinliği
    g1 = s1.goals if s1 else 0
    g2 = s2.goals if s2 else 0
    m1 = s1.matches if s1 and s1.matches > 0 else 1
    m2 = s2.matches if s2 and s2.matches > 0 else 1
    
    gpg1 = g1 / m1
    gpg2 = g2 / m2

    if gpg1 > 0 or gpg2 > 0:
        if gpg1 > gpg2:
            pct = int(round(((gpg1 - gpg2) / (gpg2 if gpg2 > 0 else 0.5)) * 100))
            pct = min(pct, 85) # Gerçekçi üst sınır
            headline = f"{p1.name} ceza sahası etkinliğinde ve gol üretkenliğinde %{pct} daha verimli."
            insights.append(f"{p1.name}, maç başına {gpg1:.2f} gol ortalamasıyla {p2.name} ({gpg2:.2f}) karşısında hücum sonlandırmada önde.")
        elif gpg2 > gpg1:
            pct = int(round(((gpg2 - gpg1) / (gpg1 if gpg1 > 0 else 0.5)) * 100))
            pct = min(pct, 85)
            headline = f"{p2.name} ceza sahası etkinliğinde ve gol üretkenliğinde %{pct} daha verimli."
            insights.append(f"{p2.name}, maç başına {gpg2:.2f} gol ortalamasıyla {p1.name} ({gpg1:.2f}) karşısında hücum sonlandırmada önde.")

    # 2. Pas ve Oyun Kurma / Kilit Pas
    kp1 = s1.key_passes_per_game if s1 else 0.0
    kp2 = s2.key_passes_per_game if s2 else 0.0
    pa1 = s1.pass_accuracy if s1 else 0.0
    pa2 = s2.pass_accuracy if s2 else 0.0

    if kp1 > kp2 and kp1 > 0:
        insights.append(f"{p1.name}, maç başına {kp1} kilit pas ile rakip savunma arkasına sarkmada daha yaratıcı.")
    elif kp2 > kp1 and kp2 > 0:
        insights.append(f"{p2.name}, maç başına {kp2} kilit pas ile rakip savunma arkasına sarkmada daha yaratıcı.")

    # 3. Şut ve Tehlike Yaratma
    spg1 = s1.shots_per_game if s1 else 0.0
    spg2 = s2.shots_per_game if s2 else 0.0
    if spg1 > spg2 and spg1 > 0:
        diff_pct = int(round(((spg1 - spg2) / (spg2 if spg2 > 0 else 1.0)) * 100))
        insights.append(f"{p1.name}, maç başına şut denemelerinde (%{diff_pct} farkla) kaleyi daha sık yokluyor.")
    elif spg2 > spg1 and spg2 > 0:
        diff_pct = int(round(((spg2 - spg1) / (spg1 if spg1 > 0 else 1.0)) * 100))
        insights.append(f"{p2.name}, maç başına şut denemelerinde (%{diff_pct} farkla) kaleyi daha sık yokluyor.")

    # 4. Fiziksel ve Radar Nitelikleri
    if a1 and a2:
        if a1.physical > a2.physical + 5:
            insights.append(f"{p1.name}, ikili mücadelelerde ve hava topu üstünlüğünde fizik gücüyle (%{a1.physical} vs %{a2.physical}) avantajlı.")
        elif a2.physical > a1.physical + 5:
            insights.append(f"{p2.name}, ikili mücadelelerde ve hava topu üstünlüğünde fizik gücüyle (%{a2.physical} vs %{a1.physical}) avantajlı.")

        if a1.pace > a2.pace + 5:
            insights.append(f"{p1.name}, açık alanda ve kontra atak geçişlerinde sprint süratiyle fark yaratıyor.")
        elif a2.pace > a1.pace + 5:
            insights.append(f"{p2.name}, açık alanda ve kontra atak geçişlerinde sprint süratiyle fark yaratıyor.")

    if not headline:
        headline = f"{p1.name} ve {p2.name} dengeli profil sergiliyor; takım kurgusuna göre farklı roller üstleniyorlar."

    if not insights:
        insights.append("Her iki oyuncu da benzer taktiksel disiplin ve hücum parametrelerine sahip.")

    return {
        "headline": f"Algoritmik Analiz: {headline}",
        "insights": insights
    }


def compare_players(player1_id, player2_id, season_id=None):
    """
    İki oyuncuyu (güncel veya eski efsane) karşılaştırır.
    2. fotoğraftaki Veri Analizi & Karşılaştırma ekranı için tam JSON üretir.
    """
    try:
        p1 = Player.objects.select_related('current_team').prefetch_related('attributes').get(id=player1_id)
        p2 = Player.objects.select_related('current_team').prefetch_related('attributes').get(id=player2_id)
    except Player.DoesNotExist:
        return None

    s1 = get_player_stats_for_season(p1, season_id)
    s2 = get_player_stats_for_season(p2, season_id)

    a1 = getattr(p1, 'attributes', None)
    a2 = getattr(p2, 'attributes', None)

    # Karşılaştırma metrikleri hesaplama (Barlar için)
    def calc_bar(v1, v2):
        total = float(v1 + v2)
        if total == 0:
            return {"val1": v1, "val2": v2, "pct1": 50.0, "pct2": 50.0}
        p1_rate = round((float(v1) / total) * 100, 1)
        p2_rate = round((float(v2) / total) * 100, 1)
        return {"val1": v1, "val2": v2, "pct1": p1_rate, "pct2": p2_rate}

    comparison_bars = {
        "goals": {
            "label": "Gol",
            **calc_bar(s1.goals if s1 else 0, s2.goals if s2 else 0)
        },
        "assists": {
            "label": "Asist",
            **calc_bar(s1.assists if s1 else 0, s2.assists if s2 else 0)
        },
        "matches": {
            "label": "Maç Sayısı",
            **calc_bar(s1.matches if s1 else 0, s2.matches if s2 else 0)
        },
        "shots_per_game": {
            "label": "Şut / Maç",
            **calc_bar(s1.shots_per_game if s1 else 0.0, s2.shots_per_game if s2 else 0.0)
        },
        "pass_accuracy": {
            "label": "Pas İsabeti (%)",
            **calc_bar(s1.pass_accuracy if s1 else 0.0, s2.pass_accuracy if s2 else 0.0)
        },
        "key_passes_per_game": {
            "label": "Kilit Pas / Maç",
            **calc_bar(s1.key_passes_per_game if s1 else 0.0, s2.key_passes_per_game if s2 else 0.0)
        },
        "rating": {
            "label": "Reyting",
            **calc_bar(s1.rating if s1 else 6.0, s2.rating if s2 else 6.0)
        }
    }

    # Radar Karşılaştırma Verileri
    radar = {
        "categories": ["Hız (Pace)", "Şut (Shooting)", "Pas (Passing)", "Teknik (Dribbling)", "Savunma (Defending)", "Fizik (Physical)"],
        "player1": [
            a1.pace if a1 else 60,
            a1.shooting if a1 else 60,
            a1.passing if a1 else 60,
            a1.dribbling if a1 else 60,
            a1.defending if a1 else 50,
            a1.physical if a1 else 60,
        ],
        "player2": [
            a2.pace if a2 else 60,
            a2.shooting if a2 else 60,
            a2.passing if a2 else 60,
            a2.dribbling if a2 else 60,
            a2.defending if a2 else 50,
            a2.physical if a2 else 60,
        ]
    }

    # Algoritmik Analiz Cümlesi
    algo_analysis = generate_algorithmic_analysis(p1, s1, a1, p2, s2, a2)

    return {
        "player1": {
            "id": p1.id,
            "name": p1.name,
            "team_name": s1.team.name if (s1 and s1.team) else (p1.current_team.name if p1.current_team else "Serbest"),
            "team_short": s1.team.short_name if (s1 and s1.team) else (p1.current_team.short_name if p1.current_team else ""),
            "team_short_name": s1.team.short_name if (s1 and s1.team) else (p1.current_team.short_name if p1.current_team else ""),
            "team_logo": s1.team.logo_url if (s1 and s1.team) else (p1.current_team.logo_url if p1.current_team else None),
            "position": p1.position,
            "age": p1.age,
            "nationality": p1.nationality,
            "jersey_number": p1.jersey_number,
            "image_url": p1.image_url,
            "market_value": str(s1.market_value if (s1 and s1.market_value) else (p1.market_value or 0)),
            "season_name": s1.season.name if (s1 and s1.season) else "2026/2027",
            "matches": s1.matches if s1 else 0,
            "goals": s1.goals if s1 else 0,
            "assists": s1.assists if s1 else 0,
            "rating": s1.rating if s1 else 6.0,
        },
        "player2": {
            "id": p2.id,
            "name": p2.name,
            "team_name": s2.team.name if (s2 and s2.team) else (p2.current_team.name if p2.current_team else "Serbest"),
            "team_short": s2.team.short_name if (s2 and s2.team) else (p2.current_team.short_name if p2.current_team else ""),
            "team_short_name": s2.team.short_name if (s2 and s2.team) else (p2.current_team.short_name if p2.current_team else ""),
            "team_logo": s2.team.logo_url if (s2 and s2.team) else (p2.current_team.logo_url if p2.current_team else None),
            "position": p2.position,
            "age": p2.age,
            "nationality": p2.nationality,
            "jersey_number": p2.jersey_number,
            "image_url": p2.image_url,
            "market_value": str(s2.market_value if (s2 and s2.market_value) else (p2.market_value or 0)),
            "season_name": s2.season.name if (s2 and s2.season) else "2026/2027",
            "matches": s2.matches if s2 else 0,
            "goals": s2.goals if s2 else 0,
            "assists": s2.assists if s2 else 0,
            "rating": s2.rating if s2 else 6.0,
        },
        "bars": comparison_bars,
        "radar": radar,
        "algorithmic_analysis": algo_analysis
    }
