import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Image,
  ActivityIndicator,
  Modal,
  FlatList,
  TextInput,
  RefreshControl,
} from 'react-native';
import { superligApi } from '../services/api';
import { COLORS } from '../theme/colors';
import { DEFAULT_TEAM_LOGO } from '../utils/format';

const HISTORICAL_CLUBS = [
  'Bursaspor',
  'Eskişehirspor',
  'Ankaragücü',
  'Altay',
  'Sivasspor',
  'Antalyaspor',
  'Kayserispor',
  'Adana Demirspor',
  'Sakaryaspor',
  'Gaziantepspor',
  'Denizlispor',
  'İstanbulspor',
  'Hatayspor',
  'Fatih Karagümrük',
  'Karşıyaka',
  'Adanaspor',
  'Boluspor',
];

const DERBY_PRESETS = [
  { label: 'GS vs FB', t1: 'Galatasaray', t2: 'Fenerbahçe' },
  { label: 'GS vs BJK', t1: 'Galatasaray', t2: 'Beşiktaş' },
  { label: 'FB vs BJK', t1: 'Fenerbahçe', t2: 'Beşiktaş' },
  { label: 'FB vs TS', t1: 'Fenerbahçe', t2: 'Trabzonspor' },
  { label: 'GS vs TS', t1: 'Galatasaray', t2: 'Trabzonspor' },
  { label: 'BJK vs TS', t1: 'Beşiktaş', t2: 'Trabzonspor' },
  { label: 'GÖZ vs KSK', t1: 'Göztepe', t2: 'Karşıyaka' },
  { label: 'BUR vs ESK', t1: 'Bursaspor', t2: 'Eskişehirspor' },
];

export default function RivalryScreen({ navigation, route }) {
  const [teams, setTeams] = useState([]);
  const [t1Id, setT1Id] = useState(route?.params?.team1Id || null);
  const [t2Id, setT2Id] = useState(route?.params?.team2Id || null);
  const [competition, setCompetition] = useState('ALL');
  const [rivalryData, setRivalryData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const [pickerTarget, setPickerTarget] = useState(null); // 1 | 2 | null
  const [pickerSearch, setPickerSearch] = useState('');
  const [matchSearch, setMatchSearch] = useState('');
  const [visibleCount, setVisibleCount] = useState(60);
  const [selectedMatch, setSelectedMatch] = useState(null);
  const [matchDetail, setMatchDetail] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const activeDetailReqRef = useRef(0);

  const handleOpenMatchDetail = useCallback(async (matchObj) => {
    if (!matchObj?.id) return;
    const reqId = ++activeDetailReqRef.current;
    setSelectedMatch(matchObj);
    setMatchDetail(null);
    setDetailLoading(true);
    try {
      const detail = await superligApi.getRivalryMatchDetail(matchObj.id);
      if (activeDetailReqRef.current === reqId && detail) {
        setMatchDetail(detail);
      }
    } catch (err) {
      console.log('Rivalry match detail error:', err?.message);
    } finally {
      if (activeDetailReqRef.current === reqId) {
        setDetailLoading(false);
      }
    }
  }, []);

  const handleCloseMatchDetail = useCallback(() => {
    activeDetailReqRef.current += 1;
    setSelectedMatch(null);
    setMatchDetail(null);
    setDetailLoading(false);
  }, []);

  const loadRivalry = useCallback(
    async (id1, id2, comp = competition, forceRefresh = false) => {
      if (!id1 || !id2) return;
      try {
        if (!forceRefresh) setLoading(true);
        const data = await superligApi.getRivalry(id1, id2, comp, forceRefresh);
        setRivalryData(data);
        setVisibleCount(60);
      } catch (err) {
        console.log('Rivalry load error:', err?.message);
      } finally {
        setLoading(false);
        setRefreshing(false);
      }
    },
    [competition]
  );

  useEffect(() => {
    let cancelled = false;
    async function init() {
      try {
        const p1 = route?.params?.team1Id;
        const p2 = route?.params?.team2Id;
        const hasInitialPair = Boolean(p1 && p2 && String(p1) !== String(p2));
        if (hasInitialPair) {
          loadRivalry(p1, p2, 'ALL', false);
        }

        const scopeTeams = await superligApi.getTeams({ scope: 'rivalry' });
        if (cancelled) return;

        const list = Array.isArray(scopeTeams) ? scopeTeams : [];
        const activeList = list.filter((t) => t.is_super_lig);
        const histList = list.filter(
          (t) => !t.is_super_lig && HISTORICAL_CLUBS.includes(t.name)
        );
        const combined = [...activeList, ...histList];
        setTeams(combined);

        if (!hasInitialPair) {
          if (combined.length >= 2) {
            const gs = combined.find((t) => t.name?.includes('Galatasaray'));
            const fb = combined.find((t) => t.name?.includes('Fenerbahçe'));
            const byName1 =
              route?.params?.team1Name &&
              combined.find(
                (t) => t.name?.toLowerCase() === String(route.params.team1Name).toLowerCase()
              );
            const byName2 =
              route?.params?.team2Name &&
              combined.find(
                (t) => t.name?.toLowerCase() === String(route.params.team2Name).toLowerCase()
              );
            const init1 =
              route?.params?.team1Id || byName1?.id || t1Id || gs?.id || combined[0].id;
            let init2 =
              route?.params?.team2Id || byName2?.id || t2Id || fb?.id || combined[1].id;
            if (String(init1) === String(init2)) {
              init2 = combined.find((t) => String(t.id) !== String(init1))?.id || combined[1].id;
            }
            setT1Id(init1);
            setT2Id(init2);
            loadRivalry(init1, init2, 'ALL', false);
          } else {
            setLoading(false);
          }
        }
      } catch (err) {
        console.log('Rivalry init error:', err?.message);
        setLoading(false);
      }
    }
    init();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    const p1 = route?.params?.team1Id;
    const p2 = route?.params?.team2Id;
    const n1 = route?.params?.team1Name;
    const n2 = route?.params?.team2Name;
    if (!p1 && !p2 && !n1 && !n2) return;

    let resolved1 = p1;
    let resolved2 = p2;
    if (!resolved1 && n1 && teams.length > 0) {
      resolved1 = teams.find((t) => t.name?.toLowerCase() === String(n1).toLowerCase())?.id;
    }
    if (!resolved2 && n2 && teams.length > 0) {
      resolved2 = teams.find((t) => t.name?.toLowerCase() === String(n2).toLowerCase())?.id;
    }
    if (resolved1 && resolved2 && String(resolved1) !== String(resolved2)) {
      setT1Id(resolved1);
      setT2Id(resolved2);
      setCompetition('ALL');
      loadRivalry(resolved1, resolved2, 'ALL', false);
    }
  }, [
    route?.params?.team1Id,
    route?.params?.team2Id,
    route?.params?.team1Name,
    route?.params?.team2Name,
    route?.params?.ts,
  ]);

  const handleSwapTeams = () => {
    if (!t1Id || !t2Id) return;
    const next1 = t2Id;
    const next2 = t1Id;
    setT1Id(next1);
    setT2Id(next2);
    loadRivalry(next1, next2, competition, false);
  };

  const handleSelectTeam = (id) => {
    const target = pickerTarget;
    setPickerTarget(null);
    setPickerSearch('');
    if (target === 1) {
      let next2 = t2Id;
      if (String(id) === String(t2Id)) {
        next2 = t1Id;
        setT2Id(next2);
      }
      setT1Id(id);
      loadRivalry(id, next2, competition, false);
    } else if (target === 2) {
      let next1 = t1Id;
      if (String(id) === String(t1Id)) {
        next1 = t2Id;
        setT1Id(next1);
      }
      setT2Id(id);
      loadRivalry(next1, id, competition, false);
    }
  };

  const handleSelectCompetition = (compKey) => {
    setCompetition(compKey);
    loadRivalry(t1Id, t2Id, compKey, false);
  };

  const handlePresetPress = (preset) => {
    const found1 = teams.find((t) => t.name?.toLowerCase().includes(preset.t1.toLowerCase()));
    const found2 = teams.find((t) => t.name?.toLowerCase().includes(preset.t2.toLowerCase()));
    if (found1 && found2) {
      setT1Id(found1.id);
      setT2Id(found2.id);
      setCompetition('ALL');
      loadRivalry(found1.id, found2.id, 'ALL', false);
    }
  };

  const onRefresh = () => {
    setRefreshing(true);
    loadRivalry(t1Id, t2Id, competition, true);
  };

  const team1 = rivalryData?.team1 || teams.find((t) => String(t.id) === String(t1Id)) || {};
  const team2 = rivalryData?.team2 || teams.find((t) => String(t.id) === String(t2Id)) || {};
  const summary = rivalryData?.summary || {};
  const competitions = rivalryData?.competitions || [];
  const allMatches = rivalryData?.matches || [];

  const filteredMatches = useMemo(() => {
    const q = matchSearch.trim().toLowerCase();
    if (!q) return allMatches;
    return allMatches.filter((m) => {
      const seasonStr = (m.season_label || '').toLowerCase();
      const dateStr = (m.match_date_display || '').toLowerCase();
      const compStr = (m.competition || '').toLowerCase();
      const roundStr = (m.round_label || '').toLowerCase();
      const scoreStr =
        m.home_score !== null && m.away_score !== null ? `${m.home_score}:${m.away_score}` : '';
      const scoreDash =
        m.home_score !== null && m.away_score !== null ? `${m.home_score}-${m.away_score}` : '';
      return (
        seasonStr.includes(q) ||
        dateStr.includes(q) ||
        compStr.includes(q) ||
        roundStr.includes(q) ||
        scoreStr.includes(q) ||
        scoreDash.includes(q)
      );
    });
  }, [allMatches, matchSearch]);

  const displayedMatches = useMemo(
    () => filteredMatches.slice(0, visibleCount),
    [filteredMatches, visibleCount]
  );

  const filteredPickerTeams = useMemo(() => {
    const q = pickerSearch.trim().toLowerCase();
    if (!q) return teams;
    return teams.filter(
      (t) =>
        t.name?.toLowerCase().includes(q) ||
        t.city?.toLowerCase().includes(q) ||
        t.short_name?.toLowerCase().includes(q)
    );
  }, [teams, pickerSearch]);

  const renderBiggestWinRow = (label, matchObj, badgeColor) => {
    if (!matchObj) return null;
    return (
      <TouchableOpacity
        style={styles.recordItem}
        activeOpacity={0.75}
        onPress={() => handleOpenMatchDetail(matchObj)}
      >
        <View style={[styles.recordDot, { backgroundColor: badgeColor }]} />
        <View style={{ flex: 1 }}>
          <Text style={styles.recordLabel}>{label}</Text>
          <Text style={styles.recordVal}>
            {matchObj.home_team?.name} {matchObj.home_score} - {matchObj.away_score}{' '}
            {matchObj.away_team?.name}
          </Text>
        </View>
        <View style={styles.recordMetaBox}>
          <Text style={styles.recordSeason}>{matchObj.season_label}</Text>
          <Text style={styles.recordDate}>{matchObj.match_date_display}</Text>
        </View>
      </TouchableOpacity>
    );
  };

  return (
    <View style={styles.container}>
      {/* TOP HEADER */}
      <View style={styles.topHeader}>
        <TouchableOpacity style={styles.backBtn} onPress={() => navigation.goBack()}>
          <Text style={styles.backBtnText}>←</Text>
        </TouchableOpacity>
        <View style={{ alignItems: 'center' }}>
          <Text style={styles.headerTitle}>İKİLİ REKABET & MAÇLAR</Text>
          <Text style={styles.headerSub}>1959’dan Günümüze Tüm Karşılaşmalar</Text>
        </View>
        <TouchableOpacity style={styles.refreshBtn} onPress={onRefresh}>
          <Text style={styles.refreshBtnText}>🔄</Text>
        </TouchableOpacity>
      </View>

      <ScrollView
        contentContainerStyle={styles.content}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={COLORS.accentRed} />
        }
      >
        {/* QUICK DERBY PRESETS */}
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={styles.presetRow}
        >
          {DERBY_PRESETS.map((p) => {
            const isSelected =
              (team1?.name?.toLowerCase().includes(p.t1.toLowerCase()) &&
                team2?.name?.toLowerCase().includes(p.t2.toLowerCase())) ||
              (team1?.name?.toLowerCase().includes(p.t2.toLowerCase()) &&
                team2?.name?.toLowerCase().includes(p.t1.toLowerCase()));
            return (
              <TouchableOpacity
                key={p.label}
                style={[styles.presetChip, isSelected && styles.presetChipActive]}
                onPress={() => handlePresetPress(p)}
              >
                <Text style={[styles.presetChipText, isSelected && styles.presetChipTextActive]}>
                  ⚔️ {p.label}
                </Text>
              </TouchableOpacity>
            );
          })}
        </ScrollView>

        {/* 2-TEAM SELECTOR CARD */}
        <View style={styles.selectorCard}>
          <TouchableOpacity
            style={[styles.teamBox, styles.team1Box]}
            activeOpacity={0.85}
            onPress={() => setPickerTarget(1)}
          >
            <Image
              source={{ uri: team1.logo_url || DEFAULT_TEAM_LOGO }}
              style={styles.teamLogo}
            />
            <Text style={styles.teamName} numberOfLines={1}>
              {team1.name || '1. Takım'}
            </Text>
            <Text style={styles.teamSub} numberOfLines={1}>
              {team1.city || 'Süper Lig'}
            </Text>
            <View style={[styles.changePill, { backgroundColor: 'rgba(239,68,68,0.18)' }]}>
              <Text style={[styles.changePillText, { color: '#f87171' }]}>Takım Seç ▾</Text>
            </View>
          </TouchableOpacity>

          <View style={styles.vsColumn}>
            <View style={styles.vsCircle}>
              <Text style={styles.vsText}>VS</Text>
            </View>
            <TouchableOpacity style={styles.swapBtn} onPress={handleSwapTeams}>
              <Text style={styles.swapBtnText}>⇄</Text>
            </TouchableOpacity>
          </View>

          <TouchableOpacity
            style={[styles.teamBox, styles.team2Box]}
            activeOpacity={0.85}
            onPress={() => setPickerTarget(2)}
          >
            <Image
              source={{ uri: team2.logo_url || DEFAULT_TEAM_LOGO }}
              style={styles.teamLogo}
            />
            <Text style={styles.teamName} numberOfLines={1}>
              {team2.name || '2. Takım'}
            </Text>
            <Text style={styles.teamSub} numberOfLines={1}>
              {team2.city || 'Süper Lig'}
            </Text>
            <View style={[styles.changePill, { backgroundColor: 'rgba(56,189,248,0.18)' }]}>
              <Text style={[styles.changePillText, { color: '#38bdf8' }]}>Takım Seç ▾</Text>
            </View>
          </TouchableOpacity>
        </View>

        {/* COMPETITION FILTER TABS */}
        {competitions.length > 0 && (
          <ScrollView
            horizontal
            showsHorizontalScrollIndicator={false}
            contentContainerStyle={styles.compTabsRow}
          >
            {competitions.map((c) => {
              const active = competition === c.key;
              return (
                <TouchableOpacity
                  key={c.key}
                  style={[styles.compTab, active && styles.compTabActive]}
                  onPress={() => handleSelectCompetition(c.key)}
                >
                  <Text style={[styles.compTabText, active && styles.compTabTextActive]}>
                    {c.label} ({c.count})
                  </Text>
                </TouchableOpacity>
              );
            })}
          </ScrollView>
        )}

        {loading ? (
          <View style={styles.loadingWrap}>
            <ActivityIndicator size="large" color={COLORS.accentRed} />
            <Text style={styles.loadingText}>Rekabet arşivi yükleniyor...</Text>
          </View>
        ) : (
          <>
            {/* HEAD-TO-HEAD SUMMARY BANNER */}
            <View style={styles.summaryCard}>
              <Text style={styles.cardSectionTitle}>GENEL REKABET ÖZETİ</Text>

              <View style={styles.bigStatsRow}>
                <View style={styles.bigStatCol}>
                  <Text style={[styles.bigStatNum, { color: '#f87171' }]}>
                    {summary.team1_wins ?? 0}
                  </Text>
                  <Text style={styles.bigStatLabel} numberOfLines={1}>
                    {team1.short_name || team1.name} Galibiyet
                  </Text>
                  <Text style={styles.bigStatPct}>%{summary.team1_win_pct ?? 0}</Text>
                </View>

                <View style={styles.bigStatColCenter}>
                  <Text style={[styles.bigStatNum, { color: COLORS.accentGold }]}>
                    {summary.draws ?? 0}
                  </Text>
                  <Text style={styles.bigStatLabel}>Beraberlik</Text>
                  <Text style={styles.bigStatPct}>%{summary.draw_pct ?? 0}</Text>
                </View>

                <View style={styles.bigStatCol}>
                  <Text style={[styles.bigStatNum, { color: '#38bdf8' }]}>
                    {summary.team2_wins ?? 0}
                  </Text>
                  <Text style={styles.bigStatLabel} numberOfLines={1}>
                    {team2.short_name || team2.name} Galibiyet
                  </Text>
                  <Text style={styles.bigStatPct}>%{summary.team2_win_pct ?? 0}</Text>
                </View>
              </View>

              {/* 3-SEGMENT WIN/DRAW/LOSS BAR */}
              <View style={styles.triBarTrack}>
                <View
                  style={[
                    styles.triBarSeg,
                    {
                      flex: Math.max(summary.team1_win_pct || 1, 2),
                      backgroundColor: '#ef4444',
                    },
                  ]}
                />
                <View
                  style={[
                    styles.triBarSeg,
                    {
                      flex: Math.max(summary.draw_pct || 1, 2),
                      backgroundColor: '#f59e0b',
                    },
                  ]}
                />
                <View
                  style={[
                    styles.triBarSeg,
                    {
                      flex: Math.max(summary.team2_win_pct || 1, 2),
                      backgroundColor: '#38bdf8',
                    },
                  ]}
                />
              </View>

              {/* GOALS & AVERAGES STRIP */}
              <View style={styles.metricsStrip}>
                <View style={styles.metricBox}>
                  <Text style={styles.metricVal}>{summary.total_matches ?? 0}</Text>
                  <Text style={styles.metricLbl}>Oynanan Maç</Text>
                </View>
                <View style={styles.metricDivider} />
                <View style={styles.metricBox}>
                  <Text style={[styles.metricVal, { color: '#f87171' }]}>
                    {summary.team1_goals ?? 0}
                  </Text>
                  <Text style={styles.metricLbl}>{team1.short_name || '1. Takım'} Gol</Text>
                </View>
                <View style={styles.metricDivider} />
                <View style={styles.metricBox}>
                  <Text style={[styles.metricVal, { color: '#38bdf8' }]}>
                    {summary.team2_goals ?? 0}
                  </Text>
                  <Text style={styles.metricLbl}>{team2.short_name || '2. Takım'} Gol</Text>
                </View>
                <View style={styles.metricDivider} />
                <View style={styles.metricBox}>
                  <Text style={[styles.metricVal, { color: COLORS.accentGreen }]}>
                    {summary.avg_goals_per_match ?? 0}
                  </Text>
                  <Text style={styles.metricLbl}>Gol / Maç</Text>
                </View>
              </View>

              {/* HOME / AWAY BREAKDOWN */}
              <View style={styles.homeSplitRow}>
                <View style={styles.homeSplitCard}>
                  <Text style={styles.homeSplitTitle} numberOfLines={1}>
                    🏟️ {team1.name} Evinde ({summary.team1_home?.played ?? 0} Maç)
                  </Text>
                  <Text style={styles.homeSplitStats}>
                    <Text style={{ color: '#f87171', fontWeight: '800' }}>
                      {summary.team1_home?.wins ?? 0}G
                    </Text>
                    {' • '}
                    <Text style={{ color: COLORS.accentGold, fontWeight: '800' }}>
                      {summary.team1_home?.draws ?? 0}B
                    </Text>
                    {' • '}
                    <Text style={{ color: '#38bdf8', fontWeight: '800' }}>
                      {summary.team1_home?.losses ?? 0}M
                    </Text>
                    {'  ('}
                    {summary.team1_home?.goals_for ?? 0}:{summary.team1_home?.goals_against ?? 0}
                    {')'}
                  </Text>
                </View>

                <View style={styles.homeSplitCard}>
                  <Text style={styles.homeSplitTitle} numberOfLines={1}>
                    🏟️ {team2.name} Evinde ({summary.team2_home?.played ?? 0} Maç)
                  </Text>
                  <Text style={styles.homeSplitStats}>
                    <Text style={{ color: '#38bdf8', fontWeight: '800' }}>
                      {summary.team2_home?.wins ?? 0}G
                    </Text>
                    {' • '}
                    <Text style={{ color: COLORS.accentGold, fontWeight: '800' }}>
                      {summary.team2_home?.draws ?? 0}B
                    </Text>
                    {' • '}
                    <Text style={{ color: '#f87171', fontWeight: '800' }}>
                      {summary.team2_home?.losses ?? 0}M
                    </Text>
                    {'  ('}
                    {summary.team2_home?.goals_for ?? 0}:{summary.team2_home?.goals_against ?? 0}
                    {')'}
                  </Text>
                </View>
              </View>

              {/* RECORDS / BIGGEST WINS */}
              {(summary.biggest_team1_win ||
                summary.biggest_team2_win ||
                summary.highest_scoring_match) && (
                <View style={styles.recordsBox}>
                  {renderBiggestWinRow(
                    `En Farklı ${team1.name} Galibiyeti`,
                    summary.biggest_team1_win,
                    '#ef4444'
                  )}
                  {renderBiggestWinRow(
                    `En Farklı ${team2.name} Galibiyeti`,
                    summary.biggest_team2_win,
                    '#38bdf8'
                  )}
                  {renderBiggestWinRow(
                    'En Gollü Karşılaşma',
                    summary.highest_scoring_match,
                    '#10b981'
                  )}
                </View>
              )}

              {/* ALGORITHMIC ANALYSIS BOX */}
              {Boolean(summary.analysis) && (
                <View style={styles.analysisBox}>
                  <Text style={styles.analysisTitle}>📊 REKABET ANALİZİ</Text>
                  <Text style={styles.analysisText}>{summary.analysis}</Text>
                </View>
              )}
            </View>

            {/* SEARCH & MATCH LIST HEADER */}
            <View style={styles.matchesHeaderRow}>
              <Text style={styles.sectionTitle}>
                TÜM KARŞILAŞMALAR ({filteredMatches.length})
              </Text>
              {summary.upcoming_matches > 0 && (
                <Text style={styles.upcomingBadge}>
                  +{summary.upcoming_matches} Planlanan Maç
                </Text>
              )}
            </View>

            <View style={styles.searchBarWrap}>
              <Text style={styles.searchIcon}>🔍</Text>
              <TextInput
                style={styles.searchInput}
                placeholder="Sezon, tarih, turnuva veya skor ara (örn: 2026/2027, 1959, 3:0)..."
                placeholderTextColor={COLORS.textDim}
                value={matchSearch}
                onChangeText={(txt) => {
                  setMatchSearch(txt);
                  setVisibleCount(60);
                }}
              />
              {Boolean(matchSearch) && (
                <TouchableOpacity onPress={() => setMatchSearch('')}>
                  <Text style={styles.clearBtn}>✕</Text>
                </TouchableOpacity>
              )}
            </View>

            {/* ALL MATCHES LIST */}
            {displayedMatches.length === 0 ? (
              <View style={styles.emptyCard}>
                <Text style={styles.emptyTitle}>Kayıtlı Karşılaşma Bulunamadı</Text>
                <Text style={styles.emptySub}>
                  Seçilen filtrede bu iki takım arasında maç kaydı yer almıyor.
                </Text>
              </View>
            ) : (
              displayedMatches.map((m) => {
                const isNS = m.status !== 'FT' || m.home_score === null || m.away_score === null;
                const isT1Winner = m.winner_team_id && String(m.winner_team_id) === String(team1.id);
                const isT2Winner = m.winner_team_id && String(m.winner_team_id) === String(team2.id);
                const homeWon = !isNS && m.home_score > m.away_score;
                const awayWon = !isNS && m.away_score > m.home_score;

                return (
                  <TouchableOpacity
                    key={m.tm_match_id || m.id}
                    activeOpacity={0.78}
                    onPress={() => handleOpenMatchDetail(m)}
                    style={[
                      styles.matchCard,
                      isT1Winner && styles.matchCardT1,
                      isT2Winner && styles.matchCardT2,
                    ]}
                  >
                    {/* Top Meta Row */}
                    <View style={styles.matchTopRow}>
                      <View style={styles.matchTagRow}>
                        <View style={styles.seasonPill}>
                          <Text style={styles.seasonPillText}>{m.season_label}</Text>
                        </View>
                        <Text style={styles.compLabelText}>
                          {m.competition}
                          {m.round_label ? ` • ${m.round_label}` : ''}
                        </Text>
                      </View>
                      <Text style={styles.dateText}>
                        {m.match_date_display}
                        {m.match_time ? ` • ${m.match_time}` : ''}
                      </Text>
                    </View>

                    {/* Teams & Score Row */}
                    <View style={styles.matchBodyRow}>
                      <View style={styles.matchTeamHome}>
                        <Image
                          source={{ uri: m.home_team?.logo_url || DEFAULT_TEAM_LOGO }}
                          style={styles.matchTeamLogo}
                        />
                        <View style={{ flex: 1 }}>
                          <Text
                            style={[styles.matchTeamName, homeWon && styles.matchTeamWinner]}
                            numberOfLines={1}
                          >
                            {m.home_team?.name}
                          </Text>
                          {Boolean(m.home_team?.rank) && (
                            <Text style={styles.rankSubText}>Sıra: {m.home_team.rank}</Text>
                          )}
                        </View>
                      </View>

                      <View
                        style={[
                          styles.scoreBox,
                          isNS && styles.scoreBoxNS,
                          isT1Winner && styles.scoreBoxT1,
                          isT2Winner && styles.scoreBoxT2,
                        ]}
                      >
                        <Text style={styles.scoreText}>
                          {isNS ? 'v' : `${m.home_score} : ${m.away_score}`}
                        </Text>
                        {Boolean(m.score_note) && (
                          <Text style={styles.scoreNoteText}>{m.score_note}</Text>
                        )}
                        {isNS && <Text style={styles.nsLabel}>Oynanacak</Text>}
                      </View>

                      <View style={styles.matchTeamAway}>
                        <View style={{ flex: 1, alignItems: 'flex-end' }}>
                          <Text
                            style={[styles.matchTeamName, awayWon && styles.matchTeamWinner]}
                            numberOfLines={1}
                          >
                            {m.away_team?.name}
                          </Text>
                          {Boolean(m.away_team?.rank) && (
                            <Text style={styles.rankSubText}>Sıra: {m.away_team.rank}</Text>
                          )}
                        </View>
                        <Image
                          source={{ uri: m.away_team?.logo_url || DEFAULT_TEAM_LOGO }}
                          style={styles.matchTeamLogo}
                        />
                      </View>
                    </View>

                    {/* Footer */}
                    <View style={styles.matchFooterRow}>
                      {Boolean(m.attendance) ? (
                        <Text style={styles.attendanceText}>👥 Seyirci: {m.attendance}</Text>
                      ) : (
                        <View />
                      )}
                      <Text style={styles.detailHintText}>Detaylar →</Text>
                    </View>
                  </TouchableOpacity>
                );
              })
            )}

            {/* LOAD MORE BUTTON */}
            {filteredMatches.length > visibleCount && (
              <TouchableOpacity
                style={styles.loadMoreBtn}
                onPress={() => setVisibleCount((prev) => prev + 80)}
              >
                <Text style={styles.loadMoreText}>
                  Daha Fazla Maç Göster ({filteredMatches.length - visibleCount} maç kaldı) ↓
                </Text>
              </TouchableOpacity>
            )}
          </>
        )}
      </ScrollView>

      {/* TEAM PICKER MODAL */}
      <Modal
        visible={pickerTarget !== null}
        animationType="slide"
        transparent
        onRequestClose={() => setPickerTarget(null)}
      >
        <View style={styles.modalBackdrop}>
          <View style={styles.modalSheet}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>
                {pickerTarget === 1 ? '1. Takımı Seç' : '2. Takımı Seç'}
              </Text>
              <TouchableOpacity
                style={styles.modalCloseBtn}
                onPress={() => {
                  setPickerTarget(null);
                  setPickerSearch('');
                }}
              >
                <Text style={styles.modalCloseText}>✕</Text>
              </TouchableOpacity>
            </View>

            <TextInput
              style={styles.modalSearchInput}
              placeholder="Kulüp veya şehir ara..."
              placeholderTextColor={COLORS.textDim}
              value={pickerSearch}
              onChangeText={setPickerSearch}
            />

            <FlatList
              data={filteredPickerTeams}
              keyExtractor={(item) => String(item.id)}
              renderItem={({ item }) => {
                const isSelected =
                  (pickerTarget === 1 && String(item.id) === String(t1Id)) ||
                  (pickerTarget === 2 && String(item.id) === String(t2Id));
                return (
                  <TouchableOpacity
                    style={[styles.modalTeamRow, isSelected && styles.modalTeamRowSelected]}
                    onPress={() => handleSelectTeam(item.id)}
                  >
                    <Image
                      source={{ uri: item.logo_url || DEFAULT_TEAM_LOGO }}
                      style={styles.modalTeamLogo}
                    />
                    <View style={{ flex: 1 }}>
                      <Text style={styles.modalTeamName}>{item.name}</Text>
                      <Text style={styles.modalTeamSub}>
                        {item.is_super_lig ? '2026/2027 Süper Lig' : 'Tarihi Süper Lig Kulübü'}
                        {item.city ? ` • ${item.city}` : ''}
                      </Text>
                    </View>
                    {isSelected && <Text style={styles.selectedCheck}>✓</Text>}
                  </TouchableOpacity>
                );
              }}
            />
          </View>
        </View>
      </Modal>

      {/* MATCH DETAIL MODAL */}
      <Modal
        visible={Boolean(selectedMatch)}
        transparent
        animationType="fade"
        onRequestClose={handleCloseMatchDetail}
      >
        <TouchableOpacity
          style={styles.detailModalOverlay}
          activeOpacity={1}
          onPress={handleCloseMatchDetail}
        >
          {selectedMatch && (() => {
            const activeMatch =
              matchDetail && String(matchDetail.id) === String(selectedMatch.id)
                ? matchDetail
                : selectedMatch;
            const isNS =
              activeMatch.status !== 'FT' ||
              activeMatch.home_score === null ||
              activeMatch.away_score === null;
            const events = Array.isArray(activeMatch.events) ? activeMatch.events : [];
            const cards = Array.isArray(activeMatch.cards) ? activeMatch.cards : [];

            return (
              <View style={styles.detailModalCard} onStartShouldSetResponder={() => true}>
                <Text style={styles.detailModalHeader}>
                  {activeMatch.season_label} • {activeMatch.competition}
                  {activeMatch.round_label ? ` • ${activeMatch.round_label}` : ''}
                </Text>

                <View style={styles.detailTeamsRow}>
                  <View style={styles.detailTeamCol}>
                    <Image
                      source={{ uri: activeMatch.home_team?.logo_url || DEFAULT_TEAM_LOGO }}
                      style={styles.detailTeamLogo}
                    />
                    <Text style={styles.detailTeamName} numberOfLines={2}>
                      {activeMatch.home_team?.name}
                    </Text>
                  </View>

                  <View style={styles.detailScoreWrap}>
                    <Text style={styles.detailScoreText}>
                      {isNS ? '- : -' : `${activeMatch.home_score} - ${activeMatch.away_score}`}
                    </Text>
                    {Boolean(activeMatch.score_note) && (
                      <Text style={styles.detailScoreNote}>{activeMatch.score_note}</Text>
                    )}
                  </View>

                  <View style={styles.detailTeamCol}>
                    <Image
                      source={{ uri: activeMatch.away_team?.logo_url || DEFAULT_TEAM_LOGO }}
                      style={styles.detailTeamLogo}
                    />
                    <Text style={styles.detailTeamName} numberOfLines={2}>
                      {activeMatch.away_team?.name}
                    </Text>
                  </View>
                </View>

                <ScrollView style={{ maxHeight: 280 }} showsVerticalScrollIndicator={false}>
                  <Text style={styles.detailMeta}>
                    • Durum: {activeMatch.status_display || (isNS ? 'Oynanacak' : 'Maç Bitti (MS)')}
                  </Text>
                  <Text style={styles.detailMeta}>
                    • Tarih: {activeMatch.match_date_display || '-'}
                    {activeMatch.match_time ? ` • ${activeMatch.match_time}` : ''}
                  </Text>
                  {Boolean(activeMatch.halftime_score) && (
                    <Text style={styles.detailMeta}>
                      • İlk Yarı: {activeMatch.halftime_score}
                    </Text>
                  )}
                  <Text style={styles.detailMeta}>
                    • Stadyum: {activeMatch.venue || 'Belirtilmedi'}
                  </Text>
                  <Text style={styles.detailMeta}>
                    • Hakem: {activeMatch.referee || 'TFF Ataması'}
                  </Text>
                  {Boolean(activeMatch.attendance) && (
                    <Text style={styles.detailMeta}>• Seyirci: {activeMatch.attendance}</Text>
                  )}

                  {detailLoading ? (
                    <View style={styles.detailLoadingBox}>
                      <ActivityIndicator size="small" color={COLORS.accentBlue} />
                      <Text style={styles.detailLoadingText}>
                        Gol ve maç olayları yükleniyor...
                      </Text>
                    </View>
                  ) : (
                    <>
                      {events.length > 0 ? (
                        <View style={styles.detailEventsBox}>
                          <Text style={styles.detailEvTitle}>Goller:</Text>
                          {events.map((e, i) => (
                            <Text key={i} style={styles.detailMeta}>
                              ⚽ {e.minute ? `${e.minute} ` : ''}
                              {e.scorer}
                              {e.is_penalty ? ' (P)' : ''}
                              {e.is_own_goal ? ' (KK)' : ''}
                              {e.assist && !e.is_own_goal ? ` (Asist: ${e.assist})` : ''}{' '}
                              ({e.team_short || e.team_name})
                            </Text>
                          ))}
                        </View>
                      ) : !isNS && Number(activeMatch.home_score || 0) + Number(activeMatch.away_score || 0) === 0 ? (
                        <View style={styles.detailEventsBox}>
                          <Text style={styles.detailMeta}>⚽ Gol sesi çıkmadı (0 - 0)</Text>
                        </View>
                      ) : null}

                      {cards.length > 0 && (
                        <View style={styles.detailEventsBox}>
                          <Text style={styles.detailEvTitle}>Kırmızı Kartlar:</Text>
                          {cards.map((c, i) => (
                            <Text key={i} style={styles.detailMeta}>
                              🟥 {c.minute ? `${c.minute} ` : ''}
                              {c.player} ({c.card_type}) ({c.team_short || c.team_name})
                            </Text>
                          ))}
                        </View>
                      )}
                    </>
                  )}
                </ScrollView>

                <TouchableOpacity style={styles.detailCloseBtn} onPress={handleCloseMatchDetail}>
                  <Text style={styles.detailCloseBtnText}>Tamam</Text>
                </TouchableOpacity>
              </View>
            );
          })()}
        </TouchableOpacity>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.background },
  topHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 14,
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.cardBorder,
    backgroundColor: COLORS.backgroundCard,
  },
  backBtn: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: 'rgba(255,255,255,0.06)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  backBtnText: { color: COLORS.white, fontSize: 18, fontWeight: '900' },
  headerTitle: { color: COLORS.white, fontSize: 14, fontWeight: '900', letterSpacing: 0.6 },
  headerSub: { color: COLORS.accentGold, fontSize: 10, fontWeight: '700', marginTop: 1 },
  refreshBtn: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: 'rgba(255,255,255,0.06)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  refreshBtnText: { fontSize: 15 },
  content: { padding: 14, paddingBottom: 44 },
  presetRow: { gap: 8, paddingBottom: 12 },
  presetChip: {
    backgroundColor: COLORS.backgroundCard,
    borderWidth: 1,
    borderColor: COLORS.cardBorder,
    borderRadius: 20,
    paddingHorizontal: 12,
    paddingVertical: 6,
  },
  presetChipActive: {
    borderColor: COLORS.accentGold,
    backgroundColor: 'rgba(245,158,11,0.14)',
  },
  presetChipText: { color: COLORS.textMuted, fontSize: 11, fontWeight: '800' },
  presetChipTextActive: { color: COLORS.accentGold },
  selectorCard: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: COLORS.backgroundCard,
    borderRadius: 18,
    borderWidth: 1,
    borderColor: COLORS.cardBorder,
    padding: 12,
    marginBottom: 12,
  },
  teamBox: {
    flex: 1,
    alignItems: 'center',
    paddingVertical: 10,
    paddingHorizontal: 8,
    borderRadius: 14,
    borderWidth: 1,
  },
  team1Box: {
    borderColor: 'rgba(239,68,68,0.35)',
    backgroundColor: 'rgba(239,68,68,0.06)',
  },
  team2Box: {
    borderColor: 'rgba(56,189,248,0.35)',
    backgroundColor: 'rgba(56,189,248,0.06)',
  },
  teamLogo: { width: 52, height: 52, resizeMode: 'contain', marginBottom: 8 },
  teamName: { color: COLORS.white, fontSize: 13, fontWeight: '900', textAlign: 'center' },
  teamSub: { color: COLORS.textDim, fontSize: 10, marginTop: 2, marginBottom: 8 },
  changePill: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 10,
  },
  changePillText: { fontSize: 10, fontWeight: '800' },
  vsColumn: { alignItems: 'center', paddingHorizontal: 8, gap: 8 },
  vsCircle: {
    width: 34,
    height: 34,
    borderRadius: 17,
    backgroundColor: 'rgba(255,255,255,0.07)',
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: COLORS.cardBorderStrong,
  },
  vsText: { color: COLORS.accentGold, fontSize: 11, fontWeight: '900' },
  swapBtn: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: 'rgba(56,189,248,0.14)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  swapBtnText: { color: '#38bdf8', fontSize: 15, fontWeight: '900' },
  compTabsRow: { gap: 8, paddingBottom: 12 },
  compTab: {
    backgroundColor: COLORS.backgroundCard,
    borderWidth: 1,
    borderColor: COLORS.cardBorder,
    borderRadius: 12,
    paddingHorizontal: 12,
    paddingVertical: 7,
  },
  compTabActive: {
    backgroundColor: COLORS.accentRedSoft,
    borderColor: COLORS.accentRedBorder,
  },
  compTabText: { color: COLORS.textMuted, fontSize: 11, fontWeight: '800' },
  compTabTextActive: { color: '#f87171' },
  loadingWrap: { alignItems: 'center', justifyContent: 'center', paddingVertical: 50 },
  loadingText: { color: COLORS.textMuted, fontSize: 12, marginTop: 10 },
  summaryCard: {
    backgroundColor: COLORS.backgroundCard,
    borderRadius: 18,
    borderWidth: 1,
    borderColor: COLORS.cardBorder,
    padding: 14,
    marginBottom: 16,
  },
  cardSectionTitle: {
    color: COLORS.textMuted,
    fontSize: 11,
    fontWeight: '900',
    letterSpacing: 0.7,
    textAlign: 'center',
    marginBottom: 12,
  },
  bigStatsRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  bigStatCol: { flex: 1, alignItems: 'center' },
  bigStatColCenter: { flex: 1, alignItems: 'center' },
  bigStatNum: { fontSize: 28, fontWeight: '900' },
  bigStatLabel: { color: COLORS.white, fontSize: 11, fontWeight: '800', marginTop: 2 },
  bigStatPct: { color: COLORS.textDim, fontSize: 10, fontWeight: '700', marginTop: 2 },
  triBarTrack: {
    flexDirection: 'row',
    height: 10,
    borderRadius: 5,
    overflow: 'hidden',
    backgroundColor: 'rgba(255,255,255,0.06)',
    gap: 2,
    marginBottom: 14,
  },
  triBarSeg: { height: '100%' },
  metricsStrip: {
    flexDirection: 'row',
    backgroundColor: 'rgba(255,255,255,0.03)',
    borderRadius: 12,
    paddingVertical: 10,
    paddingHorizontal: 6,
    alignItems: 'center',
    justifyContent: 'space-around',
    marginBottom: 12,
  },
  metricBox: { flex: 1, alignItems: 'center' },
  metricVal: { color: COLORS.white, fontSize: 15, fontWeight: '900' },
  metricLbl: { color: COLORS.textDim, fontSize: 10, marginTop: 2, fontWeight: '700' },
  metricDivider: { width: 1, height: 24, backgroundColor: COLORS.cardBorder },
  homeSplitRow: { flexDirection: 'row', gap: 8, marginBottom: 12 },
  homeSplitCard: {
    flex: 1,
    backgroundColor: 'rgba(255,255,255,0.03)',
    borderRadius: 10,
    padding: 9,
    borderWidth: 1,
    borderColor: COLORS.cardBorder,
  },
  homeSplitTitle: { color: COLORS.textSoft, fontSize: 10, fontWeight: '800', marginBottom: 4 },
  homeSplitStats: { color: COLORS.textMuted, fontSize: 11, fontWeight: '700' },
  recordsBox: {
    backgroundColor: 'rgba(255,255,255,0.025)',
    borderRadius: 12,
    padding: 10,
    gap: 8,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: COLORS.cardBorder,
  },
  recordItem: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  recordDot: { width: 8, height: 8, borderRadius: 4 },
  recordLabel: { color: COLORS.textDim, fontSize: 10, fontWeight: '700' },
  recordVal: { color: COLORS.white, fontSize: 11, fontWeight: '800', marginTop: 1 },
  recordMetaBox: { alignItems: 'flex-end' },
  recordSeason: { color: COLORS.accentGold, fontSize: 10, fontWeight: '800' },
  recordDate: { color: COLORS.textDim, fontSize: 9 },
  analysisBox: {
    backgroundColor: 'rgba(56,189,248,0.08)',
    borderRadius: 12,
    padding: 11,
    borderWidth: 1,
    borderColor: 'rgba(56,189,248,0.25)',
  },
  analysisTitle: { color: '#38bdf8', fontSize: 10, fontWeight: '900', marginBottom: 4 },
  analysisText: { color: COLORS.textSoft, fontSize: 11, lineHeight: 16 },
  matchesHeaderRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  sectionTitle: {
    color: COLORS.white,
    fontSize: 12,
    fontWeight: '900',
    letterSpacing: 0.6,
  },
  upcomingBadge: {
    color: COLORS.accentGold,
    fontSize: 10,
    fontWeight: '800',
  },
  searchBarWrap: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.backgroundCard,
    borderWidth: 1,
    borderColor: COLORS.cardBorder,
    borderRadius: 12,
    paddingHorizontal: 11,
    paddingVertical: 8,
    marginBottom: 12,
    gap: 8,
  },
  searchIcon: { fontSize: 13 },
  searchInput: { flex: 1, color: COLORS.white, fontSize: 12, paddingVertical: 0 },
  clearBtn: { color: COLORS.textMuted, fontSize: 14, fontWeight: '900', paddingHorizontal: 4 },
  emptyCard: {
    backgroundColor: COLORS.backgroundCard,
    borderRadius: 14,
    padding: 24,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: COLORS.cardBorder,
  },
  emptyTitle: { color: COLORS.white, fontSize: 13, fontWeight: '800', marginBottom: 4 },
  emptySub: { color: COLORS.textDim, fontSize: 11, textAlign: 'center' },
  matchCard: {
    backgroundColor: COLORS.backgroundCard,
    borderRadius: 14,
    borderWidth: 1,
    borderColor: COLORS.cardBorder,
    padding: 11,
    marginBottom: 8,
  },
  matchCardT1: { borderLeftWidth: 3, borderLeftColor: '#ef4444' },
  matchCardT2: { borderLeftWidth: 3, borderLeftColor: '#38bdf8' },
  matchTopRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  matchTagRow: { flexDirection: 'row', alignItems: 'center', gap: 6, flex: 1 },
  seasonPill: {
    backgroundColor: 'rgba(255,255,255,0.07)',
    paddingHorizontal: 7,
    paddingVertical: 2,
    borderRadius: 6,
  },
  seasonPillText: { color: COLORS.accentGold, fontSize: 10, fontWeight: '800' },
  compLabelText: { color: COLORS.textMuted, fontSize: 10, fontWeight: '700', flexShrink: 1 },
  dateText: { color: COLORS.textDim, fontSize: 10, fontWeight: '700' },
  matchBodyRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: 8,
  },
  matchTeamHome: { flex: 1, flexDirection: 'row', alignItems: 'center', gap: 7 },
  matchTeamAway: { flex: 1, flexDirection: 'row', alignItems: 'center', justifyContent: 'flex-end', gap: 7 },
  matchTeamLogo: { width: 24, height: 24, resizeMode: 'contain' },
  matchTeamName: { color: COLORS.textSoft, fontSize: 12, fontWeight: '700' },
  matchTeamWinner: { color: COLORS.white, fontWeight: '900' },
  rankSubText: { color: COLORS.textDim, fontSize: 9, marginTop: 1 },
  scoreBox: {
    minWidth: 64,
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 10,
    backgroundColor: 'rgba(255,255,255,0.07)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  scoreBoxNS: { backgroundColor: 'rgba(245,158,11,0.14)' },
  scoreBoxT1: { backgroundColor: 'rgba(239,68,68,0.22)' },
  scoreBoxT2: { backgroundColor: 'rgba(56,189,248,0.22)' },
  scoreText: { color: COLORS.white, fontSize: 14, fontWeight: '900' },
  scoreNoteText: { color: COLORS.accentGold, fontSize: 8, fontWeight: '900', marginTop: 1 },
  nsLabel: { color: COLORS.accentGold, fontSize: 8, fontWeight: '800', marginTop: 1 },
  matchFooterRow: {
    marginTop: 7,
    paddingTop: 6,
    borderTopWidth: 1,
    borderTopColor: 'rgba(255,255,255,0.04)',
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  attendanceText: { color: COLORS.textDim, fontSize: 9, fontWeight: '600' },
  detailHintText: { color: COLORS.accentBlue, fontSize: 10, fontWeight: '800' },
  loadMoreBtn: {
    backgroundColor: COLORS.backgroundCard,
    borderWidth: 1,
    borderColor: COLORS.accentBlue,
    borderRadius: 12,
    paddingVertical: 12,
    alignItems: 'center',
    marginTop: 6,
  },
  loadMoreText: { color: COLORS.accentBlue, fontSize: 12, fontWeight: '800' },
  modalBackdrop: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.75)',
    justifyContent: 'flex-end',
  },
  modalSheet: {
    backgroundColor: COLORS.backgroundCard,
    borderTopLeftRadius: 22,
    borderTopRightRadius: 22,
    maxHeight: '80%',
    padding: 16,
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  modalTitle: { color: COLORS.white, fontSize: 15, fontWeight: '900' },
  modalCloseBtn: {
    width: 30,
    height: 30,
    borderRadius: 15,
    backgroundColor: 'rgba(255,255,255,0.08)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  modalCloseText: { color: COLORS.white, fontSize: 14, fontWeight: '900' },
  modalSearchInput: {
    backgroundColor: COLORS.background,
    borderWidth: 1,
    borderColor: COLORS.cardBorder,
    borderRadius: 10,
    paddingHorizontal: 12,
    paddingVertical: 9,
    color: COLORS.white,
    fontSize: 12,
    marginBottom: 10,
  },
  modalTeamRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 10,
    paddingHorizontal: 8,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.cardBorder,
    gap: 10,
  },
  modalTeamRowSelected: {
    backgroundColor: 'rgba(56,189,248,0.1)',
    borderRadius: 10,
  },
  modalTeamLogo: { width: 32, height: 32, resizeMode: 'contain' },
  modalTeamName: { color: COLORS.white, fontSize: 13, fontWeight: '800' },
  modalTeamSub: { color: COLORS.textDim, fontSize: 10, marginTop: 1 },
  selectedCheck: { color: COLORS.accentGreen, fontSize: 16, fontWeight: '900' },
  detailModalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.75)',
    justifyContent: 'center',
    padding: 20,
  },
  detailModalCard: {
    backgroundColor: '#101626',
    borderRadius: 16,
    borderWidth: 1,
    borderColor: COLORS.cardBorderStrong,
    padding: 16,
  },
  detailModalHeader: {
    color: COLORS.accentBlue,
    fontSize: 12,
    fontWeight: '800',
    textAlign: 'center',
    marginBottom: 12,
  },
  detailTeamsRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 14,
    paddingBottom: 12,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.cardBorder,
  },
  detailTeamCol: { flex: 1, alignItems: 'center', gap: 6 },
  detailTeamLogo: { width: 38, height: 38, resizeMode: 'contain' },
  detailTeamName: {
    color: COLORS.white,
    fontSize: 12,
    fontWeight: '800',
    textAlign: 'center',
  },
  detailScoreWrap: { alignItems: 'center', paddingHorizontal: 10 },
  detailScoreText: { color: COLORS.white, fontSize: 22, fontWeight: '900' },
  detailScoreNote: { color: COLORS.accentGold, fontSize: 10, fontWeight: '800', marginTop: 2 },
  detailMeta: { color: COLORS.textSoft, fontSize: 12, marginBottom: 5, lineHeight: 18 },
  detailLoadingBox: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginTop: 8,
    paddingVertical: 6,
  },
  detailLoadingText: { color: COLORS.textMuted, fontSize: 11 },
  detailEventsBox: {
    marginTop: 8,
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: COLORS.cardBorder,
  },
  detailEvTitle: { color: COLORS.white, fontSize: 12, fontWeight: '800', marginBottom: 4 },
  detailCloseBtn: {
    backgroundColor: COLORS.accentRed,
    borderRadius: 10,
    paddingVertical: 10,
    alignItems: 'center',
    marginTop: 14,
  },
  detailCloseBtnText: { color: COLORS.white, fontSize: 13, fontWeight: '800' },
});

