import React, { useEffect, useLayoutEffect, useMemo, useState } from 'react';
import { View, Text, FlatList, ActivityIndicator, RefreshControl, I18nManager, StyleSheet, Alert } from 'react-native';
import { addCartItemVariant, listProducts } from '../api';
import theme from '../theme';
import ProductCard from '../components/ProductCard';
import { SafeAreaView } from 'react-native-safe-area-context';
import EmptyState from '../components/EmptyState';
import { useAuth } from '../auth/AuthContext';
import LoginRequiredSheet from '../components/LoginRequiredSheet';
import { useCart } from '../cart/CartContext';

export default function ProductsScreen({ navigation, route }) {
  const { accessToken } = useAuth();
  const { refreshCartCount } = useCart();
  const params = route.params || {};
  const filterType = params.filterType ?? null;
  const legacyMode = params.mode || 'all';
  const typeFromMode = {
    all: 'all_products',
    offers: 'offers',
    flash: 'flash_sales',
    banners: 'promotion_banners',
    category: 'category',
    categories: 'all_categories',
    search: 'search_results',
  };
  const typeFromFilterType = {
    flash_sale: 'flash_sales',
    new_arrival: 'new_arrivals',
    offer: 'offers',
    promotion_banner: 'promotion_banners',
  };
  const explicitType = params.type || null;
  const type = typeFromFilterType[filterType] || explicitType || typeFromMode[legacyMode] || 'all_products';
  const categoryId = params.categoryId ?? null;
  const categoryLabel = params.categoryLabel || '';
  const q = params.q || '';
  const storeId = params.storeId ?? null;
  const listTitle = params.listTitle || params.title || '';
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState('');
  const [loginSheetVisible, setLoginSheetVisible] = useState(false);
  const [pendingNext, setPendingNext] = useState(null);

  const extractProductsArray = (payload) => {
    if (Array.isArray(payload)) return payload;
    if (Array.isArray(payload?.products)) return payload.products;
    if (Array.isArray(payload?.results)) return payload.results;
    if (Array.isArray(payload?.items)) return payload.items;
    if (Array.isArray(payload?.data)) return payload.data;
    return [];
  };

  const mapProduct = (item, index) => {
    const id = item?.id ?? item?.product_id ?? item?.productId ?? `tmp-${index}`;
    const mainImage = item?.main_image;
    const resolvedImage =
      item?.image ||
      item?.image_url ||
      item?.thumbnail ||
      item?.imageUrl ||
      mainImage?.image_url ||
      mainImage?.url ||
      item?.main_image_url ||
      (Array.isArray(item?.images) ? (item.images[0]?.url || item.images[0]?.image_url || item.images[0]) : '');
    return {
      ...item,
      id,
      name: item?.name || item?.title || item?.product_name || 'منتج',
      price: item?.price ?? item?.base_price ?? item?.final_price ?? 0,
      image: resolvedImage || '',
    };
  };

  const load = async () => {
    setError('');
    setLoading(true);
    try {
      const params = {};
      if (filterType) {
        params.filterType = filterType;
      }
      if (!filterType && explicitType) {
        params.type = explicitType;
      }
      if (type === 'category' && categoryId) {
        params.category = categoryId;
      } else if (type === 'search_results' && q) {
        params.search = q;
      } else if (type === 'new_arrivals') {
        params.is_new = true;
        params.ordering = '-created_at';
      } else if (type === 'flash_sales') {
        params.is_flash = true;
      } else if (type === 'promotion_banners') {
        params.is_featured = true;
      } else if (type === 'offers') {
        params.on_offer = true;
      }
      if (storeId) {
        params.store = storeId;
      }
      const data = await listProducts(params);
      const arr = extractProductsArray(data);
      const mapped = arr.map(mapProduct);
      if (__DEV__) {
        try {
          console.log('[ProductsScreen] type=', type, 'filterType=', filterType, 'params=', params, 'count=', mapped.length);
          console.log('[ProductsScreen] response.data=', data);
          if (mapped[0]) console.log('[ProductsScreen] sample item=', mapped[0]);
        } catch {}
      }
      setItems(mapped);
    } catch (e) {
      console.error('[ProductsScreen] load failed', {
        message: e?.message,
        status: e?.response?.status,
        data: e?.response?.data,
        routeParams: params,
      });
      setError('تعذر تحميل المنتجات. يرجى المحاولة لاحقاً.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    load();
  }, [type, categoryId, q, storeId, filterType, explicitType]);

  const viewTitle = useMemo(() => {
    if (listTitle) return listTitle;
    if (type === 'offers') return 'العروض';
    if (type === 'flash_sales') return 'عروض فلاش';
    if (type === 'promotion_banners') return 'بنرات ترويجية';
    if (type === 'new_arrivals') return 'وصل حديثاً';
    if (type === 'all_categories') return 'كل الأقسام';
    if (type === 'category' && categoryLabel) return categoryLabel;
    if (type === 'search_results' && q) return `نتائج البحث: ${q}`;
    return 'المنتجات';
  }, [categoryLabel, listTitle, q, type]);

  useLayoutEffect(() => {
    navigation.setOptions({ title: viewTitle });
  }, [navigation, viewTitle]);

  const filteredItems = useMemo(() => {
    const hasTag = (product, expected) => {
      const raw = `${product?.badge || ''} ${product?.tag || ''} ${product?.tags || ''}`.toLowerCase();
      return raw.includes(expected);
    };
    if (type === 'offers') {
      const res = items.filter((p) => p?.oldPrice || p?.old_price || p?.discount_price || p?.offer_price || hasTag(p, 'offer'));
      return res.length ? res : items;
    }
    if (type === 'flash_sales') {
      const res = items.filter((p) => p?.is_flash || p?.discount_price || p?.offer_price || hasTag(p, 'flash') || String(p?.badge || '').includes('فلاش'));
      if (res.length) return res;
      const sorted = [...items].sort((a, b) => new Date(b?.created_at || 0).getTime() - new Date(a?.created_at || 0).getTime());
      return sorted.slice(0, 12);
    }
    if (type === 'new_arrivals') {
      const res = items.filter((p) => p?.is_new || hasTag(p, 'new') || hasTag(p, 'جديد'));
      if (res.length) return res;
      return [...items].sort((a, b) => new Date(b?.created_at || 0).getTime() - new Date(a?.created_at || 0).getTime());
    }
    if (type === 'promotion_banners') {
      const res = items.filter((p) => p?.is_featured || hasTag(p, 'banner') || hasTag(p, 'promo'));
      return res.length ? res : items;
    }
    if (type === 'category' && !categoryId && categoryLabel) {
      const normalized = categoryLabel.trim();
      const res = items.filter((p) => String(p?.category || p?.category_name || '').includes(normalized));
      return res.length ? res : items;
    }
    return items;
  }, [categoryId, categoryLabel, items, type]);

  const onRefresh = () => {
    setRefreshing(true);
    load();
  };
  const requestLogin = (next) => {
    setPendingNext(next || { name: route.name, params: route.params || {} });
    setLoginSheetVisible(true);
  };

  const resolveDefaultVariantId = (product) => {
    const variants = Array.isArray(product?.variants) ? product.variants : [];
    const available = variants.find((v) => Number(v?.stock_qty ?? 1) > 0 && Number(v?.id) > 0);
    const fallback = variants.find((v) => Number(v?.id) > 0);
    return available?.id || fallback?.id || null;
  };

  const handleQuickAddToCart = async (item) => {
    if (!accessToken) {
      requestLogin({
        action: 'add_to_cart',
        product_id: item?.id,
        variant_id: resolveDefaultVariantId(item),
        quantity: 1,
        returnTo: { name: route.name, params: route.params || {} },
      });
      return;
    }
    try {
      await addCartItemVariant({
        product_id: item?.id,
        variant_id: resolveDefaultVariantId(item),
        quantity: 1,
        product_snapshot: item,
      });
      await refreshCartCount();
      Alert.alert('تم', 'تمت إضافة المنتج إلى السلة');
    } catch (e) {
      const code = String(e?.response?.data?.code || '').toUpperCase();
      if (code === 'VARIANT_REQUIRED') {
        navigation.navigate('ProductDetail', { productId: item?.id });
        return;
      }
      Alert.alert('تنبيه', 'تعذر إضافة المنتج حالياً');
    }
  };

  if (loading) {
    return (
      <SafeAreaView style={{ flex: 1, alignItems: 'center', justifyContent: 'center', backgroundColor: theme.colors.background }}>
        <ActivityIndicator />
        <Text style={{ marginTop: 8, color: theme.colors.textSecondary, fontFamily: theme.typography.fontRegular }}>جاري تحميل المنتجات...</Text>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: theme.colors.background }}>
      <FlatList
        data={filteredItems}
        keyExtractor={(item) => String(item.id)}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
        numColumns={2}
        contentContainerStyle={styles.list}
        columnWrapperStyle={styles.row}
        removeClippedSubviews
        initialNumToRender={8}
        windowSize={7}
        ListHeaderComponent={
          <View style={styles.header}>
            <Text style={styles.title}>{viewTitle}</Text>
            {type === 'offers' && <Text style={styles.subtitle}>خصومات مميزة لهذا اليوم</Text>}
            {type === 'flash_sales' && <Text style={styles.subtitle}>عروض محدودة الوقت</Text>}
            {type === 'new_arrivals' && <Text style={styles.subtitle}>اكتشف أحدث المنتجات المضافة</Text>}
            {type === 'promotion_banners' && <Text style={styles.subtitle}>منتجات مرتبطة بالبنرات الترويجية</Text>}
            {type === 'category' && categoryLabel ? (
              <View style={styles.chip}>
                <Text style={styles.chipText}>{categoryLabel}</Text>
              </View>
            ) : null}
            {type === 'search_results' && q ? <Text style={styles.subtitle}>نتائج البحث عن "{q}"</Text> : null}
            {refreshing ? (
              <View style={styles.filteringState}>
                <ActivityIndicator size="small" color={theme.colors.accent} />
                <Text style={styles.filteringStateText}>جاري تحديث النتائج...</Text>
              </View>
            ) : null}
          </View>
        }
        ListEmptyComponent={
          <EmptyState
            icon="shopping-outline"
            title="لا توجد منتجات حالياً"
            subtitle={error || 'جرّب تحديث الصفحة أو تغيير الفئة'}
            ctaLabel="إعادة المحاولة"
            onPress={load}
          />
        }
        renderItem={({ item }) => (
          <View style={styles.cardWrap}>
            <ProductCard
              product={item}
              addToCart={() => handleQuickAddToCart(item)}
            />
          </View>
        )}
      />
      <LoginRequiredSheet
        visible={loginSheetVisible}
        onClose={() => setLoginSheetVisible(false)}
        onLogin={() => {
          setLoginSheetVisible(false);
          navigation.replace('Login', pendingNext ? { next: pendingNext } : undefined);
        }}
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  list: {
    paddingHorizontal: 16,
    paddingVertical: theme.spacing.md,
    backgroundColor: theme.colors.background,
  },
  row: {
    justifyContent: 'space-between',
  },
  header: {
    marginBottom: theme.spacing.md,
  },
  title: {
    color: theme.colors.textPrimary,
    fontFamily: theme.typography.fontBold,
    fontSize: theme.typography.sizes.lg,
    textAlign: I18nManager.isRTL ? 'right' : 'left',
    marginBottom: 4,
  },
  subtitle: {
    color: theme.colors.textSecondary,
    fontFamily: theme.typography.fontRegular,
    textAlign: I18nManager.isRTL ? 'right' : 'left',
  },
  filteringState: {
    marginTop: theme.spacing.sm,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    alignSelf: 'flex-end',
  },
  filteringStateText: {
    color: theme.colors.textSecondary,
    fontFamily: theme.typography.fontRegular,
    fontSize: theme.typography.sizes.sm,
  },
  chip: {
    alignSelf: 'flex-end',
    marginTop: theme.spacing.sm,
    backgroundColor: theme.colors.surface,
    borderRadius: 18,
    borderWidth: 1,
    borderColor: theme.colors.cardBorder,
    paddingHorizontal: theme.spacing.md,
    paddingVertical: theme.spacing.xs,
  },
  chipText: {
    color: theme.colors.textPrimary,
    fontFamily: theme.typography.fontRegular,
    fontSize: theme.typography.sizes.sm,
  },
  cardWrap: {
    width: '48%',
    marginBottom: theme.spacing.md,
  },
});
