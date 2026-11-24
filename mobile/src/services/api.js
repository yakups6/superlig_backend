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
  timeout: 25000,
  headers: {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  },
});

const CACHE_STORAGE_PREFIX = 'sl_cache_v1_';
const memoryCache = new Map();
const inFlightRequests = new Map();

function buildCacheKey(url, params = {}) {
  const cleanParams = {};
  Object.keys(params || {})
    .sort()
    .forEach((k) => {
      if (k !== '_t' && params[k] !== undefined && params[k] !== null && params[k] !== '') {
        cleanParams[k] = params[k];
      }
    });
  return `${activeBaseUrl}|${url}|${JSON.stringify(cleanParams)}`;
}

export async function clearApiCache() {
  memoryCache.clear();
  try {
    const keys = await AsyncStorage.getAllKeys();
    const cacheKeys = keys.filter((k) => k.startsWith(CACHE_STORAGE_PREFIX));
    if (cacheKeys.length > 0) {
      await AsyncStorage.multiRemove(cacheKeys);
    }
  } catch (e) {}
}

async function cachedGet(url, params = {}, options = {}) {
  const { ttlMs = 120000, persist = false, skipCache = false, headers } = options;
  const key = buildCacheKey(url, params);
  const now = Date.now();

  if (!skipCache) {
    const mem = memoryCache.get(key);
    if (mem && now - mem.ts < ttlMs) {
      return mem.data;
    }
    if (!mem && persist) {
      try {
        const raw = await AsyncStorage.getItem(CACHE_STORAGE_PREFIX + key);
        if (raw) {
          const parsed = JSON.parse(raw);
          if (parsed && typeof parsed.ts === 'number') {
            memoryCache.set(key, parsed);
            if (now - parsed.ts < Math.max(ttlMs, 1800000)) {
              if (now - parsed.ts >= ttlMs && !inFlightRequests.has(key)) {
                const bgReq = apiClient
                  .get(url, { params, headers })
                  .then(async (res) => {
                    const entry = { data: res.data, ts: Date.now() };
                    memoryCache.set(key, entry);
                    try {
                      await AsyncStorage.setItem(CACHE_STORAGE_PREFIX + key, JSON.stringify(entry));
                    } catch (e) {}
                    return res.data;
                  })
                  .catch(() => parsed.data)
                  .finally(() => inFlightRequests.delete(key));
                inFlightRequests.set(key, bgReq);
              }
              return parsed.data;
            }
          }
        }
      } catch (e) {}
    }
  }

  if (!skipCache && inFlightRequests.has(key)) {
    return inFlightRequests.get(key);
  }

  const reqPromise = apiClient
    .get(url, { params, headers })
    .then(async (res) => {
      const entry = { data: res.data, ts: Date.now() };
      memoryCache.set(key, entry);
      if (persist) {
        try {
          await AsyncStorage.setItem(CACHE_STORAGE_PREFIX + key, JSON.stringify(entry));
        } catch (e) {}
      }
      return res.data;
    })
    .finally(() => {
      inFlightRequests.delete(key);
    });

  if (!skipCache) {
    inFlightRequests.set(key, reqPromise);
  }
  return reqPromise;
}

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
  getHomeSummary: async (forceRefresh = false) => {
    return cachedGet('/home-summary/', {}, {
      ttlMs: 30000,
      persist: true,
      skipCache: forceRefresh,
    });
  },
  getSeasons: async (forceRefresh = false) => {
    return cachedGet('/seasons/', {}, {
      ttlMs: 600000,
      persist: true,
      skipCache: forceRefresh,
    });
  },
  getCurrentSeason: async (forceRefresh = false) => {
    return cachedGet('/seasons/current/', {}, {
      ttlMs: 300000,
      persist: true,
      skipCache: forceRefresh,
    });
  },

  // 3. Fixtures & Live Scores (Maçkolik)
  getLiveSummary: async (params = {}) => {
    const isForce = Boolean(params?.force);
    return cachedGet(
      '/fixtures/live_summary/',
      isForce ? { ...params, _t: Date.now() } : params,
      {
        ttlMs: 4000,
        skipCache: isForce,
        headers: { 'Cache-Control': 'no-cache' },
      }
    );
  },
  getFixtures: async (params = {}, forceRefresh = false) => {
    return cachedGet('/fixtures/', params, {
      ttlMs: 60000,
      skipCache: forceRefresh,
    });
  },

  // 4. Teams
  getTeams: async (params = {}, forceRefresh = false) => {
    const persist = !params.search;
    return cachedGet('/teams/', params, {
      ttlMs: 600000,
      persist,
      skipCache: forceRefresh,
    });
  },
  getTeamDetail: async (teamId, season, forceRefresh = false) => {
    const params = season ? { season } : {};
    return cachedGet(`/teams/${teamId}/`, params, {
      ttlMs: 180000,
      skipCache: forceRefresh,
    });
  },

  // 5. Players & Legends
  getPlayers: async (params = {}, forceRefresh = false) => {
    const persist = !params.search && !params.team && (!params.season || params.season === '2026/2027');
    return cachedGet('/players/', params, {
      ttlMs: 300000,
      persist,
      skipCache: forceRefresh,
    });
  },
  getPlayerDetail: async (playerId) => {
    return cachedGet(`/players/${playerId}/`, {}, { ttlMs: 180000 });
  },
  getLegends: async (params = {}, forceRefresh = false) => {
    const persist = !params.search;
    return cachedGet('/legends/', params, {
      ttlMs: 300000,
      persist,
      skipCache: forceRefresh,
    });
  },

  // 6. Transfers
  getTransfers: async (params = {}, forceRefresh = false) => {
    const persist = !params.search;
    return cachedGet('/transfers/', params, {
      ttlMs: 300000,
      persist,
      skipCache: forceRefresh,
    });
  },

  // 7. Compare & Rivalry (Rekabet)
  comparePlayers: async (player1, player2, season) => {
    const params = { player1, player2 };
    if (season) params.season = season;
    return cachedGet('/compare/', params, { ttlMs: 180000 });
  },
  getRivalry: async (team1, team2, competition = 'ALL', refresh = false) => {
    const params = { team1, team2 };
    if (competition && competition !== 'ALL') params.competition = competition;
    if (refresh) params.refresh = 'true';
    return cachedGet('/rivalry/', params, {
      ttlMs: 300000,
      persist: !refresh && (!competition || competition === 'ALL'),
      skipCache: refresh,
    });
  },
  getRivalryMatchDetail: async (matchId, forceRefresh = false) => {
    const params = forceRefresh ? { refresh: 'true' } : {};
    return cachedGet(`/rivalry/match/${matchId}/`, params, {
      ttlMs: 600000,
      skipCache: forceRefresh,
    });
  },

  // 8. Standings & Leaders
  getStandings: async (params = {}, forceRefresh = false) => {
    const persist = !params.season || params.season === '2026/2027';
    return cachedGet('/standings/', params, {
      ttlMs: 60000,
      persist,
      skipCache: forceRefresh,
    });
  },
  getLeaderboards: async (params = {}, forceRefresh = false) => {
    return cachedGet('/leaderboards/', params, {
      ttlMs: 120000,
      skipCache: forceRefresh,
    });
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
