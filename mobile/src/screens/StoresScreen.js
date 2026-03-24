import React, { useCallback, useEffect, useState } from 'react';
import { View, Text, FlatList, TouchableOpacity, I18nManager, RefreshControl, Modal, StyleSheet, LayoutAnimation, Platform, UIManager } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Image } from 'expo-image';
import theme from '../theme';
import { listStores, listTopStores } from '../api';
import SearchBar from '../components/SearchBar';
import AdBannerDismissible from '../components/AdBannerDismissible';
import EmptyState from '../components/EmptyState';

const filters = [
  { key: 'all', label: 'الكل' },
  { key: 'top', label: 'الأعلى تقييماً' },
  { key: 'near', label: 'الأقرب' },
];

const FeaturedStoreItem = React.memo(function FeaturedStoreItem({ item, onPress }) {
  return (
    <TouchableOpacity onPress={() => onPress(item?.id)} style={styles.featuredCardWrap}>
      <View style={styles.featuredMediaWrap}>
        {item?.logo ? (
          <Image source={{ uri: item.logo }} style={styles.featuredMedia} contentFit="cover" transition={0} cachePolicy="memory-disk" />
        ) : (
          <Text style={styles.featuredNameFallback}>{item?.name}</Text>
        )}
      </View>
    </TouchableOpacity>
  );
});

const StoreGridItem = React.memo(function StoreGridItem({ item, onPress }) {
  const stars = `${((item?.store_rating || 0) >= 1 ? '★' : '☆')}${((item?.store_rating || 0) >= 2 ? '★' : '☆')}${((item?.store_rating || 0) >= 3 ? '★' : '☆')}${((item?.store_rating || 0) >= 4 ? '★' : '☆')}${((item?.store_rating || 0) >= 5 ? '★' : '☆')}`;
  return (
    <TouchableOpacity style={styles.storeCard} onPress={() => onPress(item?.id)}>
      {item?.logo ? (
        <Image source={{ uri: item.logo }} style={styles.storeCardMedia} contentFit="cover" transition={0} cachePolicy="memory-disk" />
      ) : null}
      <View style={styles.storeCardBody}>
        <Text numberOfLines={1} style={styles.storeCardTitle}>{item?.name}</Text>
        <View style={styles.ratingRow}>
          <Text style={styles.ratingLabel}>تقييم: </Text>
          <Text style={styles.ratingStars}>{stars}</Text>
        </View>
        <Text style={styles.metaText}>منتجات: {item?.products_count ?? 0} • {item?.is_open ? 'مفتوح' : 'مغلق'}</Text>
        <Text style={styles.metaText}>توصيل: {item?.delivery_time_text || 'غير محدد'}</Text>
        {item?.fast_delivery ? (
          <View style={styles.fastBadge}>
            <Text style={styles.fastBadgeText}>توصيل سريع</Text>
          </View>
        ) : null}
        <TouchableOpacity onPress={() => onPress(item?.id)} style={styles.visitButton}>
          <Text style={styles.visitButtonText}>زيارة المتجر</Text>
        </TouchableOpacity>
      </View>
    </TouchableOpacity>
  );
});

export default function StoresScreen({ navigation }) {
  const [q, setQ] = useState('');
  const [active, setActive] = useState('all');
  const [stores, setStores] = useState([]);
  const [featured, setFeatured] = useState([]);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const [sheetOpen, setSheetOpen] = useState(false);
  const [isTopAdVisible, setIsTopAdVisible] = useState(true);
  const handleTopAdDismiss = useCallback(() => {
    LayoutAnimation.configureNext(LayoutAnimation.Presets.easeInEaseOut);
    setIsTopAdVisible(false);
  }, []);

  useEffect(() => {
    if (Platform.OS === 'android' && UIManager.setLayoutAnimationEnabledExperimental) {
      UIManager.setLayoutAnimationEnabledExperimental(true);
    }
  }, []);

  const load = async (opts = {}) => {
    const nextPage = opts.page ?? page;
    const isRefresh = !!opts.refresh;
    if (!isRefresh) setLoading(true);
    try {
      const params = { search: q || undefined, page: nextPage || undefined, sort: active !== 'all' ? active : undefined };
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
  const goToStore = useCallback((id) => {
    if (!id) return;
    navigation.navigate('StoreDetail', { id });
  }, [navigation]);
  const renderFeatured = useCallback(({ item }) => (
    <FeaturedStoreItem item={item} onPress={goToStore} />
  ), [goToStore]);
  const renderStore = useCallback(({ item }) => (
    <StoreGridItem item={item} onPress={goToStore} />
  ), [goToStore]);
  const listHeader = (
    <View style={styles.collapsibleWrap}>
      <View style={styles.searchWrap}>
        <SearchBar initial={q} onChange={setQ} placeholder="ابحث عن متجر..." />
      </View>
      {isTopAdVisible ? (
        <AdBannerDismissible
          position="home_top"
          compact
          onDismiss={handleTopAdDismiss}
        />
      ) : null}
      <View style={styles.featuredHeader}>
        <Text style={styles.featuredTitle}>أفضل المتاجر</Text>
        <TouchableOpacity onPress={() => navigation.navigate('Stores')}>
          <Text style={styles.featuredLink}>عرض الكل</Text>
        </TouchableOpacity>
      </View>
      <FlatList
        horizontal
        data={featured}
        keyExtractor={(it) => String(it.id)}
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.featuredListContent}
        initialNumToRender={4}
        maxToRenderPerBatch={4}
        windowSize={3}
        renderItem={renderFeatured}
      />
    </View>
  );

  return (
    <SafeAreaView style={styles.screen}>
      <View style={styles.staticHeader}>
        <Text style={styles.title}>المتاجر</Text>
        <TouchableOpacity onPress={() => setSheetOpen(true)} style={styles.filterButton}>
          <Text style={styles.filterButtonText}>فلتر ⚙️</Text>
        </TouchableOpacity>
      </View>

      <View style={styles.stickyFilters}>
        <FlatList
          horizontal
          data={filters}
          keyExtractor={(f) => f.key}
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={styles.filtersRow}
          renderItem={({ item: f }) => (
            <TouchableOpacity
              onPress={() => setActive(f.key)}
              style={[styles.filterChip, active === f.key && styles.filterChipActive]}
            >
              <Text style={[styles.filterChipText, active === f.key && styles.filterChipTextActive]}>{f.label}</Text>
            </TouchableOpacity>
          )}
        />
      </View>

      <FlatList
        data={filtered}
        keyExtractor={(it) => String(it.id)}
        numColumns={2}
        style={styles.list}
        contentContainerStyle={styles.listContent}
        ListHeaderComponent={listHeader}
        columnWrapperStyle={styles.listColumn}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); setPage(1); setHasMore(true); load({ page: 1, refresh: true }); }} />}
        onEndReachedThreshold={0.5}
        onEndReached={() => { if (hasMore && !loading) load({ page: page + 1 }); }}
        removeClippedSubviews={true}
        initialNumToRender={6}
        maxToRenderPerBatch={6}
        updateCellsBatchingPeriod={60}
        windowSize={5}
        renderItem={renderStore}
        ListEmptyComponent={
          loading ? (
            <View style={{ padding: theme.spacing.lg, flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'space-between' }}>
              {[...Array(6)].map((_, idx) => (
                <View key={idx} style={{ width: '48%', height: 160, marginBottom: theme.spacing.lg, borderRadius: theme.radius.lg, backgroundColor: theme.colors.surfaceAlt, borderWidth: 1, borderColor: theme.colors.cardBorder }} />
              ))}
            </View>
          ) : (
            <EmptyState
              icon="store-search-outline"
              title="لا توجد متاجر متاحة حالياً"
              subtitle="جرّب تعديل البحث أو الفلاتر"
              ctaLabel="إعادة المحاولة"
              onPress={() => load({ page: 1 })}
            />
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
              <TouchableOpacity onPress={() => { setSheetOpen(false); load({ page: 1 }); }} style={{ paddingVertical: theme.spacing.sm, paddingHorizontal: theme.spacing.md, borderRadius: theme.radius.md, backgroundColor: theme.colors.accent }}>
                <Text style={{ color: '#000', fontFamily: theme.typography.fontBold }}>تطبيق</Text>
              </TouchableOpacity>
              <TouchableOpacity onPress={() => { setActive('all'); setSheetOpen(false); }} style={{ paddingVertical: theme.spacing.sm, paddingHorizontal: theme.spacing.md, borderRadius: theme.radius.md, borderWidth: 1, borderColor: theme.colors.cardBorder }}>
                <Text style={{ color: theme.colors.textPrimary, fontFamily: theme.typography.fontBold }}>مسح</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: theme.colors.background,
  },
  staticHeader: {
    zIndex: 30,
    elevation: 12,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: theme.spacing.md,
    backgroundColor: theme.colors.background,
    borderBottomWidth: 1,
    borderBottomColor: theme.colors.border,
  },
  title: {
    color: theme.colors.textPrimary,
    fontFamily: theme.typography.fontBold,
    fontSize: theme.typography.sizes.lg,
    textAlign: I18nManager.isRTL ? 'right' : 'left',
  },
  filterButton: {
    paddingHorizontal: theme.spacing.md,
    paddingVertical: theme.spacing.xs,
    borderRadius: theme.radius.md,
    borderWidth: 1,
    borderColor: theme.colors.cardBorder,
    backgroundColor: theme.colors.surface,
  },
  filterButtonText: {
    color: theme.colors.textPrimary,
    fontFamily: theme.typography.fontBold,
  },
  collapsibleWrap: {
    zIndex: 20,
    elevation: 8,
    overflow: 'visible',
    backgroundColor: theme.colors.background,
    paddingHorizontal: 16,
    paddingBottom: theme.spacing.sm,
  },
  searchWrap: {
    marginTop: theme.spacing.sm,
  },
  featuredHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: theme.spacing.md,
  },
  featuredTitle: {
    color: theme.colors.textPrimary,
    fontFamily: theme.typography.fontBold,
    fontSize: theme.typography.sizes.md,
    textAlign: I18nManager.isRTL ? 'right' : 'left',
  },
  featuredLink: {
    color: theme.colors.accent,
    fontFamily: theme.typography.fontBold,
  },
  featuredListContent: {
    paddingVertical: theme.spacing.sm,
  },
  featuredCardWrap: {
    width: 170,
    marginRight: theme.spacing.md,
  },
  featuredMediaWrap: {
    height: 88,
    borderRadius: theme.radius.lg,
    backgroundColor: theme.colors.surface,
    borderWidth: 1,
    borderColor: theme.colors.cardBorder,
    alignItems: 'center',
    justifyContent: 'center',
    ...theme.shadows.card,
  },
  featuredMedia: {
    width: 170,
    height: 88,
    borderRadius: theme.radius.lg,
  },
  featuredNameFallback: {
    color: theme.colors.textPrimary,
    fontFamily: theme.typography.fontBold,
  },
  collapsedHint: {
    marginTop: theme.spacing.sm,
    marginBottom: theme.spacing.xs,
    borderRadius: theme.radius.md,
    borderWidth: 1,
    borderColor: theme.colors.cardBorder,
    backgroundColor: theme.colors.surface,
    paddingVertical: theme.spacing.xs,
    paddingHorizontal: theme.spacing.sm,
    alignItems: 'center',
  },
  collapsedHintText: {
    color: theme.colors.textSecondary,
    fontFamily: theme.typography.fontRegular,
    fontSize: theme.typography.sizes.xs,
  },
  stickyFilters: {
    zIndex: 25,
    elevation: 10,
    backgroundColor: theme.colors.background,
    borderBottomWidth: 1,
    borderBottomColor: theme.colors.border,
    paddingHorizontal: 16,
    paddingTop: theme.spacing.sm,
    paddingBottom: theme.spacing.xs,
  },
  filtersRow: {
    paddingBottom: theme.spacing.xs,
  },
  filterChip: {
    paddingHorizontal: theme.spacing.md,
    paddingVertical: theme.spacing.xs,
    borderRadius: theme.radius.md,
    borderWidth: 1,
    borderColor: theme.colors.cardBorder,
    backgroundColor: theme.colors.surface,
    marginRight: theme.spacing.sm,
  },
  filterChipActive: {
    borderColor: theme.colors.accent,
  },
  filterChipText: {
    color: theme.colors.textPrimary,
    fontFamily: theme.typography.fontRegular,
  },
  filterChipTextActive: {
    color: theme.colors.accent,
  },
  list: {
    flex: 1,
  },
  listContent: {
    paddingHorizontal: 16,
    paddingVertical: theme.spacing.lg,
    paddingBottom: 100,
  },
  listColumn: {
    justifyContent: 'space-between',
  },
  storeCard: {
    width: '48%',
    marginBottom: theme.spacing.lg,
    borderWidth: 1,
    borderColor: theme.colors.cardBorder,
    borderRadius: theme.radius.lg,
    backgroundColor: theme.colors.surface,
    ...theme.shadows.card,
  },
  storeCardMedia: {
    width: '100%',
    height: 100,
    borderTopLeftRadius: theme.radius.lg,
    borderTopRightRadius: theme.radius.lg,
  },
  storeCardBody: {
    padding: theme.spacing.md,
  },
  storeCardTitle: {
    color: theme.colors.textPrimary,
    fontFamily: theme.typography.fontBold,
    textAlign: I18nManager.isRTL ? 'right' : 'left',
  },
  ratingRow: {
    flexDirection: 'row',
    marginTop: theme.spacing.xs,
  },
  ratingLabel: {
    color: theme.colors.textSecondary,
    fontFamily: theme.typography.fontRegular,
  },
  ratingStars: {
    color: theme.colors.accent,
    fontFamily: theme.typography.fontBold,
  },
  metaText: {
    color: theme.colors.textSecondary,
    fontFamily: theme.typography.fontRegular,
    marginTop: theme.spacing.xs,
    textAlign: I18nManager.isRTL ? 'right' : 'left',
  },
  fastBadge: {
    marginTop: theme.spacing.xs,
    alignSelf: I18nManager.isRTL ? 'flex-start' : 'flex-end',
    paddingHorizontal: theme.spacing.sm,
    paddingVertical: 2,
    borderRadius: theme.radius.md,
    backgroundColor: theme.colors.accent,
  },
  fastBadgeText: {
    color: '#000',
    fontFamily: theme.typography.fontBold,
  },
  visitButton: {
    marginTop: theme.spacing.md,
    paddingVertical: theme.spacing.sm,
    borderRadius: theme.radius.md,
    backgroundColor: theme.colors.accent,
    alignItems: 'center',
  },
  visitButtonText: {
    color: '#000',
    fontFamily: theme.typography.fontBold,
  },
});
