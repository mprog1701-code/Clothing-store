import React from 'react';
import { View, ActivityIndicator, I18nManager } from 'react-native';
import AppNavigator from './navigation/AppNavigator';
import { AuthProvider } from './auth/AuthContext';
import { useFonts, Cairo_400Regular, Cairo_700Bold } from '@expo-google-fonts/cairo';

export default function App() {
  const [fontsLoaded] = useFonts({ Cairo_400Regular, Cairo_700Bold });
  try {
    I18nManager.allowRTL(true);
  } catch {}
  if (!fontsLoaded) {
    return (
      <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center' }}>
        <ActivityIndicator />
      </View>
    );
  }
  return (
    <AuthProvider>
      <AppNavigator />
    </AuthProvider>
  );
}
