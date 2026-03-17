import React, { useEffect, useMemo, useState, useCallback } from 'react';
import { View, Text, FlatList, TouchableOpacity, Image, I18nManager, ActivityIndicator, RefreshControl, Alert } from 'react-native';
import theme from '../theme';
import { clearTokens } from '../auth/tokenStorage';
import { useAuth } from '../auth/AuthContext';
import { getCart, updateCartItem, removeCartItem } from '../api';
import LoginRequiredSheet from '../components/LoginRequiredSheet';

export default function CartScreen({ navigation }) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState('');
  const [requireLogin, setRequireLogin] = useState(false);
  const [sheetVisible, setSheetVisible] = useState(false);
  const { isHydrating, accessToken, user, isAuthenticated } = useAuth();
  const load = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await getCart();
      const arr = Array.isArray(data) ? data : (data.items || data.results || []);
      setItems(arr || []);
    } catch (e) {
      const status = e?.response?.status;
      if (status === 401) {
        await clearTokens();
        setRequireLogin(true);
        setItems([]);
      } else {
        setError('تعذر تحميل السلة. يرجى تسجيل الدخول أو المحاولة لاحقاً.');
      }
    } finally {
      setLoading(false);
    }
  };
  const refresh = async () => {
    setRefreshing(true);
    try {
      const data = await getCart();
      const arr = Array.isArray(data) ? data : (data.items || data.results || []);
      setItems(arr || []);
    } catch {
    } finally {
      setRefreshing(false);
    }
  };
  useEffect(() => {
    const onFocus = async () => {
      if (isHydrating) {
        setLoading(true);
        return;
      }
      if (!isAuthenticated && !(accessToken && user)) {
        setRequireLogin(true);
        setLoading(false);
        return;
      }
      setRequireLogin(false);
      await load();
    };
    const unsubscribe = navigation.addListener('focus', onFocus);
    return unsubscribe;
  }, [navigation, isHydrating, accessToken, user, isAuthenticated]);

  useEffect(() => {
    if (isHydrating) return;
    if (isAuthenticated || (accessToken && user)) {
      setRequireLogin(false);
    }
  }, [isHydrating, isAuthenticated, accessToken, user]);
  const subtotal = useMemo(() => items.reduce((sum, it) => sum + (it.product?.base_price || 0) * it.quantity, 0), [items]);
  const inc = useCallback(async (id) => {
    setItems(prev => prev.map(it => it.id === id ? { ...it, quantity: it.quantity + 1 } : it));
    try {
      const it = items.find(x => x.id === id);
      await updateCartItem(id, (it?.quantity || 0) + 1);
    } catch {
      Alert.alert('خطأ', 'فشل تحديث الكمية'); load();
    }
  }, [items]);
  const dec = useCallback(async (id) => {
    const current = items.find(x => x.id === id);
    const nextQty = Math.max(1, (current?.quantity || 1) - 1);
    setItems(prev => prev.map(it => it.id === id ? { ...it, quantity: nextQty } : it));
    try {
      await updateCartItem(id, nextQty);
    } catch {
      Alert.alert('خطأ', 'فشل تحديث الكمية'); load();
    }
  }, [items]);
  const del = useCallback(async (id) => {
    const old = items;
    setItems(prev => prev.filter(it => it.id !== id));
    try {
      await removeCartItem(id);
      Alert.alert('تم', 'تم حذف المنتج من السلة');
    } catch {
      setItems(old);
      Alert.alert('خطأ', 'تعذر حذف المنتج، حاول مرة أخرى');
    }
  }, [items]);
  const Header = (
    <View style={{ paddingHorizontal: theme.spacing.lg, paddingTop: theme.spacing.lg, paddingBottom: theme.spacing.md, borderBottomWidth: 1, borderColor: theme.colors.border, backgroundColor: theme.colors.surface }}>
      <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
        <Text style={{ color: theme.colors.textPrimary, fontFamily: theme.typography.fontBold, fontSize: theme.typography.sizes.lg, textAlign: I18nManager.isRTL ? 'right' : 'left' }}>السلة</Text>
        <Text style={{ color: theme.colors.textSecondary, fontFamily: theme.typography.fontRegular }}>{items.length}</Text>
      </View>
      {error ? (
        <View style={{ marginTop: theme.spacing.sm }}>
          <Text style={{ color: theme.colors.danger, fontFamily: theme.typography.fontBold, textAlign: I18nManager.isRTL ? 'right' : 'left' }}>{error}</Text>
        </View>
      ) : null}
    </View>
  );
  const Row = ({ item }) => (
    <View style={{ flexDirection: 'row', padding: theme.spacing.md, borderBottomWidth: 1, borderColor: theme.colors.cardBorder, backgroundColor: theme.colors.surface }}>
      {item.product?.main_image?.image_url ? (
        <Image source={{ uri: item.product.main_image.image_url }} style={{ width: 80, height: 80, borderRadius: theme.radius.md, marginLeft: I18nManager.isRTL ? theme.spacing.md : 0, marginRight: I18nManager.isRTL ? 0 : theme.spacing.md }} />
      ) : (
        <View style={{ width: 80, height: 80, borderRadius: theme.radius.md, backgroundColor: theme.colors.surfaceAlt, marginLeft: I18nManager.isRTL ? theme.spacing.md : 0, marginRight: I18nManager.isRTL ? 0 : theme.spacing.md }} />
      )}
      <View style={{ flex: 1 }}>
        <Text numberOfLines={2} style={{ color: theme.colors.textPrimary, fontFamily: theme.typography.fontBold, textAlign: I18nManager.isRTL ? 'right' : 'left' }}>{item.product?.name || 'منتج'}</Text>
        <Text style={{ color: theme.colors.textSecondary, fontFamily: theme.typography.fontRegular, marginTop: 4, textAlign: I18nManager.isRTL ? 'right' : 'left' }}>{item.variant_text || ''}</Text>
        <Text style={{ color: theme.colors.textPrimary, fontFamily: theme.typography.fontBold, marginTop: 4, textAlign: I18nManager.isRTL ? 'right' : 'left' }}>{item.product?.base_price ?? '-'}</Text>
        <View style={{ flexDirection: 'row', marginTop: theme.spacing.sm, alignItems: 'center' }}>
          <TouchableOpacity onPress={() => dec(item.id)} disabled={item.quantity <= 1} style={{ paddingHorizontal: theme.spacing.md, paddingVertical: 6, borderRadius: theme.radius.md, borderWidth: 1, borderColor: theme.colors.cardBorder, backgroundColor: item.quantity <= 1 ? theme.colors.surfaceAlt : theme.colors.surface }}>
            <Text style={{ color: theme.colors.textPrimary, fontFamily: theme.typography.fontBold }}>−</Text>
          </TouchableOpacity>
          <Text style={{ marginHorizontal: theme.spacing.md, color: theme.colors.textPrimary, fontFamily: theme.typography.fontBold }}>{item.quantity}</Text>
          <TouchableOpacity onPress={() => inc(item.id)} style={{ paddingHorizontal: theme.spacing.md, paddingVertical: 6, borderRadius: theme.radius.md, borderWidth: 1, borderColor: theme.colors.cardBorder, backgroundColor: theme.colors.surface }}>
            <Text style={{ color: theme.colors.textPrimary, fontFamily: theme.typography.fontBold }}>+</Text>
          </TouchableOpacity>
          <View style={{ flex: 1 }} />
          <TouchableOpacity onPress={() => del(item.id)} style={{ paddingHorizontal: theme.spacing.md, paddingVertical: 6, borderRadius: theme.radius.md, borderWidth: 1, borderColor: theme.colors.cardBorder, backgroundColor: theme.colors.surfaceAlt }}>
            <Text style={{ color: theme.colors.danger, fontFamily: theme.typography.fontBold }}>حذف</Text>
          </TouchableOpacity>
        </View>
      </View>
    </View>
  );
  if (requireLogin) {
    return (
      <View style={{ flex: 1, backgroundColor: theme.colors.background, alignItems: 'center', justifyContent: 'center', padding: theme.spacing.lg }}>
        <Text style={{ color: theme.colors.textPrimary, fontFamily: theme.typography.fontBold, textAlign: 'center' }}>سجّل دخول حتى نعرض سلتك</Text>
        <TouchableOpacity onPress={() => navigation.replace('Login', { next: { name: 'Root', params: { screen: 'Cart' } } })} style={{ marginTop: theme.spacing.md, paddingVertical: theme.spacing.sm, paddingHorizontal: theme.spacing.md, borderRadius: theme.radius.md, backgroundColor: theme.colors.accent }}>
          <Text style={{ color: '#000', fontFamily: theme.typography.fontBold }}>تسجيل الدخول</Text>
        </TouchableOpacity>
      </View>
    );
  }
  if (loading) {
    return (
      <View style={{ flex: 1, backgroundColor: theme.colors.background, alignItems: 'center', justifyContent: 'center' }}>
        <ActivityIndicator />
        <Text style={{ marginTop: 8, color: theme.colors.textSecondary, fontFamily: theme.typography.fontRegular }}>جاري تحميل السلة...</Text>
      </View>
    );
  }
  if (!items.length) {
    return (
      <View style={{ flex: 1, backgroundColor: theme.colors.background }}>
        {Header}
        <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center', padding: theme.spacing.lg }}>
          <Text style={{ color: theme.colors.textSecondary, fontFamily: theme.typography.fontRegular, textAlign: 'center' }}>سلتك فارغة حالياً</Text>
          <TouchableOpacity onPress={() => navigation.navigate('Home')} style={{ marginTop: theme.spacing.md, paddingVertical: theme.spacing.sm, paddingHorizontal: theme.spacing.md, borderRadius: theme.radius.md, backgroundColor: theme.colors.accent }}>
            <Text style={{ color: '#000', fontFamily: theme.typography.fontBold }}>تصفح المنتجات</Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  }
  return (
    <View style={{ flex: 1, backgroundColor: theme.colors.background }}>
      <FlatList
        data={items}
        keyExtractor={(it) => String(it.id)}
        ListHeaderComponent={Header}
        ListFooterComponent={<View style={{ height: 120 }} />}
        renderItem={Row}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={refresh} />}
        removeClippedSubviews
        initialNumToRender={8}
        windowSize={7}
        contentContainerStyle={{ paddingBottom: 140 }}
      />
      <View style={{ position: 'absolute', left: 0, right: 0, bottom: 0 }}>
        <View style={{ paddingHorizontal: theme.spacing.lg, paddingVertical: theme.spacing.md, borderTopWidth: 1, borderColor: theme.colors.border, backgroundColor: theme.colors.surface }}>
          <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
            <Text style={{ color: theme.colors.textSecondary, fontFamily: theme.typography.fontRegular }}>الإجمالي</Text>
            <Text style={{ color: theme.colors.textPrimary, fontFamily: theme.typography.fontBold }}>{subtotal}</Text>
          </View>
          <TouchableOpacity
            onPress={() => {
              if (!accessToken) {
                setSheetVisible(true);
                return;
              }
              navigation.navigate('Checkout');
            }}
            style={{ marginTop: theme.spacing.md, paddingVertical: theme.spacing.md, borderRadius: theme.radius.lg, backgroundColor: theme.colors.accent, alignItems: 'center' }}
          >
            <Text style={{ color: '#000', fontFamily: theme.typography.fontBold }}>إتمام الشراء</Text>
          </TouchableOpacity>
        </View>
      </View>
      <LoginRequiredSheet
        visible={sheetVisible}
        onClose={() => setSheetVisible(false)}
        onLogin={() => {
          setSheetVisible(false);
          navigation.replace('Login', { next: { name: 'Checkout' } });
        }}
      />
    </View>
  );
}
