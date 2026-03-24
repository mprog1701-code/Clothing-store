import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import RootTabs from './RootTabs';
import SplashScreen from '../screens/SplashScreen';
import HomeScreen from '../screens/HomeScreen';
import LoginScreen from '../screens/LoginScreen';
import RegisterScreen from '../screens/RegisterScreen';
import ForgotPasswordScreen from '../screens/ForgotPasswordScreen';
import VerifyAccountScreen from '../screens/VerifyAccountScreen';
import ProductsScreen from '../screens/ProductsScreen';
import CategoriesScreen from '../screens/CategoriesScreen';
import AllCategoriesScreen from '../screens/AllCategoriesScreen';
import ProductDetailScreen from '../screens/ProductDetailScreen';
import theme from '../theme';
import CartScreen from '../screens/CartScreen';
import CheckoutScreen from '../screens/CheckoutScreen';
import ProfileScreen from '../screens/ProfileScreen';
import ProfileDetailsScreen from '../screens/ProfileDetailsScreen';
import EditProfileScreen from '../screens/EditProfileScreen';
import AddressesScreen from '../screens/AddressesScreen';
import SettingsScreen from '../screens/SettingsScreen';
import OrdersScreen from '../screens/OrdersScreen';
import OrderDetailScreen from '../screens/OrderDetailScreen';
import StoreDetailScreen from '../screens/StoreDetailScreen';
import FavoritesScreen from '../screens/FavoritesScreen';
import NotificationsScreen from '../screens/NotificationsScreen';
import SupportScreen from '../screens/SupportScreen';
import { withAuthGate } from '../auth/RequireAuth';

const Stack = createNativeStackNavigator();

export default function AppNavigator() {
  return (
    <NavigationContainer>
      <Stack.Navigator initialRouteName="Splash" screenOptions={{ headerTitleAlign: 'center' }}>
        <Stack.Screen name="Splash" component={SplashScreen} options={{ headerShown: false }} />
        <Stack.Screen name="Root" component={RootTabs} options={{ headerShown: false }} />
        <Stack.Screen name="Home" component={HomeScreen} options={{ title: 'الرئيسية' }} />
        <Stack.Screen name="StoreDetail" component={StoreDetailScreen} options={{ title: 'المتجر' }} />
        <Stack.Screen name="Login" component={LoginScreen} options={{ headerShown: false, presentation: 'modal' }} />
        <Stack.Screen
          name="Register"
          component={RegisterScreen}
          options={{
            title: 'تسجيل',
            headerStyle: { backgroundColor: theme.colors.background },
            headerTintColor: '#fff',
            headerShadowVisible: false,
            headerTitleStyle: { color: '#fff' },
          }}
        />
        <Stack.Screen name="ForgotPassword" component={ForgotPasswordScreen} options={{ title: 'استعادة كلمة المرور' }} />
        <Stack.Screen name="VerifyAccount" component={VerifyAccountScreen} options={{ title: 'تفعيل الحساب' }} />
        <Stack.Screen name="Products" component={ProductsScreen} options={{ title: 'المنتجات' }} />
        <Stack.Screen name="ProductsList" component={ProductsScreen} options={{ title: 'المنتجات' }} />
        <Stack.Screen name="Categories" component={CategoriesScreen} options={{ title: 'الأقسام' }} />
        <Stack.Screen name="AllCategories" component={AllCategoriesScreen} options={{ title: 'كل الأقسام' }} />
        <Stack.Screen
          name="ProductDetail"
          component={ProductDetailScreen}
          options={{
            title: 'تفاصيل المنتج',
            headerStyle: { backgroundColor: theme.colors.background },
            headerTintColor: '#fff',
            headerShadowVisible: false,
            headerTitleStyle: { color: '#fff' },
          }}
        />
        <Stack.Screen name="Cart" component={withAuthGate(CartScreen)} options={{ title: 'السلة' }} />
        <Stack.Screen name="Checkout" component={withAuthGate(CheckoutScreen)} options={{ title: 'الدفع' }} />
        <Stack.Screen name="Profile" component={withAuthGate(ProfileScreen)} options={{ title: 'حسابي' }} />
        <Stack.Screen name="ProfileDetails" component={ProfileDetailsScreen} options={{ title: 'تفاصيل الحساب' }} />
        <Stack.Screen name="EditProfile" component={EditProfileScreen} options={{ title: 'تعديل الملف' }} />
        <Stack.Screen name="Addresses" component={AddressesScreen} options={{ title: 'العناوين' }} />
        <Stack.Screen name="Favorites" component={withAuthGate(FavoritesScreen)} options={{ title: 'المفضلة' }} />
        <Stack.Screen name="Notifications" component={withAuthGate(NotificationsScreen)} options={{ title: 'الإشعارات' }} />
        <Stack.Screen name="Support" component={SupportScreen} options={{ title: 'الدعم والمساعدة' }} />
        <Stack.Screen name="Settings" component={SettingsScreen} options={{ title: 'الإعدادات' }} />
        <Stack.Screen name="Orders" component={withAuthGate(OrdersScreen)} options={{ title: 'طلباتي' }} />
        <Stack.Screen name="OrderDetail" component={OrderDetailScreen} options={{ title: 'تفاصيل الطلب' }} />
      </Stack.Navigator>
    </NavigationContainer>
  );
}
