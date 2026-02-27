import React from 'react';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { I18nManager } from 'react-native';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import theme from '../theme';
import HomeScreen from '../screens/HomeScreen';
import SearchScreen from '../screens/SearchScreen';
import CartScreen from '../screens/CartScreen';
import OrdersScreen from '../screens/OrdersScreen';
import ProfileScreen from '../screens/ProfileScreen';
import StoresScreen from '../screens/StoresScreen';

const Tab = createBottomTabNavigator();

export default function RootTabs() {
  return (
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
      <Tab.Screen name="Cart" component={CartScreen} options={{ title: 'السلة' }} />
      <Tab.Screen name="Orders" component={OrdersScreen} options={{ title: 'طلباتي' }} />
      <Tab.Screen name="Profile" component={ProfileScreen} options={{ title: 'حسابي' }} />
    </Tab.Navigator>
  );
}
