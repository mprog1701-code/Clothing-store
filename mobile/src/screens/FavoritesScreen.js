import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { SafeAreaView } from 'react-native-safe-area-context';
import { View, Text, FlatList, TouchableOpacity, Image, I18nManager, RefreshControl } from 'react-native';
import theme from '../theme';
import EmptyState from '../components/EmptyState';
import { getFavorites, toggleFavoriteProduct } from '../favorites/storage';
import { API_BASE_URL } from '../api/config';

export default function FavoritesScreen({ navigation }) {
  const [items, setItems] = useState([]);
  const [refreshing, setRefreshing] = useState(false);

  const toAbsoluteImageUri = useCallback((value) => {
    let raw = String(value || '').trim();
    raw = raw.replace(/^[`'"\s]+|[`'"\s]+$/g, '');
    if (!raw) return '';
    if (/^https?:\/\//i.test(raw)) return raw;
    const base = String(API_BASE_URL || '').replace(/\/+$/g, '');
    const path = raw.startsWith('/') ? raw : `/${raw}`;
    return base ? `${base}${path}` : raw;
  }, []);

  const load = useCallback(async () => {
    const arr = await getFavorites();
    setItems(arr);
  }, []);

  useEffect(() => {
    const unsub = navigation.addListener('focus', load);
    return unsub;
  }, [navigation, load]);

  const onRefresh = async () => {
    setRefreshing(true);
    await load();
    setRefreshing(false);
  };

  const sorted = useMemo(
    () => [...items].sort((a, b) => new Date(b?.created_at || 0).getTime() - new Date(a?.created_at || 0).getTime()),
    [items]
  );

  const Row = ({ item }) => {
    const imageUri = toAbsoluteImageUri(item?.image_url);
    return (
      <View style={{ paddingHorizontal: 16, paddingTop: theme.spacing.md }}>
        <TouchableOpacity
          onPress={() => navigation.navigate('ProductDetail', { productId: Number(item?.id) })}
          style={{ borderRadius: theme.radius.md, borderWidth: 1, borderColor: theme.colors.cardBorder, backgroundColor: theme.colors.surface, padding: theme.spacing.md, flexDirection: 'row', alignItems: 'center' }}
        >
          {imageUri ? (
            <Image source={{ uri: imageUri }} style={{ width: 68, height: 68, borderRadius: theme.radius.md, marginLeft: I18nManager.isRTL ? theme.spacing.md : 0, marginRight: I18nManager.isRTL ? 0 : theme.spacing.md }} />
          ) : (
            <View style={{ width: 68, height: 68, borderRadius: theme.radius.md, backgroundColor: theme.colors.surfaceAlt, marginLeft: I18nManager.isRTL ? theme.spacing.md : 0, marginRight: I18nManager.isRTL ? 0 : theme.spacing.md }} />
          )}
          <View style={{ flex: 1 }}>
            <Text numberOfLines={2} style={{ color: theme.colors.textPrimary, fontFamily: theme.typography.fontBold, textAlign: I18nManager.isRTL ? 'right' : 'left' }}>{item?.name || 'منتج'}</Text>
            <Text style={{ marginTop: 4, color: theme.colors.accent, fontFamily: theme.typography.fontBold, textAlign: I18nManager.isRTL ? 'right' : 'left' }}>{Number(item?.price || 0).toLocaleString('en-US')} د.ع</Text>
          </View>
          <TouchableOpacity
            onPress={async () => {
              await toggleFavoriteProduct(item);
              await load();
            }}
            style={{ paddingHorizontal: theme.spacing.md, paddingVertical: 8, borderRadius: theme.radius.md, borderWidth: 1, borderColor: theme.colors.cardBorder }}
          >
            <Text style={{ color: theme.colors.textPrimary, fontFamily: theme.typography.fontBold }}>حذف</Text>
          </TouchableOpacity>
        </TouchableOpacity>
      </View>
    );
  };

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: theme.colors.background }}>
      <FlatList
        data={sorted}
        keyExtractor={(it) => String(it?.id)}
        renderItem={Row}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
        ListEmptyComponent={
          <View style={{ flex: 1, justifyContent: 'center', marginTop: 80 }}>
            <EmptyState
              icon="heart-outline"
              title="المفضلة فارغة حالياً"
              subtitle="احفظ المنتجات التي تعجبك لتظهر هنا"
              ctaLabel="تصفح المنتجات"
              onPress={() => navigation.navigate('Home')}
            />
          </View>
        }
        contentContainerStyle={{ paddingBottom: theme.spacing.lg, flexGrow: sorted.length ? 0 : 1 }}
      />
    </SafeAreaView>
  );
}
