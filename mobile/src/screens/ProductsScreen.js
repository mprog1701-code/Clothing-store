import React, { useEffect, useMemo, useState } from 'react';
import { View, Text, FlatList, TouchableOpacity, ActivityIndicator, RefreshControl, I18nManager, StyleSheet } from 'react-native';
import { listProducts } from '../api';
import theme from '../theme';
import ProductCard from '../components/ProductCard';

export default function ProductsScreen({ navigation, route }) {
  const { mode = 'all', categoryId = null, q = '', storeId = null, title = '', categoryLabel = '' } = route.params || {};
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState('');

  const load = async () => {
    setError('');
    setLoading(true);
    try {
      const params = {};
      if (mode === 'category' && categoryId) {
        params.category = categoryId;
      } else if (mode === 'search' && q) {
        params.search = q;
      } else if (storeId) {
        params.store = storeId;
      }
      const data = await listProducts(params);
      const arr = Array.isArray(data) ? data : (data.results || []);
      if (__DEV__) {
        try {
          console.log('[ProductsScreen] mode=', mode, 'params=', params, 'count=', arr.length);
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
  }, [mode, categoryId, q, storeId]);

  const viewTitle = useMemo(() => {
    if (title) return title;
    if (mode === 'offers') return 'العروض';
    if (mode === 'flash') return 'عروض فلاش';
    if (mode === 'category' && categoryLabel) return categoryLabel;
    if (mode === 'search' && q) return `نتائج البحث: ${q}`;
    return 'المنتجات';
  }, [categoryLabel, mode, q, title]);

  const filteredItems = useMemo(() => {
    if (mode === 'offers') {
      const res = items.filter((p) => p?.oldPrice || p?.badge);
      return res.length ? res : items;
    }
    if (mode === 'flash') {
      const res = items.filter((p) => p?.is_flash || p?.badge);
      return res.length ? res : items;
    }
    return items;
  }, [items, mode]);

  const onRefresh = () => {
    setRefreshing(true);
    load();
  };

  if (loading) {
    return (
      <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center', backgroundColor: theme.colors.background }}>
        <ActivityIndicator />
        <Text style={{ marginTop: 8, color: theme.colors.textSecondary, fontFamily: theme.typography.fontRegular }}>جاري تحميل المنتجات...</Text>
      </View>
    );
  }

  if (!items.length) {
    return (
      <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center', backgroundColor: theme.colors.background }}>
        <Text style={{ color: theme.colors.textSecondary, fontFamily: theme.typography.fontRegular }}>لا توجد منتجات.</Text>
        <TouchableOpacity onPress={load} style={{ marginTop: theme.spacing.md, paddingVertical: theme.spacing.sm, paddingHorizontal: theme.spacing.md, borderRadius: theme.radius.md, backgroundColor: theme.colors.accent }}>
          <Text style={{ color: '#000', fontFamily: theme.typography.fontBold }}>إعادة المحاولة</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <FlatList
      data={filteredItems}
      keyExtractor={(item) => String(item.id)}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
      numColumns={2}
      contentContainerStyle={styles.list}
      columnWrapperStyle={styles.row}
      ListHeaderComponent={
        <View style={styles.header}>
          <Text style={styles.title}>{viewTitle}</Text>
          {mode === 'offers' && <Text style={styles.subtitle}>خصومات مميزة لهذا اليوم</Text>}
          {mode === 'flash' && <Text style={styles.subtitle}>عروض محدودة الوقت</Text>}
          {mode === 'category' && categoryLabel ? (
            <View style={styles.chip}>
              <Text style={styles.chipText}>{categoryLabel}</Text>
            </View>
          ) : null}
          {mode === 'search' && q ? <Text style={styles.subtitle}>نتائج البحث عن "{q}"</Text> : null}
        </View>
      }
      renderItem={({ item }) => (
        <View style={styles.cardWrap}>
          <ProductCard product={item} addToCart={() => navigation.navigate('Cart')} />
        </View>
      )}
    />
  );
}

const styles = StyleSheet.create({
  list: {
    padding: theme.spacing.md,
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
    marginBottom: theme.spacing.md,
  },
});
