import React from 'react';
import { View } from 'react-native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { I18nManager } from 'react-native';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { useFocusEffect, useNavigation } from '@react-navigation/native';
import theme from '../theme';
import HomeScreen from '../screens/HomeScreen';
import SearchScreen from '../screens/SearchScreen';
import CartScreen from '../screens/CartScreen';
import OrdersScreen from '../screens/OrdersScreen';
import ProfileScreen from '../screens/ProfileScreen';
import StoresScreen from '../screens/StoresScreen';
import { useAuth } from '../auth/AuthContext';
import LoginRequiredSheet from '../components/LoginRequiredSheet';
import { getCart } from '../api';

const Tab = createBottomTabNavigator();

export default function RootTabs() {
  const navigation = useNavigation();
  const { accessToken } = useAuth();
  const [sheetVisible, setSheetVisible] = React.useState(false);
  const [pendingNext, setPendingNext] = React.useState(null);
  const [cartCount, setCartCount] = React.useState(0);

  const requestLogin = React.useCallback((next) => {
    setPendingNext(next);
    setSheetVisible(true);
  }, []);

  const refreshCartBadge = React.useCallback(async () => {
    if (!accessToken) {
      setCartCount(0);
      return;
    }
    try {
      const data = await getCart();
      const arr = Array.isArray(data) ? data : (data.items || data.results || []);
      const nextCount = arr.reduce((sum, it) => sum + Number(it?.quantity || 0), 0);
      setCartCount(nextCount);
    } catch {
      setCartCount(0);
    }
  }, [accessToken]);

  React.useEffect(() => {
    refreshCartBadge();
  }, [refreshCartBadge]);

  useFocusEffect(
    React.useCallback(() => {
      refreshCartBadge();
    }, [refreshCartBadge])
  );

  return (
    <View style={{ flex: 1 }}>
      <Tab.Navigator
        initialRouteName="Home"
        screenOptions={({ route }) => ({
          headerShown: false,
          tabBarStyle: { backgroundColor: theme.colors.surface, borderTopColor: theme.colors.border },
          tabBarActiveTintColor: theme.colors.accent,
          tabBarInactiveTintColor: theme.colors.textSecondary,
          tabBarLabelStyle: { fontFamily: theme.typography.fontRegular },
          tabBarIcon: ({ color, size }) => {
            const name =
              route.name === 'Home' ? 'home' :
              route.name === 'Stores' ? 'store' :
              route.name === 'Search' ? 'magnify' :
              route.name === 'Cart' ? 'cart' :
              route.name === 'Orders' ? 'receipt' :
              'account';
            return <MaterialCommunityIcons name={name} size={size} color={color} />;
          },
        })}
      >
        <Tab.Screen name="Home" component={HomeScreen} options={{ title: 'الرئيسية' }} />
        <Tab.Screen name="Stores" component={StoresScreen} options={{ title: 'المتاجر' }} />
        <Tab.Screen
          name="Cart"
          component={CartScreen}
          options={{
            title: 'السلة',
            tabBarBadge: cartCount > 0 ? cartCount : undefined,
            tabBarBadgeStyle: { backgroundColor: theme.colors.danger, color: '#fff', fontFamily: theme.typography.fontBold },
          }}
          listeners={{
            tabPress: () => {
              refreshCartBadge();
            },
          }}
        />
        <Tab.Screen
          name="Orders"
          component={OrdersScreen}
          options={{ title: 'طلباتي' }}
          listeners={{
            tabPress: (e) => {
              if (accessToken) return;
              e.preventDefault();
              requestLogin({ name: 'Root', params: { screen: 'Orders' } });
            },
          }}
        />
        <Tab.Screen
          name="Profile"
          component={ProfileScreen}
          options={{ title: 'حسابي' }}
          listeners={{
            tabPress: (e) => {
              if (accessToken) return;
              e.preventDefault();
              requestLogin({ name: 'Root', params: { screen: 'Profile' } });
            },
          }}
        />
      </Tab.Navigator>
      <LoginRequiredSheet
        visible={sheetVisible}
        onClose={() => setSheetVisible(false)}
        onLogin={() => {
          setSheetVisible(false);
          navigation.replace('Login', pendingNext ? { next: pendingNext } : undefined);
        }}
      />
    </View>
  );
}
