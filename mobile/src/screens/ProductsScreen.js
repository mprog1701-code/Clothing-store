import React, { useEffect, useState } from 'react';
import { View, Text, FlatList, TouchableOpacity, ActivityIndicator, RefreshControl, I18nManager } from 'react-native';
import { listProducts } from '../api';
import theme from '../theme';

export default function ProductsScreen({ navigation, route }) {
  const { mode = 'all', categoryId = null, q = '', storeId = null } = route.params || {};
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
      data={items}
      keyExtractor={(item) => String(item.id)}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
      renderItem={({ item }) => (
        <TouchableOpacity
          onPress={() => navigation.navigate('ProductDetail', { productId: item.id })}
          style={{ padding: theme.spacing.md, borderBottomWidth: 1, borderColor: theme.colors.cardBorder, backgroundColor: theme.colors.background }}
        >
          <Text style={{ fontFamily: theme.typography.fontBold, color: theme.colors.textPrimary, textAlign: I18nManager.isRTL ? 'right' : 'left' }}>{item.name}</Text>
          <Text style={{ color: theme.colors.textSecondary, fontFamily: theme.typography.fontRegular, textAlign: I18nManager.isRTL ? 'right' : 'left' }}>{item.description}</Text>
        </TouchableOpacity>
      )}
    />
  );
}
