import axios from 'axios';
import NetInfo from '@react-native-community/netinfo';
import { API_BASE_URL } from './config';
import { getAccessToken, getRefreshToken, saveTokens, clearTokens } from '../auth/tokenStorage';

const NORMALIZED_BASE_URL = String(API_BASE_URL || '')
  .replace(/[`'"\s]/g, '')
  .replace(/\/+$/g, '');

const client = axios.create({
  baseURL: NORMALIZED_BASE_URL,
  timeout: 15000
});

console.log('[client] BASE_URL =', NORMALIZED_BASE_URL || '(empty)', 'envDev=', !!__DEV__);

client.interceptors.request.use(async (config) => {
  const state = await NetInfo.fetch();
  if (!state.isConnected) {
    return Promise.reject({ isOffline: true });
  }
  const base = NORMALIZED_BASE_URL;
  const isProd = !__DEV__;
  const invalidHost = !base || (isProd && /localhost|127\.0\.0\.1|192\.168\.|10\.0\.2\.2/i.test(base));
  if (invalidHost) {
    console.error('[client] INVALID_BASE_URL =', base || '(empty)');
    return Promise.reject({ message: 'Invalid API_BASE_URL', isMisconfig: true });
  }
  const token = await getAccessToken();
  if (token) {
    config.headers = config.headers || {};
    config.headers.Authorization = `Bearer ${token}`;
  }
  try {
    const m = (config.method || 'get').toUpperCase();
    const full = `${base}${config.url || ''}`;
    console.log('[client] REQUEST', m, full);
  } catch {}
  return config;
});

let refreshing = null;

client.interceptors.response.use(
  (resp) => {
    try {
      console.log('[client] HTTP', resp.status, resp.config?.method?.toUpperCase(), resp.config?.url);
    } catch {}
    return resp;
  },
  async (error) => {
    const cfg = error.config || {};
    const status = error.response && error.response.status;
    const isCart500 = status === 500 && String(cfg?.url || '').includes('/api/cart/');
    try {
      if (!isCart500) {
        console.log('[client] ERROR status=', status, 'url=', cfg?.url, 'message=', error?.message);
        const details = {
          isAxiosError: !!error.isAxiosError,
          code: error.code || '',
          method: (cfg?.method || '').toUpperCase(),
          base: NORMALIZED_BASE_URL || '',
          hasResponse: !!error.response,
          hasRequest: !!error.request
        };
        console.log('[client] ERROR details', details);
        try {
          const j = typeof error.toJSON === 'function' ? error.toJSON() : null;
          if (j) console.log('[client] ERROR toJSON', j);
        } catch {}
      }
    } catch {}
    if (error.isOffline) {
      return Promise.reject(error);
    }
    if (error.isMisconfig) {
      return Promise.reject(error);
    }
    if ((status === 401 || status === 403) && !cfg._retry) {
      cfg._retry = true;
      if (!refreshing) {
        refreshing = (async () => {
          const refresh = await getRefreshToken();
          if (!refresh) {
            await clearTokens();
            throw error;
          }
          try {
            const r = await axios.post(`${NORMALIZED_BASE_URL}/api/token/refresh/`, { refresh });
            const access = r.data && r.data.access;
            if (access) {
              await saveTokens({ access, refresh });
            }
            return access;
          } catch {
            await clearTokens();
            throw error;
          } finally {
            refreshing = null;
          }
        })();
      }
      try {
        const newAccess = await refreshing;
        if (newAccess) {
          cfg.headers = cfg.headers || {};
          cfg.headers.Authorization = `Bearer ${newAccess}`;
          return client(cfg);
        }
      } catch (e) {
        return Promise.reject(e);
      }
    }
    return Promise.reject(error);
  }
);

export default client;
