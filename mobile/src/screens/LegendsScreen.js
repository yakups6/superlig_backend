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
} from 'react-native';
import { superligApi } from '../services/api';
import { COLORS } from '../theme/colors';
import { useAuth } from '../context/AuthContext';
import SeasonPickerBar from '../components/SeasonPickerBar';
import PlayerDetailModal from '../components/PlayerDetailModal';
import { DEFAULT_PLAYER_IMG, cleanPlayerDisplayName } from '../utils/format';

const POS_TABS = [
  { key: 'ALL', label: 'Tümü' },
  { key: 'FORVET', label: 'Forvet' },
  { key: 'ORTA', label: 'Orta Saha' },
  { key: 'DEFANS', label: 'Defans' },
  { key: 'KALECI', label: 'Kaleci' },
];

export default function LegendsScreen({ navigation }) {
  const { seasons } = useAuth();
  const [selectedSeason, setSelectedSeason] = useState('ALL');
  const [posFilter, setPosFilter] = useState('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [legends, setLegends] = useState([]);
  const [loading, setLoading] = useState(true);
  const [detailPlayer, setDetailPlayer] = useState(null);

  const loadLegends = useCallback(async (seasonName, pos) => {
    try {
      setLoading(true);
      const params = {};
      if (seasonName && seasonName !== 'ALL') params.season = seasonName;
      if (pos && pos !== 'ALL') params.position = pos;
      const data = await superligApi.getLegends(params);
      setLegends(Array.isArray(data) ? data : []);
    } catch (err) {
      console.log('Legends load error:', err?.message);
      setLegends([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadLegends(selectedSeason, posFilter);
  }, [selectedSeason, posFilter, loadLegends]);

  const filtered = legends.filter((l) => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    return (
      l.name?.toLowerCase().includes(q) ||
      l.position?.toLowerCase().includes(q) ||
      l.team_name?.toLowerCase().includes(q) ||
      l.nationality?.toLowerCase().includes(q)
    );
  });

  return (
    <View style={styles.container}>
      <View style={styles.headerRow}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backBtn}>
          <Text style={styles.backText}>←</Text>
        </TouchableOpacity>
        <Text style={styles.headerTitle}>ESKİ OYUNCULAR & EFSANELER</Text>
        <View style={{ width: 32 }} />
      </View>

      <ScrollView contentContainerStyle={styles.scrollContent}>
        <SeasonPickerBar
          seasons={seasons}
          selectedSeasonName={selectedSeason}
          onSelectSeason={setSelectedSeason}
          includeAllOption
          allOptionLabel="Tüm Zamanların Efsaneleri"
          subtitle={
            selectedSeason === 'ALL'
              ? '1959’dan Günümüze Tüm Efsaneler'
              : `${selectedSeason} Dönemi Yıldızları`
          }
        />

        <TextInput
          style={styles.searchInput}
          placeholder="Efsane oyuncu, kulüp veya mevki ara..."
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

        <View style={styles.headRow}>
          <Text style={styles.headTitle}>
            {selectedSeason === 'ALL'
              ? 'TÜM ZAMANLARIN EFSANELERİ'
              : `${selectedSeason} DÖNEMİ`}
          </Text>
          <View style={styles.countBadge}>
            <Text style={styles.countBadgeText}>{filtered.length} Oyuncu</Text>
          </View>
        </View>

        {loading ? (
          <ActivityIndicator size="large" color={COLORS.accentGold} style={{ marginTop: 36 }} />
        ) : filtered.length === 0 ? (
          <Text style={styles.emptyText}>Arama kriterlerine uygun oyuncu bulunamadı.</Text>
        ) : (
          filtered.map((item, idx) => {
            const hasMatches = item.season_matches > 0 || item.career_matches > 0;
            const m = item.season_matches ?? item.career_matches ?? 0;
            const g = item.season_goals ?? item.career_goals ?? 0;
            const a = item.season_assists ?? item.career_assists ?? 0;
            const sub = hasMatches
              ? `${item.team_short_name || item.team_name || ''} • ${item.position || 'Futbolcu'} • ${m}M ${g}G ${a}A`
              : `${item.team_short_name || item.team_name || ''} • ${item.position || 'Efsane'} • ${item.nationality || ''}`;

            return (
              <TouchableOpacity
                key={`${item.id}-${idx}`}
                style={styles.legendCard}
                activeOpacity={0.78}
                onPress={() => setDetailPlayer(item)}
              >
                <View style={styles.cardLeft}>
                  <Image
                    source={{ uri: item.image_url || DEFAULT_PLAYER_IMG }}
                    style={[
                      styles.avatarImg,
                      !item.is_legend && { borderColor: COLORS.cardBorderStrong },
                    ]}
                  />
                  <View style={{ flex: 1 }}>
                    <Text style={styles.legendName} numberOfLines={1}>
                      {cleanPlayerDisplayName(item.name)}
                    </Text>
                    <Text style={styles.legendPos} numberOfLines={1}>
                      {sub}
                    </Text>
                  </View>
                </View>

                {item.is_legend ? (
                  <View style={styles.starBadge}>
                    <Text style={styles.starText}>★ Efsane</Text>
                  </View>
                ) : (
                  <View style={styles.goalBadge}>
                    <Text style={styles.goalBadgeText}>{g} Gol</Text>
                  </View>
                )}
              </TouchableOpacity>
            );
          })
        )}
      </ScrollView>

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
  headerTitle: { color: COLORS.white, fontSize: 13, fontWeight: '800' },
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
  posTabsRow: { gap: 8, marginBottom: 12 },
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
  headRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  headTitle: { color: COLORS.white, fontSize: 12, fontWeight: '800' },
  countBadge: {
    backgroundColor: COLORS.accentGoldSoft,
    borderWidth: 1,
    borderColor: 'rgba(245,158,11,0.4)',
    borderRadius: 8,
    paddingHorizontal: 8,
    paddingVertical: 3,
  },
  countBadgeText: { color: COLORS.accentGold, fontSize: 10, fontWeight: '800' },
  emptyText: { color: COLORS.textDim, textAlign: 'center', marginTop: 28, fontSize: 12 },
  legendCard: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: COLORS.backgroundCard,
    borderRadius: 14,
    padding: 10,
    borderWidth: 1,
    borderColor: COLORS.cardBorder,
    marginBottom: 8,
    gap: 8,
  },
  cardLeft: { flexDirection: 'row', alignItems: 'center', flex: 1, gap: 10 },
  avatarImg: {
    width: 44,
    height: 44,
    borderRadius: 22,
    borderWidth: 2,
    borderColor: COLORS.avatarRingGold,
    backgroundColor: 'rgba(251,191,36,0.08)',
  },
  legendName: { color: COLORS.white, fontSize: 13, fontWeight: '800' },
  legendPos: { color: '#fcd34d', fontSize: 10, marginTop: 2, fontWeight: '600' },
  starBadge: {
    backgroundColor: COLORS.accentGoldSoft,
    borderWidth: 1,
    borderColor: COLORS.accentGoldBorder,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
  },
  starText: { color: COLORS.accentGold, fontSize: 10, fontWeight: '800' },
  goalBadge: {
    backgroundColor: COLORS.primarySoft,
    borderWidth: 1,
    borderColor: COLORS.primaryGlow,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
  },
  goalBadgeText: { color: COLORS.primaryGlow, fontSize: 10, fontWeight: '800' },
});
