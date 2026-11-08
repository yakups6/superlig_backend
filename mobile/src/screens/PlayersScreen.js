import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Image,
  TextInput,
  ActivityIndicator,
  Modal,
  FlatList,
} from 'react-native';
import { COLORS } from '../theme/colors';
import { superligApi } from '../services/api';
import { useAuth } from '../context/AuthContext';
import SeasonPickerBar from '../components/SeasonPickerBar';
import PlayerDetailModal from '../components/PlayerDetailModal';
import {
  DEFAULT_PLAYER_IMG,
  formatMarketValue,
  cleanPlayerDisplayName,
} from '../utils/format';

const POS_TABS = [
  { key: 'ALL', label: 'Tümü' },
  { key: 'FORVET', label: 'Forvet' },
  { key: 'ORTA', label: 'Orta Saha' },
  { key: 'DEFANS', label: 'Defans' },
  { key: 'KALECI', label: 'Kaleci' },
];

export default function PlayersScreen({ navigation }) {
  const { seasons, activeSeason } = useAuth();
  const [selectedSeason, setSelectedSeason] = useState(activeSeason?.name || '2026/2027');
  const [players, setPlayers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [posFilter, setPosFilter] = useState('ALL');
  const [teamFilter, setTeamFilter] = useState('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [teamModalOpen, setTeamModalOpen] = useState(false);
  const [detailPlayer, setDetailPlayer] = useState(null);

  const loadPlayersForSeason = async (seasonName) => {
    try {
      setLoading(true);
      const data = await superligApi.getPlayers({ season: seasonName });
      setPlayers(Array.isArray(data) ? data : []);
    } catch (e) {
      console.log('Players error:', e?.message);
      setPlayers([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPlayersForSeason(selectedSeason);
  }, [selectedSeason]);

  const clubMap = new Map();
  players.forEach((p) => {
    const tId = p.team_id || p.current_team;
    if (tId && p.team_name && !clubMap.has(String(tId))) {
      clubMap.set(String(tId), p.team_name);
    }
  });
  const clubs = Array.from(clubMap.entries())
    .sort((a, b) => a[1].localeCompare(b[1], 'tr'))
    .map(([id, name]) => ({ id, name }));

  const filtered = players
    .filter((p) => {
      if (posFilter !== 'ALL') {
        const pos = (p.position || '').toLowerCase();
        if (posFilter === 'FORVET' && !pos.includes('forvet') && !pos.includes('santr') && !pos.includes('kanat'))
          return false;
        if (posFilter === 'ORTA' && !pos.includes('orta') && !pos.includes('on numara') && !pos.includes('önlibero'))
          return false;
        if (posFilter === 'DEFANS' && !pos.includes('stoper') && !pos.includes('bek') && !pos.includes('defans'))
          return false;
        if (posFilter === 'KALECI' && !pos.includes('kaleci')) return false;
      }
      if (teamFilter !== 'ALL') {
        if (String(p.team_id) !== String(teamFilter) && String(p.current_team) !== String(teamFilter)) {
          return false;
        }
      }
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        return (
          p.name?.toLowerCase().includes(q) ||
          p.position?.toLowerCase().includes(q) ||
          p.team_name?.toLowerCase().includes(q)
        );
      }
      return true;
    })
    .sort((a, b) => {
      const valDiff = (Number(b.market_value) || 0) - (Number(a.market_value) || 0);
      if (valDiff !== 0) return valDiff;
      return (Number(b.season_matches) || 0) - (Number(a.season_matches) || 0);
    });

  const isHistorical = parseInt(String(selectedSeason), 10) < 2004;
  const activeClubLabel =
    teamFilter === 'ALL'
      ? `Tüm Kulüpler (${clubs.length})`
      : clubMap.get(String(teamFilter)) || 'Kulüp';

  return (
    <View style={styles.container}>
      <View style={styles.headerRow}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backBtn}>
          <Text style={styles.backText}>←</Text>
        </TouchableOpacity>
        <Text style={styles.headerTitle}>SÜPER LİG OYUNCULARI</Text>
        <View style={{ width: 32 }} />
      </View>

      <ScrollView contentContainerStyle={styles.scrollContent}>
        <SeasonPickerBar
          seasons={seasons}
          selectedSeasonName={selectedSeason}
          onSelectSeason={(s) => {
            setTeamFilter('ALL');
            setSelectedSeason(s);
          }}
          subtitle={
            selectedSeason === '2026/2027'
              ? 'Aktif Sezon Kadroları'
              : `${selectedSeason} Dönem Kadroları`
          }
        />

        <TextInput
          style={styles.searchInput}
          placeholder="Tüm ligde oyuncu adı veya mevki ara..."
          placeholderTextColor={COLORS.textDim}
          value={searchQuery}
          onChangeText={setSearchQuery}
        />

        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={styles.posTabsRow}
        >
          {POS_TABS.map((t) => {
            const active = posFilter === t.key;
            return (
              <TouchableOpacity
                key={t.key}
                style={[styles.posPill, active && styles.posPillActive]}
                onPress={() => setPosFilter(t.key)}
              >
                <Text style={[styles.posPillText, active && styles.posPillTextActive]}>
                  {t.label}
                </Text>
              </TouchableOpacity>
            );
          })}
        </ScrollView>

        <TouchableOpacity
          style={styles.clubSelectBtn}
          onPress={() => setTeamModalOpen(true)}
        >
          <Text style={styles.clubSelectText}>{activeClubLabel}</Text>
          <Text style={styles.clubArrow}>▼</Text>
        </TouchableOpacity>

        <View style={styles.sectionHead}>
          <Text style={styles.sectionTitle}>Piyasa Değerine Göre Sıralı</Text>
          <Text style={styles.countText}>{filtered.length} Oyuncu</Text>
        </View>

        {loading ? (
          <ActivityIndicator size="large" color={COLORS.accentRed} style={{ marginTop: 30 }} />
        ) : filtered.length === 0 ? (
          <Text style={styles.emptyText}>Bu sezon ve kriterlere uygun oyuncu bulunamadı.</Text>
        ) : (
          filtered.slice(0, 120).map((p, idx) => {
            const hasStats = p.season_matches > 0;
            const sub = hasStats
              ? `${p.team_short_name || p.team_name || ''} • ${p.position || ''} • ${p.season_matches}M ${p.season_goals || 0}G ${p.season_assists || 0}A`
              : `${p.team_short_name || p.team_name || ''} • ${p.position || ''} • #${p.jersey_number || '-'}`;
            return (
              <TouchableOpacity
                key={`${p.id}-${idx}`}
                style={styles.playerCard}
                activeOpacity={0.78}
                onPress={() => setDetailPlayer(p)}
              >
                <View style={styles.cardLeft}>
                  <Image
                    source={{ uri: p.image_url || DEFAULT_PLAYER_IMG }}
                    style={styles.avatar}
                  />
                  <View style={{ flex: 1 }}>
                    <Text style={styles.playerName} numberOfLines={1}>
                      {cleanPlayerDisplayName(p.name)}
                    </Text>
                    <Text
                      style={[styles.playerSub, hasStats && { color: '#93c5fd' }]}
                      numberOfLines={1}
                    >
                      {sub}
                    </Text>
                  </View>
                </View>
                <View style={styles.valPill}>
                  <Text style={styles.valPillText}>
                    {formatMarketValue(p.market_value, p.is_legend, isHistorical)}
                  </Text>
                </View>
              </TouchableOpacity>
            );
          })
        )}
      </ScrollView>

      {/* CLUB PICKER MODAL */}
      <Modal
        visible={teamModalOpen}
        transparent
        animationType="fade"
        onRequestClose={() => setTeamModalOpen(false)}
      >
        <TouchableOpacity
          style={styles.modalOverlay}
          activeOpacity={1}
          onPress={() => setTeamModalOpen(false)}
        >
          <View style={styles.modalCard} onStartShouldSetResponder={() => true}>
            <Text style={styles.modalTitle}>Kulüp Filtresi</Text>
            <FlatList
              data={[{ id: 'ALL', name: `Tüm Kulüpler (${clubs.length} Takım)` }, ...clubs]}
              keyExtractor={(item) => String(item.id)}
              style={{ maxHeight: 360 }}
              renderItem={({ item }) => {
                const active = String(teamFilter) === String(item.id);
                return (
                  <TouchableOpacity
                    style={[styles.modalRow, active && styles.modalRowActive]}
                    onPress={() => {
                      setTeamFilter(item.id);
                      setTeamModalOpen(false);
                    }}
                  >
                    <Text style={[styles.modalRowText, active && { color: COLORS.white, fontWeight: '800' }]}>
                      {item.name}
                    </Text>
                  </TouchableOpacity>
                );
              }}
            />
          </View>
        </TouchableOpacity>
      </Modal>

      <PlayerDetailModal
        visible={Boolean(detailPlayer)}
        player={detailPlayer}
        seasonName={selectedSeason}
        onClose={() => setDetailPlayer(null)}
        onCompare={(p) =>
          navigation.navigate('MainTabs', {
            screen: 'CompareTab',
            params: { initialPlayer1: p.id, seasonName: selectedSeason, ts: Date.now() },
          })
        }
      />
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
  searchInput: {
    backgroundColor: COLORS.backgroundCard,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: COLORS.cardBorder,
    paddingHorizontal: 14,
    paddingVertical: 10,
    color: COLORS.white,
    fontSize: 12,
    marginBottom: 10,
  },
  posTabsRow: { gap: 8, marginBottom: 10 },
  posPill: {
    backgroundColor: COLORS.backgroundCard,
    borderWidth: 1,
    borderColor: COLORS.cardBorder,
    borderRadius: 999,
    paddingHorizontal: 12,
    paddingVertical: 6,
  },
  posPillActive: { backgroundColor: COLORS.primarySoft, borderColor: COLORS.primaryGlow },
  posPillText: { color: COLORS.textMuted, fontSize: 11, fontWeight: '700' },
  posPillTextActive: { color: COLORS.primaryGlow, fontWeight: '800' },
  clubSelectBtn: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: COLORS.backgroundCard,
    borderWidth: 1,
    borderColor: COLORS.cardBorderStrong,
    borderRadius: 12,
    paddingHorizontal: 14,
    paddingVertical: 10,
    marginBottom: 12,
  },
  clubSelectText: { color: COLORS.white, fontSize: 12, fontWeight: '700' },
  clubArrow: { color: COLORS.secondary, fontSize: 11, fontWeight: '800' },
  sectionHead: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  sectionTitle: { color: COLORS.white, fontSize: 12, fontWeight: '800' },
  countText: { color: COLORS.textMuted, fontSize: 11, fontWeight: '700' },
  playerCard: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: COLORS.backgroundCard,
    borderWidth: 1,
    borderColor: COLORS.cardBorder,
    borderRadius: 14,
    padding: 11,
    marginBottom: 8,
    gap: 8,
  },
  cardLeft: { flexDirection: 'row', alignItems: 'center', gap: 11, flex: 1 },
  avatar: {
    width: 44,
    height: 44,
    borderRadius: 22,
    borderWidth: 2,
    borderColor: COLORS.avatarRingEmerald,
    backgroundColor: 'rgba(16,185,129,0.08)',
  },
  playerName: { color: COLORS.white, fontSize: 13, fontWeight: '800' },
  playerSub: { color: COLORS.textMuted, fontSize: 10, marginTop: 2 },
  valPill: {
    backgroundColor: COLORS.accentCyanSoft,
    borderWidth: 1,
    borderColor: COLORS.accentCyanBorder,
    borderRadius: 8,
    paddingHorizontal: 9,
    paddingVertical: 5,
  },
  valPillText: { color: COLORS.secondary, fontSize: 11, fontWeight: '800' },
  emptyText: { color: COLORS.textDim, textAlign: 'center', marginTop: 24, fontSize: 12 },
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
  modalTitle: { color: COLORS.white, fontSize: 14, fontWeight: '800', marginBottom: 10 },
  modalRow: { paddingVertical: 10, paddingHorizontal: 10, borderRadius: 8 },
  modalRowActive: { backgroundColor: 'rgba(52,211,153,0.15)' },
  modalRowText: { color: COLORS.textSoft, fontSize: 13 },
});
