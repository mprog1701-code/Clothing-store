const RAW = process.env.EXPO_PUBLIC_API_BASE_URL || '';
const CLEAN = RAW
  .trim()
  .replace(/^[`'"]|[`'"]$/g, '')
  .replace(/[)]+$/g, '')
  .replace(/\s+/g, '');
export const API_BASE_URL = CLEAN;
