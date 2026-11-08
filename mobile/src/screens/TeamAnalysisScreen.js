import React, { useState, useEffect, useCallback } from 'react';
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
import { superligApi } from '../services/api';
import { COLORS } from '../theme/colors';
import { useAuth } from '../context/AuthContext';
import SeasonPickerBar from '../components/SeasonPickerBar';
import PlayerDetailModal from '../components/PlayerDetailModal';
import {
  DEFAULT_PLAYER_IMG,
  DEFAULT_TEAM_LOGO,
  formatMarketValue,
  cleanPlayerDisplayName,
} from '../utils/format';

const HISTORICAL_CLUBS = [
  'Bursaspor',
  'Eskişehirspor',
  'Altay',
  'Ankaragücü',
  'Gençlerbirliği',
  'Gaziantepspor',
  'Antalyaspor',
  'Kayserispor',
  'Sivasspor',
  'Adanaspor',
  'Boluspor',
  'Sakaryaspor',
  'İstanbulspor',
];

export default function TeamAnalysisScreen({ navigation, route }) {
  const { seasons, activeSeason, isTeamFavorite, toggleFavoriteTeam } = useAuth();
  const [selectedSeason, setSelectedSeason] = useState(activeSeason?.name || '2026/2027');
  const [teams, setTeams] = useState([]);
  const [selectedTeamId, setSelectedTeamId] = useState(null);
  const [teamDetail, setTeamDetail] = useState(null);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [teamModalOpen, setTeamModalOpen] = useState(false);
  const [detailPlayer, setDetailPlayer] = useState(null);

  const loadTeamDetail = useCallback(async (teamId, seasonName) => {
    if (!teamId) return;
    try {
      setLoading(true);
      const detail = await superligApi.getTeamDetail(teamId, seasonName);
      setTeamDetail(detail);
      setSelectedTeamId(teamId);
    } catch (err) {
      console.log('Team detail error:', err?.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    async function init() {
      try {
        const [slTeams, allTeams] = await Promise.all([
          superligApi.getTeams({ is_super_lig: true }),
          superligApi.getTeams(),
        ]);
        const activeList = Array.isArray(slTeams) ? slTeams : [];
        const histList = (Array.isArray(allTeams) ? allTeams : []).filter(
          (t) => !t.is_super_lig && HISTORICAL_CLUBS.includes(t.name)
        );
        const combined = [...activeList, ...histList];
        setTeams(combined);
        if (combined.length > 0) {
          const initId = route?.params?.teamId || combined[0].id;
          setSelectedTeamId(initId);
          loadTeamDetail(initId, selectedSeason);
        } else {
          setLoading(false);
        }
      } catch (err) {
        console.log('Teams load error:', err?.message);
        setLoading(false);
      }
    }
    init();
  }, []);

  const handleSelectSeason = (sName) => {
    setSelectedSeason(sName);
    if (selectedTeamId) {
      loadTeamDetail(selectedTeamId, sName);
    }
  };

  const handleSelectTeam = (id) => {
    setTeamModalOpen(false);
    setSearchQuery('');
    loadTeamDetail(id, selectedSeason);
  };

  const filteredPlayers = (teamDetail?.players || [])
    .filter(
      (p) =>
        p.name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        p.position?.toLowerCase().includes(searchQuery.toLowerCase())
    )
    .sort((a, b) => (Number(b.market_value) || 0) - (Number(a.market_value) || 0));

  const selectedTeamObj =
    teams.find((t) => t.id === selectedTeamId) || teamDetail || { name: 'Takım Seçiniz' };

  const isHistorical = parseInt(String(selectedSeason), 10) < 2004;

  const teamValueLabel = (() => {
    const mv = Number(teamDetail?.market_value);
    if (!mv) return '-';
    const inM = mv / 1000000;
    return inM % 1 === 0 ? `${inM}M €` : `${inM.toFixed(1)}M €`;
  })();

  const seasonSub = (() => {
    if (selectedSeason === '2026/2027') return 'Aktif Sezon • Süper Lig Kadrosu';
    if (teamDetail?.standing) {
      const st = teamDetail.standing;
      return `${selectedSeason} • ${st.rank}. Sıra • ${st.won}G ${st.drawn}B ${st.lost}M (${st.points} P)`;
    }
    return `${selectedSeason} Sezonu Kadro & İstatistikleri`;
  })();

  const isFavTeam = Boolean(selectedTeamObj?.id && isTeamFavorite(selectedTeamObj.id));

  return (
    <View style={styles.container}>
      <View style={styles.headerRow}>
        <TouchableOpacity onPress={() => navigation.navigate('HomeTab')} style={styles.backBtn}>
          <Text style={styles.backText}>←</Text>
        </TouchableOpacity>
        <Text style={styles.headerTitle}>TAKIM ANALİZİ</Text>
        <View style={{ width: 32 }} />
      </View>

      <ScrollView contentContainerStyle={styles.scrollContent}>
        <SeasonPickerBar
          seasons={seasons}
          selectedSeasonName={selectedSeason}
          onSelectSeason={handleSelectSeason}
          subtitle={seasonSub}
        />

        <Text style={styles.fieldLabel}>Kulüp Seçimi</Text>
        <TouchableOpacity
          style={styles.dropdownToggle}
          activeOpacity={0.8}
          onPress={() => setTeamModalOpen(true)}
        >
          <View style={styles.dropdownTeamRow}>
            {Boolean(selectedTeamObj?.logo_url) && (
              <Image
                source={{ uri: selectedTeamObj.logo_url || DEFAULT_TEAM_LOGO }}
                style={styles.clubLogo}
              />
            )}
            <Text style={styles.dropdownText} numberOfLines={1}>
              {selectedTeamObj?.name}
            </Text>
          </View>
          <Text style={styles.dropdownArrow}>▼</Text>
        </TouchableOpacity>

        {/* FAVORİ TAKIM & BİLDİRİM BUTONU */}
        {Boolean(selectedTeamObj?.id) && (
          <TouchableOpacity
            style={[styles.favTeamBtn, isFavTeam && styles.favTeamBtnActive]}
            activeOpacity={0.8}
            onPress={() => toggleFavoriteTeam(selectedTeamObj)}
          >
            <Text style={[styles.favTeamText, isFavTeam && styles.favTeamTextActive]}>
              {isFavTeam
                ? '⭐ Favori Kulübüm (⚽ Canlı Gol & Kadro Bildirimleri Aktif)'
                : '☆ Bu Kulübü Favorilere Ekle (Canlı Bildirim Al)'}
            </Text>
          </TouchableOpacity>
        )}

        {/* 3 METRIC BADGES */}
        <View style={styles.metricsRow}>
          <View style={styles.metricCard}>
            <Text style={styles.metricValue}>
              {teamDetail?.standing ? `${teamDetail.standing.points} P` : '-'}
            </Text>
            <Text style={styles.metricLabel}>Puan</Text>
          </View>

          <View style={styles.metricCard}>
            <Text style={styles.metricValue}>
              {teamDetail?.standing?.rank
                ? teamDetail.standing.rank === 1
                  ? '1. Sıra 🏆'
                  : `${teamDetail.standing.rank}. Sıra`
                : '-'}
            </Text>
            <Text style={styles.metricLabel}>Ligdeki Sıra</Text>
          </View>

          <View style={styles.metricCard}>
            <Text style={styles.metricValue}>{teamValueLabel}</Text>
            <Text style={styles.metricLabel}>Kadro Değeri</Text>
          </View>
        </View>

        <View style={styles.listHeader}>
          <Text style={styles.listTitle}>Oyuncu Listesi</Text>
          <Text style={styles.squadCount}>
            {teamDetail?.players?.length || 0} Oyuncu ({selectedSeason})
          </Text>
        </View>

        <TextInput
          style={styles.searchInput}
          placeholder="Kadroda oyuncu veya mevki ara..."
          placeholderTextColor={COLORS.textDim}
          value={searchQuery}
          onChangeText={setSearchQuery}
        />

        {loading ? (
          <ActivityIndicator size="large" color={COLORS.accentRed} style={{ marginTop: 28 }} />
        ) : filteredPlayers.length === 0 ? (
          <Text style={styles.emptyText}>
            Bu sezon ve takım için kadro kaydı bulunmuyor.
          </Text>
        ) : (
          filteredPlayers.map((p, idx) => {
            const hasStats = p.season_matches > 0;
            const sub = hasStats
              ? `${p.position || 'Futbolcu'} • ${p.season_matches} Maç • ${p.season_goals || 0} Gol • ${p.season_assists || 0} Asist`
              : `${p.position || 'Futbolcu'} • #${p.jersey_number || '-'}`;

            return (
              <TouchableOpacity
                key={`${p.id}-${idx}`}
                style={styles.playerCard}
                activeOpacity={0.78}
                onPress={() => setDetailPlayer({ ...p, team_name: selectedTeamObj?.name })}
              >
                <View style={styles.cardLeft}>
                  <Image
                    source={{ uri: p.image_url || DEFAULT_PLAYER_IMG }}
                    style={styles.avatar}
                  />
                  <View style={{ flex: 1 }}>
                    <View style={styles.nameRow}>
                      <Text style={styles.playerName} numberOfLines={1}>
                        {cleanPlayerDisplayName(p.name)}
                      </Text>
                      {Boolean(p.transfer_note) && (
                        <View style={styles.noteTag}>
                          <Text style={styles.noteTagText}>{p.transfer_note}</Text>
                        </View>
                      )}
                    </View>
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

      {/* TEAM SELECTOR MODAL */}
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
            <View style={styles.modalHead}>
              <Text style={styles.modalTitle}>Kulüp Seç ({teams.length})</Text>
              <TouchableOpacity onPress={() => setTeamModalOpen(false)}>
                <Text style={styles.modalClose}>✕</Text>
              </TouchableOpacity>
            </View>
            <FlatList
              data={teams}
              keyExtractor={(item) => String(item.id)}
              style={{ maxHeight: 380 }}
              renderItem={({ item }) => {
                const active = item.id === selectedTeamId;

                return (
                  <TouchableOpacity
                    style={[styles.modalRow, active && styles.modalRowActive]}
                    onPress={() => handleSelectTeam(item.id)}
                  >
                    <Image
                      source={{ uri: item.logo_url || DEFAULT_TEAM_LOGO }}
                      style={styles.clubLogo}
                    />
                    <Text
                      style={[
                        styles.modalRowText,
                        active && { color: COLORS.white, fontWeight: '800' },
                      ]}
                    >
                      {item.name}
                    </Text>
                    {!item.is_super_lig && (
                      <Text style={styles.histTag}>Tarihi</Text>
                    )}
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
          navigation.navigate('CompareTab', {
            initialPlayer1: p.id,
            seasonName: selectedSeason,
            ts: Date.now(),
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
  fieldLabel: { color: COLORS.textMuted, fontSize: 11, fontWeight: '700', marginBottom: 6 },
  dropdownToggle: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: COLORS.backgroundCard,
    borderWidth: 1,
    borderColor: COLORS.cardBorderStrong,
    borderRadius: 12,
    paddingHorizontal: 12,
    paddingVertical: 11,
    marginBottom: 12,
  },
  dropdownTeamRow: { flexDirection: 'row', alignItems: 'center', gap: 10, flex: 1 },
  clubLogo: { width: 22, height: 22, resizeMode: 'contain' },
  dropdownText: { color: COLORS.white, fontSize: 14, fontWeight: '800', flex: 1 },
  dropdownArrow: { color: COLORS.secondary, fontSize: 11, fontWeight: '800' },
  favTeamBtn: {
    backgroundColor: 'rgba(255,255,255,0.04)',
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.1)',
    borderRadius: 12,
    paddingVertical: 10,
    paddingHorizontal: 12,
    alignItems: 'center',
    marginBottom: 14,
  },
  favTeamBtnActive: {
    backgroundColor: 'rgba(16,185,129,0.15)',
    borderColor: COLORS.primaryGlow,
  },
  favTeamText: {
    color: COLORS.textSoft,
    fontSize: 11,
    fontWeight: '800',
  },
  favTeamTextActive: {
    color: COLORS.primaryGlow,
    fontWeight: '900',
  },
  metricsRow: { flexDirection: 'row', gap: 8, marginBottom: 14 },
  metricCard: {
    flex: 1,
    backgroundColor: COLORS.backgroundCard,
    borderWidth: 1,
    borderColor: COLORS.cardBorder,
    borderRadius: 14,
    paddingVertical: 12,
    paddingHorizontal: 8,
    alignItems: 'center',
  },
  metricValue: { color: COLORS.primaryGlow, fontSize: 15, fontWeight: '900' },
  metricLabel: { color: COLORS.textMuted, fontSize: 10, fontWeight: '600', marginTop: 3 },
  listHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  listTitle: { color: COLORS.white, fontSize: 13, fontWeight: '800' },
  squadCount: { color: COLORS.textMuted, fontSize: 11, fontWeight: '700' },
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
  playerCard: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: COLORS.backgroundCard,
    borderWidth: 1,
    borderColor: COLORS.cardBorder,
    borderRadius: 14,
    padding: 10,
    marginBottom: 8,
    gap: 8,
  },
  cardLeft: { flexDirection: 'row', alignItems: 'center', gap: 10, flex: 1 },
  avatar: {
    width: 44,
    height: 44,
    borderRadius: 22,
    borderWidth: 2,
    borderColor: COLORS.avatarRingEmerald,
    backgroundColor: 'rgba(16,185,129,0.08)',
  },
  nameRow: { flexDirection: 'row', alignItems: 'center', gap: 6, flexWrap: 'wrap' },
  playerName: { color: COLORS.white, fontSize: 13, fontWeight: '800' },
  noteTag: {
    backgroundColor: COLORS.accentGoldSoft,
    borderRadius: 5,
    paddingHorizontal: 5,
    paddingVertical: 1,
  },
  noteTagText: { color: COLORS.accentGold, fontSize: 9, fontWeight: '800' },
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
  modalHead: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  modalTitle: { color: COLORS.white, fontSize: 14, fontWeight: '800' },
  modalClose: { color: COLORS.textMuted, fontSize: 16, fontWeight: '800', paddingHorizontal: 6 },
  modalRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 10,
    paddingHorizontal: 8,
    borderRadius: 10,
    gap: 10,
  },
  modalRowActive: { backgroundColor: 'rgba(52,211,153,0.15)' },
  modalRowText: { color: COLORS.textSoft, fontSize: 13, flex: 1 },
  histTag: { color: COLORS.accentGold, fontSize: 10, fontWeight: '700' },
});
