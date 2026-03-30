import axios from 'axios';
import NetInfo from '@react-native-community/netinfo';
import { API_BASE_URL } from './config';
import { getAccessToken, getRefreshToken, saveTokens, clearTokens } from '../auth/tokenStorage';

function normalizeBaseUrl(value) {
  const stripped = String(value || '')
    .replace(/\u200E|\u200F|\u202A|\u202B|\u202C|\u202D|\u202E/g, '')
    .replace(/\s+/g, '')
    .replace(/^['"`\s]+|['"`\s]+$/g, '');
  const match = stripped.match(/https?:\/\/[^\s'"`]+/i);
  const candidate = match ? match[0] : stripped;
  if (!candidate) return '';
  try {
    const parsed = new URL(candidate);
    const protocol = String(parsed.protocol || '').toLowerCase();
    if (protocol !== 'http:' && protocol !== 'https:') return '';
    return `${protocol}//${parsed.host}${parsed.pathname}`.replace(/\/+$/g, '');
  } catch {
    return '';
  }
}

const FALLBACK_BASE_URL = 'https://clothing-store-production-4387.up.railway.app';
const NORMALIZED_BASE_URL = normalizeBaseUrl(API_BASE_URL) || FALLBACK_BASE_URL;

function buildAbsoluteUrl(base, url, params) {
  const normalizedBase = normalizeBaseUrl(base) || NORMALIZED_BASE_URL;
  const path = String(url || '');
  const merged = `${normalizedBase}${path.startsWith('/') ? path : `/${path}`}`;
  const qs = new URLSearchParams();
  Object.entries(params || {}).forEach(([k, v]) => {
    if (v === undefined || v === null || v === '') return;
    qs.append(k, String(v));
  });
  const query = qs.toString();
  return query ? `${merged}?${query}` : merged;
}

const client = axios.create({
  baseURL: NORMALIZED_BASE_URL,
  timeout: 15000
});

const PUBLIC_PATH_PREFIXES = [
  '/api/auth/firebase_login/',
  '/api/auth/firebase_reset_password/',
  '/api/auth/login/',
  '/api/auth/register/',
  '/api/auth/signup/',
  '/api/auth/forgot_password_request/',
  '/api/auth/forgot_password_confirm/',
  '/api/advertisements/',
  '/api/banners',
  '/api/products/',
  '/api/stores/',
  '/api/categories',
];

console.log('[client] BASE_URL =', NORMALIZED_BASE_URL || '(empty)', 'envDev=', !!__DEV__);

client.interceptors.request.use(async (config) => {
  const state = await NetInfo.fetch();
  if (!state.isConnected) {
    return Promise.reject({ isOffline: true });
  }
  const base = normalizeBaseUrl(API_BASE_URL) || NORMALIZED_BASE_URL;
  const isProd = !__DEV__;
  const invalidHost = !base || (isProd && /localhost|127\.0\.0\.1|192\.168\.|10\.0\.2\.2/i.test(base));
  if (invalidHost) {
    console.error('[client] INVALID_BASE_URL =', base || '(empty)');
    return Promise.reject({ message: 'Invalid API_BASE_URL', isMisconfig: true });
  }
  const currentUrl = String(config.url || '');
  const isPublicPath = PUBLIC_PATH_PREFIXES.some((prefix) => currentUrl.startsWith(prefix));
  const token = await getAccessToken();
  if (token && !isPublicPath) {
    config.headers = config.headers || {};
    config.headers.Authorization = `Bearer ${token}`;
  }
  config.baseURL = base;
  try {
    const hasApiSuffix = /\/api$/i.test(base);
    const currentUrl = String(config.url || '');
    if (hasApiSuffix && /^\/api\//i.test(currentUrl)) {
      config.url = currentUrl.replace(/^\/api/i, '');
    }
  } catch {}
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
          base: normalizeBaseUrl(API_BASE_URL) || NORMALIZED_BASE_URL || '',
          hasResponse: !!error.response,
          hasRequest: !!error.request
        };
        console.log('[client] ERROR details', details);
        try {
          if (error?.response?.data) {
            console.log('[client] ERROR response.data', error.response.data);
          }
        } catch {}
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
    if (!status && String(cfg?.method || '').toLowerCase() === 'get' && !cfg._fetch_fallback_tried) {
      cfg._fetch_fallback_tried = true;
      try {
        const base = normalizeBaseUrl(API_BASE_URL) || NORMALIZED_BASE_URL;
        const url = buildAbsoluteUrl(base, cfg?.url, cfg?.params);
        const headers = {};
        Object.entries(cfg?.headers || {}).forEach(([k, v]) => {
          if (v === undefined || v === null) return;
          if (String(k).toLowerCase() === 'content-type') return;
          headers[k] = String(v);
        });
        const resp = await fetch(url, { method: 'GET', headers });
        const ct = String(resp.headers?.get?.('content-type') || '');
        const data = ct.includes('application/json') ? await resp.json() : await resp.text();
        if (resp.ok) {
          return {
            data,
            status: resp.status,
            statusText: String(resp.status),
            headers: {},
            config: cfg,
            request: null,
          };
        }
        const fallbackError = new Error(`Request failed with status code ${resp.status}`);
        fallbackError.config = cfg;
        fallbackError.request = null;
        fallbackError.response = {
          data,
          status: resp.status,
          statusText: String(resp.status),
          headers: {},
          config: cfg,
          request: null,
        };
        fallbackError.isAxiosError = true;
        return Promise.reject(fallbackError);
      } catch {}
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
            const refreshBase = normalizeBaseUrl(API_BASE_URL) || NORMALIZED_BASE_URL;
            const r = await axios.post(`${refreshBase}/api/token/refresh/`, { refresh });
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
