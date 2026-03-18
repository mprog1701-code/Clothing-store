import Constants from 'expo-constants';

function sanitizeUrl(value) {
  let raw = String(value || '')
    .trim()
    .replace(/\s+/g, '')
    .replace(/^['"`\s]+|['"`\s]+$/g, '')
    .replace(/[)]+$/g, '')
    .replace(/,+$/g, '');
  while (raw.length > 1 && /^[`'"]/.test(raw) && /[`'"]$/.test(raw)) {
    raw = raw.slice(1, -1).trim();
  }
  if (!raw) return '';
  if (/your-railway-domain|example\.com|localhost:8000/i.test(raw)) return '';
  return raw.replace(/\/+$/g, '');
}

const extra = Constants?.expoConfig?.extra || Constants?.manifest?.extra || {};
const envBase = sanitizeUrl(process.env.EXPO_PUBLIC_API_BASE_URL);
const extraBase = sanitizeUrl(extra.apiBaseUrl);
const fallbackBase = 'https://clothing-store-production-4387.up.railway.app';

export const API_BASE_URL = envBase || extraBase || fallbackBase;
export const LOGIN_URL = sanitizeUrl(process.env.EXPO_PUBLIC_LOGIN_URL) || sanitizeUrl(extra.loginUrl) || `${API_BASE_URL}/login/`;
export const GOOGLE_OAUTH_START_URL =
  sanitizeUrl(process.env.EXPO_PUBLIC_GOOGLE_OAUTH_START_URL) ||
  sanitizeUrl(extra.googleOauthStartUrl) ||
  `${API_BASE_URL}/login/?provider=google`;

export const GOOGLE_ANDROID_CLIENT_ID = process.env.EXPO_PUBLIC_GOOGLE_ANDROID_CLIENT_ID || extra.googleAndroidClientId || '';
export const GOOGLE_IOS_CLIENT_ID = process.env.EXPO_PUBLIC_GOOGLE_IOS_CLIENT_ID || extra.googleIosClientId || '';
