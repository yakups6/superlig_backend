import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Image,
  ActivityIndicator,
  RefreshControl,
  Modal,
  FlatList,
} from 'react-native';
import { useIsFocused } from '@react-navigation/native';
import { COLORS } from '../theme/colors';
import { superligApi } from '../services/api';
import { DEFAULT_TEAM_LOGO } from '../utils/format';
import { computeClientLiveClock } from '../utils/liveClock';

const STATUS_FILTERS = [
  { key: 'ALL', label: 'Tümü' },
  { key: 'LIVE', label: '🔴 Canlı' },
  { key: 'FT', label: '✅ Bitenler (MS)' },
  { key: 'NS', label: '⏳ Gelecek' },
];

export default function FixturesScreen({ navigation, route }) {
  const isFocused = useIsFocused();
  const [summary, setSummary] = useState(null);
  const [selectedRound, setSelectedRound] = useState(route?.params?.round ?? null);
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [roundModalOpen, setRoundModalOpen] = useState(false);
  const [selectedMatch, setSelectedMatch] = useState(null);
  const [miniStandings, setMiniStandings] = useState([]);
  const [finishAlert, setFinishAlert] = useState('');
  const [nowMs, setNowMs] = useState(Date.now());

  const prevLiveIdsRef = useRef(new Set());
  const inFlightRef = useRef(false);

  useEffect(() => {
    if (route?.params?.round !== undefined && route?.params?.round !== null) {
      setSelectedRound(route.params.round);
    }
  }, [route?.params?.round, route?.params?.ts]);

  const fetchData = useCallback(async (force = false, targetRoundOverride = undefined) => {
    if (inFlightRef.current && !force) return;
    inFlightRef.current = true;
    try {
      const roundToFetch = targetRoundOverride !== undefined ? targetRoundOverride : selectedRound;
      const params = {};
      if (roundToFetch !== null && roundToFetch !== undefined) {
        params.round = roundToFetch;
      }
      if (force) params.force = 1;

      const data = await superligApi.getLiveSummary(params);
      if (!data) return;

      const recvAt = Date.now();
      const liveList = (data.live_fixtures || []).map((m) => ({ ...m, _clientReceivedMs: recvAt }));
      const roundList = (data.round_fixtures || []).map((m) => ({ ...m, _clientReceivedMs: recvAt }));

      const curLiveIds = new Set(liveList.map((m) => m.id));
      if (prevLiveIdsRef.current.size > 0) {
        for (const oldId of prevLiveIdsRef.current) {
          if (!curLiveIds.has(oldId)) {
            const finished = roundList.find((f) => f.id === oldId && f.status === 'FT');
            if (finished) {
              setFinishAlert(
                `${finished.home_team_name} ${finished.home_score} - ${finished.away_score} ${finished.away_team_name} sona erdi (MS)! Puan durumu güncellendi.`
              );
              setTimeout(() => setFinishAlert(''), 9000);
            }
          }
        }
      }
      prevLiveIdsRef.current = curLiveIds;

      setSummary({
        ...data,
        live_fixtures: liveList,
        round_fixtures: roundList,
      });

      if ((roundToFetch === null || roundToFetch === undefined) && data.current_round) {
        setSelectedRound(data.current_round);
      }

      try {
        const st = await superligApi.getStandings({ season: data.season_name || '2026/2027' });
        setMiniStandings(Array.isArray(st) ? st.slice(0, 6) : []);
      } catch (e) {}
    } catch (e) {
      console.log('Fixtures load error:', e?.message);
    } finally {
      inFlightRef.current = false;
      setLoading(false);
      setRefreshing(false);
    }
  }, [selectedRound]);

  useEffect(() => {
    if (!isFocused) return;
    fetchData(false);
    const pollId = setInterval(() => fetchData(false), 8000);
    return () => clearInterval(pollId);
  }, [isFocused, fetchData]);

  useEffect(() => {
    if (!isFocused) return;
    const tickId = setInterval(() => setNowMs(Date.now()), 1000);
    return () => clearInterval(tickId);
  }, [isFocused]);

  const allRounds = summary?.all_rounds?.length ? summary.all_rounds : Array.from({ length: 34 }, (_, i) => i + 1);
  const maxRound = Math.max(...allRounds);
  const minRound = Math.min(...allRounds);
  const activeRound = summary?.active_round || 11;
  const effectiveRound = selectedRound ?? summary?.current_round ?? activeRound;
  const isAll = effectiveRound === 'ALL';

  const selectRound = (r) => {
    setSelectedRound(r);
    setLoading(true);
    fetchData(false, r);
  };

  const stepRound = (delta) => {
    const cur = isAll ? activeRound : Number(effectiveRound);
    const next = Math.max(minRound, Math.min(maxRound, cur + delta));
    if (next !== cur || isAll) {
      selectRound(next);
    }
  };

  const quickRoundsSet = new Set([1, activeRound - 2, activeRound - 1, activeRound, activeRound + 1, 17, maxRound]);
  if (!isAll && effectiveRound) quickRoundsSet.add(Number(effectiveRound));
  const quickRounds = [...quickRoundsSet].filter((r) => allRounds.includes(r)).sort((a, b) => a - b);

  const liveFixtures = summary?.live_fixtures || [];
  const rawFixtures = summary?.round_fixtures || [];
  const filteredFixtures = rawFixtures.filter((m) => {
    if (statusFilter === 'LIVE') return m.is_live;
    if (statusFilter === 'FT') return m.status === 'FT';
    if (statusFilter === 'NS') return m.status === 'NS';
    return true;
  });

  const roundStateLabel = isAll
    ? `${summary?.season_name || '2026/2027'} • Tüm Sezon Fikstürü`
    : `${summary?.season_name || '2026/2027'} • ${
        Number(effectiveRound) === activeRound
          ? 'Bu Hafta (Aktif)'
          : Number(effectiveRound) === activeRound - 1
          ? 'Son Hafta'
          : Number(effectiveRound) > activeRound
          ? 'Gelecek Hafta'
          : 'Tamamlandı'
      }`;

  let lastGroupRound = null;

  return (
    <View style={styles.container}>
      {/* HEADER */}
      <View style={styles.headerRow}>
        <TouchableOpacity onPress={() => navigation.navigate('HomeTab')} style={styles.backBtn}>
          <Text style={styles.backText}>←</Text>
        </TouchableOpacity>
        <View style={styles.headerTitleWrap}>
          <View style={styles.pulseDot} />
          <Text style={styles.headerTitle}>CANLI SKOR & FİKSTÜR</Text>
        </View>
        <TouchableOpacity
          style={styles.refreshBtn}
          onPress={() => {
            setRefreshing(true);
            fetchData(true);
          }}
        >
          <Text style={styles.refreshBtnText}>🔄 Yenile</Text>
        </TouchableOpacity>
      </View>

      <ScrollView
        contentContainerStyle={styles.scrollContent}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={() => {
              setRefreshing(true);
              fetchData(true);
            }}
            tintColor={COLORS.accentRed}
          />
        }
      >
        {/* COMPACT WEEK SELECTOR */}
        <View style={styles.weekWidget}>
          <View style={styles.weekTopRow}>
            <View style={styles.weekLeft}>
              <View style={styles.weekPillBadge}>
                <Text style={styles.weekPillText}>{isAll ? 'TÜMÜ' : `${effectiveRound}.H`}</Text>
              </View>
              <View style={{ flex: 1 }}>
                <Text style={styles.weekTitle} numberOfLines={1}>
                  {isAll ? `Tüm Haftalar (1-${maxRound})` : `${effectiveRound}. Hafta Maçları`}
                </Text>
                <Text style={styles.weekSub} numberOfLines={1}>
                  {roundStateLabel}
                </Text>
              </View>
            </View>

            <View style={styles.weekControls}>
              <TouchableOpacity style={styles.stepBtn} onPress={() => stepRound(-1)}>
                <Text style={styles.stepBtnText}>◀</Text>
              </TouchableOpacity>
              <TouchableOpacity style={styles.weekDropBtn} onPress={() => setRoundModalOpen(true)}>
                <Text style={styles.weekDropBtnText}>
                  {isAll ? 'Tümü' : `${effectiveRound}. Hafta`} ▾
                </Text>
              </TouchableOpacity>
              <TouchableOpacity style={styles.stepBtn} onPress={() => stepRound(1)}>
                <Text style={styles.stepBtnText}>▶</Text>
              </TouchableOpacity>
            </View>
          </View>

          <ScrollView
            horizontal
            showsHorizontalScrollIndicator={false}
            contentContainerStyle={styles.quickChipsRow}
          >
            <TouchableOpacity
              style={[styles.quickChip, isAll && styles.quickChipActive]}
              onPress={() => selectRound('ALL')}
            >
              <Text style={[styles.quickChipText, isAll && styles.quickChipTextActive]}>
                🌟 Tümü
              </Text>
            </TouchableOpacity>
            {quickRounds.map((r) => {
              const active = !isAll && Number(effectiveRound) === r;
              let lbl = `${r}.H`;
              if (r === activeRound) lbl = `${r}.H (Aktif)`;
              else if (r === activeRound - 1) lbl = `${r}.H (Son)`;
              else if (r === 17) lbl = '17.H (Devre)';
              else if (r === maxRound) lbl = `${maxRound}.H (Final)`;
              return (
                <TouchableOpacity
                  key={r}
                  style={[styles.quickChip, active && styles.quickChipActive]}
                  onPress={() => selectRound(r)}
                >
                  <Text style={[styles.quickChipText, active && styles.quickChipTextActive]}>
                    {lbl}
                  </Text>
                </TouchableOpacity>
              );
            })}
          </ScrollView>
        </View>

        {/* STATUS FILTER TABS */}
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={styles.filterTabsRow}
        >
          {STATUS_FILTERS.map((f) => {
            const active = statusFilter === f.key;
            return (
              <TouchableOpacity
                key={f.key}
                style={[styles.filterPill, active && styles.filterPillActive]}
                onPress={() => setStatusFilter(f.key)}
              >
                <Text style={[styles.filterPillText, active && styles.filterPillTextActive]}>
                  {f.label}
                </Text>
              </TouchableOpacity>
            );
          })}
        </ScrollView>

        {Boolean(finishAlert) && (
          <View style={styles.alertBanner}>
            <Text style={styles.alertBannerText}>✅ {finishAlert}</Text>
          </View>
        )}

        {/* LIVE FEATURED HERO CARDS */}
        {liveFixtures.map((match) => {
          const clk = computeClientLiveClock(match, nowMs);
          const isHT = clk.type === 'HT';
          const evList = Array.isArray(match.events) ? match.events : [];
          return (
            <TouchableOpacity
              key={`live-${match.id}`}
              activeOpacity={0.85}
              onPress={() => setSelectedMatch(match)}
              style={[styles.liveHeroCard, isHT && styles.liveHeroCardHT]}
            >
              <View style={styles.liveHeroTop}>
                <View style={[styles.liveHeroPill, isHT && styles.liveHeroPillHT]}>
                  <Text style={[styles.liveHeroPillText, isHT && { color: COLORS.accentGold }]}>
                    {isHT
                      ? `⏸️ ${match.round_name || ''} • İLK YARI SONU (İY)`
                      : `🔴 ${match.round_name || ''} • CANLI MAÇ`}
                  </Text>
                </View>
                <Text style={styles.venueSmall} numberOfLines={1}>
                  {match.venue || 'Süper Lig'}
                </Text>
              </View>

              <View style={styles.liveMatchupRow}>
                <View style={styles.heroTeamCol}>
                  <Image
                    source={{ uri: match.home_team_logo || DEFAULT_TEAM_LOGO }}
                    style={styles.heroLogo}
                  />
                  <Text style={styles.heroTeamName} numberOfLines={2}>
                    {match.home_team_name}
                  </Text>
                </View>

                <View style={styles.heroScoreCol}>
                  <Text style={styles.heroBigScore}>
                    {match.home_score ?? 0} - {match.away_score ?? 0}
                  </Text>
                  <Text style={[styles.heroClockText, isHT && { color: COLORS.accentGold }]}>
                    {clk.heroLabel}
                  </Text>
                </View>

                <View style={styles.heroTeamCol}>
                  <Image
                    source={{ uri: match.away_team_logo || DEFAULT_TEAM_LOGO }}
                    style={styles.heroLogo}
                  />
                  <Text style={styles.heroTeamName} numberOfLines={2}>
                    {match.away_team_name}
                  </Text>
                </View>
              </View>

              <View style={styles.heroEventsBox}>
                {evList.length > 0 ? (
                  evList.map((ev, i) => (
                    <View key={i} style={styles.heroEventRow}>
                      <Text style={styles.heroEventTxt}>
                        ⚽ {ev.minute} {ev.scorer}
                        {ev.is_penalty ? ' (P)' : ''}
                        {ev.is_own_goal ? ' (KK)' : ''}
                        {ev.assist && !ev.is_own_goal ? ` (Asist: ${ev.assist})` : ''}
                      </Text>
                      <Text style={styles.heroEventTeam}>{ev.team_short || ''}</Text>
                    </View>
                  ))
                ) : (
                  <Text style={styles.heroEventEmpty}>
                    ⚽ Henüz gol sesi çıkmadı • Canlı dakika akışı aktif
                  </Text>
                )}
              </View>
            </TouchableOpacity>
          );
        })}

        {/* LIST HEADER */}
        <View style={styles.listHeader}>
          <Text style={styles.listTitle}>
            {isAll ? `Tüm Sezon Fikstürü (1-${maxRound}. Hafta)` : `${effectiveRound}. Hafta Maçları`}
          </Text>
          <Text style={styles.listCount}>{filteredFixtures.length} Maç</Text>
        </View>

        {loading && !summary ? (
          <ActivityIndicator size="large" color={COLORS.accentRed} style={{ marginVertical: 30 }} />
        ) : filteredFixtures.length === 0 ? (
          <View style={styles.emptyBox}>
            <Text style={styles.emptyText}>Bu filtreye uygun maç bulunamadı.</Text>
          </View>
        ) : (
          filteredFixtures.map((m) => {
            const clk = computeClientLiveClock(m, nowMs);
            const evs = Array.isArray(m.events) ? m.events : [];
            let showDivider = false;
            if (isAll && m.round_number !== lastGroupRound) {
              lastGroupRound = m.round_number;
              showDivider = true;
            }
            const rStatus =
              m.round_number < activeRound
                ? '✅ Tamamlandı'
                : m.round_number === activeRound
                ? '🔴 Bu Hafta'
                : '⏳ Gelecek';

            return (
              <React.Fragment key={m.id}>
                {showDivider && (
                  <View style={styles.roundDivider}>
                    <Text style={styles.roundDividerTitle}>
                      📅 {m.round_name || `${m.round_number}. Hafta`}
                    </Text>
                    <Text style={styles.roundDividerStatus}>{rStatus}</Text>
                  </View>
                )}

                <TouchableOpacity
                  activeOpacity={0.78}
                  onPress={() => setSelectedMatch(m)}
                  style={[styles.fixtureCard, m.is_live && styles.fixtureCardLive]}
                >
                  <View style={styles.fixtureStatusCol}>
                    <View
                      style={[
                        styles.statusBadge,
                        clk.type === 'HT'
                          ? styles.badgeHT
                          : clk.type === 'LIVE'
                          ? styles.badgeLIVE
                          : clk.type === 'FT'
                          ? styles.badgeFT
                          : styles.badgeNS,
                      ]}
                    >
                      <Text
                        style={[
                          styles.statusBadgeText,
                          clk.type === 'HT' && { color: COLORS.accentGold },
                          clk.type === 'LIVE' && { color: '#f87171' },
                          clk.type === 'FT' && { color: COLORS.accentGreen },
                        ]}
                      >
                        {clk.shortLabel}
                      </Text>
                    </View>
                  </View>

                  <View style={styles.fixtureTeamsCol}>
                    <View style={styles.teamLine}>
                      <View style={styles.teamInfo}>
                        <Image
                          source={{ uri: m.home_team_logo || DEFAULT_TEAM_LOGO }}
                          style={styles.smallLogo}
                        />
                        <Text style={styles.teamName} numberOfLines={1}>
                          {m.home_team_name}
                        </Text>
                      </View>
                      <Text style={styles.scoreNum}>
                        {m.home_score !== null && m.home_score !== undefined ? m.home_score : '-'}
                      </Text>
                    </View>

                    <View style={styles.teamLine}>
                      <View style={styles.teamInfo}>
                        <Image
                          source={{ uri: m.away_team_logo || DEFAULT_TEAM_LOGO }}
                          style={styles.smallLogo}
                        />
                        <Text style={styles.teamName} numberOfLines={1}>
                          {m.away_team_name}
                        </Text>
                      </View>
                      <Text style={styles.scoreNum}>
                        {m.away_score !== null && m.away_score !== undefined ? m.away_score : '-'}
                      </Text>
                    </View>

                    {evs.length > 0 && (
                      <Text style={styles.goalsStrip} numberOfLines={2}>
                        ⚽ {evs.map((e) => `${e.minute} ${e.scorer}`).join(' • ')}
                      </Text>
                    )}
                  </View>
                </TouchableOpacity>
              </React.Fragment>
            );
          })
        )}

        {/* MINI STANDINGS PREVIEW */}
        {miniStandings.length > 0 && (
          <View style={styles.miniStandingsCard}>
            <View style={styles.miniHead}>
              <Text style={styles.miniTitle}>🏆 Güncel Puan Durumu</Text>
              <TouchableOpacity onPress={() => navigation.navigate('Standings')}>
                <Text style={styles.miniLink}>Tam Tablo →</Text>
              </TouchableOpacity>
            </View>
            {miniStandings.map((s) => (
              <View key={s.id || s.rank} style={styles.miniRow}>
                <Text
                  style={[
                    styles.miniRank,
                    s.rank <= 2 && { color: COLORS.accentGreen },
                    s.rank > 2 && s.rank <= 4 && { color: COLORS.accentBlue },
                  ]}
                >
                  {s.rank}
                </Text>
                <Image
                  source={{ uri: s.team_logo || DEFAULT_TEAM_LOGO }}
                  style={styles.miniLogo}
                />
                <Text style={styles.miniTeam} numberOfLines={1}>
                  {s.team_short_name || s.team_name}
                </Text>
                <Text style={styles.miniStat}>{s.played}O</Text>
                <Text style={styles.miniStat}>
                  {s.goal_difference > 0 ? `+${s.goal_difference}` : s.goal_difference}
                </Text>
                <Text style={styles.miniPts}>{s.points}P</Text>
              </View>
            ))}
          </View>
        )}
      </ScrollView>

      {/* ROUND PICKER MODAL */}
      <Modal
        visible={roundModalOpen}
        transparent
        animationType="fade"
        onRequestClose={() => setRoundModalOpen(false)}
      >
        <TouchableOpacity
          style={styles.modalOverlay}
          activeOpacity={1}
          onPress={() => setRoundModalOpen(false)}
        >
          <View style={styles.modalCard} onStartShouldSetResponder={() => true}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Hafta Seç (1-{maxRound})</Text>
              <TouchableOpacity onPress={() => setRoundModalOpen(false)}>
                <Text style={styles.modalClose}>✕</Text>
              </TouchableOpacity>
            </View>
            <FlatList
              data={['ALL', ...allRounds]}
              keyExtractor={(item) => String(item)}
              style={{ maxHeight: 360 }}
              renderItem={({ item }) => {
                const isItemAll = item === 'ALL';
                const active = isItemAll ? isAll : !isAll && Number(effectiveRound) === Number(item);
                let label = isItemAll ? `Tüm Haftalar (1-${maxRound})` : `${item}. Hafta`;
                if (!isItemAll && item === activeRound) label += ' (Bu Hafta)';
                else if (!isItemAll && item === activeRound - 1) label += ' (Son Hafta)';

                return (
                  <TouchableOpacity
                    style={[styles.modalRow, active && styles.modalRowActive]}
                    onPress={() => {
                      setRoundModalOpen(false);
                      selectRound(item);
                    }}
                  >
                    <Text style={[styles.modalRowText, active && { color: COLORS.white, fontWeight: '800' }]}>
                      {label}
                    </Text>
                  </TouchableOpacity>
                );
              }}
            />
          </View>
        </TouchableOpacity>
      </Modal>

      {/* MATCH DETAIL MODAL */}
      <Modal
        visible={Boolean(selectedMatch)}
        transparent
        animationType="fade"
        onRequestClose={() => setSelectedMatch(null)}
      >
        <TouchableOpacity
          style={styles.modalOverlay}
          activeOpacity={1}
          onPress={() => setSelectedMatch(null)}
        >
          {selectedMatch && (
            <View style={styles.modalCard} onStartShouldSetResponder={() => true}>
              <Text style={styles.matchModalHeader}>
                {selectedMatch.round_name || 'Süper Lig'} Maç Detayı
              </Text>
              <Text style={styles.matchModalScore}>
                {selectedMatch.home_team_name} {selectedMatch.home_score ?? '-'} -{' '}
                {selectedMatch.away_score ?? '-'} {selectedMatch.away_team_name}
              </Text>
              <Text style={styles.matchModalMeta}>
                • Durum: {computeClientLiveClock(selectedMatch, nowMs).heroLabel}
              </Text>
              <Text style={styles.matchModalMeta}>
                • Stadyum: {selectedMatch.venue || 'Belirtilmedi'}
              </Text>
              <Text style={styles.matchModalMeta}>
                • Hakem: {selectedMatch.referee || 'TFF Ataması'}
              </Text>
              {Array.isArray(selectedMatch.events) && selectedMatch.events.length > 0 && (
                <View style={styles.matchModalEvents}>
                  <Text style={styles.matchModalEvTitle}>Goller:</Text>
                  {selectedMatch.events.map((e, i) => (
                    <Text key={i} style={styles.matchModalMeta}>
                      ⚽ {e.minute} {e.scorer}
                      {e.is_penalty ? ' (P)' : ''}
                      {e.is_own_goal ? ' (KK)' : ''} ({e.team_short || e.team_name})
                    </Text>
                  ))}
                </View>
              )}
              <TouchableOpacity
                style={styles.modalCloseBtn}
                onPress={() => setSelectedMatch(null)}
              >
                <Text style={styles.modalCloseBtnText}>Tamam</Text>
              </TouchableOpacity>
            </View>
          )}
        </TouchableOpacity>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.background },
  headerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingTop: 14,
    paddingBottom: 10,
  },
  backBtn: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: 'rgba(255,255,255,0.08)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  backText: { color: COLORS.white, fontSize: 16, fontWeight: '700' },
  headerTitleWrap: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  pulseDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: COLORS.accentRed,
  },
  headerTitle: { color: COLORS.white, fontSize: 14, fontWeight: '800', letterSpacing: 0.4 },
  refreshBtn: {
    backgroundColor: 'rgba(56,189,248,0.14)',
    borderWidth: 1,
    borderColor: 'rgba(56,189,248,0.35)',
    borderRadius: 8,
    paddingHorizontal: 9,
    paddingVertical: 5,
  },
  refreshBtnText: { color: COLORS.accentBlue, fontSize: 11, fontWeight: '800' },
  scrollContent: { padding: 14, paddingBottom: 40 },
  weekWidget: {
    backgroundColor: COLORS.backgroundCard,
    borderRadius: 14,
    borderWidth: 1,
    borderColor: COLORS.cardBorder,
    padding: 10,
    marginBottom: 10,
  },
  weekTopRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: 8,
    marginBottom: 8,
  },
  weekLeft: { flexDirection: 'row', alignItems: 'center', gap: 8, flex: 1 },
  weekPillBadge: {
    backgroundColor: COLORS.primarySoft,
    borderWidth: 1,
    borderColor: COLORS.primaryGlow,
    borderRadius: 8,
    paddingHorizontal: 8,
    paddingVertical: 5,
  },
  weekPillText: { color: COLORS.primaryGlow, fontSize: 11, fontWeight: '900' },
  weekTitle: { color: COLORS.white, fontSize: 12, fontWeight: '800' },
  weekSub: { color: COLORS.textMuted, fontSize: 10, marginTop: 1 },
  weekControls: { flexDirection: 'row', alignItems: 'center', gap: 4 },
  stepBtn: {
    backgroundColor: 'rgba(255,255,255,0.08)',
    borderWidth: 1,
    borderColor: COLORS.cardBorderStrong,
    borderRadius: 8,
    paddingHorizontal: 8,
    paddingVertical: 6,
  },
  stepBtnText: { color: COLORS.white, fontSize: 10, fontWeight: '800' },
  weekDropBtn: {
    backgroundColor: 'rgba(6,182,212,0.16)',
    borderWidth: 1,
    borderColor: 'rgba(6,182,212,0.4)',
    borderRadius: 8,
    paddingHorizontal: 9,
    paddingVertical: 6,
  },
  weekDropBtnText: { color: COLORS.secondary, fontSize: 11, fontWeight: '800' },
  quickChipsRow: { gap: 6, paddingTop: 2 },
  quickChip: {
    backgroundColor: 'rgba(255,255,255,0.05)',
    borderWidth: 1,
    borderColor: COLORS.cardBorder,
    borderRadius: 999,
    paddingHorizontal: 10,
    paddingVertical: 4,
  },
  quickChipActive: {
    backgroundColor: COLORS.primarySoft,
    borderColor: COLORS.primaryGlow,
  },
  quickChipText: { color: COLORS.textMuted, fontSize: 10, fontWeight: '700' },
  quickChipTextActive: { color: COLORS.primaryGlow, fontWeight: '800' },
  filterTabsRow: { gap: 8, marginBottom: 12 },
  filterPill: {
    backgroundColor: COLORS.backgroundCard,
    borderWidth: 1,
    borderColor: COLORS.cardBorder,
    borderRadius: 999,
    paddingHorizontal: 12,
    paddingVertical: 6,
  },
  filterPillActive: {
    backgroundColor: COLORS.primarySoft,
    borderColor: COLORS.primaryGlow,
  },
  filterPillText: { color: COLORS.textMuted, fontSize: 11, fontWeight: '700' },
  filterPillTextActive: { color: COLORS.primaryGlow, fontWeight: '800' },
  alertBanner: {
    backgroundColor: COLORS.primarySoft,
    borderWidth: 1,
    borderColor: 'rgba(16,185,129,0.4)',
    borderRadius: 12,
    padding: 10,
    marginBottom: 12,
  },
  alertBannerText: { color: COLORS.primaryGlow, fontSize: 12, fontWeight: '700' },
  liveHeroCard: {
    backgroundColor: '#0a1a24',
    borderWidth: 1.5,
    borderColor: COLORS.cardBorderStrong,
    borderRadius: 16,
    padding: 14,
    marginBottom: 12,
  },
  liveHeroCardHT: {
    borderColor: 'rgba(245,158,11,0.45)',
    backgroundColor: '#17150f',
  },
  liveHeroTop: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
    gap: 8,
  },
  liveHeroPill: {
    backgroundColor: COLORS.accentRedSoft,
    borderWidth: 1,
    borderColor: 'rgba(244,63,94,0.4)',
    borderRadius: 8,
    paddingHorizontal: 8,
    paddingVertical: 3,
  },
  liveHeroPillHT: {
    backgroundColor: COLORS.accentGoldSoft,
  },
  liveHeroPillText: { color: '#f87171', fontSize: 10, fontWeight: '800' },
  venueSmall: { color: COLORS.textMuted, fontSize: 10, flex: 1, textAlign: 'right' },
  liveMatchupRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  heroTeamCol: { flex: 1, alignItems: 'center', gap: 6 },
  heroLogo: {
    width: 42,
    height: 42,
    resizeMode: 'contain',
    borderRadius: 21,
    borderWidth: 2,
    borderColor: COLORS.avatarRingEmerald,
    backgroundColor: 'rgba(16,185,129,0.08)',
  },
  heroTeamName: { color: COLORS.white, fontSize: 12, fontWeight: '800', textAlign: 'center' },
  heroScoreCol: { alignItems: 'center', paddingHorizontal: 10 },
  heroBigScore: { color: COLORS.white, fontSize: 28, fontWeight: '900', letterSpacing: 2 },
  heroClockText: { color: COLORS.primaryGlow, fontSize: 10, fontWeight: '800', marginTop: 2 },
  heroEventsBox: {
    marginTop: 10,
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: 'rgba(255,255,255,0.08)',
    gap: 3,
  },
  heroEventRow: { flexDirection: 'row', justifyContent: 'space-between' },
  heroEventTxt: { color: COLORS.textSoft, fontSize: 11 },
  heroEventTeam: { color: COLORS.primaryGlow, fontSize: 10, fontWeight: '800' },
  heroEventEmpty: { color: COLORS.textDim, fontSize: 11 },
  listHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  listTitle: { color: COLORS.white, fontSize: 13, fontWeight: '800' },
  listCount: { color: COLORS.textMuted, fontSize: 11, fontWeight: '700' },
  roundDivider: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: 'rgba(6,182,212,0.08)',
    borderWidth: 1,
    borderColor: 'rgba(6,182,212,0.25)',
    borderRadius: 10,
    paddingHorizontal: 10,
    paddingVertical: 7,
    marginTop: 10,
    marginBottom: 6,
  },
  roundDividerTitle: { color: COLORS.secondary, fontSize: 12, fontWeight: '800' },
  roundDividerStatus: { color: COLORS.textSoft, fontSize: 10, fontWeight: '700' },
  fixtureCard: {
    flexDirection: 'row',
    backgroundColor: COLORS.backgroundCard,
    borderWidth: 1,
    borderColor: COLORS.cardBorder,
    borderRadius: 14,
    padding: 11,
    marginBottom: 8,
    alignItems: 'center',
    gap: 10,
  },
  fixtureCardLive: {
    borderColor: COLORS.primaryGlow,
    backgroundColor: '#0a1a24',
  },
  fixtureStatusCol: { width: 64, alignItems: 'center' },
  statusBadge: {
    paddingHorizontal: 7,
    paddingVertical: 4,
    borderRadius: 7,
    minWidth: 56,
    alignItems: 'center',
  },
  badgeLIVE: {
    backgroundColor: COLORS.accentRedSoft,
    borderWidth: 1,
    borderColor: 'rgba(244,63,94,0.4)',
  },
  badgeHT: {
    backgroundColor: COLORS.accentGoldSoft,
    borderWidth: 1,
    borderColor: 'rgba(245,158,11,0.4)',
  },
  badgeFT: {
    backgroundColor: COLORS.primarySoft,
    borderWidth: 1,
    borderColor: 'rgba(52,211,153,0.35)',
  },
  badgeNS: { backgroundColor: 'rgba(255,255,255,0.06)' },
  statusBadgeText: { color: COLORS.textSoft, fontSize: 10, fontWeight: '800' },
  fixtureTeamsCol: { flex: 1, gap: 5 },
  teamLine: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  teamInfo: { flexDirection: 'row', alignItems: 'center', gap: 7, flex: 1 },
  smallLogo: { width: 18, height: 18, resizeMode: 'contain' },
  teamName: { color: COLORS.textMain, fontSize: 12, fontWeight: '700', flex: 1 },
  scoreNum: { color: COLORS.white, fontSize: 14, fontWeight: '900', minWidth: 20, textAlign: 'right' },
  goalsStrip: {
    color: COLORS.textMuted,
    fontSize: 10,
    marginTop: 3,
    paddingTop: 4,
    borderTopWidth: 1,
    borderTopColor: 'rgba(255,255,255,0.06)',
  },
  emptyBox: { padding: 30, alignItems: 'center' },
  emptyText: { color: COLORS.textDim, fontSize: 12 },
  miniStandingsCard: {
    backgroundColor: COLORS.backgroundCard,
    borderWidth: 1,
    borderColor: COLORS.cardBorder,
    borderRadius: 14,
    padding: 12,
    marginTop: 12,
  },
  miniHead: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  miniTitle: { color: COLORS.white, fontSize: 12, fontWeight: '800' },
  miniLink: { color: COLORS.accentBlue, fontSize: 11, fontWeight: '700' },
  miniRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 5,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(255,255,255,0.04)',
    gap: 8,
  },
  miniRank: { width: 18, color: COLORS.textMuted, fontSize: 11, fontWeight: '800', textAlign: 'center' },
  miniLogo: { width: 16, height: 16, resizeMode: 'contain' },
  miniTeam: { flex: 1, color: COLORS.white, fontSize: 11, fontWeight: '700' },
  miniStat: { width: 30, color: COLORS.textMuted, fontSize: 10, textAlign: 'right' },
  miniPts: { width: 32, color: COLORS.white, fontSize: 11, fontWeight: '900', textAlign: 'right' },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.75)',
    justifyContent: 'center',
    padding: 20,
  },
  modalCard: {
    backgroundColor: '#101626',
    borderRadius: 16,
    borderWidth: 1,
    borderColor: COLORS.cardBorderStrong,
    padding: 16,
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  modalTitle: { color: COLORS.white, fontSize: 14, fontWeight: '800' },
  modalClose: { color: COLORS.textMuted, fontSize: 16, fontWeight: '800', paddingHorizontal: 6 },
  modalRow: { paddingVertical: 10, paddingHorizontal: 10, borderRadius: 8 },
  modalRowActive: { backgroundColor: COLORS.accentRedSoft },
  modalRowText: { color: COLORS.textSoft, fontSize: 13 },
  matchModalHeader: { color: COLORS.accentBlue, fontSize: 12, fontWeight: '800', textAlign: 'center', marginBottom: 8 },
  matchModalScore: { color: COLORS.white, fontSize: 16, fontWeight: '900', textAlign: 'center', marginBottom: 12 },
  matchModalMeta: { color: COLORS.textSoft, fontSize: 12, marginBottom: 5, lineHeight: 18 },
  matchModalEvents: {
    marginTop: 8,
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: COLORS.cardBorder,
  },
  matchModalEvTitle: { color: COLORS.white, fontSize: 12, fontWeight: '800', marginBottom: 4 },
  modalCloseBtn: {
    backgroundColor: COLORS.accentRed,
    borderRadius: 10,
    paddingVertical: 10,
    alignItems: 'center',
    marginTop: 12,
  },
  modalCloseBtnText: { color: COLORS.white, fontSize: 13, fontWeight: '800' },
});

