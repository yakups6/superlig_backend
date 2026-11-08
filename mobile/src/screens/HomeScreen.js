import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Image,
  ActivityIndicator,
  RefreshControl,
} from 'react-native';
import { useIsFocused } from '@react-navigation/native';
import { superligApi } from '../services/api';
import { COLORS } from '../theme/colors';
import { useAuth } from '../context/AuthContext';
import { getActiveApiUrl } from '../services/api';
import { DEFAULT_TEAM_LOGO } from '../utils/format';
import { computeClientLiveClock } from '../utils/liveClock';

export default function HomeScreen({ navigation }) {
  const isFocused = useIsFocused();
  const { user, isLoggedIn, activeSeason, favorites, favoriteTeams = [], unreadCount = 0 } = useAuth();
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [summary, setSummary] = useState(null);
  const [tickerData, setTickerData] = useState(null);
  const [apiErrorMsg, setApiErrorMsg] = useState('');
  const [nowMs, setNowMs] = useState(Date.now());

  const loadData = useCallback(async () => {
    try {
      const [sumRes, liveRes] = await Promise.allSettled([
        superligApi.getHomeSummary(),
        superligApi.getLiveSummary(),
      ]);
      if (sumRes.status === 'fulfilled' && sumRes.value) {
        setSummary(sumRes.value);
        setApiErrorMsg('');
      } else if (sumRes.status === 'rejected') {
        setApiErrorMsg(sumRes.reason?.message || 'Sunucuya ulaşılamadı');
      }
      if (liveRes.status === 'fulfilled' && liveRes.value) {
        const recvAt = Date.now();
        const lv = liveRes.value;
        setTickerData({
          ...lv,
          live_fixtures: (lv.live_fixtures || []).map((m) => ({ ...m, _clientReceivedMs: recvAt })),
          round_fixtures: (lv.round_fixtures || []).map((m) => ({ ...m, _clientReceivedMs: recvAt })),
        });
      }
    } catch (err) {
      console.log('Home load error:', err?.message);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    if (!isFocused) return;
    loadData();
    const poll = setInterval(loadData, 8000);
    return () => clearInterval(poll);
  }, [isFocused, loadData]);

  useEffect(() => {
    if (!isFocused) return;
    const t = setInterval(() => setNowMs(Date.now()), 1000);
    return () => clearInterval(t);
  }, [isFocused]);

  const onRefresh = () => {
    setRefreshing(true);
    loadData();
  };

  if (loading && !summary) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color={COLORS.accentRed} />
        <Text style={styles.loadingText}>Süper Lig Verileri Yükleniyor...</Text>
      </View>
    );
  }

  const tickerMatches = [];
  (tickerData?.live_fixtures || []).forEach((m) => tickerMatches.push(m));
  (tickerData?.round_fixtures || []).forEach((m) => {
    if (!tickerMatches.some((x) => x.id === m.id)) tickerMatches.push(m);
  });

  const leaderObj = summary?.league_leader;
  const leaderShort = leaderObj?.team_name?.split(' ')[0] || 'GS';
  const leaderPts = leaderObj?.points !== undefined ? `${leaderObj.points}P` : '';
  const totalTransfers =
    (summary?.incoming_transfers_count || 0) + (summary?.outgoing_transfers_count || 0);
  const currentRoundLabel = tickerData?.active_round
    ? `${tickerData.active_round}. Hafta`
    : '2026/27';

  const initials = isLoggedIn
    ? (user?.first_name?.[0] || user?.username?.[0] || 'U').toUpperCase() +
      (user?.last_name?.[0] || user?.username?.[1] || '').toUpperCase()
    : '👤';

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={COLORS.accentRed} />
      }
    >
      {/* TOP BAR */}
      <View style={styles.topHeader}>
        <TouchableOpacity
          style={[styles.topIconBtn, isLoggedIn && styles.topIconBtnActive]}
          onPress={() => navigation.navigate('Auth')}
        >
          <Text style={styles.topIconText}>{initials}</Text>
        </TouchableOpacity>
        <View style={styles.logoTitleWrap}>
          <Text style={styles.topBrand}>TRENDYOL SÜPER LİG</Text>
          <Text style={styles.topSubBrand}>Adnan Süvari Sezonu</Text>
        </View>
        <TouchableOpacity
          style={styles.topIconBtn}
          onPress={() => navigation.navigate('ScoutTab')}
        >
          <Text style={styles.topIconText}>🔔</Text>
          {Boolean(unreadCount > 0) && (
            <View style={styles.bellBadge}>
              <Text style={styles.bellBadgeText}>{unreadCount}</Text>
            </View>
          )}
        </TouchableOpacity>
      </View>

      {/* AUTH ACCOUNT STRIP */}
      {!summary && Boolean(apiErrorMsg) && (
        <View style={styles.offlineBanner}>
          <Text style={styles.offlineTitle}>⚠️ Backend Sunucusuna Bağlanılamadı</Text>
          <Text style={styles.offlineSub}>
            Denenen adres: {getActiveApiUrl()} ({apiErrorMsg})
          </Text>
          <View style={styles.offlineActions}>
            <TouchableOpacity style={styles.offlineBtn} onPress={onRefresh}>
              <Text style={styles.offlineBtnText}>🔄 Tekrar Dene</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.offlineBtn, styles.offlineBtnAlt]}
              onPress={() => navigation.navigate('Auth')}
            >
              <Text style={styles.offlineBtnText}>⚙️ Sunucu IP Ayarla</Text>
            </TouchableOpacity>
          </View>
        </View>
      )}

      <TouchableOpacity
        style={[styles.authStrip, isLoggedIn && styles.authStripLogged]}
        activeOpacity={0.8}
        onPress={() => navigation.navigate('Auth')}
      >
        <Text style={styles.authStripIcon}>{isLoggedIn ? '🟢' : '👤'}</Text>
        <View style={{ flex: 1 }}>
          <Text style={styles.authStripTitle} numberOfLines={1}>
            {isLoggedIn
              ? `Hoş geldin, ${[user?.first_name, user?.last_name].filter(Boolean).join(' ') || user?.username}`
              : 'Giriş Yap veya Kayıt Ol'}
          </Text>
          <Text style={styles.authStripSub} numberOfLines={1}>
            {isLoggedIn
              ? `@${user?.username} • ${favorites.length} Favori senkronize`
              : 'Favori oyuncularını hesabında sakla • Ücretsiz'}
          </Text>
        </View>
        <Text style={[styles.authStripLink, isLoggedIn && { color: COLORS.accentGreen }]}>
          {isLoggedIn ? 'Profilim →' : 'Giriş →'}
        </Text>
      </TouchableOpacity>

      {/* HERO SUMMARY CARD */}
      <View style={styles.heroCard}>
        <View style={styles.badgeRow}>
          <View style={styles.liveBadge}>
            <View style={styles.liveDot} />
            <Text style={styles.liveText}>
              {summary?.season || activeSeason?.name || '2026/2027'} SEZONU
            </Text>
          </View>
          <Text style={styles.seasonText}>{currentRoundLabel}</Text>
        </View>

        <Text style={styles.heroTitle}>Süper Lig Analiz & Scout</Text>
        <Text style={styles.heroSubtitle}>
          Canlı skor akışı, 1959’dan günümüze istatistikler ve transfer analitiği
        </Text>

        <View style={styles.statsStrip}>
          <View style={styles.stripItem}>
            <Text style={styles.stripValue}>{summary?.super_lig_teams_count ?? 18}</Text>
            <Text style={styles.stripLabel}>Takım</Text>
          </View>
          <View style={styles.stripDivider} />
          <View style={styles.stripItem}>
            <Text style={styles.stripValue}>{summary?.active_players_count ?? '-'}</Text>
            <Text style={styles.stripLabel}>Oyuncu</Text>
          </View>
          <View style={styles.stripDivider} />
          <View style={styles.stripItem}>
            <Text style={styles.stripValue}>{totalTransfers || '-'}</Text>
            <Text style={styles.stripLabel}>Transfer</Text>
          </View>
          <View style={styles.stripDivider} />
          <View style={styles.stripItem}>
            <Text style={[styles.stripValue, { color: COLORS.accentGold }]} numberOfLines={1}>
              {leaderShort}
            </Text>
            <Text style={styles.stripLabel}>Lider {leaderPts ? `(${leaderPts})` : ''}</Text>
          </View>
        </View>
      </View>

      {/* MAÇKOLİK LIVE TICKER STRIP */}
      <View style={styles.tickerHeader}>
        <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6 }}>
          <View style={styles.liveDot} />
          <Text style={styles.sectionHeader}>CANLI & HAFTANIN MAÇLARI</Text>
        </View>
        <TouchableOpacity onPress={() => navigation.navigate('FixturesTab')}>
          <Text style={styles.tickerAllLink}>Tüm Fikstür →</Text>
        </TouchableOpacity>
      </View>

      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.tickerScroll}
      >
        {tickerMatches.length === 0 ? (
          <View style={styles.emptyTicker}>
            <Text style={{ color: COLORS.textDim, fontSize: 11 }}>
              Fikstür yükleniyor...
            </Text>
          </View>
        ) : (
          tickerMatches.map((m) => {
            const clk = computeClientLiveClock(m, nowMs);
            const isHT = clk.type === 'HT';
            return (
              <TouchableOpacity
                key={m.id}
                style={[
                  styles.matchPill,
                  m.is_live && styles.matchPillLive,
                  isHT && styles.matchPillHT,
                ]}
                activeOpacity={0.8}
                onPress={() =>
                  navigation.navigate('FixturesTab', {
                    round: m.round_number,
                    ts: Date.now(),
                  })
                }
              >
                <View style={styles.matchPillTop}>
                  <Text style={styles.matchPillRound}>
                    {m.round_name || `${m.round_number}. Hafta`}
                  </Text>
                  <Text
                    style={[
                      styles.matchPillStatus,
                      clk.type === 'LIVE' && { color: '#f87171' },
                      clk.type === 'HT' && { color: COLORS.accentGold },
                      clk.type === 'FT' && { color: COLORS.accentGreen },
                    ]}
                  >
                    {clk.shortLabel}
                  </Text>
                </View>

                <View style={styles.matchPillBody}>
                  <View style={styles.pillTeam}>
                    <Image
                      source={{ uri: m.home_team_logo || DEFAULT_TEAM_LOGO }}
                      style={styles.pillLogo}
                    />
                    <Text style={styles.pillTeamShort}>
                      {m.home_team_short_name || m.home_team_name?.slice(0, 3).toUpperCase()}
                    </Text>
                  </View>

                  <Text
                    style={[
                      styles.pillScore,
                      m.is_live && { color: '#f87171' },
                    ]}
                  >
                    {m.home_score ?? '-'} : {m.away_score ?? '-'}
                  </Text>

                  <View style={styles.pillTeam}>
                    <Text style={styles.pillTeamShort}>
                      {m.away_team_short_name || m.away_team_name?.slice(0, 3).toUpperCase()}
                    </Text>
                    <Image
                      source={{ uri: m.away_team_logo || DEFAULT_TEAM_LOGO }}
                      style={styles.pillLogo}
                    />
                  </View>
                </View>
              </TouchableOpacity>
            );
          })
        )}
      </ScrollView>

      {/* MENU GRID */}
      <Text style={[styles.sectionHeader, { marginTop: 16, marginBottom: 12 }]}>
        MODÜLLER
      </Text>

      <View style={styles.gridContainer}>
        <TouchableOpacity
          style={[styles.gridCard, { borderColor: COLORS.accentRedBorder }]}
          onPress={() => navigation.navigate('FixturesTab')}
        >
          <View style={[styles.iconCircle, { backgroundColor: COLORS.accentRedSoft }]}>
            <Text style={styles.iconEmoji}>📡</Text>
          </View>
          <Text style={styles.cardTitle}>Canlı Skor</Text>
          <Text style={styles.cardDesc}>Fikstür & Anlık Dakika</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.gridCard}
          onPress={() => navigation.navigate('Players')}
        >
          <View style={styles.iconCircle}>
            <Text style={styles.iconEmoji}>👥</Text>
          </View>
          <Text style={styles.cardTitle}>Oyuncular</Text>
          <Text style={styles.cardDesc}>Tüm Lig & Mevkiler</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.gridCard}
          onPress={() => navigation.navigate('Legends')}
        >
          <View style={styles.iconCircle}>
            <Text style={styles.iconEmoji}>⭐</Text>
          </View>
          <Text style={styles.cardTitle}>Eski Oyuncular</Text>
          <Text style={styles.cardDesc}>Geçmiş Sezonlar & Efsaneler</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.gridCard}
          onPress={() => navigation.navigate('TransfersTab')}
        >
          <View style={styles.iconCircle}>
            <Text style={styles.iconEmoji}>🔄</Text>
          </View>
          <Text style={styles.cardTitle}>Transferler</Text>
          <Text style={styles.cardDesc}>Gelen, Giden & Bedeller</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.gridCard}
          onPress={() => navigation.navigate('CompareTab')}
        >
          <View style={styles.iconCircle}>
            <Text style={styles.iconEmoji}>⚖️</Text>
          </View>
          <Text style={styles.cardTitle}>Karşılaştırma</Text>
          <Text style={styles.cardDesc}>Radar & Algoritmik Analiz</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.gridCard}
          onPress={() => navigation.navigate('TeamsTab')}
        >
          <View style={styles.iconCircle}>
            <Text style={styles.iconEmoji}>🛡️</Text>
          </View>
          <Text style={styles.cardTitle}>Takımlar</Text>
          <Text style={styles.cardDesc}>18 Kulüp & Kadro Değerleri</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.gridCard}
          onPress={() => navigation.navigate('Standings')}
        >
          <View style={styles.iconCircle}>
            <Text style={styles.iconEmoji}>🏆</Text>
          </View>
          <Text style={styles.cardTitle}>Lig İstatistikleri</Text>
          <Text style={styles.cardDesc}>Puan Cetveli & Krallıklar</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.gridCard}
          onPress={() => navigation.navigate('ScoutTab')}
        >
          <View style={styles.iconCircle}>
            <Text style={styles.iconEmoji}>🔔</Text>
          </View>
          <Text style={styles.cardTitle}>Favoriler & Bildirim</Text>
          <Text style={styles.cardDesc}>
            {favorites.length} Oyuncu • {favoriteTeams.length} Kulüp
          </Text>
        </TouchableOpacity>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.background },
  content: { padding: 14, paddingBottom: 40 },
  center: {
    flex: 1,
    backgroundColor: COLORS.background,
    alignItems: 'center',
    justifyContent: 'center',
  },
  loadingText: { color: COLORS.textMuted, marginTop: 12, fontSize: 13 },
  topHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  topIconBtn: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: COLORS.backgroundCard,
    borderWidth: 1,
    borderColor: COLORS.cardBorderStrong,
    alignItems: 'center',
    justifyContent: 'center',
  },
  topIconBtnActive: {
    borderColor: COLORS.accentGreen,
    backgroundColor: COLORS.accentGreenSoft,
  },
  topIconText: { color: COLORS.white, fontSize: 13, fontWeight: '900' },
  bellBadge: {
    position: 'absolute',
    top: -3,
    right: -3,
    backgroundColor: COLORS.accentRed,
    borderRadius: 8,
    minWidth: 16,
    height: 16,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 3,
    borderWidth: 1.5,
    borderColor: '#060f14',
  },
  bellBadgeText: {
    color: COLORS.white,
    fontSize: 9,
    fontWeight: '900',
  },
  logoTitleWrap: { alignItems: 'center' },
  topBrand: { color: COLORS.white, fontSize: 14, fontWeight: '900', letterSpacing: 0.8 },
  topSubBrand: { color: COLORS.accentGold, fontSize: 10, fontWeight: '700' },
  authStrip: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.backgroundCard,
    borderWidth: 1,
    borderColor: 'rgba(56,189,248,0.28)',
    borderRadius: 12,
    paddingHorizontal: 12,
    paddingVertical: 9,
    gap: 10,
    marginBottom: 12,
  },
  authStripLogged: {
    borderColor: 'rgba(16,185,129,0.4)',
    backgroundColor: 'rgba(16,185,129,0.08)',
  },
  authStripIcon: { fontSize: 16 },
  authStripTitle: { color: COLORS.white, fontSize: 12, fontWeight: '800' },
  authStripSub: { color: COLORS.textMuted, fontSize: 10 },
  authStripLink: { color: COLORS.accentBlue, fontSize: 11, fontWeight: '800' },
  heroCard: {
    backgroundColor: COLORS.backgroundCard,
    borderRadius: 18,
    padding: 16,
    borderWidth: 1,
    borderColor: COLORS.cardBorder,
    marginBottom: 16,
  },
  badgeRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  liveBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.accentRedSoft,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 10,
  },
  liveDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: COLORS.accentRed,
    marginRight: 6,
  },
  liveText: { color: COLORS.accentRed, fontSize: 10, fontWeight: '800' },
  seasonText: { color: COLORS.accentBlue, fontSize: 11, fontWeight: '800' },
  heroTitle: { color: COLORS.white, fontSize: 20, fontWeight: '900', marginBottom: 4 },
  heroSubtitle: { color: COLORS.textMuted, fontSize: 12, lineHeight: 17, marginBottom: 14 },
  statsStrip: {
    flexDirection: 'row',
    backgroundColor: 'rgba(255,255,255,0.03)',
    borderRadius: 12,
    paddingVertical: 10,
    paddingHorizontal: 6,
    alignItems: 'center',
    justifyContent: 'space-around',
  },
  stripItem: { alignItems: 'center', flex: 1 },
  stripValue: { color: COLORS.white, fontSize: 15, fontWeight: '900' },
  stripLabel: { color: COLORS.textDim, fontSize: 10, marginTop: 2, fontWeight: '600' },
  stripDivider: { width: 1, height: 26, backgroundColor: COLORS.cardBorder },
  tickerHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  sectionHeader: {
    color: COLORS.textMuted,
    fontSize: 11,
    fontWeight: '800',
    letterSpacing: 0.7,
  },
  tickerAllLink: { color: COLORS.accentBlue, fontSize: 11, fontWeight: '800' },
  tickerScroll: { gap: 10, paddingBottom: 4 },
  emptyTicker: {
    backgroundColor: COLORS.backgroundCard,
    borderRadius: 12,
    padding: 14,
  },
  matchPill: {
    width: 174,
    backgroundColor: COLORS.backgroundCard,
    borderWidth: 1,
    borderColor: COLORS.cardBorder,
    borderRadius: 12,
    padding: 10,
  },
  matchPillLive: {
    borderColor: COLORS.accentRedBorder,
    backgroundColor: '#18111b',
  },
  matchPillHT: {
    borderColor: 'rgba(245,158,11,0.45)',
  },
  matchPillTop: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  matchPillRound: { color: COLORS.textDim, fontSize: 10, fontWeight: '700' },
  matchPillStatus: { color: COLORS.textMuted, fontSize: 10, fontWeight: '800' },
  matchPillBody: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  pillTeam: { flexDirection: 'row', alignItems: 'center', gap: 4 },
  pillLogo: { width: 16, height: 16, resizeMode: 'contain' },
  pillTeamShort: { color: COLORS.white, fontSize: 11, fontWeight: '800' },
  pillScore: { color: COLORS.white, fontSize: 13, fontWeight: '900' },
  gridContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    gap: 10,
  },
  gridCard: {
    width: '48.2%',
    backgroundColor: COLORS.backgroundCard,
    borderWidth: 1,
    borderColor: COLORS.cardBorder,
    borderRadius: 16,
    padding: 14,
    alignItems: 'center',
  },
  iconCircle: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: 'rgba(255,255,255,0.05)',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 8,
  },
  iconEmoji: { fontSize: 20 },
  cardTitle: { color: COLORS.white, fontSize: 13, fontWeight: '800', marginBottom: 2 },
  cardDesc: { color: COLORS.textDim, fontSize: 10, textAlign: 'center' },
  offlineBanner: {
    backgroundColor: 'rgba(239,68,68,0.12)',
    borderWidth: 1,
    borderColor: COLORS.accentRedBorder,
    borderRadius: 12,
    padding: 12,
    marginBottom: 12,
  },
  offlineTitle: { color: '#f87171', fontSize: 12, fontWeight: '800', marginBottom: 3 },
  offlineSub: { color: COLORS.textSoft, fontSize: 10, lineHeight: 15, marginBottom: 8 },
  offlineActions: { flexDirection: 'row', gap: 8 },
  offlineBtn: {
    backgroundColor: COLORS.accentRed,
    borderRadius: 8,
    paddingHorizontal: 10,
    paddingVertical: 6,
  },
  offlineBtnAlt: { backgroundColor: '#1e3a5f' },
  offlineBtnText: { color: COLORS.white, fontSize: 11, fontWeight: '800' },
});
