const RAW = process.env.EXPO_PUBLIC_API_BASE_URL || '';
function sanitize(u) {
  return String(u || '')
    .trim()
    .replace(/^[`'"]|[`'"]$/g, '')
    .replace(/[)]+$/g, '')
    .replace(/\s+/g, '')
    .replace(/\/+$/g, '');
}
const DEV_DEFAULT = 'https://clothing-store-production-4387.up.railway.app';
const PROD_DEFAULT = 'https://clothing-store-production-4387.up.railway.app';
const FROM_ENV = sanitize(RAW);
export const API_BASE_URL =
  FROM_ENV && FROM_ENV.length > 0
    ? FROM_ENV
    : (__DEV__ ? DEV_DEFAULT : PROD_DEFAULT);
