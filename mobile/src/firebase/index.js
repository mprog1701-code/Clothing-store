import Constants from 'expo-constants';
import { Platform } from 'react-native';
import { initializeApp, getApps, getApp } from 'firebase/app';
import { getAuth, initializeAuth, getReactNativePersistence } from 'firebase/auth';
import AsyncStorage from '@react-native-async-storage/async-storage';

const extra = Constants.expoConfig?.extra || Constants.manifest?.extra || {};
const projectId = String(
  extra.firebaseProjectId ||
  process.env.EXPO_PUBLIC_FIREBASE_PROJECT_ID ||
  'daar-dfa7a'
);
const authDomain = String(
  extra.firebaseAuthDomain ||
  process.env.EXPO_PUBLIC_FIREBASE_AUTH_DOMAIN ||
  (projectId ? `${projectId}.firebaseapp.com` : 'daar-dfa7a.firebaseapp.com')
);
const apiKey = String(
  extra.firebaseApiKey ||
  process.env.EXPO_PUBLIC_FIREBASE_API_KEY ||
  'AIzaSyBoubJjNU1Z09RDvYZCMOlAwSOko3-F8CY'
);
const storageBucket = String(
  extra.firebaseStorageBucket ||
  process.env.EXPO_PUBLIC_FIREBASE_STORAGE_BUCKET ||
  'daar-dfa7a.firebasestorage.app'
);
const messagingSenderId = String(
  extra.firebaseMessagingSenderId ||
  process.env.EXPO_PUBLIC_FIREBASE_MESSAGING_SENDER_ID ||
  '990572778073'
);
const webAppId = String(
  extra.firebaseWebAppId ||
  process.env.EXPO_PUBLIC_FIREBASE_WEB_APP_ID ||
  '1:990572778073:web:0af0c79b506c99d0085748'
);
const androidAppId = String(
  extra.firebaseAndroidAppId ||
  process.env.EXPO_PUBLIC_FIREBASE_ANDROID_APP_ID ||
  ''
);
const iosAppId = String(
  extra.firebaseIosAppId ||
  process.env.EXPO_PUBLIC_FIREBASE_IOS_APP_ID ||
  ''
);

export const firebaseConfig = {
  apiKey,
  authDomain,
  projectId,
  storageBucket,
  messagingSenderId,
  appId: webAppId || (Platform.OS === 'ios' ? iosAppId : androidAppId),
};

export const firebaseConfigReady = Boolean(
  firebaseConfig.apiKey &&
  firebaseConfig.authDomain &&
  firebaseConfig.projectId
);

export const firebaseWebAppReady = Boolean(firebaseConfig.appId);

export async function ensureFirebasePhoneAuthReady() {
  if (!firebaseConfigReady) {
    throw new Error('FIREBASE_CONFIG_INVALID');
  }
  const normalizedAuthDomain = String(firebaseConfig.authDomain || '').replace(/^https?:\/\//, '');
  const domainsToTry = [normalizedAuthDomain];
  if (projectId) {
    const firebaseAppDomain = `${projectId}.firebaseapp.com`;
    const webAppDomain = `${projectId}.web.app`;
    if (!domainsToTry.includes(firebaseAppDomain)) domainsToTry.push(firebaseAppDomain);
    if (!domainsToTry.includes(webAppDomain)) domainsToTry.push(webAppDomain);
  }
  let hasNetworkError = false;
  for (const domain of domainsToTry) {
    const initUrl = `https://${domain}/__/firebase/init.json`;
    try {
      const response = await fetch(initUrl, { method: 'GET' });
      if (response.ok) {
        firebaseConfig.authDomain = domain;
        return;
      }
    } catch {
      hasNetworkError = true;
    }
  }
  if (hasNetworkError) {
    throw new Error('FIREBASE_AUTH_DOMAIN_UNREACHABLE');
  }
  return;
}

export const firebaseApp = getApps().length ? getApp() : initializeApp(firebaseConfig);

let authInstance = null;

export function firebaseAuth() {
  if (authInstance) return authInstance;
  try {
    authInstance = initializeAuth(firebaseApp, {
      persistence: getReactNativePersistence(AsyncStorage),
    });
  } catch {
    authInstance = getAuth(firebaseApp);
  }
  return authInstance;
}
