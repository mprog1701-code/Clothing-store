import React, { useEffect } from 'react';
import { View, ActivityIndicator } from 'react-native';
import { me } from '../api';

export default function SplashScreen({ navigation }) {
  useEffect(() => {
    (async () => {
      try {
        await me();
        navigation.replace('Root');
      } catch {
        navigation.replace('Root');
      }
    })();
  }, []);
  return (
    <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center' }}>
      <ActivityIndicator />
    </View>
  );
}
