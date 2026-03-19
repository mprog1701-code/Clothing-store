import React, { useEffect, useMemo, useRef, useState } from 'react';
import { View, Text, FlatList, TouchableOpacity, ActivityIndicator, RefreshControl, I18nManager, Animated, Alert } from 'react-native';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { SafeAreaView } from 'react-native-safe-area-context';
import theme from '../theme';
import { me, listOrders, getCart, logout } from '../api';
import { clearTokens } from '../auth/tokenStorage';
import { useAuth } from '../auth/AuthContext';
import EmptyState from '../components/EmptyState';

// ملاحظة: صفحة حسابي تستخدم FlatList كجذر لمنع تحذير Nested VirtualizedLists
export default function ProfileScreen({ navigation }) {
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState('');
  const [user, setUser] = useState(null);
  const [stats, setStats] = useState({ orders: 0, cart: 0, addresses: 0 });
  const fade = useRef(new Animated.Value(0)).current;
  const { accessToken, logout: doLogout } = useAuth();

  const load = async () => {
    setLoading(true);
    setError('');
    try {
      const u = await me();
      setUser(u || null);
      try {
        const or = await listOrders({ limit: 1 });
        const ordersCount = Array.isArray(or) ? or.length : (or.count ?? (or.results?.length || 0));
        const cartData = await getCart();
        const cartCount = Array.isArray(cartData) ? cartData.length : (cartData.items?.length || cartData.results?.length || 0);
        setStats({ orders: ordersCount, cart: cartCount, addresses: (u?.addresses_count ?? 0) });
      } catch {
        setStats(s => ({ ...s, orders: s.orders || 0, cart: s.cart || 0 }));
      }
    } catch (e) {
      setError('تعذر تحميل الملف الشخصي. يرجى تسجيل الدخول أو المحاولة لاحقاً.');
    } finally {
      setLoading(false);
      Animated.timing(fade, { toValue: 1, duration: 250, useNativeDriver: true }).start();
    }
  };

  const refresh = async () => {
    setRefreshing(true);
    await load();
    setRefreshing(false);
  };

  useEffect(() => { load(); }, []);

  const options = useMemo(() => {
    const base = [
    { key: 'profile', label: 'ملفي الشخصي', icon: 'account-circle-outline', onPress: () => navigation.navigate('ProfileDetails') },
    { key: 'addresses', label: 'العناوين', icon: 'map-marker', onPress: () => navigation.navigate('Addresses') },
    { key: 'payments', label: 'طرق الدفع', icon: 'credit-card-outline', onPress: () => Alert.alert('طرق الدفع', 'طريقة الدفع من التطبيق غير متاحة حالياً، يتم إتمام الطلب حالياً بالدفع عند الاستلام.') },
    { key: 'favorites', label: 'المفضلة', icon: 'heart-outline', onPress: () => navigation.navigate('Favorites') },
    { key: 'notifications', label: 'الإشعارات', icon: 'bell-outline', onPress: () => navigation.navigate('Notifications') },
    { key: 'support', label: 'الدعم والمساعدة', icon: 'lifebuoy', onPress: () => navigation.navigate('Support') },
    { key: 'settings', label: 'الإعدادات', icon: 'cog-outline', onPress: () => navigation.navigate('Settings') },
    ];
    if (user && accessToken) {
      return [...base, { key: 'logout', label: 'تسجيل الخروج', icon: 'logout', danger: true, onPress: async () => {
        try { await logout(); } catch {}
        await clearTokens();
        await doLogout();
        navigation.reset({ index: 0, routes: [{ name: 'Login' }] });
      } }];
    }
    return [...base, { key: 'login', label: 'تسجيل الدخول', icon: 'login', onPress: () => navigation.navigate('Login') }];
  }, [navigation, user, accessToken, doLogout]);

  const HeaderStatCard = ({ label, value, onPress }) => (
    <TouchableOpacity
      onPress={onPress}
      activeOpacity={0.85}
      style={{ paddingVertical: theme.spacing.md, flex: 1, borderRadius: theme.radius.md, backgroundColor: theme.colors.surfaceAlt, alignItems: 'center', marginHorizontal: theme.spacing.xs }}
    >
      <Text style={{ color: theme.colors.textSecondary, fontFamily: theme.typography.fontRegular }}>{label}</Text>
      <Text style={{ color: theme.colors.textPrimary, fontFamily: theme.typography.fontBold }}>{value}</Text>
    </TouchableOpacity>
  );

  const Header = (
    <Animated.View style={{ opacity: fade, paddingHorizontal: 16, paddingTop: theme.spacing.lg, paddingBottom: theme.spacing.md, backgroundColor: theme.colors.surface, borderBottomWidth: 1, borderColor: theme.colors.border }}>
      <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' }}>
        <View style={{ flexDirection: 'row', alignItems: 'center' }}>
          <View style={{ width: 56, height: 56, borderRadius: 28, backgroundColor: theme.colors.surfaceAlt, alignItems: 'center', justifyContent: 'center', marginLeft: I18nManager.isRTL ? theme.spacing.md : 0, marginRight: I18nManager.isRTL ? 0 : theme.spacing.md }}>
            <MaterialCommunityIcons name="account" color={theme.colors.textPrimary} size={28} />
          </View>
          <View>
            <Text style={{ color: theme.colors.textPrimary, fontFamily: theme.typography.fontBold }}>{user?.name || user?.username || 'مستخدم'}</Text>
            <Text style={{ color: theme.colors.textSecondary, fontFamily: theme.typography.fontRegular }}>{user?.email || user?.phone || ''}</Text>
          </View>
        </View>
        <TouchableOpacity onPress={() => navigation.navigate('EditProfile')} style={{ paddingHorizontal: theme.spacing.md, paddingVertical: theme.spacing.xs, borderRadius: theme.radius.md, borderWidth: 1, borderColor: theme.colors.cardBorder }}>
          <Text style={{ color: theme.colors.textPrimary, fontFamily: theme.typography.fontBold }}>تعديل</Text>
        </TouchableOpacity>
      </View>
      <View style={{ marginTop: theme.spacing.md, flexDirection: 'row' }}>
        <HeaderStatCard label="طلباتي" value={stats.orders} onPress={() => navigation.navigate('Orders')} />
        <HeaderStatCard label="السلة" value={stats.cart} onPress={() => navigation.navigate('Cart')} />
        <HeaderStatCard label="العناوين" value={stats.addresses} onPress={() => navigation.navigate('Addresses')} />
      </View>
      {error ? (
        <View style={{ marginTop: theme.spacing.sm }}>
          <EmptyState
            icon="account-alert-outline"
            title="مشكلة في تحميل الحساب"
            subtitle={error}
            ctaLabel={accessToken ? 'إعادة المحاولة' : 'تسجيل الدخول'}
            onPress={accessToken ? load : () => navigation.navigate('Login')}
          />
        </View>
      ) : null}
    </Animated.View>
  );

  const Row = ({ item }) => (
    <View style={{ paddingHorizontal: 16, backgroundColor: theme.colors.background }}>
      <TouchableOpacity
        onPress={item.onPress}
        style={{ marginTop: theme.spacing.md, padding: theme.spacing.md, borderRadius: theme.radius.md, backgroundColor: theme.colors.surface, borderWidth: 1, borderColor: item.danger ? theme.colors.danger : theme.colors.cardBorder, flexDirection: 'row', alignItems: 'center' }}
      >
        <MaterialCommunityIcons name={item.icon} size={22} color={item.danger ? theme.colors.danger : theme.colors.textPrimary} />
        <Text style={{ marginStart: theme.spacing.md, color: item.danger ? theme.colors.danger : theme.colors.textPrimary, fontFamily: theme.typography.fontBold }}>{item.label}</Text>
      </TouchableOpacity>
    </View>
  );

  if (loading) {
    return (
      <SafeAreaView style={{ flex: 1, backgroundColor: theme.colors.background, alignItems: 'center', justifyContent: 'center' }}>
        <ActivityIndicator />
        <Text style={{ marginTop: 8, color: theme.colors.textSecondary, fontFamily: theme.typography.fontRegular }}>جاري تحميل حسابك...</Text>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: theme.colors.background }}>
      <FlatList
        data={options}
        keyExtractor={(it) => it.key}
        ListHeaderComponent={Header}
        renderItem={Row}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={refresh} />}
        removeClippedSubviews
        initialNumToRender={8}
        windowSize={7}
        ListEmptyComponent={
          <EmptyState
            icon="playlist-remove"
            title="لا خيارات متاحة"
            subtitle="جرّب تحديث الصفحة"
            ctaLabel="تحديث"
            onPress={refresh}
          />
        }
        contentContainerStyle={{ paddingBottom: theme.spacing.lg }}
      />
    </SafeAreaView>
  );
}
