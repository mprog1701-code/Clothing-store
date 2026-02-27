import React, { useEffect } from 'react';
import { View, ActivityIndicator } from 'react-native';
import { useNavigation, useRoute } from '@react-navigation/native';
import { useAuth } from './AuthContext';
import theme from '../theme';

export function withAuthGate(Component) {
  return function Guarded(props) {
    const { accessToken, isHydrating } = useAuth();
    const navigation = useNavigation();
    const route = useRoute();
    useEffect(() => {
      if (!isHydrating && !accessToken) {
        navigation.navigate('Login', { next: { name: route.name, params: props.route?.params || {} } });
      }
    }, [isHydrating, accessToken]);
    if (!accessToken) {
      return (
        <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center', backgroundColor: theme.colors.background }}>
          <ActivityIndicator />
        </View>
      );
    }
    return <Component {...props} />;
  };
}
