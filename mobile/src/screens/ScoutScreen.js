import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Image,
  RefreshControl,
  Alert,
  Modal,
  FlatList,
  TextInput,
  ActivityIndicator,
} from 'react-native';
import { useIsFocused } from '@react-navigation/native';
import { COLORS } from '../theme/colors';
import { useAuth } from '../context/AuthContext';
import { superligApi } from '../services/api';
import PlayerDetailModal from '../components/PlayerDetailModal';
import { DEFAULT_PLAYER_IMG, DEFAULT_TEAM_LOGO } from '../utils/format';

const TABS = [
  { key: 'PLAYERS', label: '👥 Oyuncularım' },
  { key: 'TEAMS', label: '🛡️ Kulüplerim' },
  { key: 'INBOX', label: '🔔 Bildirimler' },
];

export default function ScoutScreen({ navigation }) {
  const isFocused = useIsFocused();
  const {
    isLoggedIn,
    favorites,
    favoriteTeams,
    unreadCount,
    refreshFavorites,
    refreshFavoriteTeams,
    refreshUnreadCount,
    toggleFavorite,
    updatePlayerPrefs,
    toggleFavoriteTeam,
    updateTeamPrefs,
    triggerTestNotification,
  } = useAuth();

  const [activeTab, setActiveTab] = useState('PLAYERS');
  const [refreshing, setRefreshing] = useState(false);
  const [detailPlayer, setDetailPlayer] = useState(null);

  // Bildirim Kutusu
  const [notifications, setNotifications] = useState([]);
  const [loadingInbox, setLoadingInbox] = useState(false);
  const [testBusy, setTestBusy] = useState(false);

  // Kulüp Ekleme Modalı
  const [teamModalOpen, setTeamModalOpen] = useState(false);
  const [allTeams, setAllTeams] = useState([]);
  const [teamSearch, setTeamSearch] = useState('');

  const loadInbox = useCallback(async () => {
    try {
      setLoadingInbox(true);
      const list = await superligApi.getNotificationInbox();
      setNotifications(Array.isArray(list) ? list : []);
      await refreshUnreadCount();
    } catch (e) {
      setNotifications([]);
    } finally {
      setLoadingInbox(false);
    }
  }, [refreshUnreadCount]);

  const loadAllTeams = useCallback(async () => {
    try {
      const data = await superligApi.getTeams({ is_super_lig: true });
      setAllTeams(Array.isArray(data) ? data : []);
    } catch (e) {}
  }, []);

  useEffect(() => {
    if (isFocused) {
      refreshFavorites();
      refreshFavoriteTeams();
      refreshUnreadCount();
      if (activeTab === 'INBOX') loadInbox();
    }
  }, [isFocused, activeTab, refreshFavorites, refreshFavoriteTeams, refreshUnreadCount, loadInbox]);

  const onRefresh = async () => {
    setRefreshing(true);
    await Promise.allSettled([
      refreshFavorites(),
      refreshFavoriteTeams(),
      refreshUnreadCount(),
      activeTab === 'INBOX' ? loadInbox() : Promise.resolve(),
    ]);
    setRefreshing(false);
  };

  const handleMarkAllRead = async () => {
    try {
      await superligApi.markAllNotificationsRead();
      await loadInbox();
      await refreshUnreadCount();
    } catch (e) {}
  };

  return (
    <View style={styles.container}>
      {/* HEADER */}
      <View style={styles.headerRow}>
        <TouchableOpacity onPress={() => navigation.navigate('HomeTab')} style={styles.backBtn}>
          <Text style={styles.backText}>←</Text>
        </TouchableOpacity>
        <Text style={styles.headerTitle}>FAVORİLER & BİLDİRİM MERKEZİ</Text>
        <View style={{ width: 32 }} />
      </View>

      {/* 3 TOP TABS */}
      <View style={styles.tabsRow}>
        {TABS.map((t) => {
          const active = activeTab === t.key;
          const badgeVal =
            t.key === 'PLAYERS'
              ? favorites.length
              : t.key === 'TEAMS'
              ? favoriteTeams.length
              : unreadCount;

          return (
            <TouchableOpacity
              key={t.key}
              style={[styles.tabBtn, active && styles.tabBtnActive]}
              onPress={() => {
                setActiveTab(t.key);
                if (t.key === 'INBOX') loadInbox();
              }}
            >
              <Text style={[styles.tabBtnText, active && styles.tabBtnTextActive]}>
                {t.label}
              </Text>
              {Boolean(badgeVal > 0) && (
                <View
                  style={[
                    styles.tabBadge,
                    t.key === 'INBOX' && styles.tabBadgeRed,
                    active && styles.tabBadgeActive,
                  ]}
                >
                  <Text style={styles.tabBadgeText}>{badgeVal}</Text>
                </View>
              )}
            </TouchableOpacity>
          );
        })}
      </View>

      <ScrollView
        contentContainerStyle={styles.scrollContent}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={COLORS.primary} />
        }
      >
        {!isLoggedIn && (
          <TouchableOpacity
            style={styles.guestHint}
            onPress={() => navigation.navigate('Auth')}
          >
            <Text style={styles.guestHintText}>
              👤 Favorilerinizi ve bildirim tercihlerinizi kalıcı saklamak için giriş yapın.
            </Text>
            <Text style={styles.guestHintLink}>Giriş / Kayıt →</Text>
          </TouchableOpacity>
        )}

        {/* ========================================== */}
        {/* TAB 1: OYUNCULARIM (SCOUT)                  */}
        {/* ========================================== */}
        {activeTab === 'PLAYERS' && (
          <>
            <View style={styles.sectionHeader}>
              <Text style={styles.sectionTitle}>
                Takip Ettiğim Futbolcular ({favorites.length})
              </Text>
              <TouchableOpacity
                style={styles.addBtn}
                onPress={() => navigation.navigate('Players')}
              >
                <Text style={styles.addBtnText}>+ Oyuncu Ekle</Text>
              </TouchableOpacity>
            </View>

            {favorites.length === 0 ? (
              <View style={styles.emptyCard}>
                <Text style={styles.emptyIcon}>⚽</Text>
                <Text style={styles.emptyTitle}>Henüz favori oyuncunuz yok</Text>
                <Text style={styles.emptyDesc}>
                  Oyuncu karşılaştırma, arama veya takım listelerinden istediğiniz futbolcuyu
                  ekleyerek ilk 11, gol ve asist anlık bildirimlerini alabilirsiniz.
                </Text>
                <TouchableOpacity
                  style={styles.browseBtn}
                  onPress={() => navigation.navigate('Players')}
                >
                  <Text style={styles.browseBtnText}>👥 Oyuncuları Keşfet</Text>
                </TouchableOpacity>
              </View>
            ) : (
              favorites.map((item, idx) => {
                const det = item.player_details || {};
                const pid = item.player || det.id || item.id;
                const pName = det.name || item.player_name || 'Futbolcu';
                const pObj = {
                  id: pid,
                  name: pName,
                  team_name: det.team_name || item.team_name || '',
                  position: det.position || item.position || '',
                  image_url: det.image_url || item.image_url || '',
                  market_value: det.market_value || '0',
                };

                const notifyGoals = item.notify_goals !== false;
                const notifyAssists = item.notify_assists !== false;
                const notify11 = item.notify_starting_11 !== false;

                return (
                  <View key={`${pid}-${idx}`} style={styles.itemCard}>
                    <TouchableOpacity
                      style={styles.itemTopRow}
                      activeOpacity={0.8}
                      onPress={() => setDetailPlayer(pObj)}
                    >
                      <Image
                        source={{ uri: pObj.image_url || DEFAULT_PLAYER_IMG }}
                        style={styles.avatar}
                      />
                      <View style={{ flex: 1 }}>
                        <Text style={styles.itemName} numberOfLines={1}>
                          {pName}
                        </Text>
                        <Text style={styles.itemSub} numberOfLines={1}>
                          {pObj.team_name ? `${pObj.team_name} • ` : ''}
                          {pObj.position || 'Süper Lig'}
                        </Text>
                      </View>
                      <TouchableOpacity
                        style={styles.removeBtn}
                        onPress={() => toggleFavorite(pObj)}
                      >
                        <Text style={styles.removeBtnText}>Çıkar</Text>
                      </TouchableOpacity>
                    </TouchableOpacity>

                    {/* BİLDİRİM AYARLARI HAPLARI */}
                    <View style={styles.prefPillsRow}>
                      <TouchableOpacity
                        style={[styles.prefPill, notifyGoals && styles.prefPillActive]}
                        onPress={() => updatePlayerPrefs(pid, { notify_goals: !notifyGoals })}
                      >
                        <Text style={[styles.prefPillText, notifyGoals && styles.prefPillTextActive]}>
                          {notifyGoals ? '⚽ Goller: AÇIK' : '⚽ Gol: Kapalı'}
                        </Text>
                      </TouchableOpacity>

                      <TouchableOpacity
                        style={[styles.prefPill, notifyAssists && styles.prefPillActive]}
                        onPress={() => updatePlayerPrefs(pid, { notify_assists: !notifyAssists })}
                      >
                        <Text style={[styles.prefPillText, notifyAssists && styles.prefPillTextActive]}>
                          {notifyAssists ? '🎯 Asist: AÇIK' : '🎯 Asist: Kapalı'}
                        </Text>
                      </TouchableOpacity>

                      <TouchableOpacity
                        style={[styles.prefPill, notify11 && styles.prefPillActive]}
                        onPress={() => updatePlayerPrefs(pid, { notify_starting_11: !notify11 })}
                      >
                        <Text style={[styles.prefPillText, notify11 && styles.prefPillTextActive]}>
                          {notify11 ? '📋 İlk 11: AÇIK' : '📋 İlk 11: Kapalı'}
                        </Text>
                      </TouchableOpacity>
                    </View>
                  </View>
                );
              })
            )}
          </>
        )}

        {/* ========================================== */}
        {/* TAB 2: KULÜPLERİM                          */}
        {/* ========================================== */}
        {activeTab === 'TEAMS' && (
          <>
            <View style={styles.sectionHeader}>
              <Text style={styles.sectionTitle}>
                Takip Ettiğim Kulüpler ({favoriteTeams.length})
              </Text>
              <TouchableOpacity
                style={styles.addBtn}
                onPress={() => {
                  loadAllTeams();
                  setTeamModalOpen(true);
                }}
              >
                <Text style={styles.addBtnText}>+ Kulüp Ekle</Text>
              </TouchableOpacity>
            </View>

            {favoriteTeams.length === 0 ? (
              <View style={styles.emptyCard}>
                <Text style={styles.emptyIcon}>🛡️</Text>
                <Text style={styles.emptyTitle}>Henüz favori takımınız yok</Text>
                <Text style={styles.emptyDesc}>
                  Desteklediğiniz kulüpleri ekleyerek maç başlama, canlı gol ve kadro açıklandı
                  bildirimlerini anında cebinize alın.
                </Text>
                <TouchableOpacity
                  style={styles.browseBtn}
                  onPress={() => {
                    loadAllTeams();
                    setTeamModalOpen(true);
                  }}
                >
                  <Text style={styles.browseBtnText}>🛡️ Kulüp Seç ve Ekle</Text>
                </TouchableOpacity>
              </View>
            ) : (
              favoriteTeams.map((item, idx) => {
                const tid = item.team || item.team_id || item.id;
                const tName = item.team_name || item.name || 'Süper Lig Kulübü';
                const tLogo = item.team_logo || item.logo_url || DEFAULT_TEAM_LOGO;

                const notifyGoals = item.notify_goals !== false;
                const notifyMatch = item.notify_match_start !== false;
                const notifyLineups = item.notify_lineups !== false;

                return (
                  <View key={`${tid}-${idx}`} style={styles.itemCard}>
                    <View style={styles.itemTopRow}>
                      <Image source={{ uri: tLogo }} style={styles.teamLogo} />
                      <View style={{ flex: 1 }}>
                        <Text style={styles.itemName} numberOfLines={1}>
                          {tName}
                        </Text>
                        <Text style={styles.itemSub}>Trendyol Süper Lig</Text>
                      </View>
                      <TouchableOpacity
                        style={styles.removeBtn}
                        onPress={() => toggleFavoriteTeam({ id: tid, name: tName })}
                      >
                        <Text style={styles.removeBtnText}>Çıkar</Text>
                      </TouchableOpacity>
                    </View>

                    {/* TAKIM BİLDİRİM HAPLARI */}
                    <View style={styles.prefPillsRow}>
                      <TouchableOpacity
                        style={[styles.prefPill, notifyGoals && styles.prefPillActive]}
                        onPress={() => updateTeamPrefs(tid, { notify_goals: !notifyGoals })}
                      >
                        <Text style={[styles.prefPillText, notifyGoals && styles.prefPillTextActive]}>
                          {notifyGoals ? '⚽ Canlı Goller' : '⚽ Goller Kapalı'}
                        </Text>
                      </TouchableOpacity>

                      <TouchableOpacity
                        style={[styles.prefPill, notifyMatch && styles.prefPillActive]}
                        onPress={() => updateTeamPrefs(tid, { notify_match_start: !notifyMatch })}
                      >
                        <Text style={[styles.prefPillText, notifyMatch && styles.prefPillTextActive]}>
                          {notifyMatch ? '🏁 Maç Başladı/Bitti' : '🏁 Kapalı'}
                        </Text>
                      </TouchableOpacity>

                      <TouchableOpacity
                        style={[styles.prefPill, notifyLineups && styles.prefPillActive]}
                        onPress={() => updateTeamPrefs(tid, { notify_lineups: !notifyLineups })}
                      >
                        <Text style={[styles.prefPillText, notifyLineups && styles.prefPillTextActive]}>
                          {notifyLineups ? '📋 Kadrolar' : '📋 Kadro Kapalı'}
                        </Text>
                      </TouchableOpacity>
                    </View>
                  </View>
                );
              })
            )}
          </>
        )}

        {/* ========================================== */}
        {/* TAB 3: BİLDİRİM KUTUSU (MAÇKOLİK AKIŞI)    */}
        {/* ========================================== */}
        {activeTab === 'INBOX' && (
          <>
            <View style={styles.sectionHeader}>
              <Text style={styles.sectionTitle}>
                Canlı Bildirim Geçmişi ({notifications.length})
              </Text>
              {notifications.length > 0 && (
                <TouchableOpacity onPress={handleMarkAllRead}>
                  <Text style={styles.markReadText}>✓ Tümünü Okundu Say</Text>
                </TouchableOpacity>
              )}
            </View>

            {loadingInbox ? (
              <ActivityIndicator size="small" color={COLORS.primary} style={{ margin: 24 }} />
            ) : notifications.length === 0 ? (
              <View style={styles.emptyCard}>
                <Text style={styles.emptyIcon}>🔔</Text>
                <Text style={styles.emptyTitle}>Bildirim kutunuz temiz</Text>
                <Text style={styles.emptyDesc}>
                  Favori takımlarınız veya oyuncularınız maç oynadıkça canlı goller, asistler ve
                  kadro duyuruları buraya düşecek.
                </Text>
              </View>
            ) : (
              notifications.map((item) => {
                const isGoal = item.notification_type === 'GOAL';
                const isLineup = item.notification_type === 'LINEUP';

                return (
                  <View
                    key={item.id}
                    style={[
                      styles.notifCard,
                      !item.is_read && styles.notifCardUnread,
                      isGoal && styles.notifCardGoal,
                    ]}
                  >
                    <View style={styles.notifTop}>
                      <View
                        style={[
                          styles.notifBadge,
                          isGoal && styles.notifBadgeGoal,
                          isLineup && styles.notifBadgeLineup,
                        ]}
                      >
                        <Text style={styles.notifBadgeText}>
                          {isGoal ? '⚽ GOL' : isLineup ? '📋 İLK 11' : '🔔 BİLDİRİM'}
                        </Text>
                      </View>
                      <Text style={styles.notifTime}>
                        {new Date(item.created_at).toLocaleTimeString('tr-TR', {
                          hour: '2-digit',
                          minute: '2-digit',
                        })}
                      </Text>
                    </View>

                    <Text style={styles.notifTitle}>{item.title}</Text>
                    <Text style={styles.notifBody}>{item.body}</Text>
                  </View>
                );
              })
            )}
          </>
        )}
      </ScrollView>

      {/* KULÜP SEÇME MODALI */}
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
              <Text style={styles.modalTitle}>Favorilere Kulüp Ekle</Text>
              <TouchableOpacity onPress={() => setTeamModalOpen(false)}>
                <Text style={styles.modalClose}>✕</Text>
              </TouchableOpacity>
            </View>

            <TextInput
              style={styles.modalSearch}
              placeholder="Kulüp ara (Galatasaray, Fenerbahçe, Beşiktaş...)"
              placeholderTextColor={COLORS.textDim}
              value={teamSearch}
              onChangeText={setTeamSearch}
            />

            <FlatList
              data={allTeams.filter((t) =>
                t.name.toLowerCase().includes(teamSearch.toLowerCase())
              )}
              keyExtractor={(item) => String(item.id)}
              style={{ maxHeight: 380 }}
              renderItem={({ item }) => {
                const isFav = favoriteTeams.some(
                  (x) => String(x.team || x.id) === String(item.id)
                );
                return (
                  <TouchableOpacity
                    style={[styles.teamPickRow, isFav && styles.teamPickRowActive]}
                    onPress={() => {
                      toggleFavoriteTeam(item);
                      setTeamModalOpen(false);
                    }}
                  >
                    <Image
                      source={{ uri: item.logo_url || DEFAULT_TEAM_LOGO }}
                      style={styles.modalTeamLogo}
                    />
                    <Text style={styles.modalTeamName}>{item.name}</Text>
                    <Text style={[styles.favStatusText, isFav && { color: COLORS.accentRed }]}>
                      {isFav ? '★ Ekli' : '+ Ekle'}
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
        onClose={() => setDetailPlayer(null)}
        onCompare={(p) =>
          navigation.navigate('CompareTab', { initialPlayer1: p.id, ts: Date.now() })
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
  headerTitle: { color: COLORS.white, fontSize: 13, fontWeight: '800', letterSpacing: 0.3 },
  tabsRow: {
    flexDirection: 'row',
    backgroundColor: COLORS.backgroundCard,
    marginHorizontal: 14,
    marginBottom: 10,
    borderRadius: 12,
    padding: 3,
    borderWidth: 1,
    borderColor: COLORS.cardBorder,
    gap: 4,
  },
  tabBtn: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 9,
    borderRadius: 9,
    gap: 6,
  },
  tabBtnActive: {
    backgroundColor: COLORS.primary,
  },
  tabBtnText: {
    color: COLORS.textMuted,
    fontSize: 11,
    fontWeight: '800',
  },
  tabBtnTextActive: {
    color: '#060f14',
    fontWeight: '900',
  },
  tabBadge: {
    backgroundColor: 'rgba(255,255,255,0.12)',
    borderRadius: 999,
    paddingHorizontal: 6,
    paddingVertical: 1,
  },
  tabBadgeRed: {
    backgroundColor: COLORS.accentRed,
  },
  tabBadgeActive: {
    backgroundColor: '#060f14',
  },
  tabBadgeText: {
    color: COLORS.white,
    fontSize: 10,
    fontWeight: '900',
  },
  scrollContent: { padding: 14, paddingBottom: 40 },
  guestHint: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: 'rgba(6,182,212,0.1)',
    borderWidth: 1,
    borderColor: 'rgba(6,182,212,0.3)',
    borderRadius: 12,
    padding: 11,
    marginBottom: 12,
    gap: 8,
  },
  guestHintText: { color: '#bae6fd', fontSize: 11, flex: 1, lineHeight: 16 },
  guestHintLink: { color: COLORS.secondary, fontSize: 11, fontWeight: '800' },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  sectionTitle: { color: COLORS.white, fontSize: 13, fontWeight: '800' },
  addBtn: {
    backgroundColor: 'rgba(52,211,153,0.14)',
    borderWidth: 1,
    borderColor: COLORS.primaryGlow,
    borderRadius: 8,
    paddingHorizontal: 10,
    paddingVertical: 4,
  },
  addBtnText: { color: COLORS.primaryGlow, fontSize: 11, fontWeight: '800' },
  markReadText: { color: COLORS.secondary, fontSize: 11, fontWeight: '700' },
  emptyCard: {
    backgroundColor: COLORS.backgroundCard,
    borderWidth: 1,
    borderColor: COLORS.cardBorder,
    borderRadius: 16,
    padding: 24,
    alignItems: 'center',
    marginTop: 10,
  },
  emptyIcon: { fontSize: 34, marginBottom: 10 },
  emptyTitle: { color: COLORS.white, fontSize: 15, fontWeight: '800', marginBottom: 6 },
  emptyDesc: {
    color: COLORS.textMuted,
    fontSize: 12,
    textAlign: 'center',
    lineHeight: 18,
    marginBottom: 16,
  },
  browseBtn: {
    backgroundColor: COLORS.primary,
    borderRadius: 10,
    paddingHorizontal: 18,
    paddingVertical: 10,
  },
  browseBtnText: { color: '#060f14', fontSize: 12, fontWeight: '900' },
  itemCard: {
    backgroundColor: COLORS.backgroundCard,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: COLORS.cardBorder,
    padding: 12,
    marginBottom: 10,
  },
  itemTopRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  avatar: {
    width: 44,
    height: 44,
    borderRadius: 22,
    borderWidth: 2,
    borderColor: COLORS.avatarRingEmerald,
    backgroundColor: 'rgba(16,185,129,0.08)',
  },
  teamLogo: {
    width: 36,
    height: 36,
    resizeMode: 'contain',
  },
  itemName: { color: COLORS.white, fontSize: 13, fontWeight: '800' },
  itemSub: { color: COLORS.textMuted, fontSize: 11, marginTop: 2 },
  removeBtn: {
    backgroundColor: COLORS.accentRedSoft,
    borderWidth: 1,
    borderColor: COLORS.accentRedBorder,
    borderRadius: 8,
    paddingHorizontal: 10,
    paddingVertical: 5,
  },
  removeBtnText: { color: '#f87171', fontSize: 11, fontWeight: '800' },
  prefPillsRow: {
    flexDirection: 'row',
    gap: 6,
    marginTop: 10,
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: 'rgba(255,255,255,0.05)',
  },
  prefPill: {
    backgroundColor: 'rgba(255,255,255,0.04)',
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.1)',
    borderRadius: 8,
    paddingHorizontal: 8,
    paddingVertical: 4,
  },
  prefPillActive: {
    backgroundColor: 'rgba(16,185,129,0.15)',
    borderColor: COLORS.primaryGlow,
  },
  prefPillText: {
    color: COLORS.textDim,
    fontSize: 10,
    fontWeight: '700',
  },
  prefPillTextActive: {
    color: COLORS.primaryGlow,
    fontWeight: '800',
  },
  simulatorCard: {
    backgroundColor: '#0a1622',
    borderWidth: 1.5,
    borderColor: COLORS.primaryGlow,
    borderRadius: 16,
    padding: 14,
    marginBottom: 14,
  },
  simHead: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 6,
  },
  simTitle: { color: COLORS.primaryGlow, fontSize: 13, fontWeight: '900' },
  simDesc: { color: COLORS.textSoft, fontSize: 11, lineHeight: 16, marginBottom: 12 },
  simBtnsRow: { flexDirection: 'row', gap: 8 },
  simActionBtn: {
    flex: 1,
    borderRadius: 10,
    paddingVertical: 10,
    alignItems: 'center',
    justifyContent: 'center',
  },
  simGoalBtn: {
    backgroundColor: COLORS.primary,
  },
  simGoalBtnText: { color: '#060f14', fontSize: 11, fontWeight: '900' },
  simLineupBtn: {
    backgroundColor: 'rgba(6,182,212,0.16)',
    borderWidth: 1,
    borderColor: 'rgba(6,182,212,0.4)',
  },
  simLineupBtnText: { color: COLORS.secondary, fontSize: 11, fontWeight: '800' },
  notifCard: {
    backgroundColor: COLORS.backgroundCard,
    borderWidth: 1,
    borderColor: COLORS.cardBorder,
    borderRadius: 14,
    padding: 12,
    marginBottom: 8,
  },
  notifCardUnread: {
    borderColor: COLORS.primaryGlow,
    backgroundColor: '#081720',
  },
  notifCardGoal: {
    borderLeftWidth: 3,
    borderLeftColor: COLORS.primaryGlow,
  },
  notifTop: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 6,
  },
  notifBadge: {
    backgroundColor: COLORS.primarySoft,
    borderRadius: 6,
    paddingHorizontal: 6,
    paddingVertical: 2,
  },
  notifBadgeGoal: {
    backgroundColor: 'rgba(16,185,129,0.22)',
  },
  notifBadgeLineup: {
    backgroundColor: 'rgba(6,182,212,0.22)',
  },
  notifBadgeText: {
    color: COLORS.primaryGlow,
    fontSize: 9,
    fontWeight: '900',
  },
  notifTime: { color: COLORS.textDim, fontSize: 10, fontWeight: '600' },
  notifTitle: { color: COLORS.white, fontSize: 13, fontWeight: '800' },
  notifBody: { color: COLORS.textSoft, fontSize: 11, marginTop: 3, lineHeight: 16 },
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
  teamPickRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 10,
    paddingHorizontal: 8,
    borderRadius: 10,
    gap: 10,
  },
  teamPickRowActive: {
    backgroundColor: 'rgba(52,211,153,0.12)',
  },
  modalTeamLogo: { width: 26, height: 26, resizeMode: 'contain' },
  modalTeamName: { color: COLORS.white, fontSize: 13, fontWeight: '700', flex: 1 },
  favStatusText: { color: COLORS.primaryGlow, fontSize: 11, fontWeight: '800' },
});
