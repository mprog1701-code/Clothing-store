import React, { useCallback, useMemo, useState } from 'react';
import { View, Text, TouchableOpacity, ActivityIndicator, I18nManager, Alert, FlatList } from 'react-native';
import { useFocusEffect } from '@react-navigation/native';
import theme from '../theme';
import { createOrder, getCart, listAddresses, removeCartItem } from '../api';
import { useCart } from '../cart/CartContext';
import { useCheckout } from '../checkout/CheckoutContext';

export default function CheckoutScreen({ navigation }) {
  const [loading, setLoading] = useState(true);
  const [placing, setPlacing] = useState(false);
  const [items, setItems] = useState([]);
  const [addresses, setAddresses] = useState([]);
  const [error, setError] = useState('');
  const { refreshCartCount } = useCart();
  const { selectedAddressId, selectedAddress, setSelectedAddress, clearSelectedAddress } = useCheckout();

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const [cartData, addrData] = await Promise.all([getCart(), listAddresses()]);
      const cartArr = Array.isArray(cartData) ? cartData : (cartData?.items || cartData?.results || []);
      const addrArr = Array.isArray(addrData) ? addrData : (addrData?.results || addrData?.items || addrData?.addresses || []);
      setItems(cartArr || []);
      setAddresses(addrArr || []);
      if (addrArr?.length) {
        const active = addrArr.find((a) => a.id === selectedAddressId) || addrArr[0];
        if (active) setSelectedAddress(active);
      } else {
        clearSelectedAddress();
      }
    } catch (e) {
      setError('تعذر تحميل بيانات الدفع حالياً');
      if (__DEV__) {
        console.log('[Checkout] load failed', {
          message: e?.message,
          status: e?.response?.status,
          data: e?.response?.data,
        });
      }
    } finally {
      setLoading(false);
    }
  }, [clearSelectedAddress, selectedAddressId, setSelectedAddress]);

  useFocusEffect(
    useCallback(() => {
      load();
    }, [load])
  );

  const subtotal = useMemo(
    () => items.reduce((sum, it) => sum + Number(it?.product?.base_price || 0) * Number(it?.quantity || 0), 0),
    [items]
  );

  const groups = useMemo(() => {
    const map = new Map();
    for (const it of items) {
      const sid = it?.product?.store?.id;
      if (!sid) continue;
      if (!map.has(sid)) {
        map.set(sid, { storeId: sid, storeName: it?.product?.store?.name || 'متجر', items: [] });
      }
      map.get(sid).items.push(it);
    }
    return Array.from(map.values());
  }, [items]);

  const onPlaceOrder = async () => {
    if (placing) return;
    if (!items.length) {
      Alert.alert('تنبيه', 'السلة فارغة حالياً');
      return;
    }
    if (!selectedAddressId) {
      Alert.alert('تنبيه', 'اختر عنواناً أولاً');
      return;
    }
    if (!groups.length) {
      Alert.alert('تنبيه', 'تعذر تحديد المتجر للعناصر');
      return;
    }
    setPlacing(true);
    try {
      for (const g of groups) {
        const payload = {
          store: g.storeId,
          address: selectedAddressId,
          items: g.items.map((it) => ({
            product_id: it?.product?.id,
            variant_id: it?.variant?.id || it?.variant_id || null,
            quantity: Number(it?.quantity || 1),
          })),
        };
        await createOrder(payload);
      }
      for (const it of items) {
        if (typeof it?.id === 'number') {
          try {
            await removeCartItem(it.id);
          } catch {}
        }
      }
      await refreshCartCount();
      Alert.alert('تم', 'تم إنشاء الطلب بنجاح');
      navigation.replace('Orders');
    } catch (e) {
      Alert.alert('خطأ', 'تعذر إكمال الطلب حالياً');
      if (__DEV__) {
        console.log('[Checkout] place order failed', {
          message: e?.message,
          status: e?.response?.status,
          data: e?.response?.data,
        });
      }
    } finally {
      setPlacing(false);
    }
  };

  if (loading) {
    return (
      <View style={{ flex: 1, backgroundColor: theme.colors.background, alignItems: 'center', justifyContent: 'center' }}>
        <ActivityIndicator />
      </View>
    );
  }

  return (
    <View style={{ flex: 1, backgroundColor: theme.colors.background }}>
      <FlatList
        data={items}
        keyExtractor={(it, idx) => `${it?.id || idx}`}
        ListHeaderComponent={
          <View style={{ paddingHorizontal: theme.spacing.lg, paddingTop: theme.spacing.lg }}>
            {error ? (
              <Text style={{ color: theme.colors.danger, fontFamily: theme.typography.fontBold, textAlign: I18nManager.isRTL ? 'right' : 'left' }}>{error}</Text>
            ) : null}
            <Text style={{ color: theme.colors.textPrimary, fontFamily: theme.typography.fontBold, fontSize: theme.typography.sizes.lg, textAlign: I18nManager.isRTL ? 'right' : 'left' }}>العنوان</Text>
            {addresses.length ? (
              <View style={{ marginTop: theme.spacing.sm, gap: theme.spacing.sm }}>
                {addresses.map((a) => {
                  const active = a.id === selectedAddressId;
                  const label = [a.city, a.area, a.street].filter(Boolean).join(' - ') || a.formatted_address || 'عنوان';
                  return (
                    <TouchableOpacity
                      key={a.id}
                      onPress={() => setSelectedAddress(a)}
                      style={{
                        borderWidth: 1,
                        borderColor: active ? theme.colors.accent : theme.colors.cardBorder,
                        backgroundColor: active ? 'rgba(255,214,10,0.12)' : theme.colors.surface,
                        borderRadius: theme.radius.md,
                        padding: theme.spacing.md,
                      }}
                    >
                      <Text style={{ color: theme.colors.textPrimary, fontFamily: theme.typography.fontRegular, textAlign: I18nManager.isRTL ? 'right' : 'left' }}>{label}</Text>
                    </TouchableOpacity>
                  );
                })}
              </View>
            ) : (
              <TouchableOpacity onPress={() => navigation.navigate('Addresses')} style={{ marginTop: theme.spacing.sm, backgroundColor: theme.colors.surface, borderWidth: 1, borderColor: theme.colors.cardBorder, borderRadius: theme.radius.md, padding: theme.spacing.md }}>
                <Text style={{ color: theme.colors.textSecondary, fontFamily: theme.typography.fontRegular, textAlign: I18nManager.isRTL ? 'right' : 'left' }}>لا يوجد عنوان محفوظ. افتح شاشة العناوين.</Text>
              </TouchableOpacity>
            )}
            {selectedAddress ? (
              <View style={{ marginTop: theme.spacing.md, backgroundColor: 'rgba(233,69,96,0.15)', borderWidth: 1, borderColor: theme.colors.accent, borderRadius: theme.radius.md, padding: theme.spacing.md }}>
                <Text style={{ color: theme.colors.textPrimary, fontFamily: theme.typography.fontBold, textAlign: I18nManager.isRTL ? 'right' : 'left' }}>العنوان المختار للطلب</Text>
                <Text style={{ marginTop: 4, color: theme.colors.textSecondary, fontFamily: theme.typography.fontRegular, textAlign: I18nManager.isRTL ? 'right' : 'left' }}>
                  {[selectedAddress.city, selectedAddress.area, selectedAddress.street].filter(Boolean).join(' - ') || selectedAddress.formatted_address || 'عنوان'}
                </Text>
              </View>
            ) : null}
            <Text style={{ marginTop: theme.spacing.lg, color: theme.colors.textPrimary, fontFamily: theme.typography.fontBold, fontSize: theme.typography.sizes.lg, textAlign: I18nManager.isRTL ? 'right' : 'left' }}>ملخص الطلب</Text>
          </View>
        }
        renderItem={({ item }) => (
          <View style={{ marginHorizontal: theme.spacing.lg, marginTop: theme.spacing.sm, backgroundColor: theme.colors.surface, borderWidth: 1, borderColor: theme.colors.cardBorder, borderRadius: theme.radius.md, padding: theme.spacing.md }}>
            <Text style={{ color: theme.colors.textPrimary, fontFamily: theme.typography.fontBold, textAlign: I18nManager.isRTL ? 'right' : 'left' }}>{item?.product?.name || 'منتج'}</Text>
            <Text style={{ marginTop: 4, color: theme.colors.textSecondary, fontFamily: theme.typography.fontRegular, textAlign: I18nManager.isRTL ? 'right' : 'left' }}>الكمية: {item?.quantity || 1}</Text>
            <Text style={{ marginTop: 4, color: theme.colors.textPrimary, fontFamily: theme.typography.fontBold, textAlign: I18nManager.isRTL ? 'right' : 'left' }}>{item?.product?.base_price || 0}</Text>
          </View>
        )}
        ListEmptyComponent={
          <View style={{ marginTop: theme.spacing.xl, alignItems: 'center' }}>
            <Text style={{ color: theme.colors.textSecondary, fontFamily: theme.typography.fontRegular }}>سلتك فارغة حالياً</Text>
          </View>
        }
        ListFooterComponent={<View style={{ height: 140 }} />}
      />
      <View style={{ position: 'absolute', left: 0, right: 0, bottom: 0, backgroundColor: theme.colors.surface, borderTopWidth: 1, borderColor: theme.colors.cardBorder, paddingHorizontal: theme.spacing.lg, paddingTop: theme.spacing.sm, paddingBottom: theme.spacing.lg }}>
        <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
          <Text style={{ color: theme.colors.textSecondary, fontFamily: theme.typography.fontRegular }}>الإجمالي</Text>
          <Text style={{ color: theme.colors.textPrimary, fontFamily: theme.typography.fontBold, fontSize: theme.typography.sizes.lg }}>{subtotal}</Text>
        </View>
        <TouchableOpacity onPress={onPlaceOrder} disabled={placing || !items.length || !selectedAddressId} style={{ marginTop: theme.spacing.md, backgroundColor: placing || !items.length || !selectedAddressId ? theme.colors.surfaceAlt : theme.colors.accent, borderRadius: theme.radius.lg, paddingVertical: theme.spacing.md, alignItems: 'center' }}>
          {placing ? (
            <ActivityIndicator color="#000" />
          ) : (
            <Text style={{ color: '#000', fontFamily: theme.typography.fontBold }}>تأكيد الطلب</Text>
          )}
        </TouchableOpacity>
      </View>
    </View>
  );
}
