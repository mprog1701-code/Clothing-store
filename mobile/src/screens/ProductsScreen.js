import React, { useEffect, useLayoutEffect, useMemo, useState } from 'react';
import { View, Text, FlatList, ActivityIndicator, RefreshControl, I18nManager, StyleSheet } from 'react-native';
import { listProducts } from '../api';
import theme from '../theme';
import ProductCard from '../components/ProductCard';
import { SafeAreaView } from 'react-native-safe-area-context';
import EmptyState from '../components/EmptyState';
import { useAuth } from '../auth/AuthContext';
import LoginRequiredSheet from '../components/LoginRequiredSheet';

export default function ProductsScreen({ navigation, route }) {
  const { accessToken } = useAuth();
  const params = route.params || {};
  const filterType = params.filterType || '';
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
  const type = params.type || typeFromFilterType[filterType] || typeFromMode[legacyMode] || 'all_products';
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

  const load = async () => {
    setError('');
    setLoading(true);
    try {
      const params = {};
      params.type = type;
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
      const arr = Array.isArray(data) ? data : (data.results || []);
      if (__DEV__) {
        try {
          console.log('[ProductsScreen] type=', type, 'params=', params, 'count=', arr.length);
        } catch {}
      }
      setItems(arr || []);
    } catch (e) {
      setError('تعذر تحميل المنتجات. يرجى المحاولة لاحقاً.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    load();
  }, [type, categoryId, q, storeId, filterType]);

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
      return res;
    }
    if (type === 'flash_sales') {
      const res = items.filter((p) => p?.is_flash || hasTag(p, 'flash') || String(p?.badge || '').includes('فلاش'));
      return res;
    }
    if (type === 'new_arrivals') {
      const res = items.filter((p) => p?.is_new || hasTag(p, 'new') || hasTag(p, 'جديد'));
      return res;
    }
    if (type === 'promotion_banners') {
      const res = items.filter((p) => p?.is_featured || hasTag(p, 'banner') || hasTag(p, 'promo'));
      return res;
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
              addToCart={() => {
                if (!accessToken) {
                  requestLogin({ name: 'ProductDetail', params: { productId: item.id } });
                  return;
                }
                navigation.navigate('Cart');
              }}
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
