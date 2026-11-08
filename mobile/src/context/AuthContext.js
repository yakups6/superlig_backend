import React, { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import {
  superligApi,
  STORAGE_KEYS,
  initApiClientFromStorage,
  setAuthTokensInMemory,
  setUnauthorizedHandler,
  getActiveApiUrl,
  setCustomApiUrl,
} from '../services/api';
import {
  registerForPushNotificationsAsync,
  showLocalMatchNotification,
} from '../services/notifications';
import NotificationBanner from '../components/NotificationBanner';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [accessToken, setAccessToken] = useState('');
  const [authReady, setAuthReady] = useState(false);
  const [favorites, setFavorites] = useState([]);
  const [favoriteTeams, setFavoriteTeams] = useState([]);
  const [seasons, setSeasons] = useState([]);
  const [activeSeason, setActiveSeason] = useState(null);
  const [apiBaseUrl, setApiBaseUrl] = useState(getActiveApiUrl());
  const [unreadCount, setUnreadCount] = useState(0);
  const [activeBanner, setActiveBanner] = useState(null);

  const lastSeenNotifIdRef = useRef(0);
  const pollerTimerRef = useRef(null);

  const isLoggedIn = Boolean(user && accessToken);

  const loadSeasons = useCallback(async () => {
    try {
      const list = await superligApi.getSeasons();
      const sorted = (Array.isArray(list) ? list : []).slice().sort((a, b) => {
        if (b.start_year !== a.start_year) return b.start_year - a.start_year;
        return String(b.name).localeCompare(String(a.name));
      });
      setSeasons(sorted);
      const cur =
        sorted.find((s) => s.is_current) ||
        sorted[0] || { name: '2026/2027', short_code: '26/27', is_current: true };
      setActiveSeason(cur);
      return sorted;
    } catch (e) {
      return [];
    }
  }, []);

  // --- OYUNCU FAVORİLERİ (SCOUT) ---
  const refreshFavorites = useCallback(async (loggedOverride) => {
    const logged = loggedOverride !== undefined ? loggedOverride : Boolean(user && accessToken);
    if (logged) {
      try {
        const list = await superligApi.getScoutNotes();
        setFavorites(Array.isArray(list) ? list : []);
        return list || [];
      } catch (e) {
        return [];
      }
    } else {
      try {
        const raw = await AsyncStorage.getItem(STORAGE_KEYS.GUEST_FAVS);
        const parsed = raw ? JSON.parse(raw) : [];
        const arr = Array.isArray(parsed) ? parsed : [];
        setFavorites(arr);
        return arr;
      } catch (e) {
        setFavorites([]);
        return [];
      }
    }
  }, [user, accessToken]);

  // --- TAKIM FAVORİLERİ ---
  const refreshFavoriteTeams = useCallback(async (loggedOverride) => {
    const logged = loggedOverride !== undefined ? loggedOverride : Boolean(user && accessToken);
    if (logged) {
      try {
        const list = await superligApi.getFavoriteTeams();
        setFavoriteTeams(Array.isArray(list) ? list : []);
        return list || [];
      } catch (e) {
        return [];
      }
    } else {
      try {
        const raw = await AsyncStorage.getItem(STORAGE_KEYS.GUEST_FAV_TEAMS);
        const parsed = raw ? JSON.parse(raw) : [];
        const arr = Array.isArray(parsed) ? parsed : [];
        setFavoriteTeams(arr);
        return arr;
      } catch (e) {
        setFavoriteTeams([]);
        return [];
      }
    }
  }, [user, accessToken]);

  const syncGuestFavoritesToAccount = useCallback(async () => {
    try {
      // Oyuncuları eşitle
      const rawPlayers = await AsyncStorage.getItem(STORAGE_KEYS.GUEST_FAVS);
      const localPlayers = rawPlayers ? JSON.parse(rawPlayers) : [];
      if (Array.isArray(localPlayers) && localPlayers.length > 0) {
        for (const item of localPlayers) {
          const pid = item.player || item.id;
          if (pid) {
            try {
              await superligApi.toggleScoutNote({
                player: pid,
                note: item.note || item.notes || 'Favori oyuncu',
                rating: Math.round(Number(item.rating || item.potential_rating || 9)),
              });
            } catch (e) {}
          }
        }
        await AsyncStorage.removeItem(STORAGE_KEYS.GUEST_FAVS);
      }

      // Takımları eşitle
      const rawTeams = await AsyncStorage.getItem(STORAGE_KEYS.GUEST_FAV_TEAMS);
      const localTeams = rawTeams ? JSON.parse(rawTeams) : [];
      if (Array.isArray(localTeams) && localTeams.length > 0) {
        for (const item of localTeams) {
          const tid = item.team || item.id;
          if (tid) {
            try {
              await superligApi.toggleFavoriteTeam(tid, {
                notify_match_start: item.notify_match_start ?? true,
                notify_goals: item.notify_goals ?? true,
                notify_cards: item.notify_cards ?? false,
                notify_lineups: item.notify_lineups ?? true,
              });
            } catch (e) {}
          }
        }
        await AsyncStorage.removeItem(STORAGE_KEYS.GUEST_FAV_TEAMS);
      }
    } catch (e) {}
  }, []);

  const clearSession = useCallback(async () => {
    setAuthTokensInMemory('', '');
    setAccessToken('');
    setUser(null);
    await AsyncStorage.multiRemove([
      STORAGE_KEYS.ACCESS,
      STORAGE_KEYS.REFRESH,
      STORAGE_KEYS.USER,
    ]);
    await refreshFavorites(false);
    await refreshFavoriteTeams(false);
  }, [refreshFavorites, refreshFavoriteTeams]);

  // Bildirim sayacını güncelle
  const refreshUnreadCount = useCallback(async () => {
    try {
      const res = await superligApi.getUnreadNotificationCount();
      setUnreadCount(res?.unread_count || 0);
    } catch (e) {}
  }, []);

  // --- CANLI BİLDİRİM DİNLEYİCİSİ (POLLER) ---
  const checkLiveNotifications = useCallback(async () => {
    try {
      const list = await superligApi.getNotificationInbox();
      if (!Array.isArray(list) || list.length === 0) return;

      const newest = list[0];
      const newestId = Number(newest.id) || 0;

      // İlk çalışmada hafızaya al
      if (!lastSeenNotifIdRef.current) {
        const saved = await AsyncStorage.getItem(STORAGE_KEYS.LAST_READ_NOTIF_ID);
        lastSeenNotifIdRef.current = Number(saved) || newestId;
        return;
      }

      // Yeni bir bildirim düştüyse (Maçkolik canlı gol vb.)
      if (newestId > lastSeenNotifIdRef.current) {
        lastSeenNotifIdRef.current = newestId;
        await AsyncStorage.setItem(STORAGE_KEYS.LAST_READ_NOTIF_ID, String(newestId));

        // 1. Ekranın üstünden Maçkolik neon banner'ı fırlat
        setActiveBanner(newest);

        // 2. Telefonun işletim sistemine yerel bildirim + titreşim bas
        await showLocalMatchNotification(newest.title, newest.body, newest.data_payload);

        // 3. Bildirim sayısını tazele
        setUnreadCount((c) => c + 1);
      }
    } catch (e) {
      // Sessiz hata (ağ hatasında log basma)
    }
  }, []);

  // Başlangıç yüklemeleri
  useEffect(() => {
    let isMounted = true;
    async function init() {
      try {
        const creds = await initApiClientFromStorage();
        if (creds.baseUrl) setApiBaseUrl(creds.baseUrl);

        setUnauthorizedHandler(async () => {
          await clearSession();
        });

        if (creds.access) {
          setAccessToken(creds.access);
          const cachedUser = await AsyncStorage.getItem(STORAGE_KEYS.USER);
          if (cachedUser) {
            try {
              setUser(JSON.parse(cachedUser));
            } catch (e) {}
          }
          try {
            const me = await superligApi.getMe();
            setUser(me);
            await AsyncStorage.setItem(STORAGE_KEYS.USER, JSON.stringify(me));
            await refreshFavorites(true);
            await refreshFavoriteTeams(true);
          } catch (err) {
            if (err?.response?.status === 401) {
              await clearSession();
            } else {
              await refreshFavorites(true);
              await refreshFavoriteTeams(true);
            }
          }
        } else {
          await refreshFavorites(false);
          await refreshFavoriteTeams(false);
        }
      } catch (e) {
        await refreshFavorites(false);
        await refreshFavoriteTeams(false);
      } finally {
        if (isMounted) setAuthReady(true);
      }

      await loadSeasons();
      await refreshUnreadCount();

      // Push bildirim token'ını al ve sunucuya bildir
      try {
        await registerForPushNotificationsAsync();
      } catch (e) {
        console.log('[AuthContext] Push token init error:', e);
      }
    }

    init();

    // 25 saniyede bir yeni canlı gol/maç bildirimi kontrolü
    pollerTimerRef.current = setInterval(() => {
      checkLiveNotifications();
    }, 25000);

    return () => {
      isMounted = false;
      if (pollerTimerRef.current) clearInterval(pollerTimerRef.current);
    };
  }, []);

  const saveSession = useCallback(async (userData, tokens) => {
    setUser(userData);
    setAccessToken(tokens.access);
    setAuthTokensInMemory(tokens.access, tokens.refresh);
    await AsyncStorage.setItem(STORAGE_KEYS.ACCESS, tokens.access);
    await AsyncStorage.setItem(STORAGE_KEYS.REFRESH, tokens.refresh);
    await AsyncStorage.setItem(STORAGE_KEYS.USER, JSON.stringify(userData));
    // Kullanıcı değiştiğinde cihaz token'ını yeniden bağla
    try {
      await registerForPushNotificationsAsync();
    } catch (_) {}
  }, []);

  const signIn = useCallback(
    async (username, password) => {
      const data = await superligApi.login(username, password);
      if (data?.tokens?.access) {
        await saveSession(data.user, data.tokens);
        await syncGuestFavoritesToAccount();
        await refreshFavorites(true);
        await refreshFavoriteTeams(true);
        await refreshUnreadCount();
      }
      return data;
    },
    [saveSession, syncGuestFavoritesToAccount, refreshFavorites, refreshFavoriteTeams, refreshUnreadCount]
  );

  const signUp = useCallback(
    async (payload) => {
      const data = await superligApi.register(payload);
      if (data?.tokens?.access) {
        await saveSession(data.user, data.tokens);
        await syncGuestFavoritesToAccount();
        await refreshFavorites(true);
        await refreshFavoriteTeams(true);
        await refreshUnreadCount();
      }
      return data;
    },
    [saveSession, syncGuestFavoritesToAccount, refreshFavorites, refreshFavoriteTeams, refreshUnreadCount]
  );

  const updateUserLocal = useCallback(
    async (userData) => {
      setUser(userData);
      await AsyncStorage.setItem(STORAGE_KEYS.USER, JSON.stringify(userData));
    },
    []
  );

  const signOut = useCallback(async () => {
    await clearSession();
  }, [clearSession]);

  // --- OYUNCU METOTLARI ---
  const isFavorite = useCallback(
    (playerId) => {
      if (!playerId) return false;
      return (favorites || []).some(
        (item) =>
          String(item.player) === String(playerId) ||
          String(item.id) === String(playerId) ||
          String(item.player_details?.id) === String(playerId)
      );
    },
    [favorites]
  );

  const toggleFavorite = useCallback(
    async (playerObj) => {
      if (!playerObj?.id) return null;
      const pid = playerObj.id;
      const pName = playerObj.name || 'Oyuncu';

      if (isLoggedIn) {
        const res = await superligApi.toggleScoutNote({
          player: pid,
          note: `${pName} favorilere eklendi.`,
          rating: 9,
        });
        await refreshFavorites(true);
        return res;
      }

      const raw = await AsyncStorage.getItem(STORAGE_KEYS.GUEST_FAVS);
      const local = raw ? JSON.parse(raw) : [];
      const list = Array.isArray(local) ? local : [];
      const idx = list.findIndex(
        (x) => String(x.player) === String(pid) || String(x.id) === String(pid)
      );
      if (idx !== -1) {
        list.splice(idx, 1);
        await AsyncStorage.setItem(STORAGE_KEYS.GUEST_FAVS, JSON.stringify(list));
        setFavorites(list);
        return { action: 'removed', message: `${pName} favorilerinizden çıkarıldı.` };
      }

      const entry = {
        id: pid,
        player: pid,
        note: `${pName} favorilere eklendi.`,
        rating: Math.round(Number(playerObj.rating || playerObj.season_rating || 9)),
        notify_starting_11: true,
        notify_goals: true,
        notify_assists: true,
        notify_cards: false,
        player_details: {
          id: pid,
          name: pName,
          team_name: playerObj.team_name || '',
          team_short_name: playerObj.team_short_name || '',
          position: playerObj.position || '',
          image_url: playerObj.image_url || '',
          market_value: playerObj.market_value || '0',
          nationality: playerObj.nationality || '',
          age: playerObj.age || null,
          jersey_number: playerObj.jersey_number || null,
        },
      };
      const next = [entry, ...list];
      await AsyncStorage.setItem(STORAGE_KEYS.GUEST_FAVS, JSON.stringify(next));
      setFavorites(next);
      return { action: 'added', message: `${pName} favorilerinize eklendi!` };
    },
    [isLoggedIn, refreshFavorites]
  );

  const updatePlayerPrefs = useCallback(
    async (playerId, prefs) => {
      if (isLoggedIn) {
        try {
          await superligApi.updatePlayerPreferences(playerId, prefs);
          await refreshFavorites(true);
        } catch (e) {}
      } else {
        const raw = await AsyncStorage.getItem(STORAGE_KEYS.GUEST_FAVS);
        const list = raw ? JSON.parse(raw) : [];
        const next = list.map((item) => {
          if (String(item.player || item.id) === String(playerId)) {
            return { ...item, ...prefs };
          }
          return item;
        });
        await AsyncStorage.setItem(STORAGE_KEYS.GUEST_FAVS, JSON.stringify(next));
        setFavorites(next);
      }
    },
    [isLoggedIn, refreshFavorites]
  );

  // --- TAKIM METOTLARI ---
  const isTeamFavorite = useCallback(
    (teamId) => {
      if (!teamId) return false;
      return (favoriteTeams || []).some(
        (item) =>
          String(item.team) === String(teamId) ||
          String(item.id) === String(teamId) ||
          String(item.team_id) === String(teamId)
      );
    },
    [favoriteTeams]
  );

  const toggleFavoriteTeam = useCallback(
    async (teamObj, prefs = {}) => {
      if (!teamObj?.id) return null;
      const tid = teamObj.id;
      const tName = teamObj.name || 'Takım';

      if (isLoggedIn) {
        const res = await superligApi.toggleFavoriteTeam(tid, prefs);
        await refreshFavoriteTeams(true);
        return res;
      }

      const raw = await AsyncStorage.getItem(STORAGE_KEYS.GUEST_FAV_TEAMS);
      const local = raw ? JSON.parse(raw) : [];
      const list = Array.isArray(local) ? local : [];
      const idx = list.findIndex(
        (x) => String(x.team) === String(tid) || String(x.id) === String(tid)
      );
      if (idx !== -1) {
        list.splice(idx, 1);
        await AsyncStorage.setItem(STORAGE_KEYS.GUEST_FAV_TEAMS, JSON.stringify(list));
        setFavoriteTeams(list);
        return { action: 'removed', message: `${tName} favori takımlarınızdan çıkarıldı.` };
      }

      const entry = {
        id: tid,
        team: tid,
        team_id: tid,
        team_name: tName,
        team_short_name: teamObj.short_name || '',
        team_logo: teamObj.logo_url || '',
        notify_match_start: prefs.notify_match_start ?? true,
        notify_goals: prefs.notify_goals ?? true,
        notify_cards: prefs.notify_cards ?? false,
        notify_lineups: prefs.notify_lineups ?? true,
      };
      const next = [entry, ...list];
      await AsyncStorage.setItem(STORAGE_KEYS.GUEST_FAV_TEAMS, JSON.stringify(next));
      setFavoriteTeams(next);
      return { action: 'added', message: `${tName} favori takımlarınıza eklendi!` };
    },
    [isLoggedIn, refreshFavoriteTeams]
  );

  const updateTeamPrefs = useCallback(
    async (teamId, prefs) => {
      if (isLoggedIn) {
        try {
          await superligApi.updateTeamPreferences(teamId, prefs);
          await refreshFavoriteTeams(true);
        } catch (e) {}
      } else {
        const raw = await AsyncStorage.getItem(STORAGE_KEYS.GUEST_FAV_TEAMS);
        const list = raw ? JSON.parse(raw) : [];
        const next = list.map((item) => {
          if (String(item.team || item.id) === String(teamId)) {
            return { ...item, ...prefs };
          }
          return item;
        });
        await AsyncStorage.setItem(STORAGE_KEYS.GUEST_FAV_TEAMS, JSON.stringify(next));
        setFavoriteTeams(next);
      }
    },
    [isLoggedIn, refreshFavoriteTeams]
  );

  const changeServerUrl = useCallback(
    async (url) => {
      const updated = await setCustomApiUrl(url);
      setApiBaseUrl(updated);
      await loadSeasons();
      return updated;
    },
    [loadSeasons]
  );

  return (
    <AuthContext.Provider
      value={{
        user,
        accessToken,
        isLoggedIn,
        authReady,
        favorites,
        favoriteTeams,
        seasons,
        activeSeason,
        apiBaseUrl,
        unreadCount,
        signIn,
        signUp,
        signOut,
        updateUserLocal,
        refreshFavorites,
        refreshFavoriteTeams,
        refreshUnreadCount,
        isFavorite,
        toggleFavorite,
        updatePlayerPrefs,
        isTeamFavorite,
        toggleFavoriteTeam,
        updateTeamPrefs,
        loadSeasons,
        changeServerUrl,
        triggerTestNotification: async (payload) => {
          const res = await superligApi.sendTestNotification(payload);
          await checkLiveNotifications();
          return res;
        },
      }}
    >
      {children}
      <NotificationBanner
        notification={activeBanner}
        onDismiss={() => setActiveBanner(null)}
        onPress={(notif) => {
          console.log('[NotificationBanner] Dokunuldu:', notif);
        }}
      />
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
