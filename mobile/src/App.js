import React from 'react';
import { View, ActivityIndicator, I18nManager, Text, TextInput } from 'react-native';
import AppNavigator from './navigation/AppNavigator';
import { AuthProvider } from './auth/AuthContext';
import { CartProvider } from './cart/CartContext';
import { CheckoutProvider } from './checkout/CheckoutContext';
import { useFonts, Cairo_400Regular, Cairo_700Bold } from '@expo-google-fonts/cairo';
import theme from './theme';

export default function App() {
  const [fontsLoaded] = useFonts({ Cairo_400Regular, Cairo_700Bold });
  try {
    I18nManager.allowRTL(true);
  } catch {}
  if (fontsLoaded) {
    Text.defaultProps = Text.defaultProps || {};
    TextInput.defaultProps = TextInput.defaultProps || {};
    Text.defaultProps.style = [{ fontFamily: theme.typography.fontRegular }, Text.defaultProps.style].filter(Boolean);
    TextInput.defaultProps.style = [{ fontFamily: theme.typography.fontRegular }, TextInput.defaultProps.style].filter(Boolean);
  }
  if (!fontsLoaded) {
    return (
      <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center', backgroundColor: theme.colors.background }}>
        <ActivityIndicator color={theme.colors.accent} />
      </View>
    );
  }
  return (
    <AuthProvider>
      <CartProvider>
        <CheckoutProvider>
          <AppNavigator />
        </CheckoutProvider>
      </CartProvider>
    </AuthProvider>
  );
}
