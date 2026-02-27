import React, { useEffect, useState } from 'react';
import { View, Text, FlatList, TouchableOpacity, Image, I18nManager, ActivityIndicator, RefreshControl, Modal } from 'react-native';
import theme from '../theme';
import { listStores, listTopStores, listAds } from '../api';
import SearchBar from '../components/SearchBar';
import AsyncStorage from '@react-native-async-storage/async-storage';
import AdBannerDismissible from '../components/AdBannerDismissible';

const filters = [
  { key: 'top', label: 'الأعلى تقييماً' },
  { key: 'near', label: 'الأقرب' },
  { key: 'fast', label: 'التوصيل الأسرع' },
  { key: 'open', label: 'مفتوح الآن' },
];

export default function StoresScreen({ navigation }) {
  const [q, setQ] = useState('');
  const [active, setActive] = useState('rating');
  const [stores, setStores] = useState([]);
  const [featured, setFeatured] = useState([]);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const [sheetOpen, setSheetOpen] = useState(false);

  const load = async (opts = {}) => {
    const nextPage = opts.page ?? page;
    const isRefresh = !!opts.refresh;
    if (!isRefresh) setLoading(true);
    try {
      const params = { search: q || undefined, page: nextPage || undefined, sort: active || undefined };
      const data = await listStores(params);
      const arr = Array.isArray(data) ? data : (data.results || []);
      if (isRefresh || nextPage === 1) {
        setStores(arr);
      } else {
        setStores(prev => [...prev, ...arr]);
      }
      const total = Array.isArray(data) ? data.length : (data.count ?? arr.length);
      setHasMore(arr.length > 0 && (total ? (stores.length + arr.length) < total : true));
      setPage(nextPage);
    } catch {
      if (isRefresh) {
        setStores([]);
      }
    } finally {
      if (isRefresh) setRefreshing(false);
      setLoading(false);
    }
  };

  const loadFeatured = async () => {
    try {
      const data = await listTopStores({ limit: 10 });
      const arr = Array.isArray(data) ? data : (data.results || []);
      setFeatured(arr);
    } catch {
      setFeatured([]);
    }
  };

  useEffect(() => { load({ page: 1 }); loadFeatured(); }, []);
  useEffect(() => { const t = setTimeout(() => load({ page: 1 }), 300); return () => clearTimeout(t); }, [q, active]);

  const filtered = stores;

  return (
    <View style={{ flex: 1, backgroundColor: theme.colors.background }}>
      <View style={{ padding: theme.spacing.lg, borderBottomWidth: 1, borderColor: theme.colors.border }}>
        <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
          <Text style={{ color: theme.colors.textPrimary, fontFamily: theme.typography.fontBold, fontSize: theme.typography.sizes.lg, textAlign: I18nManager.isRTL ? 'right' : 'left' }}>المتاجر</Text>
          <TouchableOpacity onPress={() => setSheetOpen(true)} style={{ paddingHorizontal: theme.spacing.md, paddingVertical: theme.spacing.xs, borderRadius: theme.radius.md, borderWidth: 1, borderColor: theme.colors.cardBorder, backgroundColor: theme.colors.surface }}>
            <Text style={{ color: theme.colors.textPrimary, fontFamily: theme.typography.fontBold }}>فلتر ⚙️</Text>
          </TouchableOpacity>
        </View>
        <View style={{ marginTop: theme.spacing.md }}>
          <SearchBar initial={q} onChange={setQ} placeholder="ابحث عن متجر..." />
        </View>
        <View style={{ flexDirection: 'row', flexWrap: 'wrap', marginTop: theme.spacing.md }}>
          {filters.map(f => (
            <TouchableOpacity
              key={f.key}
              onPress={() => setActive(f.key)}
              style={{
                paddingHorizontal: theme.spacing.md,
                paddingVertical: theme.spacing.xs,
                borderRadius: theme.radius.md,
                borderWidth: 1,
                borderColor: active === f.key ? theme.colors.accent : theme.colors.cardBorder,
                backgroundColor: theme.colors.surface,
                marginRight: theme.spacing.sm,
                marginBottom: theme.spacing.sm,
              }}
            >
              <Text style={{ color: active === f.key ? theme.colors.accent : theme.colors.textPrimary, fontFamily: theme.typography.fontRegular }}>{f.label}</Text>
            </TouchableOpacity>
          ))}
        </View>

        <AdBannerDismissible position="stores-hero" />

        <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginTop: theme.spacing.lg }}>
          <Text style={{ color: theme.colors.textPrimary, fontFamily: theme.typography.fontBold, fontSize: theme.typography.sizes.lg, textAlign: I18nManager.isRTL ? 'right' : 'left' }}>أفضل المتاجر</Text>
          <TouchableOpacity onPress={() => navigation.navigate('Stores')}>
            <Text style={{ color: theme.colors.accent, fontFamily: theme.typography.fontBold }}>عرض الكل</Text>
          </TouchableOpacity>
        </View>
        <FlatList
          horizontal
          data={featured}
          keyExtractor={(it) => String(it.id)}
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={{ paddingVertical: theme.spacing.md }}
          renderItem={({ item }) => (
            <TouchableOpacity
              onPress={() => navigation.navigate('StoreDetail', { id: item.id })}
              style={{ width: 220, marginRight: theme.spacing.md }}
            >
              <View style={{ height: 110, borderRadius: theme.radius.lg, backgroundColor: theme.colors.surface, borderWidth: 1, borderColor: theme.colors.cardBorder, alignItems: 'center', justifyContent: 'center', ...theme.shadows.card }}>
                {item.logo ? <Image source={{ uri: item.logo }} style={{ width: 220, height: 110, borderRadius: theme.radius.lg }} /> : <Text style={{ color: theme.colors.textPrimary, fontFamily: theme.typography.fontBold }}>{item.name}</Text>}
              </View>
              <Text style={{ fontFamily: theme.typography.fontBold, marginTop: theme.spacing.sm, color: theme.colors.textPrimary, textAlign: I18nManager.isRTL ? 'right' : 'left' }}>{item.name}</Text>
              <Text style={{ color: theme.colors.textSecondary, fontFamily: theme.typography.fontRegular, textAlign: I18nManager.isRTL ? 'right' : 'left' }}>تقييم: {item.store_rating ?? 0}</Text>
            </TouchableOpacity>
          )}
          ListEmptyComponent={
            loading ? (
              <View style={{ flexDirection: 'row', paddingVertical: theme.spacing.md }}>
                {[...Array(4)].map((_, idx) => (
                  <View key={idx} style={{ width: 220, height: 110, marginRight: theme.spacing.md, borderRadius: theme.radius.lg, backgroundColor: theme.colors.surfaceAlt, borderWidth: 1, borderColor: theme.colors.cardBorder }} />
                ))}
              </View>
            ) : null
          }
        />
      </View>

      <FlatList
        data={filtered}
        keyExtractor={(it) => String(it.id)}
        numColumns={2}
        contentContainerStyle={{ padding: theme.spacing.lg, paddingBottom: 100 }}
        columnWrapperStyle={{ justifyContent: 'space-between' }}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); setPage(1); setHasMore(true); load({ page: 1, refresh: true }); }} />}
        onEndReachedThreshold={0.5}
        onEndReached={() => { if (hasMore && !loading) load({ page: page + 1 }); }}
        getItemLayout={(_, index) => ({ length: 240, offset: 240 * Math.ceil((index + 1) / 2), index })}
        removeClippedSubviews
        initialNumToRender={8}
        windowSize={7}
        renderItem={({ item }) => (
          <TouchableOpacity
            style={{ width: '48%', marginBottom: theme.spacing.lg, borderWidth: 1, borderColor: theme.colors.cardBorder, borderRadius: theme.radius.lg, backgroundColor: theme.colors.surface, ...theme.shadows.card }}
            onPress={() => navigation.navigate('StoreDetail', { id: item.id })}
          >
            {item.logo ? (
              <Image source={{ uri: item.logo }} style={{ width: '100%', height: 100, borderTopLeftRadius: theme.radius.lg, borderTopRightRadius: theme.radius.lg }} />
            ) : null}
            <View style={{ padding: theme.spacing.md }}>
              <Text numberOfLines={1} style={{ color: theme.colors.textPrimary, fontFamily: theme.typography.fontBold, textAlign: I18nManager.isRTL ? 'right' : 'left' }}>{item.name}</Text>
              <View style={{ flexDirection: 'row', marginTop: theme.spacing.xs }}>
                <Text style={{ color: theme.colors.textSecondary, fontFamily: theme.typography.fontRegular }}>تقييم: </Text>
                <Text style={{ color: theme.colors.accent, fontFamily: theme.typography.fontBold }}>
                  {Array.from({ length: 5 }).map((_, i) => ((item.store_rating || 0) >= i + 1 ? '★' : '☆')).join('')}
                </Text>
              </View>
              <Text style={{ color: theme.colors.textSecondary, fontFamily: theme.typography.fontRegular, marginTop: theme.spacing.xs, textAlign: I18nManager.isRTL ? 'right' : 'left' }}>
                منتجات: {item.products_count ?? 0} • {item.is_open ? 'مفتوح' : 'مغلق'}
              </Text>
              <Text style={{ color: theme.colors.textSecondary, fontFamily: theme.typography.fontRegular, marginTop: theme.spacing.xs, textAlign: I18nManager.isRTL ? 'right' : 'left' }}>
                توصيل: {item.delivery_time_text || 'غير محدد'}
              </Text>
              {item.fast_delivery ? (
                <View style={{ marginTop: theme.spacing.xs, alignSelf: I18nManager.isRTL ? 'flex-start' : 'flex-end', paddingHorizontal: theme.spacing.sm, paddingVertical: 2, borderRadius: theme.radius.md, backgroundColor: theme.colors.accent }}>
                  <Text style={{ color: '#000', fontFamily: theme.typography.fontBold }}>توصيل سريع</Text>
                </View>
              ) : null}
              <TouchableOpacity onPress={() => navigation.navigate('StoreDetail', { id: item.id })} style={{ marginTop: theme.spacing.md, paddingVertical: theme.spacing.sm, borderRadius: theme.radius.md, backgroundColor: theme.colors.accent, alignItems: 'center' }}>
                <Text style={{ color: '#000', fontFamily: theme.typography.fontBold }}>زيارة المتجر</Text>
              </TouchableOpacity>
            </View>
          </TouchableOpacity>
        )}
        ListEmptyComponent={
          loading ? (
            <View style={{ padding: theme.spacing.lg, flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'space-between' }}>
              {[...Array(6)].map((_, idx) => (
                <View key={idx} style={{ width: '48%', height: 160, marginBottom: theme.spacing.lg, borderRadius: theme.radius.lg, backgroundColor: theme.colors.surfaceAlt, borderWidth: 1, borderColor: theme.colors.cardBorder }} />
              ))}
            </View>
          ) : (
            <View style={{ padding: theme.spacing.lg, alignItems: 'center' }}>
              <Text style={{ color: theme.colors.textSecondary, fontFamily: theme.typography.fontRegular }}>لا توجد متاجر متاحة حالياً.</Text>
              <TouchableOpacity onPress={() => load({ page: 1 })} style={{ marginTop: theme.spacing.md, paddingVertical: theme.spacing.sm, paddingHorizontal: theme.spacing.md, borderRadius: theme.radius.md, backgroundColor: theme.colors.accent }}>
                <Text style={{ color: '#000', fontFamily: theme.typography.fontBold }}>إعادة المحاولة</Text>
              </TouchableOpacity>
            </View>
          )
        }
      />

      <Modal visible={sheetOpen} transparent animationType="slide" onRequestClose={() => setSheetOpen(false)}>
        <View style={{ flex: 1, backgroundColor: 'rgba(0,0,0,0.5)', justifyContent: 'flex-end' }}>
          <View style={{ backgroundColor: theme.colors.surface, borderTopLeftRadius: theme.radius.xl, borderTopRightRadius: theme.radius.xl, padding: theme.spacing.lg }}>
            <Text style={{ color: theme.colors.textPrimary, fontFamily: theme.typography.fontBold, fontSize: theme.typography.sizes.lg, textAlign: I18nManager.isRTL ? 'right' : 'left' }}>فلاتر</Text>
            <View style={{ marginTop: theme.spacing.md }}>
              {filters.map(f => (
                <TouchableOpacity key={f.key} onPress={() => setActive(f.key)} style={{ paddingVertical: theme.spacing.sm }}>
                  <Text style={{ color: active === f.key ? theme.colors.accent : theme.colors.textPrimary, fontFamily: theme.typography.fontRegular }}>{f.label}</Text>
                </TouchableOpacity>
              ))}
            </View>
            <View style={{ flexDirection: 'row', justifyContent: 'space-between', marginTop: theme.spacing.lg }}>
              <TouchableOpacity onPress={() => { setActive('rating'); setSheetOpen(false); load({ page: 1 }); }} style={{ paddingVertical: theme.spacing.sm, paddingHorizontal: theme.spacing.md, borderRadius: theme.radius.md, backgroundColor: theme.colors.accent }}>
                <Text style={{ color: '#000', fontFamily: theme.typography.fontBold }}>تطبيق</Text>
              </TouchableOpacity>
              <TouchableOpacity onPress={() => { setActive('rating'); setSheetOpen(false); }} style={{ paddingVertical: theme.spacing.sm, paddingHorizontal: theme.spacing.md, borderRadius: theme.radius.md, borderWidth: 1, borderColor: theme.colors.cardBorder }}>
                <Text style={{ color: theme.colors.textPrimary, fontFamily: theme.typography.fontBold }}>مسح</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>
    </View>
  );
}
