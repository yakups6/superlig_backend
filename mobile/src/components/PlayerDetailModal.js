import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Modal,
  TouchableOpacity,
  Image,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { COLORS } from '../theme/colors';
import {
  DEFAULT_PLAYER_IMG,
  formatMarketValue,
  cleanPlayerDisplayName,
} from '../utils/format';
import { useAuth } from '../context/AuthContext';

export default function PlayerDetailModal({
  visible,
  player,
  seasonName = '2026/2027',
  onClose,
  onCompare,
}) {
  const { isFavorite, toggleFavorite, favorites, updatePlayerPrefs } = useAuth();
  const [favLoading, setFavLoading] = useState(false);

  if (!player) return null;

  const isHistorical =
    seasonName && seasonName !== 'ALL' && parseInt(String(seasonName), 10) < 2004;
  const valStr = formatMarketValue(player.market_value, player.is_legend, isHistorical);
  const fav = isFavorite(player.id);
  const favEntry = (favorites || []).find((x) => String(x.player || x.id) === String(player.id));
  const notifyGoals = favEntry?.notify_goals !== false;
  const notifyAssists = favEntry?.notify_assists !== false;
  const notify11 = favEntry?.notify_starting_11 !== false;

  const hasPeriodStats =
    (player.season_goals !== undefined && player.season_goals !== null) ||
    (player.season_matches !== undefined && player.season_matches !== null) ||
    (player.goals !== undefined && player.goals !== null);

  const matches = player.season_matches ?? player.matches ?? '-';
  const goals = player.season_goals ?? player.goals ?? 0;
  const assists = player.season_assists ?? player.assists ?? 0;
  const rating = player.season_rating ?? player.rating ?? '7.5';

  const handleToggleFav = async () => {
    try {
      setFavLoading(true);
      const res = await toggleFavorite(player);
      if (res?.message) {
        Alert.alert('Favoriler', res.message);
      }
    } catch (e) {
      Alert.alert('Hata', 'Favori işlemi tamamlanamadı.');
    } finally {
      setFavLoading(false);
    }
  };

  const handleComparePress = () => {
    onClose && onClose();
    onCompare && onCompare(player);
  };

  return (
    <Modal
      visible={visible}
      transparent
      animationType="fade"
      onRequestClose={onClose}
    >
      <TouchableOpacity
        style={styles.overlay}
        activeOpacity={1}
        onPress={onClose}
      >
        <View style={styles.card} onStartShouldSetResponder={() => true}>
          <View style={styles.avatarWrap}>
            <Image
              source={{ uri: player.image_url || DEFAULT_PLAYER_IMG }}
              style={styles.avatar}
            />
          </View>

          <Text style={styles.name}>
            {cleanPlayerDisplayName(player.name)}
          </Text>
          {Boolean(player.transfer_note) && (
            <View style={styles.transferTag}>
              <Text style={styles.transferTagText}>{player.transfer_note}</Text>
            </View>
          )}
          <Text style={styles.subTitle}>
            {player.team_name || player.team_short_name || 'Süper Lig'} • #
            {player.jersey_number || '-'}
          </Text>

          {hasPeriodStats && (
            <View style={styles.periodCard}>
              <Text style={styles.periodHeader}>
                {seasonName === 'ALL' ? 'KARİYER' : seasonName} PERFORMANSI
              </Text>
              <View style={styles.periodGrid}>
                <View style={styles.periodCol}>
                  <Text style={styles.periodVal}>{matches}</Text>
                  <Text style={styles.periodLbl}>Maç</Text>
                </View>
                <View style={styles.periodCol}>
                  <Text style={[styles.periodVal, { color: COLORS.accentRed }]}>
                    {goals}
                  </Text>
                  <Text style={styles.periodLbl}>Gol</Text>
                </View>
                <View style={styles.periodCol}>
                  <Text style={[styles.periodVal, { color: COLORS.accentBlue }]}>
                    {assists}
                  </Text>
                  <Text style={styles.periodLbl}>Asist</Text>
                </View>
                <View style={styles.periodCol}>
                  <Text style={[styles.periodVal, { color: COLORS.accentGold }]}>
                    ★ {rating}
                  </Text>
                  <Text style={styles.periodLbl}>Rating</Text>
                </View>
              </View>
            </View>
          )}

          <View style={styles.metaGrid}>
            <View style={styles.metaItem}>
              <Text style={styles.metaLbl}>Mevki</Text>
              <Text style={styles.metaVal} numberOfLines={1}>
                {player.position || '-'}
              </Text>
            </View>
            <View style={styles.metaItem}>
              <Text style={styles.metaLbl}>Piyasa Değeri</Text>
              <Text style={[styles.metaVal, { color: COLORS.accentBlue }]}>
                {valStr}
              </Text>
            </View>
            <View style={styles.metaItem}>
              <Text style={styles.metaLbl}>Yaş / Statü</Text>
              <Text style={styles.metaVal}>
                {player.age ? `${player.age} Yaş` : player.is_legend ? 'Efsane' : '-'}
              </Text>
            </View>
            <View style={styles.metaItem}>
              <Text style={styles.metaLbl}>Uyruk</Text>
              <Text style={styles.metaVal} numberOfLines={1}>
                {player.nationality || '-'}
              </Text>
            </View>
          </View>

          {onCompare && (
            <TouchableOpacity
              style={styles.compareBtn}
              onPress={handleComparePress}
            >
              <Text style={styles.compareBtnText}>⚖️ Bu Oyuncuyu Karşılaştır</Text>
            </TouchableOpacity>
          )}

          {/* BİLDİRİM TERCİHLERİ (FAVORİDEYSE) */}
          {fav && (
            <View style={styles.notifPrefsBox}>
              <Text style={styles.notifPrefsTitle}>🔔 Maçkolik Canlı Bildirimleri</Text>
              <View style={styles.notifPillsRow}>
                <TouchableOpacity
                  style={[styles.notifPill, notifyGoals && styles.notifPillActive]}
                  onPress={() => updatePlayerPrefs(player.id, { notify_goals: !notifyGoals })}
                >
                  <Text style={[styles.notifPillText, notifyGoals && styles.notifPillTextActive]}>
                    {notifyGoals ? '⚽ Goller: AÇIK' : '⚽ Gol: Kapalı'}
                  </Text>
                </TouchableOpacity>

                <TouchableOpacity
                  style={[styles.notifPill, notifyAssists && styles.notifPillActive]}
                  onPress={() => updatePlayerPrefs(player.id, { notify_assists: !notifyAssists })}
                >
                  <Text style={[styles.notifPillText, notifyAssists && styles.notifPillTextActive]}>
                    {notifyAssists ? '🎯 Asist: AÇIK' : '🎯 Asist: Kapalı'}
                  </Text>
                </TouchableOpacity>

                <TouchableOpacity
                  style={[styles.notifPill, notify11 && styles.notifPillActive]}
                  onPress={() => updatePlayerPrefs(player.id, { notify_starting_11: !notify11 })}
                >
                  <Text style={[styles.notifPillText, notify11 && styles.notifPillTextActive]}>
                    {notify11 ? '📋 İlk 11: AÇIK' : '📋 İlk 11: Kapalı'}
                  </Text>
                </TouchableOpacity>
              </View>
            </View>
          )}

          <TouchableOpacity
            style={[styles.favBtn, fav && styles.favBtnActive]}
            onPress={handleToggleFav}
            disabled={favLoading}
          >
            {favLoading ? (
              <ActivityIndicator size="small" color={COLORS.accentRed} />
            ) : (
              <Text style={styles.favBtnText}>
                {fav ? '💔 Favorilerden Çıkar' : '❤️ Favorilere Ekle'}
              </Text>
            )}
          </TouchableOpacity>

          <TouchableOpacity style={styles.closeBtn} onPress={onClose}>
            <Text style={styles.closeBtnText}>Kapat</Text>
          </TouchableOpacity>
        </View>
      </TouchableOpacity>
    </Modal>
  );
}

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.78)',
    justifyContent: 'center',
    padding: 20,
  },
  card: {
    backgroundColor: COLORS.backgroundCard,
    borderRadius: 22,
    borderWidth: 1.5,
    borderColor: COLORS.cardBorderStrong,
    padding: 18,
  },
  avatarWrap: {
    alignSelf: 'center',
    width: 76,
    height: 76,
    borderRadius: 38,
    borderWidth: 2,
    borderColor: COLORS.primaryGlow,
    overflow: 'hidden',
    marginBottom: 10,
    backgroundColor: 'rgba(52, 211, 153, 0.08)',
  },
  avatar: {
    width: '100%',
    height: '100%',
  },
  name: {
    color: COLORS.white,
    fontSize: 17,
    fontWeight: '900',
    textAlign: 'center',
  },
  transferTag: {
    alignSelf: 'center',
    backgroundColor: 'rgba(245,158,11,0.16)',
    borderColor: 'rgba(245,158,11,0.35)',
    borderWidth: 1,
    borderRadius: 6,
    paddingHorizontal: 8,
    paddingVertical: 2,
    marginTop: 4,
  },
  transferTagText: {
    color: COLORS.accentGold,
    fontSize: 10,
    fontWeight: '800',
  },
  subTitle: {
    color: COLORS.textMuted,
    fontSize: 12,
    fontWeight: '600',
    textAlign: 'center',
    marginTop: 4,
    marginBottom: 14,
  },
  periodCard: {
    backgroundColor: 'rgba(52, 211, 153, 0.09)',
    borderWidth: 1,
    borderColor: COLORS.cardBorderStrong,
    borderRadius: 12,
    padding: 12,
    marginBottom: 12,
  },
  periodHeader: {
    color: COLORS.primaryGlow,
    fontSize: 10,
    fontWeight: '800',
    textAlign: 'center',
    marginBottom: 8,
    letterSpacing: 0.5,
  },
  periodGrid: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  periodCol: {
    alignItems: 'center',
  },
  periodVal: {
    color: COLORS.white,
    fontSize: 17,
    fontWeight: '900',
  },
  periodLbl: {
    color: COLORS.textMuted,
    fontSize: 10,
    fontWeight: '600',
    marginTop: 2,
  },
  metaGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    backgroundColor: 'rgba(255,255,255,0.03)',
    borderRadius: 12,
    padding: 10,
    marginBottom: 14,
    gap: 8,
  },
  metaItem: {
    width: '47%',
  },
  metaLbl: {
    color: COLORS.textDim,
    fontSize: 10,
  },
  metaVal: {
    color: COLORS.white,
    fontSize: 12,
    fontWeight: '700',
    marginTop: 1,
  },
  notifPrefsBox: {
    backgroundColor: '#07161b',
    borderWidth: 1,
    borderColor: COLORS.primaryGlow,
    borderRadius: 12,
    padding: 10,
    marginBottom: 10,
  },
  notifPrefsTitle: {
    color: COLORS.primaryGlow,
    fontSize: 11,
    fontWeight: '900',
    marginBottom: 6,
    textAlign: 'center',
  },
  notifPillsRow: {
    flexDirection: 'row',
    gap: 6,
    justifyContent: 'center',
  },
  notifPill: {
    backgroundColor: 'rgba(255,255,255,0.05)',
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.1)',
    borderRadius: 8,
    paddingHorizontal: 8,
    paddingVertical: 5,
  },
  notifPillActive: {
    backgroundColor: 'rgba(16,185,129,0.18)',
    borderColor: COLORS.primaryGlow,
  },
  notifPillText: {
    color: COLORS.textDim,
    fontSize: 10,
    fontWeight: '700',
  },
  notifPillTextActive: {
    color: COLORS.primaryGlow,
    fontWeight: '800',
  },
  compareBtn: {
    backgroundColor: COLORS.primary,
    borderRadius: 12,
    paddingVertical: 12,
    alignItems: 'center',
    marginBottom: 8,
    borderWidth: 1,
    borderColor: COLORS.primaryGlow,
  },
  compareBtnText: {
    color: COLORS.white,
    fontSize: 13,
    fontWeight: '800',
  },
  favBtn: {
    backgroundColor: 'rgba(244,63,94,0.16)',
    borderWidth: 1,
    borderColor: 'rgba(244,63,94,0.4)',
    borderRadius: 10,
    paddingVertical: 10,
    alignItems: 'center',
    marginBottom: 8,
  },
  favBtnActive: {
    backgroundColor: 'rgba(239,68,68,0.22)',
  },
  favBtnText: {
    color: '#fb7185',
    fontSize: 13,
    fontWeight: '800',
  },
  closeBtn: {
    backgroundColor: 'rgba(255,255,255,0.07)',
    borderRadius: 10,
    paddingVertical: 10,
    alignItems: 'center',
  },
  closeBtnText: {
    color: COLORS.textSoft,
    fontSize: 12,
    fontWeight: '700',
  },
});

