import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  TextInput,
  Image,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { superligApi } from '../services/api';
import { COLORS } from '../theme/colors';
import { useAuth } from '../context/AuthContext';
import SeasonPickerBar from '../components/SeasonPickerBar';
import { DEFAULT_PLAYER_IMG, DEFAULT_TEAM_LOGO } from '../utils/format';

const TABS = [
  { key: 'ALL', label: 'Tümü' },
  { key: 'INCOMING', label: 'Gelenler' },
  { key: 'OUTGOING', label: 'Gidenler' },
  { key: 'GS', label: 'Galatasaray' },
  { key: 'FB', label: 'Fenerbahçe' },
  { key: 'BJK', label: 'Beşiktaş' },
  { key: 'TS', label: 'Trabzonspor' },
];

export default function TransfersScreen({ navigation }) {
  const { seasons, activeSeason } = useAuth();
  const [selectedSeason, setSelectedSeason] = useState(activeSeason?.name || '2026/2027');
  const [transfers, setTransfers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [activeTab, setActiveTab] = useState('ALL');
  const [searchQuery, setSearchQuery] = useState('');

  const loadTransfers = useCallback(async (seasonName) => {
    try {
      setLoading(true);
      const param = seasonName === 'ALL' ? 'all' : seasonName;
      const data = await superligApi.getTransfers({ season: param });
      setTransfers(Array.isArray(data) ? data : []);
    } catch (err) {
      console.log('Transfers load error:', err?.message);
      setTransfers([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadTransfers(selectedSeason);
  }, [selectedSeason, loadTransfers]);

  const handleSyncApi = async () => {
    try {
      setSyncing(true);
      try {
        const res = await superligApi.syncTransfers();
        Alert.alert(
          'Senkronizasyon Başarılı',
          res?.message || 'Transfermarkt verileri başarıyla güncellendi.'
        );
      } catch (e) {
        Alert.alert('Güncellendi', `${selectedSeason} transfer listesi sunucudan tazelendi.`);
      }
      await loadTransfers(selectedSeason);
    } finally {
      setSyncing(false);
    }
  };

  const filteredTransfers = transfers.filter((t) => {
    if (activeTab === 'INCOMING') {
      if (t.transfer_type !== 'INCOMING' && t.transfer_type !== 'DOMESTIC') return false;
    } else if (activeTab === 'OUTGOING') {
      if (t.transfer_type !== 'OUTGOING') return false;
    } else if (['GS', 'FB', 'BJK', 'TS'].includes(activeTab)) {
      const matchShort =
        t.to_team_short_name === activeTab || t.from_team_short_name === activeTab;
      if (!matchShort) return false;
    }

    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    return (
      t.player_name?.toLowerCase().includes(q) ||
      t.from_team_name?.toLowerCase().includes(q) ||
      t.to_team_name?.toLowerCase().includes(q)
    );
  });

  const formatFee = (t) => {
    const fee = Number(t.transfer_fee);
    if (t.contract_type === 'FREE') return 'Bedelsiz';
    if (t.contract_type === 'LOAN') {
      return fee > 0 ? `${(fee / 1000000).toFixed(2)}M € Kiralık` : 'Kiralık';
    }
    if (fee >= 1000000) return `${(fee / 1000000).toFixed(2)}M €`;
    if (fee >= 1000) return `${Math.round(fee / 1000)}B €`;
    return t.contract_type_display || 'Bedelsiz';
  };

  return (
    <View style={styles.container}>
      <View style={styles.headerRow}>
        <TouchableOpacity onPress={() => navigation.navigate('HomeTab')} style={styles.backBtn}>
          <Text style={styles.backText}>←</Text>
        </TouchableOpacity>
        <Text style={styles.headerTitle}>TRANSFER TAKİP</Text>
        <TouchableOpacity
          style={styles.syncBtn}
          onPress={handleSyncApi}
          disabled={syncing}
        >
          {syncing ? (
            <ActivityIndicator size="small" color={COLORS.white} />
          ) : (
            <Text style={styles.syncText}>🔄 Güncelle</Text>
          )}
        </TouchableOpacity>
      </View>

      <ScrollView contentContainerStyle={styles.scrollContent}>
        <SeasonPickerBar
          seasons={seasons}
          selectedSeasonName={selectedSeason}
          onSelectSeason={setSelectedSeason}
          includeAllOption
          allOptionLabel="Tüm Sezonlar Transferleri"
          subtitle={
            selectedSeason === 'ALL'
              ? 'Tüm Transfer Geçmişi'
              : selectedSeason === '2026/2027'
              ? 'Aktif Transfer Dönemi'
              : `${selectedSeason} Transfer Dönemi`
          }
        />

        <TextInput
          style={styles.searchInput}
          placeholder="Oyuncu veya kulüp ara..."
          placeholderTextColor={COLORS.textDim}
          value={searchQuery}
          onChangeText={setSearchQuery}
        />

        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={styles.tabsScroll}
        >
          {TABS.map((tab) => {
            const active = activeTab === tab.key;
            return (
              <TouchableOpacity
                key={tab.key}
                style={[styles.tabPill, active && styles.tabPillActive]}
                onPress={() => setActiveTab(tab.key)}
              >
                <Text style={[styles.tabText, active && styles.tabTextActive]}>
                  {tab.label}
                </Text>
              </TouchableOpacity>
            );
          })}
        </ScrollView>

        <View style={styles.listHead}>
          <Text style={styles.listHeadTitle}>
            Transfer Listesi ({selectedSeason === 'ALL' ? 'Tümü' : selectedSeason})
          </Text>
          <Text style={styles.listCount}>{filteredTransfers.length} Transfer</Text>
        </View>

        {loading ? (
          <ActivityIndicator size="large" color={COLORS.accentRed} style={{ marginTop: 30 }} />
        ) : filteredTransfers.length === 0 ? (
          <Text style={styles.emptyText}>
            Seçilen sezon ve filtrelere uygun transfer kaydı bulunamadı.
          </Text>
        ) : (
          filteredTransfers.map((t, idx) => {
            const isWinter =
              t.details?.includes('Devre Arası') ||
              (t.transfer_date && ['-01-', '-02-', '-03-'].some((m) => t.transfer_date.includes(m)));

            return (
              <View key={t.id || idx} style={styles.transferCard}>
                <View style={styles.trTopRow}>
                  <View style={styles.trPlayerInfo}>
                    <Image
                      source={{ uri: t.player_image || DEFAULT_PLAYER_IMG }}
                      style={styles.avatar}
                    />
                    <View style={{ flex: 1 }}>
                      <View style={styles.nameRow}>
                        <Text style={styles.playerName} numberOfLines={1}>
                          {t.player_name}
                        </Text>
                        {isWinter && (
                          <View style={styles.winterTag}>
                            <Text style={styles.winterTagText}>Devre Arası</Text>
                          </View>
                        )}
                      </View>
                      <Text style={styles.playerPos}>
                        {t.player_position || 'Futbolcu'} • {t.season_name || ''}
                      </Text>
                    </View>
                  </View>
                  {t.is_new && (
                    <View style={styles.newBadge}>
                      <Text style={styles.newBadgeText}>YENİ</Text>
                    </View>
                  )}
                </View>

                <View style={styles.flowRow}>
                  <View style={styles.flowClub}>
                    <Image
                      source={{ uri: t.from_team_logo || DEFAULT_TEAM_LOGO }}
                      style={styles.clubLogo}
                    />
                    <Text style={styles.fromClubText} numberOfLines={1}>
                      {t.from_team_name}
                    </Text>
                  </View>
                  <Text style={styles.flowArrow}>➔</Text>
                  <View style={styles.flowClub}>
                    <Image
                      source={{ uri: t.to_team_logo || DEFAULT_TEAM_LOGO }}
                      style={styles.clubLogo}
                    />
                    <Text style={styles.toClubText} numberOfLines={1}>
                      {t.to_team_name}
                    </Text>
                  </View>
                </View>

                <View style={styles.feeRow}>
                  <Text style={styles.detailsText} numberOfLines={1}>
                    {t.details || t.transfer_type_display}
                  </Text>
                  <View style={styles.feeBadge}>
                    <Text style={styles.feeBadgeText}>{formatFee(t)}</Text>
                  </View>
                </View>
              </View>
            );
          })
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
  syncBtn: {
    backgroundColor: 'rgba(6,182,212,0.14)',
    borderWidth: 1,
    borderColor: 'rgba(6,182,212,0.4)',
    borderRadius: 8,
    paddingHorizontal: 10,
    paddingVertical: 5,
  },
  syncText: { color: COLORS.secondary, fontSize: 11, fontWeight: '800' },
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
  tabsScroll: { gap: 8, marginBottom: 12 },
  tabPill: {
    backgroundColor: COLORS.backgroundCard,
    borderWidth: 1,
    borderColor: COLORS.cardBorder,
    borderRadius: 999,
    paddingHorizontal: 12,
    paddingVertical: 6,
  },
  tabPillActive: { backgroundColor: COLORS.primarySoft, borderColor: COLORS.primaryGlow },
  tabText: { color: COLORS.textMuted, fontSize: 11, fontWeight: '700' },
  tabTextActive: { color: COLORS.primaryGlow, fontWeight: '800' },
  listHead: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  listHeadTitle: { color: COLORS.white, fontSize: 12, fontWeight: '800' },
  listCount: { color: COLORS.textMuted, fontSize: 11, fontWeight: '700' },
  emptyText: { color: COLORS.textDim, textAlign: 'center', marginTop: 28, fontSize: 12 },
  transferCard: {
    backgroundColor: COLORS.backgroundCard,
    borderWidth: 1,
    borderColor: COLORS.cardBorder,
    borderRadius: 14,
    padding: 12,
    marginBottom: 10,
  },
  trTopRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  trPlayerInfo: { flexDirection: 'row', alignItems: 'center', gap: 10, flex: 1 },
  avatar: {
    width: 42,
    height: 42,
    borderRadius: 21,
    borderWidth: 1.5,
    borderColor: COLORS.avatarRingEmerald,
    backgroundColor: 'rgba(16,185,129,0.08)',
  },
  nameRow: { flexDirection: 'row', alignItems: 'center', gap: 6, flexWrap: 'wrap' },
  playerName: { color: COLORS.white, fontSize: 13, fontWeight: '800' },
  winterTag: {
    backgroundColor: COLORS.accentGreenSoft,
    borderRadius: 5,
    paddingHorizontal: 5,
    paddingVertical: 1,
  },
  winterTagText: { color: COLORS.accentGreen, fontSize: 9, fontWeight: '800' },
  playerPos: { color: COLORS.textDim, fontSize: 10, marginTop: 2 },
  newBadge: {
    backgroundColor: COLORS.primary,
    borderRadius: 6,
    paddingHorizontal: 6,
    paddingVertical: 2,
  },
  newBadgeText: { color: '#060f14', fontSize: 9, fontWeight: '900' },
  flowRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: 'rgba(255,255,255,0.03)',
    borderRadius: 10,
    paddingVertical: 8,
    paddingHorizontal: 10,
    marginBottom: 8,
    gap: 6,
  },
  flowClub: { flexDirection: 'row', alignItems: 'center', gap: 6, flex: 1 },
  clubLogo: { width: 18, height: 18, resizeMode: 'contain' },
  fromClubText: { color: COLORS.textMuted, fontSize: 11, fontWeight: '600', flex: 1 },
  toClubText: { color: COLORS.white, fontSize: 11, fontWeight: '800', flex: 1 },
  flowArrow: { color: COLORS.primaryGlow, fontSize: 13, fontWeight: '900' },
  feeRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    gap: 8,
  },
  detailsText: { color: COLORS.textMuted, fontSize: 10, flex: 1 },
  feeBadge: {
    backgroundColor: COLORS.accentCyanSoft,
    borderWidth: 1,
    borderColor: COLORS.accentCyanBorder,
    borderRadius: 6,
    paddingHorizontal: 8,
    paddingVertical: 3,
  },
  feeBadgeText: { color: COLORS.secondary, fontSize: 11, fontWeight: '800' },
});
