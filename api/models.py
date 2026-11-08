from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date


# 1. Sezon Tablosu
class Season(models.Model):
    name = models.CharField(max_length=20, unique=True, help_text="Örn: 2024/2025, 2026/2027")
    start_year = models.IntegerField(help_text="Başlangıç yılı (örn: 2026)")
    end_year = models.IntegerField(help_text="Bitiş yılı (örn: 2027)")
    start_date = models.DateField(null=True, blank=True, help_text="Sezon başlangıç tarihi (örn: 2026-08-01)")
    end_date = models.DateField(null=True, blank=True, help_text="Sezon bitiş tarihi (örn: 2027-06-30)")
    is_current = models.BooleanField(default=False, help_text="İçinde bulunulan aktif sezon mu?")

    @property
    def short_code(self):
        if '/' in self.name:
            parts = self.name.split('/')
            return f"{parts[0][-2:]}/{parts[1][-2:]}"
        elif '-' in self.name:
            parts = self.name.split('-')
            return f"{parts[0][-2:]}/{parts[1][-2:]}"
        return str(self.name)[-2:]

    class Meta:
        ordering = ['-start_year', '-end_year']
        verbose_name = "Sezon"
        verbose_name_plural = "Sezonlar"

    def __str__(self):
        return f"{self.name} {'(Aktif)' if self.is_current else ''}"

    def save(self, *args, **kwargs):
        # Eğer bu sezon aktif olarak işaretlendiyse diğerlerini false yap
        if self.is_current:
            Season.objects.filter(is_current=True).exclude(pk=self.pk).update(is_current=False)
        super().save(*args, **kwargs)

    @classmethod
    def get_active_season(cls):
        """
        Bugünün tarihine göre otomatik olarak aktif sezonu belirler ve döner.
        Bir sezonda takılı kalmaz; takvim ilerledikçe otomatik yeni sezona geçer.
        """
        today = timezone.now().date()
        
        # 1. Tarih aralığı eşleşen sezon var mı? (örn. 01.08.2026 - 30.06.2027 aralığında bugün)
        season = cls.objects.filter(start_date__lte=today, end_date__gte=today).first()
        
        # 2. Eğer kesin tarih aralığı bulunamadıysa, takvim yılı ve ayına göre hesapla:
        # Futbolda sezon Temmuz/Ağustos'ta başlar:
        if not season:
            if today.month >= 7:
                s_year, e_year = today.year, today.year + 1
            else:
                s_year, e_year = today.year - 1, today.year
            
            calc_name = f"{s_year}/{e_year}"
            season = cls.objects.filter(name=calc_name).first()
            if not season:
                season = cls.objects.filter(start_year=s_year).first()

        # 3. Eğer yine bulunamazsa, veritabanında is_current=True olanı veya en son eklenen sezonu al
        if not season:
            season = cls.objects.filter(is_current=True).first()
        if not season:
            season = cls.objects.order_by('-start_year').first()

        # Otomatik senkronizasyon: Eğer bulunan sezon aktif işaretli değilse, aktif yap
        if season and not season.is_current:
            cls.objects.exclude(id=season.id).update(is_current=False)
            season.is_current = True
            season.save(update_fields=['is_current'])

        return season


# 2. Takım Tablosu
class Team(models.Model):
    name = models.CharField(max_length=100)
    short_name = models.CharField(max_length=10, blank=True, help_text="Örn: GS, FB, BJK, TS")
    city = models.CharField(max_length=50, blank=True)
    stadium = models.CharField(max_length=100, blank=True)
    manager = models.CharField(max_length=100, blank=True)
    market_value = models.DecimalField(max_digits=14, decimal_places=2, default=0.00, help_text="Toplam Kadro Değeri (€)")
    logo_url = models.URLField(blank=True, null=True)
    is_super_lig = models.BooleanField(default=True, help_text="Süper Lig takımı mı yoksa transferdeki dış lig/yabancı takım mı?")
    league_name = models.CharField(max_length=100, default='Trendyol Süper Lig')

    class Meta:
        ordering = ['-is_super_lig', 'name']
        verbose_name = "Takım"
        verbose_name_plural = "Takımlar"

    def __str__(self):
        return self.name


# 3. Puan Durumu Tablosu
class LeagueStanding(models.Model):
    season = models.ForeignKey(Season, related_name='standings', on_delete=models.CASCADE)
    team = models.ForeignKey(Team, related_name='standings', on_delete=models.CASCADE)
    rank = models.PositiveIntegerField(default=1)
    played = models.PositiveIntegerField(default=0, help_text="Oynanan Maç (O)")
    won = models.PositiveIntegerField(default=0, help_text="Galibiyet (G)")
    drawn = models.PositiveIntegerField(default=0, help_text="Beraberlik (B)")
    lost = models.PositiveIntegerField(default=0, help_text="Mağlubiyet (M)")
    goals_for = models.PositiveIntegerField(default=0, help_text="Atılan Gol (AG)")
    goals_against = models.PositiveIntegerField(default=0, help_text="Yenilen Gol (YG)")
    goal_difference = models.IntegerField(default=0, help_text="Averaj (AV)")
    points = models.IntegerField(default=0, help_text="Puan (P)")

    class Meta:
        ordering = ['season', 'rank', '-points', '-goal_difference']
        unique_together = ('season', 'team')
        verbose_name = "Puan Durumu"
        verbose_name_plural = "Puan Durumları"

    def __str__(self):
        return f"{self.season.name} - {self.rank}. {self.team.name} ({self.points} P)"

    def save(self, *args, **kwargs):
        self.goal_difference = self.goals_for - self.goals_against
        if self.points is None:
            self.points = (self.won * 3) + (self.drawn * 1)
        if not self.played:
            self.played = self.won + self.drawn + self.lost
        super().save(*args, **kwargs)



# 4. Oyuncu Tablosu
class Player(models.Model):
    name = models.CharField(max_length=100)
    current_team = models.ForeignKey(Team, related_name='current_players', on_delete=models.SET_NULL, null=True, blank=True)
    position = models.CharField(max_length=50, help_text="Santrafor, Kanat, On Numara, Merkez Orta Saha, Stoper, Bek, Kaleci vb.")
    age = models.IntegerField(null=True, blank=True)
    nationality = models.CharField(max_length=50, blank=True)
    jersey_number = models.IntegerField(null=True, blank=True)
    market_value = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text="Piyasa Değeri (€)")
    image_url = models.URLField(blank=True, null=True)
    is_active = models.BooleanField(default=True, help_text="Aktif futbolcu mu?")
    is_legend = models.BooleanField(default=False, help_text="Eski / Efsane Süper Lig oyuncusu mu?")

    class Meta:
        ordering = ['name']
        verbose_name = "Oyuncu"
        verbose_name_plural = "Oyuncular"

    def __str__(self):
        team_str = f" ({self.current_team.short_name or self.current_team.name})" if self.current_team else ""
        return f"{self.name}{team_str}"


# 5. Oyuncu Radar Yetenekleri / Analitik Özellikleri (2. Fotoğraftaki Radar Grafiği İçin)
class PlayerAttribute(models.Model):
    player = models.OneToOneField(Player, related_name='attributes', on_delete=models.CASCADE)
    pace = models.IntegerField(default=70, help_text="Hız (0-100)")
    shooting = models.IntegerField(default=70, help_text="Şut / Bitiricilik (0-100)")
    passing = models.IntegerField(default=70, help_text="Pas Yeteneği (0-100)")
    dribbling = models.IntegerField(default=70, help_text="Dripling / Teknik (0-100)")
    defending = models.IntegerField(default=50, help_text="Savunma / Defans (0-100)")
    physical = models.IntegerField(default=70, help_text="Fizik Gücü (0-100)")
    strengths = models.TextField(blank=True, help_text="Güçlü yönler (örn: Ceza sahası bitiriciliği, Hava topları)")
    weaknesses = models.TextField(blank=True, help_text="Zayıf yönler (örn: Savunma desteği)")

    class Meta:
        verbose_name = "Oyuncu Özellikleri"
        verbose_name_plural = "Oyuncu Özellikleri"

    def __str__(self):
        return f"{self.player.name} - Özellikleri"


# 6. Oyuncu Sezonluk İstatistikleri (Eski ve Güncel Oyuncuların Sezon Sezon Verileri)
class PlayerSeasonStats(models.Model):
    player = models.ForeignKey(Player, related_name='season_stats', on_delete=models.CASCADE)
    season = models.ForeignKey(Season, related_name='player_stats', on_delete=models.CASCADE)
    team = models.ForeignKey(Team, related_name='team_player_stats', on_delete=models.CASCADE)
    
    matches = models.PositiveIntegerField(default=0, help_text="Oynadığı Maç")
    market_value = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, help_text="O Sezonki Piyasa Değeri (€)")
    minutes = models.PositiveIntegerField(default=0, help_text="Toplam Dakika")
    goals = models.PositiveIntegerField(default=0, help_text="Gol Sayısı")
    assists = models.PositiveIntegerField(default=0, help_text="Asist Sayısı")
    shots_per_game = models.FloatField(default=0.0, help_text="Maç Başına Şut")
    pass_accuracy = models.FloatField(default=0.0, help_text="Pas İsabet Yüzdesi (%)")
    key_passes = models.PositiveIntegerField(default=0, help_text="Toplam Kilit Pas")
    key_passes_per_game = models.FloatField(default=0.0, help_text="Maç Başına Kilit Pas")
    dribbles_per_game = models.FloatField(default=0.0, help_text="Maç Başına Başarılı Çalım")
    yellow_cards = models.PositiveIntegerField(default=0, help_text="Sarı Kart")
    red_cards = models.PositiveIntegerField(default=0, help_text="Kırmızı Kart")
    rating = models.FloatField(default=6.5, help_text="Ortalama Maç Puanı (örn: 7.8)")
    clean_sheets = models.PositiveIntegerField(default=0, help_text="Gol Yenmeyen Maç Sayısı")
    transfer_note = models.CharField(max_length=50, blank=True, default='', help_text="Örn: (Devre Arası Geldi), (Devre Arası Gitti)")

    class Meta:
        ordering = ['-season__start_year', '-goals', '-assists']
        unique_together = ('player', 'season', 'team')
        verbose_name = "Oyuncu Sezon İstatistiği"
        verbose_name_plural = "Oyuncu Sezon İstatistikleri"

    def __str__(self):
        return f"{self.player.name} - {self.season.name} ({self.team.short_name or self.team.name}): {self.goals} Gol, {self.assists} Asist"


# 7. Transfer Tablosu (Süper Lig'e Gelenler, Süper Lig'den Gidenler ve Lig İçi)
class Transfer(models.Model):
    TRANSFER_TYPE_CHOICES = [
        ('INCOMING', 'Süper Lig\'e Gelen'),
        ('OUTGOING', 'Süper Lig\'den Giden'),
        ('DOMESTIC', 'Süper Lig İçi'),
    ]

    CONTRACT_TYPE_CHOICES = [
        ('PERMANENT', 'Bonservis'),
        ('LOAN', 'Kiralık'),
        ('FREE', 'Bedelsiz'),
    ]

    player = models.ForeignKey(Player, related_name='transfers', on_delete=models.CASCADE)
    from_team = models.ForeignKey(Team, related_name='transfers_out', on_delete=models.SET_NULL, null=True, blank=True)
    to_team = models.ForeignKey(Team, related_name='transfers_in', on_delete=models.SET_NULL, null=True, blank=True)
    transfer_type = models.CharField(max_length=20, choices=TRANSFER_TYPE_CHOICES, default='DOMESTIC')
    contract_type = models.CharField(max_length=20, choices=CONTRACT_TYPE_CHOICES, default='PERMANENT')
    transfer_fee = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text="Bonservis / Kiralama Bedeli (€)")
    season = models.ForeignKey(Season, related_name='transfers', on_delete=models.SET_NULL, null=True, blank=True)
    transfer_date = models.DateField()
    is_new = models.BooleanField(default=True, help_text="YENİ rozeti gösterilsin mi?")
    details = models.CharField(max_length=255, blank=True, help_text="Örn: 18M € - Real Betis'e")

    class Meta:
        ordering = ['-transfer_date']
        verbose_name = "Transfer"
        verbose_name_plural = "Transferler"

    def __str__(self):
        from_name = self.from_team.name if self.from_team else "Serbest"
        to_name = self.to_team.name if self.to_team else "Serbest"
        return f"{self.player.name}: {from_name} -> {to_name} ({self.get_transfer_type_display()})"

    def save(self, *args, **kwargs):
        # Otomatik transfer tipi tespiti:
        if self.from_team and self.to_team:
            if not self.from_team.is_super_lig and self.to_team.is_super_lig:
                self.transfer_type = 'INCOMING'
            elif self.from_team.is_super_lig and not self.to_team.is_super_lig:
                self.transfer_type = 'OUTGOING'
            elif self.from_team.is_super_lig and self.to_team.is_super_lig:
                self.transfer_type = 'DOMESTIC'
        elif not self.from_team and self.to_team:
            if self.to_team.is_super_lig:
                self.transfer_type = 'INCOMING'
        elif self.from_team and not self.to_team:
            if self.from_team.is_super_lig:
                self.transfer_type = 'OUTGOING'
        super().save(*args, **kwargs)


# 8. Kullanıcı Takip / Scout Listesi
class ScoutList(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='scout_notes')
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    note = models.TextField()
    rating = models.IntegerField(default=5)
    notify_starting_11 = models.BooleanField(default=True, verbose_name="İlk 11 Bildirimi")
    notify_goals = models.BooleanField(default=True, verbose_name="Gol Bildirimi")
    notify_assists = models.BooleanField(default=True, verbose_name="Asist Bildirimi")
    notify_cards = models.BooleanField(default=False, verbose_name="Kart Bildirimi")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Scout Notu"
        verbose_name_plural = "Scout Notları"
        unique_together = ('user', 'player')

    def __str__(self):
        return f"{self.user.username} - {self.player.name} Notu"


# 9. Maç & Fikstür & Canlı Skor Tablosu (API-Football Entegrasyonu İçin)
class Fixture(models.Model):
    STATUS_CHOICES = [
        ('NS', 'Başlamadı (Not Started)'),
        ('1H', 'İlk Yarı (1st Half)'),
        ('HT', 'Devre Arası (Half Time)'),
        ('2H', 'İkinci Yarı (2nd Half)'),
        ('FT', 'Maç Bitti (Full Time)'),
        ('LIVE', 'Canlı Oynanıyor'),
        ('PST', 'Ertelendi (Postponed)'),
        ('CANC', 'İptal Edildi (Cancelled)'),
    ]

    api_id = models.IntegerField(unique=True, null=True, blank=True, help_text="API-Football Fixture ID")
    season = models.ForeignKey(Season, related_name='fixtures', on_delete=models.CASCADE)
    round_name = models.CharField(max_length=50, help_text="Örn: 10. Hafta veya Regular Season - 10")
    round_number = models.IntegerField(default=1, help_text="Hafta numarası (1-38)")
    home_team = models.ForeignKey(Team, related_name='home_fixtures', on_delete=models.CASCADE)
    away_team = models.ForeignKey(Team, related_name='away_fixtures', on_delete=models.CASCADE)
    home_score = models.IntegerField(null=True, blank=True, help_text="Ev Sahibi Skor")
    away_score = models.IntegerField(null=True, blank=True, help_text="Deplasman Skor")
    match_date = models.DateTimeField(help_text="Maç Tarih ve Saati")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='NS')
    status_display = models.CharField(max_length=50, default='Başlamadı', help_text="Arayüzde gösterilecek durum: 'MS', 'Canlı (65\')', '19:00'")
    venue = models.CharField(max_length=150, blank=True, help_text="Stadyum")
    referee = models.CharField(max_length=100, blank=True, help_text="Hakem")
    is_live = models.BooleanField(default=False, help_text="Şu an canlı oynanıyor mu?")
    elapsed_minute = models.IntegerField(null=True, blank=True, help_text="Canlı dakika (örn: 74)")

    class Meta:
        ordering = ['match_date', 'round_number']
        verbose_name = "Fikstür / Maç"
        verbose_name_plural = "Fikstür / Maçlar"

    def __str__(self):
        score_str = f" {self.home_score} - {self.away_score} " if self.home_score is not None and self.away_score is not None else " vs "
        return f"[{self.round_name}] {self.home_team.name}{score_str}{self.away_team.name} ({self.status_display})"


# 10. Kullanıcı Favori Takım Listesi & Bildirim Ayarları
class FavoriteTeam(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorite_teams')
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='favorited_by')
    notify_match_start = models.BooleanField(default=True, verbose_name="Maç Başladı/Bitti")
    notify_goals = models.BooleanField(default=True, verbose_name="Gol Bildirimi")
    notify_cards = models.BooleanField(default=False, verbose_name="Kırmızı Kart")
    notify_lineups = models.BooleanField(default=True, verbose_name="İlk 11 Açıklandı")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Favori Takım"
        verbose_name_plural = "Favori Takımlar"
        unique_together = ('user', 'team')

    def __str__(self):
        return f"{self.user.username} - {self.team.name} Takip"


# 11. Kullanıcı Mobil Cihaz Push Token Kaydı
class UserDevice(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='devices', null=True, blank=True)
    expo_push_token = models.CharField(max_length=255, unique=True)
    platform = models.CharField(max_length=30, default='android')
    device_name = models.CharField(max_length=100, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Kullanıcı Cihazı"
        verbose_name_plural = "Kullanıcı Cihazları"

    def __str__(self):
        u = self.user.username if self.user else "Misafir"
        return f"{u} ({self.platform}) - {self.expo_push_token[:15]}..."


# 12. Bildirim Geçmişi (Notification Inbox)
class NotificationLog(models.Model):
    NOTIFICATION_TYPES = [
        ('GOAL', 'Gol'),
        ('ASSIST', 'Asist'),
        ('LINEUP', 'İlk 11'),
        ('MATCH_START', 'Maç Başladı'),
        ('MATCH_END', 'Maç Bitti'),
        ('RED_CARD', 'Kırmızı Kart'),
        ('SYSTEM', 'Sistem / Haber'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications', null=True, blank=True)
    title = models.CharField(max_length=200)
    body = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='GOAL')
    related_fixture = models.ForeignKey(Fixture, on_delete=models.SET_NULL, null=True, blank=True)
    related_team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, blank=True)
    related_player = models.ForeignKey(Player, on_delete=models.SET_NULL, null=True, blank=True)
    data_payload = models.JSONField(default=dict, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Bildirim Kaydı"
        verbose_name_plural = "Bildirim Kayıtları"
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.notification_type}] {self.title}"