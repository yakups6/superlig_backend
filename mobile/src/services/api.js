import axios from 'axios';
import Constants from 'expo-constants';
import { Platform } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';

export const STORAGE_KEYS = {
  ACCESS: 'sl_access_token',
  REFRESH: 'sl_refresh_token',
  USER: 'sl_auth_user',
  CUSTOM_URL: 'sl_custom_api_url',
  GUEST_FAVS: 'scout_notes',
  GUEST_FAV_TEAMS: 'guest_fav_teams',
  LAST_READ_NOTIF_ID: 'sl_last_read_notif',
};

export const FALLBACK_PUBLIC_API_URL = 'https://superlig-backend.onrender.com/api';

function detectDefaultBaseUrl() {
  if (Constants.expoConfig?.extra?.defaultApiUrl) {
    return Constants.expoConfig.extra.defaultApiUrl;
  }

  const hostUri =
    Constants.expoConfig?.hostUri ||
    Constants.manifest2?.extra?.expoGo?.debuggerHost ||
    Constants.manifest?.debuggerHost ||
    '';

  if (hostUri) {
    const host = hostUri.split(':')[0];
    if (host && host !== 'localhost' && host !== '127.0.0.1') {
      return `http://${host}:8000/api`;
    }
  }

  return FALLBACK_PUBLIC_API_URL;
}

let inMemoryAccessToken = '';
let inMemoryRefreshToken = '';
let activeBaseUrl = detectDefaultBaseUrl();
let unauthorizedHandler = null;
let refreshPromise = null;
let storageInitPromise = null;

export function ensureStorageInitialized() {
  if (!storageInitPromise) {
    storageInitPromise = initApiClientFromStorage();
  }
  return storageInitPromise;
}

// Start restoring storage as soon as JS bundle is evaluated
ensureStorageInitialized();

const apiClient = axios.create({
  baseURL: activeBaseUrl,
  timeout: 12000,
  headers: {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  },
});

export function setUnauthorizedHandler(fn) {
  unauthorizedHandler = fn;
}

export function getActiveApiUrl() {
  return activeBaseUrl;
}

export async function setCustomApiUrl(url) {
  const cleaned = (url || '').trim().replace(/\/+$/, '');
  if (!cleaned) {
    await AsyncStorage.removeItem(STORAGE_KEYS.CUSTOM_URL);
    activeBaseUrl = detectDefaultBaseUrl();
  } else {
    const normalized = cleaned.endsWith('/api') ? cleaned : `${cleaned}/api`;
    await AsyncStorage.setItem(STORAGE_KEYS.CUSTOM_URL, normalized);
    activeBaseUrl = normalized;
  }
  apiClient.defaults.baseURL = activeBaseUrl;
  storageInitPromise = Promise.resolve({
    access: inMemoryAccessToken,
    refresh: inMemoryRefreshToken,
    baseUrl: activeBaseUrl,
  });
  return activeBaseUrl;
}

export async function initApiClientFromStorage() {
  try {
    const [acc, ref, customUrl] = await Promise.all([
      AsyncStorage.getItem(STORAGE_KEYS.ACCESS),
      AsyncStorage.getItem(STORAGE_KEYS.REFRESH),
      AsyncStorage.getItem(STORAGE_KEYS.CUSTOM_URL),
    ]);
    inMemoryAccessToken = acc || '';
    inMemoryRefreshToken = ref || '';
    if (customUrl && (customUrl.includes('trycloudflare.com') || customUrl.includes('loca.lt') || customUrl.includes('ngrok'))) {
      // Geçici tünel bağlantıları oturum kapandığında geçersiz kalır; kalıcı Render bulut adresine dön
      try {
        await AsyncStorage.removeItem(STORAGE_KEYS.CUSTOM_URL);
      } catch (rmErr) {}
      activeBaseUrl = detectDefaultBaseUrl();
    } else {
      activeBaseUrl = customUrl || detectDefaultBaseUrl();
    }
    apiClient.defaults.baseURL = activeBaseUrl;
    return {
      access: inMemoryAccessToken,
      refresh: inMemoryRefreshToken,
      baseUrl: activeBaseUrl,
    };
  } catch (e) {
    return {
      access: '',
      refresh: '',
      baseUrl: activeBaseUrl,
    };
  }
}

export function setAuthTokensInMemory(access, refresh) {
  inMemoryAccessToken = access || '';
  if (refresh !== undefined) {
    inMemoryRefreshToken = refresh || '';
  }
}

apiClient.interceptors.request.use(async (config) => {
  await ensureStorageInitialized();
  config.baseURL = activeBaseUrl;
  if (inMemoryAccessToken) {
    config.headers = config.headers || {};
    config.headers.Authorization = `Bearer ${inMemoryAccessToken}`;
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalReq = error?.config;
    const statusCode = error?.response?.status;
    const urlStr = String(originalReq?.url || '');

    if (
      statusCode === 401 &&
      originalReq &&
      !originalReq._retry &&
      inMemoryRefreshToken &&
      !urlStr.includes('/auth/login/') &&
      !urlStr.includes('/auth/refresh/')
    ) {
      originalReq._retry = true;
      try {
        if (!refreshPromise) {
          refreshPromise = axios
            .post(`${activeBaseUrl}/auth/refresh/`, {
              refresh: inMemoryRefreshToken,
            })
            .finally(() => {
              refreshPromise = null;
            });
        }
        const refRes = await refreshPromise;
        const newAccess = refRes?.data?.access;
        const newRefresh = refRes?.data?.refresh;
        if (newAccess) {
          inMemoryAccessToken = newAccess;
          await AsyncStorage.setItem(STORAGE_KEYS.ACCESS, newAccess);
          if (newRefresh) {
            inMemoryRefreshToken = newRefresh;
            await AsyncStorage.setItem(STORAGE_KEYS.REFRESH, newRefresh);
          }
          originalReq.headers = originalReq.headers || {};
          originalReq.headers.Authorization = `Bearer ${newAccess}`;
          return apiClient(originalReq);
        }
      } catch (refErr) {
        inMemoryAccessToken = '';
        inMemoryRefreshToken = '';
        await AsyncStorage.multiRemove([
          STORAGE_KEYS.ACCESS,
          STORAGE_KEYS.REFRESH,
          STORAGE_KEYS.USER,
        ]);
        if (typeof unauthorizedHandler === 'function') {
          unauthorizedHandler();
        }
      }
    }
    return Promise.reject(error);
  }
);

export const superligApi = {
  // 1. Auth
  login: async (username, password) => {
    const res = await apiClient.post('/auth/login/', { username, password });
    return res.data;
  },
  register: async (payload) => {
    const res = await apiClient.post('/auth/register/', payload);
    return res.data;
  },
  getProfile: async () => {
    const res = await apiClient.get('/auth/me/');
    return res.data;
  },
  updateProfile: async (payload) => {
    const res = await apiClient.put('/auth/me/', payload);
    return res.data;
  },
  changePassword: async (old_password, new_password) => {
    const res = await apiClient.post('/auth/change-password/', {
      old_password,
      new_password,
    });
    return res.data;
  },

  // 2. Home & Seasons
  getHomeSummary: async () => {
    const res = await apiClient.get('/home-summary/');
    return res.data;
  },
  getSeasons: async () => {
    const res = await apiClient.get('/seasons/');
    return res.data;
  },
  getCurrentSeason: async () => {
    const res = await apiClient.get('/seasons/current/');
    return res.data;
  },

  // 3. Fixtures & Live Scores (Maçkolik)
  getLiveSummary: async (params = {}) => {
    const res = await apiClient.get('/fixtures/live_summary/', {
      params: { ...params, _t: Date.now() },
      headers: { 'Cache-Control': 'no-cache' },
    });
    return res.data;
  },
  getFixtures: async (params = {}) => {
    const res = await apiClient.get('/fixtures/', {
      params: { ...params, _t: Date.now() },
    });
    return res.data;
  },

  // 4. Teams
  getTeams: async (params = {}) => {
    const res = await apiClient.get('/teams/', { params });
    return res.data;
  },
  getTeamDetail: async (teamId, season) => {
    const params = season ? { season } : {};
    const res = await apiClient.get(`/teams/${teamId}/`, { params });
    return res.data;
  },

  // 5. Players & Legends
  getPlayers: async (params = {}) => {
    const res = await apiClient.get('/players/', { params });
    return res.data;
  },
  getPlayerDetail: async (playerId) => {
    const res = await apiClient.get(`/players/${playerId}/`);
    return res.data;
  },
  getLegends: async (params = {}) => {
    const res = await apiClient.get('/legends/', { params });
    return res.data;
  },

  // 6. Transfers
  getTransfers: async (params = {}) => {
    const res = await apiClient.get('/transfers/', { params });
    return res.data;
  },

  // 7. Compare
  comparePlayers: async (player1, player2, season) => {
    const params = { player1, player2 };
    if (season) params.season = season;
    const res = await apiClient.get('/compare/', { params });
    return res.data;
  },

  // 8. Standings & Leaders
  getStandings: async (params = {}) => {
    const res = await apiClient.get('/standings/', {
      params: { ...params, _t: Date.now() },
    });
    return res.data;
  },
  getLeaderboards: async (params = {}) => {
    const res = await apiClient.get('/leaderboards/', { params });
    return res.data;
  },

  // 9. Scout & Favoriler
  getScoutNotes: async () => {
    const res = await apiClient.get('/scout-notes/');
    return res.data;
  },
  toggleScoutNote: async (payload) => {
    const res = await apiClient.post('/scout-notes/toggle/', payload);
    return res.data;
  },
  updatePlayerPreferences: async (playerId, prefs) => {
    const res = await apiClient.patch('/scout-notes/preferences/', { player: playerId, ...prefs });
    return res.data;
  },

  // 10. Favori Takımlar
  getFavoriteTeams: async () => {
    const res = await apiClient.get('/favorite-teams/');
    return res.data;
  },
  toggleFavoriteTeam: async (teamId, prefs = {}) => {
    const res = await apiClient.post('/favorite-teams/toggle/', { team: teamId, ...prefs });
    return res.data;
  },
  updateTeamPreferences: async (teamId, prefs) => {
    const res = await apiClient.patch('/favorite-teams/preferences/', { team: teamId, ...prefs });
    return res.data;
  },

  // 11. Bildirimler & Push Servisi
  registerDeviceToken: async (expoPushToken, platform, deviceName) => {
    const res = await apiClient.post('/notifications/register-device/', {
      expo_push_token: expoPushToken,
      platform,
      device_name: deviceName,
    });
    return res.data;
  },
  getNotificationInbox: async () => {
    const res = await apiClient.get('/notifications/inbox/');
    return res.data;
  },
  getUnreadNotificationCount: async () => {
    const res = await apiClient.get('/notifications/inbox/unread_count/');
    return res.data;
  },
  markNotificationRead: async (id) => {
    const res = await apiClient.post(`/notifications/inbox/${id}/mark_read/`);
    return res.data;
  },
  markAllNotificationsRead: async () => {
    const res = await apiClient.post('/notifications/inbox/mark_all_read/');
    return res.data;
  },
  sendTestNotification: async (payload = {}) => {
    const res = await apiClient.post('/notifications/test-event/', payload);
    return res.data;
  },

  // 10. Sync
  syncTransfers: async () => {
    const res = await apiClient.post('/sync/transfers/');
    return res.data;
  },
  syncFixtures: async () => {
    const res = await apiClient.post('/sync/fixtures/');
    return res.data;
  },
  syncAll: async () => {
    const res = await apiClient.post('/sync/all/');
    return res.data;
  },
};

export default apiClient;
