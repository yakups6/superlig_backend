import React, { useState, useEffect, useCallback } from 'react';
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
} from 'react-native';
import Svg, { Polygon, Line, Text as SvgText } from 'react-native-svg';
import { superligApi } from '../services/api';
import { COLORS } from '../theme/colors';
import { useAuth } from '../context/AuthContext';
import SeasonPickerBar from '../components/SeasonPickerBar';
import {
  DEFAULT_PLAYER_IMG,
  formatMarketValue,
  cleanPlayerDisplayName,
} from '../utils/format';

export default function CompareScreen({ navigation, route }) {
  const { seasons, activeSeason } = useAuth();
  const [selectedSeason, setSelectedSeason] = useState(
    route?.params?.seasonName || activeSeason?.name || '2026/2027'
  );

  const [players, setPlayers] = useState([]);
  const [p1Id, setP1Id] = useState(null);
  const [p2Id, setP2Id] = useState(null);
  const [pickerTarget, setPickerTarget] = useState(null); // 1 | 2 | null
  const [pickerSearch, setPickerSearch] = useState('');
  const [compData, setCompData] = useState(null);
  const [loading, setLoading] = useState(true);

  const runComparison = useCallback(
    async (id1, id2, targetSeason = selectedSeason) => {
      if (!id1 || !id2) return;
      try {
        setLoading(true);
        const seasonParam = targetSeason && targetSeason !== 'ALL' ? targetSeason : undefined;
        const res = await superligApi.comparePlayers(id1, id2, seasonParam);
        setCompData(res);
      } catch (err) {
        console.log('Comparison error:', err?.message);
      } finally {
        setLoading(false);
      }
    },
    [selectedSeason]
  );

  useEffect(() => {
    let cancelled = false;
    async function init() {
      try {
        const isAll = selectedSeason === 'ALL';
        const [pRes, lRes] = await Promise.allSettled([
          superligApi.getPlayers(isAll ? {} : { season: selectedSeason }),
          superligApi.getLegends(isAll ? { season: 'ALL' } : {}),
        ]);

        if (cancelled) return;

        const basePlayers =
          pRes.status === 'fulfilled' && Array.isArray(pRes.value) ? pRes.value : [];
        const legendPlayers =
          lRes.status === 'fulfilled' && Array.isArray(lRes.value) ? lRes.value : [];

        const mergedMap = new Map();
        basePlayers.forEach((p) => {
          if (p?.id) mergedMap.set(String(p.id), p);
        });
        legendPlayers.forEach((l) => {
          if (l?.id && !mergedMap.has(String(l.id))) {
            mergedMap.set(String(l.id), l);
          }
        });

        const sorted = Array.from(mergedMap.values()).sort((a, b) => {
          const ga = (b.season_goals ?? b.goals ?? 0) - (a.season_goals ?? a.goals ?? 0);
          if (ga !== 0) return ga;
          return (Number(b.market_value) || 0) - (Number(a.market_value) || 0);
        });
        setPlayers(sorted);

        if (sorted.length >= 2) {
          const osimhen = sorted.find((p) => p.name?.includes('Osimhen'));
          const muriqi = sorted.find((p) => p.name?.includes('Muriqi'));
          const salah = sorted.find((p) => p.name?.includes('Salah'));

          const initP1 = route?.params?.initialPlayer1 || p1Id || osimhen?.id || sorted[0].id;
          let initP2 = route?.params?.initialPlayer2 || p2Id || muriqi?.id || salah?.id || sorted[1].id;
          if (String(initP2) === String(initP1)) {
            initP2 = sorted.find((p) => String(p.id) !== String(initP1))?.id || sorted[1].id;
          }
          setP1Id(initP1);
          setP2Id(initP2);
          runComparison(initP1, initP2, selectedSeason);
        } else {
          setLoading(false);
        }
      } catch (err) {
        console.log('Compare init error:', err?.message);
        setLoading(false);
      }
    }
    init();
    return () => {
      cancelled = true;
    };
  }, [selectedSeason]);

  useEffect(() => {
    const incoming = route?.params?.initialPlayer1;
    const incomingSeason = route?.params?.seasonName;
    if (incomingSeason && incomingSeason !== selectedSeason) {
      setSelectedSeason(incomingSeason);
    }
    if (incoming) {
      let nextP2 = p2Id;
      if ((!nextP2 || String(incoming) === String(nextP2)) && players.length > 1) {
        nextP2 = players.find((p) => String(p.id) !== String(incoming))?.id || nextP2;
        setP2Id(nextP2);
      }
      setP1Id(incoming);
      if (nextP2) {
        runComparison(incoming, nextP2, incomingSeason || selectedSeason);
      }
    }
  }, [route?.params?.initialPlayer1, route?.params?.seasonName, route?.params?.ts]);

  const handleSwap = () => {
    if (!p1Id || !p2Id) return;
    setP1Id(p2Id);
    setP2Id(p1Id);
    runComparison(p2Id, p1Id, selectedSeason);
  };

  const handlePickPlayer = (id) => {
    const target = pickerTarget;
    setPickerTarget(null);
    setPickerSearch('');
    if (target === 1) {
      setP1Id(id);
      runComparison(id, p2Id, selectedSeason);
    } else if (target === 2) {
      setP2Id(id);
      runComparison(p1Id, id, selectedSeason);
    }
  };

  const p1 = compData?.player1 || {};
  const p2 = compData?.player2 || {};
  const bars = compData?.bars || {};
  const radar = compData?.radar || {};

  const barRows = [
    {
      label: 'Gol',
      v1: bars.goals?.val1 ?? '-',
      v2: bars.goals?.val2 ?? '-',
      p1Pct: bars.goals?.pct1 ?? 50,
      p2Pct: bars.goals?.pct2 ?? 50,
    },
    {
      label: 'Asist',
      v1: bars.assists?.val1 ?? '-',
      v2: bars.assists?.val2 ?? '-',
      p1Pct: bars.assists?.pct1 ?? 50,
      p2Pct: bars.assists?.pct2 ?? 50,
    },
    {
      label: 'Maç Sayısı',
      v1: bars.matches?.val1 ?? '-',
      v2: bars.matches?.val2 ?? '-',
      p1Pct: bars.matches?.pct1 ?? 50,
      p2Pct: bars.matches?.pct2 ?? 50,
    },
    {
      label: 'Şut / Maç',
      v1: bars.shots_per_game?.val1 ?? '-',
      v2: bars.shots_per_game?.val2 ?? '-',
      p1Pct: bars.shots_per_game?.pct1 ?? 50,
      p2Pct: bars.shots_per_game?.pct2 ?? 50,
    },
    {
      label: 'Kilit Pas / Maç',
      v1: bars.key_passes_per_game?.val1 ?? '-',
      v2: bars.key_passes_per_game?.val2 ?? '-',
      p1Pct: bars.key_passes_per_game?.pct1 ?? 50,
      p2Pct: bars.key_passes_per_game?.pct2 ?? 50,
    },
    {
      label: 'Pas İsabeti',
      v1: bars.pass_accuracy ? `%${bars.pass_accuracy.val1}` : '-',
      v2: bars.pass_accuracy ? `%${bars.pass_accuracy.val2}` : '-',
      p1Pct: bars.pass_accuracy?.pct1 ?? 50,
      p2Pct: bars.pass_accuracy?.pct2 ?? 50,
    },
    {
      label: 'Reyting',
      v1: bars.rating?.val1 ?? '-',
      v2: bars.rating?.val2 ?? '-',
      p1Pct: bars.rating?.pct1 ?? 50,
      p2Pct: bars.rating?.pct2 ?? 50,
    },
  ];

  // SVG Radar Geometry
  const radarLabels = ['Hız', 'Şut', 'Pas', 'Teknik', 'Defans', 'Fizik'];
  const p1Vals = radar.player1 || [70, 70, 70, 70, 55, 70];
  const p2Vals = radar.player2 || [70, 70, 70, 70, 55, 70];
  const cX = 140;
  const cY = 125;
  const maxR = 85;

  const getPointsStr = (vals) =>
    vals
      .map((val, i) => {
        const angle = (Math.PI / 3) * i - Math.PI / 2;
        const r = (Math.max(10, Math.min(100, Number(val) || 60)) / 100) * maxR;
        return `${(cX + r * Math.cos(angle)).toFixed(1)},${(cY + r * Math.sin(angle)).toFixed(1)}`;
      })
      .join(' ');

  const modalPlayers = players.filter((p) => {
    if (!pickerSearch.trim()) return true;
    const q = pickerSearch.toLowerCase();
    return (
      p.name?.toLowerCase().includes(q) ||
      p.team_name?.toLowerCase().includes(q) ||
      p.team_short_name?.toLowerCase().includes(q)
    );
  });

  const algoRaw = compData?.algorithmic_analysis;
  const algoHeadline =
    typeof algoRaw === 'string' ? algoRaw : algoRaw?.headline || '';
  const algoInsights =
    algoRaw && typeof algoRaw === 'object' && Array.isArray(algoRaw.insights)
      ? algoRaw.insights
      : [];

  return (
    <View style={styles.container}>
      <View style={styles.headerRow}>
        <TouchableOpacity onPress={() => navigation.navigate('HomeTab')} style={styles.backBtn}>
          <Text style={styles.backText}>←</Text>
        </TouchableOpacity>
        <Text style={styles.headerTitle}>OYUNCU KARŞILAŞTIRMA</Text>
        <View style={{ width: 32 }} />
      </View>

      <ScrollView contentContainerStyle={styles.scrollContent}>
        <SeasonPickerBar
          seasons={seasons}
          selectedSeasonName={selectedSeason}
          onSelectSeason={setSelectedSeason}
          includeAllOption
          allOptionLabel="Otomatik (En Güncel / Kariyer)"
          subtitle={
            selectedSeason === 'ALL'
              ? 'Oyuncuların aktif/en son sezon verisi'
              : `${selectedSeason} Sezon İstatistikleri`
          }
        />

        {/* DUAL PLAYER PICKERS + SWAP BUTTON */}
        <View style={styles.selectorsRow}>
          <TouchableOpacity
            style={styles.selectBox}
            onPress={() => setPickerTarget(1)}
          >
            <Text style={[styles.selectLbl, { color: COLORS.secondary }]}>1. OYUNCU (MAVİ)</Text>
            <Text style={styles.selectVal} numberOfLines={1}>
              {p1.name || 'Seçiniz'} ▾
            </Text>
          </TouchableOpacity>

          <TouchableOpacity style={styles.swapBtn} onPress={handleSwap}>
            <Text style={styles.swapBtnText}>⇄</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.selectBox}
            onPress={() => setPickerTarget(2)}
          >
            <Text style={[styles.selectLbl, { color: COLORS.primaryGlow }]}>2. OYUNCU (YEŞİL)</Text>
            <Text style={styles.selectVal} numberOfLines={1}>
              {p2.name || 'Seçiniz'} ▾
            </Text>
          </TouchableOpacity>
        </View>

        {loading && !compData ? (
          <ActivityIndicator size="large" color={COLORS.primary} style={{ marginTop: 40 }} />
        ) : (
          <>
            {/* HEAD-TO-HEAD VS */}
            <View style={styles.vsCard}>
              <View style={styles.vsPlayerCol}>
                <Image
                  source={{ uri: p1.image_url || DEFAULT_PLAYER_IMG }}
                  style={[styles.vsAvatar, { borderColor: COLORS.avatarRingCyan }]}
                />
                <Text style={styles.vsName} numberOfLines={2}>
                  {cleanPlayerDisplayName(p1.name) || '-'}
                </Text>
                <Text style={styles.vsTeam}>
                  ({p1.team_short_name || p1.team_short || p1.team_name || '-'})
                </Text>
                <Text style={[styles.vsVal, { color: COLORS.secondary }]}>
                  {formatMarketValue(p1.market_value, false, false)}
                </Text>
              </View>

              <View style={styles.vsBadge}>
                <Text style={styles.vsBadgeText}>VS</Text>
              </View>

              <View style={styles.vsPlayerCol}>
                <Image
                  source={{ uri: p2.image_url || DEFAULT_PLAYER_IMG }}
                  style={[styles.vsAvatar, { borderColor: COLORS.avatarRingEmerald }]}
                />
                <Text style={styles.vsName} numberOfLines={2}>
                  {cleanPlayerDisplayName(p2.name) || '-'}
                </Text>
                <Text style={styles.vsTeam}>
                  ({p2.team_short_name || p2.team_short || p2.team_name || '-'})
                </Text>
                <Text style={[styles.vsVal, { color: COLORS.primaryGlow }]}>
                  {formatMarketValue(p2.market_value, false, false)}
                </Text>
              </View>
            </View>

            {/* DUAL PROGRESS BARS */}
            <View style={styles.barsCard}>
              {barRows.map((row) => (
                <View key={row.label} style={styles.barItem}>
                  <View style={styles.barLabelRow}>
                    <Text style={[styles.barNum, { color: COLORS.secondary }]}>
                      {row.v1}
                    </Text>
                    <Text style={styles.barMetric}>{row.label}</Text>
                    <Text style={[styles.barNum, { color: COLORS.primaryGlow }]}>
                      {row.v2}
                    </Text>
                  </View>
                  <View style={styles.dualBarTrack}>
                    <View
                      style={[
                        styles.dualBarLeft,
                        { width: `${Math.max(5, Math.min(95, Number(row.p1Pct) || 50))}%` },
                      ]}
                    />
                    <View
                      style={[
                        styles.dualBarRight,
                        { width: `${Math.max(5, Math.min(95, Number(row.p2Pct) || 50))}%` },
                      ]}
                    />
                  </View>
                </View>
              ))}
            </View>

            {/* 6-AXIS SVG RADAR CHART */}
            <View style={styles.radarCard}>
              <Text style={styles.sectionTitle}>Yetenek Radarı (SofaScore / WhoScored)</Text>
              <View style={styles.legendRow}>
                <View style={styles.legendItem}>
                  <View style={[styles.legendDot, { backgroundColor: COLORS.secondary }]} />
                  <Text style={styles.legendText} numberOfLines={1}>
                    {cleanPlayerDisplayName(p1.name)}
                  </Text>
                </View>
                <View style={styles.legendItem}>
                  <View style={[styles.legendDot, { backgroundColor: COLORS.primaryGlow }]} />
                  <Text style={styles.legendText} numberOfLines={1}>
                    {cleanPlayerDisplayName(p2.name)}
                  </Text>
                </View>
              </View>
              <View style={{ alignItems: 'center' }}>
                <Svg width={280} height={250}>
                  {[0.25, 0.5, 0.75, 1].map((scale, sIdx) => {
                    const pts = radarLabels
                      .map((_, i) => {
                        const a = (Math.PI / 3) * i - Math.PI / 2;
                        const r = maxR * scale;
                        return `${(cX + r * Math.cos(a)).toFixed(1)},${(cY + r * Math.sin(a)).toFixed(1)}`;
                      })
                      .join(' ');
                    return (
                      <Polygon
                        key={sIdx}
                        points={pts}
                        fill="none"
                        stroke="rgba(255,255,255,0.1)"
                        strokeWidth={1}
                      />
                    );
                  })}

                  {radarLabels.map((lbl, i) => {
                    const a = (Math.PI / 3) * i - Math.PI / 2;
                    const x2 = cX + maxR * Math.cos(a);
                    const y2 = cY + maxR * Math.sin(a);
                    const lx = cX + (maxR + 22) * Math.cos(a);
                    const ly = cY + (maxR + 18) * Math.sin(a) + 4;
                    return (
                      <React.Fragment key={lbl}>
                        <Line
                          x1={cX}
                          y1={cY}
                          x2={x2}
                          y2={y2}
                          stroke="rgba(255,255,255,0.1)"
                          strokeWidth={1}
                        />
                        <SvgText
                          x={lx}
                          y={ly}
                          fill="#cbd5e1"
                          fontSize={11}
                          fontWeight="700"
                          textAnchor="middle"
                        >
                          {lbl}
                        </SvgText>
                      </React.Fragment>
                    );
                  })}

                  <Polygon
                    points={getPointsStr(p1Vals)}
                    fill="rgba(6, 182, 212, 0.22)"
                    stroke={COLORS.secondary}
                    strokeWidth={2}
                  />
                  <Polygon
                    points={getPointsStr(p2Vals)}
                    fill="rgba(16, 185, 129, 0.22)"
                    stroke={COLORS.primaryGlow}
                    strokeWidth={2}
                  />
                </Svg>
              </View>
            </View>

            {/* ALGORITHMIC ANALYSIS */}
            {Boolean(algoHeadline || algoInsights.length > 0) && (
              <View style={styles.algoCard}>
                <Text style={styles.algoTitle}>🤖 Algoritmik Scout Analizi</Text>
                {Boolean(algoHeadline) && (
                  <Text style={styles.algoHeadline}>{algoHeadline}</Text>
                )}
                {algoInsights.map((ins, i) => (
                  <Text key={i} style={styles.algoBullet}>
                    • {ins}
                  </Text>
                ))}
              </View>
            )}
          </>
        )}
      </ScrollView>

      {/* SEARCHABLE PLAYER PICKER MODAL */}
      <Modal
        visible={Boolean(pickerTarget)}
        transparent
        animationType="fade"
        onRequestClose={() => setPickerTarget(null)}
      >
        <TouchableOpacity
          style={styles.modalOverlay}
          activeOpacity={1}
          onPress={() => setPickerTarget(null)}
        >
          <View style={styles.modalCard} onStartShouldSetResponder={() => true}>
            <View style={styles.modalHead}>
              <Text style={styles.modalTitle}>{pickerTarget}. Oyuncuyu Seç</Text>
              <TouchableOpacity onPress={() => setPickerTarget(null)}>
                <Text style={styles.modalClose}>✕</Text>
              </TouchableOpacity>
            </View>

            <TextInput
              style={styles.modalSearch}
              placeholder="Oyuncu veya takım ara (Efsaneler dahil)..."
              placeholderTextColor={COLORS.textDim}
              value={pickerSearch}
              onChangeText={setPickerSearch}
            />

            <FlatList
              data={modalPlayers}
              keyExtractor={(item, idx) => `${item.id}-${idx}`}
              style={{ maxHeight: 350 }}
              renderItem={({ item }) => {
                const g = item.season_goals ?? item.goals ?? 0;
                const a = item.season_assists ?? item.assists ?? 0;
                const tShort = item.team_short_name || item.current_team_short_name || '';
                const selected =
                  (pickerTarget === 1 && String(item.id) === String(p1Id)) ||
                  (pickerTarget === 2 && String(item.id) === String(p2Id));

                return (
                  <TouchableOpacity
                    style={[styles.modalRow, selected && styles.modalRowActive]}
                    onPress={() => handlePickPlayer(item.id)}
                  >
                    <Image
                      source={{ uri: item.image_url || DEFAULT_PLAYER_IMG }}
                      style={styles.modalAvatar}
                    />
                    <View style={{ flex: 1 }}>
                      <Text style={styles.modalName} numberOfLines={1}>
                        {cleanPlayerDisplayName(item.name)} {tShort ? `(${tShort})` : ''}
                      </Text>
                      <Text style={styles.modalMeta}>
                        {item.position} • {g}G {a}A{item.is_legend ? ' • ★ Efsane' : ''}
                      </Text>
                    </View>
                  </TouchableOpacity>
                );
              }}
            />
          </View>
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
  headerTitle: { color: COLORS.white, fontSize: 14, fontWeight: '800' },
  scrollContent: { padding: 14, paddingBottom: 40 },
  selectorsRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 12,
  },
  selectBox: {
    flex: 1,
    backgroundColor: COLORS.backgroundCard,
    borderWidth: 1,
    borderColor: COLORS.cardBorderStrong,
    borderRadius: 12,
    paddingHorizontal: 10,
    paddingVertical: 9,
  },
  selectLbl: { fontSize: 9, fontWeight: '900', marginBottom: 2 },
  selectVal: { color: COLORS.white, fontSize: 12, fontWeight: '800' },
  swapBtn: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: 'rgba(6,182,212,0.12)',
    borderWidth: 1,
    borderColor: 'rgba(6,182,212,0.35)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  swapBtnText: { color: COLORS.secondary, fontSize: 16, fontWeight: '900' },
  vsCard: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: COLORS.backgroundCard,
    borderWidth: 1.5,
    borderColor: COLORS.cardBorderStrong,
    borderRadius: 16,
    padding: 14,
    marginBottom: 12,
  },
  vsPlayerCol: { flex: 1, alignItems: 'center' },
  vsAvatar: { width: 66, height: 66, borderRadius: 33, borderWidth: 2.5, marginBottom: 8, backgroundColor: 'rgba(0,0,0,0.3)' },
  vsName: { color: COLORS.white, fontSize: 13, fontWeight: '800', textAlign: 'center' },
  vsTeam: { color: COLORS.textMuted, fontSize: 11, marginTop: 2 },
  vsVal: { fontSize: 12, fontWeight: '900', marginTop: 4 },
  vsBadge: {
    backgroundColor: 'rgba(52,211,153,0.15)',
    borderWidth: 1,
    borderColor: COLORS.primaryGlow,
    borderRadius: 14,
    paddingHorizontal: 10,
    paddingVertical: 6,
    marginHorizontal: 6,
  },
  vsBadgeText: { color: COLORS.primaryGlow, fontSize: 12, fontWeight: '900' },
  barsCard: {
    backgroundColor: COLORS.backgroundCard,
    borderWidth: 1,
    borderColor: COLORS.cardBorder,
    borderRadius: 16,
    padding: 14,
    marginBottom: 12,
    gap: 12,
  },
  barItem: {},
  barLabelRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 5,
  },
  barNum: { fontSize: 13, fontWeight: '900' },
  barMetric: { color: COLORS.textSoft, fontSize: 11, fontWeight: '700' },
  dualBarTrack: {
    flexDirection: 'row',
    height: 7,
    borderRadius: 4,
    overflow: 'hidden',
    backgroundColor: 'rgba(255,255,255,0.06)',
  },
  dualBarLeft: { backgroundColor: COLORS.secondary, height: '100%' },
  dualBarRight: { backgroundColor: COLORS.primaryGlow, height: '100%' },
  radarCard: {
    backgroundColor: COLORS.backgroundCard,
    borderWidth: 1,
    borderColor: COLORS.cardBorder,
    borderRadius: 16,
    padding: 14,
    marginBottom: 12,
  },
  sectionTitle: {
    color: COLORS.white,
    fontSize: 13,
    fontWeight: '800',
    marginBottom: 8,
    textAlign: 'center',
  },
  legendRow: {
    flexDirection: 'row',
    justifyContent: 'center',
    gap: 16,
    marginBottom: 4,
  },
  legendItem: { flexDirection: 'row', alignItems: 'center', gap: 5, maxWidth: '45%' },
  legendDot: { width: 8, height: 8, borderRadius: 4 },
  legendText: { color: COLORS.textSoft, fontSize: 11, fontWeight: '700' },
  algoCard: {
    backgroundColor: 'rgba(6,182,212,0.08)',
    borderWidth: 1,
    borderColor: 'rgba(6,182,212,0.28)',
    borderRadius: 16,
    padding: 14,
  },
  algoTitle: { color: COLORS.secondary, fontSize: 13, fontWeight: '800', marginBottom: 6 },
  algoHeadline: { color: COLORS.white, fontSize: 12, fontWeight: '700', lineHeight: 18, marginBottom: 6 },
  algoBullet: { color: COLORS.textSoft, fontSize: 12, lineHeight: 18, marginTop: 3 },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.75)',
    justifyContent: 'center',
    padding: 20,
  },
  modalCard: {
    backgroundColor: '#0a161f',
    borderRadius: 16,
    borderWidth: 1,
    borderColor: COLORS.cardBorderStrong,
    padding: 14,
  },
  modalHead: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  modalTitle: { color: COLORS.white, fontSize: 14, fontWeight: '800' },
  modalClose: { color: COLORS.textMuted, fontSize: 16, fontWeight: '800', paddingHorizontal: 6 },
  modalSearch: {
    backgroundColor: '#060f14',
    borderWidth: 1,
    borderColor: COLORS.cardBorderStrong,
    borderRadius: 10,
    paddingHorizontal: 12,
    paddingVertical: 8,
    color: COLORS.white,
    fontSize: 12,
    marginBottom: 10,
  },
  modalRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 9,
    paddingHorizontal: 8,
    borderRadius: 10,
    gap: 10,
  },
  modalRowActive: { backgroundColor: 'rgba(52,211,153,0.15)' },
  modalAvatar: { width: 34, height: 34, borderRadius: 17, borderWidth: 1.5, borderColor: COLORS.avatarRingEmerald },
  modalName: { color: COLORS.white, fontSize: 13, fontWeight: '700' },
  modalMeta: { color: COLORS.textMuted, fontSize: 10, marginTop: 1 },
});
