import * as SecureStore from 'expo-secure-store';

const ACCESS_KEY = 'auth_access_token';
const REFRESH_KEY = 'auth_refresh_token';

const isWeb = typeof window !== 'undefined' && typeof window.localStorage !== 'undefined';

async function setItem(key, value) {
  if (isWeb) {
    window.localStorage.setItem(key, value || '');
    return;
  }
  await SecureStore.setItemAsync(key, value || '');
}

async function getItem(key) {
  if (isWeb) {
    return window.localStorage.getItem(key) || '';
  }
  return (await SecureStore.getItemAsync(key)) || '';
}

async function deleteItem(key) {
  if (isWeb) {
    window.localStorage.removeItem(key);
    return;
  }
  await SecureStore.deleteItemAsync(key);
}

export async function saveTokens({ access, refresh }) {
  await setItem(ACCESS_KEY, access || '');
  await setItem(REFRESH_KEY, refresh || '');
}

export async function setTokens({ access, refresh }) {
  return saveTokens({ access, refresh });
}

export async function getAccessToken() {
  return await getItem(ACCESS_KEY);
}

export async function getRefreshToken() {
  return await getItem(REFRESH_KEY);
}

export async function clearTokens() {
  await deleteItem(ACCESS_KEY);
  await deleteItem(REFRESH_KEY);
}

export async function isLoggedIn() {
  const access = await getAccessToken();
  return !!(access && access.length > 0);
}
