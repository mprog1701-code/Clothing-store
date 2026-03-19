import React, { useEffect, useMemo, useState, useCallback } from 'react';
import { View, Text, FlatList, TouchableOpacity, Image, I18nManager, ActivityIndicator, RefreshControl, Alert } from 'react-native';
import theme from '../theme';
import { clearTokens } from '../auth/tokenStorage';
import { useAuth } from '../auth/AuthContext';
import { useCart } from '../cart/CartContext';
import { getCart, getProduct, updateCartItem, removeCartItem } from '../api';
import { API_BASE_URL } from '../api/config';
import LoginRequiredSheet from '../components/LoginRequiredSheet';

export default function CartScreen({ navigation }) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState('');
  const [requireLogin, setRequireLogin] = useState(false);
  const [sheetVisible, setSheetVisible] = useState(false);
  const { isHydrating, accessToken, user, isAuthenticated } = useAuth();
  const { setCartCount, refreshCartCount } = useCart();
  const resolveSelectedVariant = useCallback((item) => {
    const direct = item?.variant || null;
    const directId = Number(direct?.id || item?.variant_id || 0);
    const variants = Array.isArray(item?.product?.variants) ? item.product.variants : [];
    if (direct?.color_name || direct?.size || Number.isFinite(Number(direct?.stock_qty))) {
      return { ...direct, id: directId || direct?.id || null };
    }
    if (directId > 0) {
      const matched = variants.find((v) => Number(v?.id) === directId);
      if (matched) return matched;
    }
    if (direct && directId > 0) return { ...direct, id: directId };
    return null;
  }, []);
  const hydrateCartItems = useCallback(async (arr) => {
    const source = Array.isArray(arr) ? arr : [];
    const productIds = Array.from(
      new Set(
        source
          .map((it) => Number(it?.product?.id))
          .filter((id) => Number.isFinite(id) && id > 0)
      )
    );
    if (!productIds.length) return source;
    const productMap = new Map();
    await Promise.all(
      productIds.map(async (pid) => {
        try {
          const p = await getProduct(pid);
          if (p?.id) productMap.set(Number(p.id), p);
        } catch {}
      })
    );
    return source.map((it) => {
      const pid = Number(it?.product?.id);
      const product = productMap.get(pid);
      if (!product) return it;
      const variantId = Number(it?.variant?.id || it?.variant_id || 0);
      const variants = Array.isArray(product?.variants) ? product.variants : [];
      const selectedVariant = variantId > 0 ? variants.find((v) => Number(v?.id) === variantId) : null;
      return {
        ...it,
        product: {
          ...(it?.product || {}),
          ...product,
          main_image: product?.main_image || it?.product?.main_image || null,
        },
        variant: selectedVariant || it?.variant || null,
      };
    });
  }, []);
  const resolveMaxQuantity = useCallback((item) => {
    const variant = resolveSelectedVariant(item);
    const variantStock = Number(variant?.stock_qty);
    if (Number.isFinite(variantStock) && variantStock > 0) return variantStock;
    const productStock = Number(item?.product?.stock_qty);
    if (Number.isFinite(productStock) && productStock > 0) return productStock;
    return null;
  }, [resolveSelectedVariant]);
  const normalizeCartItems = useCallback((arr) => {
    const source = Array.isArray(arr) ? arr : [];
    return source.map((it) => {
      const maxQty = resolveMaxQuantity(it);
      if (!maxQty) return it;
      const qty = Number(it?.quantity || 1);
      const safeQty = Math.max(1, Math.min(maxQty, Number.isFinite(qty) ? qty : 1));
      if (safeQty === qty) return it;
      return { ...it, quantity: safeQty };
    });
  }, [resolveMaxQuantity]);
  const load = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await getCart();
      const arrRaw = Array.isArray(data) ? data : (data.items || data.results || []);
      const arrHydrated = await hydrateCartItems(arrRaw || []);
      const arr = normalizeCartItems(arrHydrated || []);
      setItems(arr || []);
      setCartCount((arr || []).reduce((sum, it) => sum + Number(it?.quantity || 0), 0));
      setRequireLogin(false);
      for (const it of (arr || [])) {
        const oldQty = Number(arrRaw?.find((x) => String(x?.id) === String(it?.id))?.quantity || 0);
        if (oldQty > 0 && oldQty !== Number(it?.quantity || 0)) {
          try {
            await updateCartItem(it.id, Number(it.quantity || 1));
          } catch {}
        }
      }
    } catch (e) {
      const status = e?.response?.status;
      if (status === 401 || status === 403) {
        await clearTokens();
        setRequireLogin(true);
        setError('');
        setItems([]);
      } else {
        if (__DEV__) {
          console.error('[CartScreen] load failed', {
            message: e?.message,
            status,
            data: e?.response?.data,
          });
        }
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
      const arrRaw = Array.isArray(data) ? data : (data.items || data.results || []);
      const arrHydrated = await hydrateCartItems(arrRaw || []);
      const arr = normalizeCartItems(arrHydrated || []);
      setItems(arr || []);
      setCartCount((arr || []).reduce((sum, it) => sum + Number(it?.quantity || 0), 0));
      setRequireLogin(false);
      setError('');
    } catch (e) {
      const status = e?.response?.status;
      if (status === 401 || status === 403) {
        await clearTokens();
        setRequireLogin(true);
        setItems([]);
        setError('');
      } else if (__DEV__) {
        console.error('[CartScreen] refresh failed', {
          message: e?.message,
          status,
          data: e?.response?.data,
        });
      }
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
  const toAbsoluteImageUri = useCallback((value) => {
    let raw = String(value || '').trim();
    raw = raw.replace(/^[`'"\s]+|[`'"\s]+$/g, '');
    if (!raw) return '';
    if (/^https?:\/\//i.test(raw)) return raw;
    const base = String(API_BASE_URL || '').replace(/\/+$/g, '');
    const path = raw.startsWith('/') ? raw : `/${raw}`;
    return base ? `${base}${path}` : raw;
  }, []);
  const resolveCartItemImage = useCallback((item) => {
    const variant = resolveSelectedVariant(item);
    const productImages = Array.isArray(item?.product?.images) ? item.product.images : [];
    const variantId = Number(variant?.id || item?.variant_id || 0);
    const colorAttrId = Number(variant?.color_attr_id || 0);
    const colorObjId = Number(variant?.color_obj_id || 0);
    const colorKey = String(variant?.color_key || '').trim();
    const colorName = String(variant?.color_name || '').trim();
    const byVariant = variantId > 0
      ? productImages.filter((im) => Number(im?.variant_id || 0) === variantId)
      : [];
    const byColor = productImages.filter((im) => {
      const imColorAttrId = Number(im?.color_attr_id || 0);
      const imColorObjId = Number(im?.color_obj_id || 0);
      const imColorId = Number(im?.color_id || 0);
      const imColorKey = String(im?.color_key || '').trim();
      const imColorName = String(im?.color_name || '').trim();
      if (colorAttrId > 0 && imColorAttrId === colorAttrId) return true;
      if (colorObjId > 0 && (imColorObjId === colorObjId || imColorId === colorObjId)) return true;
      if (colorKey && imColorKey && imColorKey === colorKey) return true;
      if (colorName && imColorName && imColorName === colorName) return true;
      return false;
    });
    const pickImageFromList = (arr) => {
      if (!Array.isArray(arr) || !arr.length) return null;
      const main = arr.find((im) => im?.is_main);
      return main || arr[0];
    };
    const pickedByVariant = pickImageFromList(byVariant);
    const pickedByColor = pickImageFromList(byColor);
    const pickedGeneric = pickImageFromList(productImages);
    const candidates = [
      variant?.images?.[0]?.image_url,
      variant?.images?.[0]?.url,
      variant?.images?.[0]?.image,
      pickedByVariant?.image_url,
      pickedByVariant?.url,
      pickedByVariant?.image,
      pickedByColor?.image_url,
      pickedByColor?.url,
      pickedByColor?.image,
      item?.product?.main_image?.image_url,
      item?.product?.main_image?.url,
      item?.product?.main_image?.image,
      item?.product?.image_url,
      item?.product?.image,
      item?.product?.thumbnail,
      pickedGeneric?.image_url,
      pickedGeneric?.url,
      pickedGeneric?.image,
    ];
    for (const c of candidates) {
      const uri = toAbsoluteImageUri(c);
      if (uri) return uri;
    }
    return '';
  }, [resolveSelectedVariant, toAbsoluteImageUri]);
  const resolveCartDetailsText = useCallback((item) => {
    const variant = resolveSelectedVariant(item);
    const color =
      variant?.color_name ||
      variant?.color?.name ||
      '';
    const size = variant?.size || '';
    const parts = [];
    if (color) parts.push(`اللون: ${color}`);
    if (size) parts.push(`المقاس: ${size}`);
    if (parts.length) return parts.join(' • ');
    const explicit = String(item?.variant_text || '').trim();
    if (explicit) return explicit;
    const extra = [];
    const category = String(item?.product?.category_name || item?.product?.category || '').trim();
    const store = String(item?.product?.store?.name || '').trim();
    if (category) extra.push(`الفئة: ${category}`);
    if (store) extra.push(`المتجر: ${store}`);
    return extra.join(' • ');
  }, [resolveSelectedVariant]);
  const inc = useCallback(async (id) => {
    const current = items.find(x => x.id === id);
    const maxQty = resolveMaxQuantity(current);
    const currentQty = Number(current?.quantity || 1);
    if (maxQty && currentQty >= maxQty) {
      Alert.alert('تنبيه', `الكمية القصوى المتاحة هي ${maxQty}`);
      return;
    }
    const nextQty = currentQty + 1;
    setItems(prev => prev.map(it => it.id === id ? { ...it, quantity: nextQty } : it));
    try {
      await updateCartItem(id, nextQty);
      refreshCartCount();
    } catch {
      Alert.alert('خطأ', 'فشل تحديث الكمية'); load();
    }
  }, [items, refreshCartCount, resolveMaxQuantity]);
  const dec = useCallback(async (id) => {
    const current = items.find(x => x.id === id);
    const nextQty = Math.max(1, (current?.quantity || 1) - 1);
    setItems(prev => prev.map(it => it.id === id ? { ...it, quantity: nextQty } : it));
    try {
      await updateCartItem(id, nextQty);
      refreshCartCount();
    } catch {
      Alert.alert('خطأ', 'فشل تحديث الكمية'); load();
    }
  }, [items, refreshCartCount]);
  const del = useCallback(async (id) => {
    const old = items;
    setItems(prev => prev.filter(it => it.id !== id));
    try {
      await removeCartItem(id);
      refreshCartCount();
      Alert.alert('تم', 'تم حذف المنتج من السلة');
    } catch {
      setItems(old);
      Alert.alert('خطأ', 'تعذر حذف المنتج، حاول مرة أخرى');
    }
  }, [items, refreshCartCount]);
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
  const Row = ({ item }) => {
    const imageUri = resolveCartItemImage(item);
    const detailsText = resolveCartDetailsText(item);
    return (
      <TouchableOpacity
        activeOpacity={0.9}
        onPress={() => navigation.navigate('ProductDetail', { productId: item?.product?.id })}
        style={{ flexDirection: 'row', padding: theme.spacing.md, borderBottomWidth: 1, borderColor: theme.colors.cardBorder, backgroundColor: theme.colors.surface }}
      >
        {imageUri ? (
          <Image source={{ uri: imageUri }} style={{ width: 80, height: 80, borderRadius: theme.radius.md, marginLeft: I18nManager.isRTL ? theme.spacing.md : 0, marginRight: I18nManager.isRTL ? 0 : theme.spacing.md }} />
        ) : (
          <View style={{ width: 80, height: 80, borderRadius: theme.radius.md, backgroundColor: theme.colors.surfaceAlt, marginLeft: I18nManager.isRTL ? theme.spacing.md : 0, marginRight: I18nManager.isRTL ? 0 : theme.spacing.md }} />
        )}
        <View style={{ flex: 1 }}>
          <Text numberOfLines={2} style={{ color: theme.colors.textPrimary, fontFamily: theme.typography.fontBold, textAlign: I18nManager.isRTL ? 'right' : 'left' }}>{item.product?.name || 'منتج'}</Text>
          {detailsText ? (
            <Text style={{ color: theme.colors.textSecondary, fontFamily: theme.typography.fontRegular, marginTop: 4, textAlign: I18nManager.isRTL ? 'right' : 'left' }}>{detailsText}</Text>
          ) : null}
          <View style={{ flexDirection: 'row', marginTop: theme.spacing.sm, alignItems: 'center' }}>
            <TouchableOpacity onPress={(event) => { event?.stopPropagation?.(); dec(item.id); }} disabled={item.quantity <= 1} style={{ paddingHorizontal: theme.spacing.md, paddingVertical: 6, borderRadius: theme.radius.md, borderWidth: 1, borderColor: theme.colors.cardBorder, backgroundColor: item.quantity <= 1 ? theme.colors.surfaceAlt : theme.colors.surface }}>
              <Text style={{ color: theme.colors.textPrimary, fontFamily: theme.typography.fontBold }}>−</Text>
            </TouchableOpacity>
            <Text style={{ marginHorizontal: theme.spacing.md, color: theme.colors.textPrimary, fontFamily: theme.typography.fontBold }}>{item.quantity}</Text>
            <TouchableOpacity onPress={(event) => { event?.stopPropagation?.(); inc(item.id); }} style={{ paddingHorizontal: theme.spacing.md, paddingVertical: 6, borderRadius: theme.radius.md, borderWidth: 1, borderColor: theme.colors.cardBorder, backgroundColor: theme.colors.surface }}>
              <Text style={{ color: theme.colors.textPrimary, fontFamily: theme.typography.fontBold }}>+</Text>
            </TouchableOpacity>
            <View style={{ flex: 1 }} />
            <TouchableOpacity onPress={(event) => { event?.stopPropagation?.(); del(item.id); }} style={{ paddingHorizontal: theme.spacing.md, paddingVertical: 6, borderRadius: theme.radius.md, borderWidth: 1, borderColor: theme.colors.cardBorder, backgroundColor: theme.colors.surfaceAlt }}>
              <Text style={{ color: theme.colors.danger, fontFamily: theme.typography.fontBold }}>حذف</Text>
            </TouchableOpacity>
          </View>
        </View>
      </TouchableOpacity>
    );
  };
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
