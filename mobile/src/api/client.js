import axios from 'axios';
import NetInfo from '@react-native-community/netinfo';
import { API_BASE_URL } from '../config';
import { getAccessToken, getRefreshToken, saveTokens, clearTokens } from '../auth/tokenStorage';

const client = axios.create({
  baseURL: API_BASE_URL.replace(/\/+$/, ''),
  timeout: 15000
});

console.log('[client] API_BASE_URL =', API_BASE_URL || '(empty)');

client.interceptors.request.use(async (config) => {
  const state = await NetInfo.fetch();
  if (!state.isConnected) {
    return Promise.reject({ isOffline: true });
  }
  if (!API_BASE_URL) {
    return Promise.reject({ message: 'API_BASE_URL is not set', isMisconfig: true });
  }
  const token = await getAccessToken();
  if (token) {
    config.headers = config.headers || {};
    config.headers.Authorization = `Bearer ${token}`;
  }
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
    try {
      console.log('[client] ERROR status=', status, 'url=', cfg?.url, 'message=', error?.message);
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
            const r = await axios.post(`${API_BASE_URL}/api/token/refresh/`, { refresh });
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
