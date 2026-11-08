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
import { superligApi } from '../services/api';
import { COLORS } from '../theme/colors';
import { useAuth } from '../context/AuthContext';
import SeasonPickerBar from '../components/SeasonPickerBar';
import { DEFAULT_PLAYER_IMG, DEFAULT_TEAM_LOGO } from '../utils/format';

export default function StandingsScreen({ navigation }) {
  const { seasons, activeSeason } = useAuth();
  const [selectedSeason, setSelectedSeason] = useState(activeSeason?.name || '2026/2027');
  const [standings, setStandings] = useState([]);
  const [leaders, setLeaders] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const loadSeasonStats = useCallback(async (seasonName) => {
    try {
      setLoading(true);
      const [standingsData, leadersData] = await Promise.all([
        superligApi.getStandings({ season: seasonName }),
        superligApi.getLeaderboards({ season: seasonName }),
      ]);
      setStandings(Array.isArray(standingsData) ? standingsData : []);
      setLeaders(leadersData?.leaders || null);
    } catch (err) {
      console.log('Standings load error:', err?.message);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    loadSeasonStats(selectedSeason);
  }, [selectedSeason, loadSeasonStats]);

  const champion = standings[0];
  const runnerUp = standings[1];
  const topScorer = leaders?.top_scorers?.[0];
  const isCurrent = selectedSeason === '2026/2027';

  return (
    <View style={styles.container}>
      <View style={styles.headerRow}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backBtn}>
          <Text style={styles.backText}>←</Text>
        </TouchableOpacity>
        <Text style={styles.headerTitle}>LİG İSTATİSTİKLERİ</Text>
        <View style={{ width: 32 }} />
      </View>

      <ScrollView
        contentContainerStyle={styles.scrollContent}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={() => {
              setRefreshing(true);
              loadSeasonStats(selectedSeason);
            }}
            tintColor={COLORS.primary}
          />
        }
      >
        <SeasonPickerBar
          seasons={seasons}
          selectedSeasonName={selectedSeason}
          onSelectSeason={setSelectedSeason}
          subtitle={
            isCurrent
              ? 'Aktif Sezon • Canlı Puan Durumu'
              : `${selectedSeason} Tarihsel Sezon Tablosu`
          }
        />

        {!isCurrent && champion && (
          <View style={styles.champCard}>
            <View style={{ flex: 1 }}>
              <Text style={styles.champTitle}>🏆 Şampiyon: {champion.team_name}</Text>
              <Text style={styles.champMeta}>
                {runnerUp ? `İkinci: ${runnerUp.team_name}` : ''}
                {topScorer ? ` • Gol Kralı: ${topScorer.player_name} (${topScorer.goals}G)` : ''}
              </Text>
            </View>
            <View style={styles.champPtsBadge}>
              <Text style={styles.champPtsText}>{champion.points} P</Text>
            </View>
          </View>
        )}

        <View style={styles.sectionHead}>
          <Text style={styles.sectionTitle}>Puan Cetveli ({selectedSeason})</Text>
          <Text style={styles.sectionSub}>{standings.length} Takım</Text>
        </View>

        <View style={styles.tableCard}>
          <View style={styles.tableHead}>
            <Text style={[styles.th, { width: 22 }]}>#</Text>
            <Text style={[styles.th, { flex: 1, textAlign: 'left', paddingLeft: 4 }]}>Takım</Text>
            <Text style={[styles.th, { width: 24 }]}>O</Text>
            <Text style={[styles.th, { width: 24 }]}>G</Text>
            <Text style={[styles.th, { width: 24 }]}>B</Text>
            <Text style={[styles.th, { width: 24 }]}>M</Text>
            <Text style={[styles.th, { width: 28 }]}>AV</Text>
            <Text style={[styles.th, { width: 28, color: COLORS.white }]}>P</Text>
          </View>

          {loading ? (
            <ActivityIndicator size="small" color={COLORS.accentRed} style={{ margin: 22 }} />
          ) : standings.length === 0 ? (
            <Text style={styles.emptyTable}>Bu sezon için puan cetveli bulunamadı.</Text>
          ) : (
            standings.map((row, idx) => {
              const av =
                row.goal_difference !== undefined
                  ? row.goal_difference
                  : (row.goals_for || 0) - (row.goals_against || 0);
              const isFirst = row.rank === 1;
              const isTop4 = row.rank <= 4;
              const isDropZone = standings.length >= 16 && row.rank >= standings.length - 2;

              return (
                <View
                  key={row.id || idx}
                  style={[
                    styles.tableRow,
                    isFirst && styles.firstRow,
                    idx % 2 === 1 && styles.evenRow,
                  ]}
                >
                  <Text
                    style={[
                      styles.rankCol,
                      isTop4 && { color: COLORS.accentGreen },
                      isDropZone && { color: COLORS.accentRed },
                    ]}
                  >
                    {row.rank}
                  </Text>
                  <View style={styles.teamCol}>
                    <Image
                      source={{ uri: row.team_logo || DEFAULT_TEAM_LOGO }}
                      style={styles.teamLogo}
                    />
                    <Text style={styles.teamNameText} numberOfLines={1}>
                      {row.team_name}
                    </Text>
                  </View>
                  <Text style={styles.statCol}>{row.played ?? 0}</Text>
                  <Text style={styles.statCol}>{row.won ?? 0}</Text>
                  <Text style={styles.statCol}>{row.drawn ?? 0}</Text>
                  <Text style={styles.statCol}>{row.lost ?? 0}</Text>
                  <Text
                    style={[
                      styles.statCol,
                      av > 0 && { color: COLORS.accentGreen },
                      av < 0 && { color: '#f87171' },
                    ]}
                  >
                    {av > 0 ? `+${av}` : av}
                  </Text>
                  <Text style={styles.pointsCol}>{row.points ?? 0}</Text>
                </View>
              );
            })
          )}
        </View>

        {/* TOP SCORERS */}
        <View style={styles.sectionHead}>
          <Text style={styles.sectionTitle}>⚽ Gol Krallığı Zirvesi</Text>
        </View>
        {(leaders?.top_scorers || []).length === 0 ? (
          <Text style={styles.emptySmall}>Gol istatistiği bulunmuyor.</Text>
        ) : (
          (leaders?.top_scorers || []).slice(0, 8).map((p, idx) => (
            <View key={`sc-${idx}`} style={styles.leaderCard}>
              <Text style={styles.leaderRank}>{idx + 1}.</Text>
              <Image
                source={{ uri: p.player_image || DEFAULT_PLAYER_IMG }}
                style={styles.leaderAvatar}
              />
              <View style={{ flex: 1 }}>
                <Text style={styles.leaderName} numberOfLines={1}>
                  {p.player_name}
                </Text>
                <Text style={styles.leaderSub} numberOfLines={1}>
                  {p.team_name} • {p.matches || 0} Maç
                </Text>
              </View>
              <View style={styles.leaderStatWrap}>
                <Text style={styles.leaderNum}>{p.goals}</Text>
                <Text style={styles.leaderUnit}>Gol</Text>
              </View>
            </View>
          ))
        )}

        {/* TOP ASSISTS */}
        <View style={[styles.sectionHead, { marginTop: 16 }]}>
          <Text style={styles.sectionTitle}>🎯 Asist Krallığı Zirvesi</Text>
        </View>
        {(leaders?.top_assists || []).length === 0 ? (
          <Text style={styles.emptySmall}>Asist istatistiği bulunmuyor.</Text>
        ) : (
          (leaders?.top_assists || []).slice(0, 8).map((p, idx) => (
            <View key={`as-${idx}`} style={styles.leaderCard}>
              <Text style={[styles.leaderRank, { color: COLORS.accentBlue }]}>
                {idx + 1}.
              </Text>
              <Image
                source={{ uri: p.player_image || DEFAULT_PLAYER_IMG }}
                style={styles.leaderAvatar}
              />
              <View style={{ flex: 1 }}>
                <Text style={styles.leaderName} numberOfLines={1}>
                  {p.player_name}
                </Text>
                <Text style={styles.leaderSub} numberOfLines={1}>
                  {p.team_name} • {p.matches || 0} Maç
                </Text>
              </View>
              <View style={styles.leaderStatWrap}>
                <Text style={[styles.leaderNum, { color: COLORS.accentBlue }]}>
                  {p.assists}
                </Text>
                <Text style={styles.leaderUnit}>Asist</Text>
              </View>
            </View>
          ))
        )}
      </ScrollView>
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
  champCard: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: 'rgba(245,158,11,0.12)',
    borderWidth: 1,
    borderColor: 'rgba(245,158,11,0.38)',
    borderRadius: 14,
    padding: 12,
    marginBottom: 12,
    gap: 10,
  },
  champTitle: { color: COLORS.accentGold, fontSize: 13, fontWeight: '900' },
  champMeta: { color: COLORS.textSoft, fontSize: 11, marginTop: 3 },
  champPtsBadge: {
    backgroundColor: 'rgba(245,158,11,0.22)',
    borderRadius: 8,
    paddingHorizontal: 9,
    paddingVertical: 5,
  },
  champPtsText: { color: COLORS.accentGold, fontSize: 12, fontWeight: '900' },
  sectionHead: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 6,
    marginBottom: 8,
  },
  sectionTitle: { color: COLORS.white, fontSize: 13, fontWeight: '800' },
  sectionSub: { color: COLORS.textDim, fontSize: 11, fontWeight: '600' },
  tableCard: {
    backgroundColor: COLORS.backgroundCard,
    borderRadius: 14,
    borderWidth: 1,
    borderColor: COLORS.cardBorder,
    overflow: 'hidden',
    marginBottom: 16,
  },
  tableHead: {
    flexDirection: 'row',
    backgroundColor: 'rgba(255,255,255,0.04)',
    paddingVertical: 9,
    paddingHorizontal: 8,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.cardBorder,
    alignItems: 'center',
  },
  th: { color: COLORS.textDim, fontSize: 10, fontWeight: '800', textAlign: 'center' },
  emptyTable: { color: COLORS.textDim, textAlign: 'center', padding: 20, fontSize: 12 },
  tableRow: {
    flexDirection: 'row',
    paddingVertical: 9,
    paddingHorizontal: 8,
    alignItems: 'center',
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(255,255,255,0.03)',
  },
  firstRow: { backgroundColor: 'rgba(52,211,153,0.12)' },
  evenRow: { backgroundColor: 'rgba(255,255,255,0.015)' },
  rankCol: { width: 22, color: COLORS.textMuted, fontSize: 11, fontWeight: '800', textAlign: 'center' },
  teamCol: { flex: 1, flexDirection: 'row', alignItems: 'center', gap: 6, paddingLeft: 4 },
  teamLogo: { width: 18, height: 18, resizeMode: 'contain' },
  teamNameText: { color: COLORS.white, fontSize: 11, fontWeight: '700', flex: 1 },
  statCol: { width: 24, color: COLORS.textSoft, fontSize: 11, textAlign: 'center' },
  pointsCol: { width: 28, color: COLORS.white, fontSize: 13, fontWeight: '900', textAlign: 'center' },
  emptySmall: { color: COLORS.textDim, fontSize: 12, marginBottom: 10 },
  leaderCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.backgroundCard,
    borderWidth: 1,
    borderColor: COLORS.cardBorder,
    borderRadius: 14,
    padding: 10,
    marginBottom: 8,
    gap: 10,
  },
  leaderRank: { color: COLORS.primaryGlow, fontSize: 13, fontWeight: '900', width: 22, textAlign: 'center' },
  leaderAvatar: {
    width: 38,
    height: 38,
    borderRadius: 19,
    borderWidth: 1.5,
    borderColor: COLORS.avatarRingEmerald,
    backgroundColor: 'rgba(16,185,129,0.08)',
  },
  leaderName: { color: COLORS.white, fontSize: 13, fontWeight: '800' },
  leaderSub: { color: COLORS.textMuted, fontSize: 10, marginTop: 2 },
  leaderStatWrap: { alignItems: 'center', minWidth: 36 },
  leaderNum: { color: COLORS.primaryGlow, fontSize: 16, fontWeight: '900' },
  leaderUnit: { color: COLORS.textDim, fontSize: 9, fontWeight: '700' },
});
