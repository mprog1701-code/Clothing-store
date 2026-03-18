import React, { useEffect, useMemo, useRef, useState } from 'react';
import { ScrollView, View, Text, TouchableOpacity, StyleSheet, TextInput, I18nManager, Animated, Dimensions } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import theme from '../theme';
import { listAds, listBanners, listProducts } from '../api';
import ProductCard from '../components/ProductCard';
import AdSlider from '../components/AdSlider';
import PromoBannerGrid from '../components/PromoBannerGrid';
import { useAuth } from '../auth/AuthContext';
import { useCart } from '../cart/CartContext';
import LoginRequiredSheet from '../components/LoginRequiredSheet';
import { useFocusEffect } from '@react-navigation/native';

const { width } = Dimensions.get('window');
const CATEGORY_MAP = {
  رجالي: 'men',
  نسائي: 'women',
  أطفال: 'kids',
  كوزمتك: 'cosmetics',
  عطور: 'perfumes',
};

const HomeScreen = ({ navigation }) => {
  const { accessToken } = useAuth();
  const { cartCount, refreshCartCount } = useCart();
  const [query, setQuery] = useState('');
  const headerAnim = useRef(new Animated.Value(0)).current;
  const searchAnim = useRef(new Animated.Value(0)).current;
  const adAnim = useRef(new Animated.Value(0)).current;
  const offersAnim = useRef(new Animated.Value(0)).current;
  const categoriesAnim = useRef(new Animated.Value(0)).current;
  const flashAnim = useRef(new Animated.Value(0)).current;

  const [adItems, setAdItems] = useState([]);
  const [promotionItems, setPromotionItems] = useState([]);
  const [loginSheetVisible, setLoginSheetVisible] = useState(false);
  const [pendingNext, setPendingNext] = useState(null);

  const [homeProducts, setHomeProducts] = useState([]);

  useEffect(() => {
    Animated.stagger(120, [
      Animated.timing(headerAnim, { toValue: 1, duration: 420, useNativeDriver: true }),
      Animated.timing(searchAnim, { toValue: 1, duration: 420, useNativeDriver: true }),
      Animated.timing(adAnim, { toValue: 1, duration: 420, useNativeDriver: true }),
      Animated.timing(offersAnim, { toValue: 1, duration: 420, useNativeDriver: true }),
      Animated.timing(categoriesAnim, { toValue: 1, duration: 420, useNativeDriver: true }),
      Animated.timing(flashAnim, { toValue: 1, duration: 420, useNativeDriver: true }),
    ]).start();
  }, [adAnim, categoriesAnim, flashAnim, headerAnim, offersAnim, searchAnim]);

  useEffect(() => {
    let mounted = true;
    const mediaUrl = (item) => item?.image_url || item?.image || item?.banner_image || '';
    const getTag = (item) => String(item?.tag || item?.type || item?.kind || item?.category || '').toLowerCase();
    const getPlacement = (item) => String(item?.placement || item?.position || item?.slot || '').toLowerCase();
    const isAdTag = (tag) => tag.includes('ad') || tag.includes('sponsor');
    const isPromotionTag = (tag) => tag.includes('promo') || tag.includes('banner') || tag.includes('offer');

    const loadHomeMedia = async () => {
      let adsRaw = [];
      let bannersRaw = [];
      try {
        const [adsRes, bannersRes] = await Promise.all([listAds(), listBanners()]);
        adsRaw = Array.isArray(adsRes) ? adsRes : [];
        bannersRaw = Array.isArray(bannersRes) ? bannersRes : [];
      } catch {
        try {
          adsRaw = await listAds();
        } catch {
          adsRaw = [];
        }
      }
      const merged = [
        ...(Array.isArray(adsRaw) ? adsRaw : []).map((item) => ({ ...item, source: 'ads' })),
        ...(Array.isArray(bannersRaw) ? bannersRaw : []).map((item) => ({ ...item, source: 'banners' })),
      ].filter((item) => !!mediaUrl(item));
      const normalized = merged.map((item) => {
        const rawTag = getTag(item);
        const inferredTag = item.source === 'ads' ? 'ad' : 'promotion';
        return { ...item, __tag: rawTag || inferredTag, __placement: getPlacement(item) };
      });
      const adsOnly = normalized.filter((item) => isAdTag(item.__tag));
      const promotionsOnly = normalized.filter((item) => isPromotionTag(item.__tag));
      if (!mounted) return;
      setAdItems(adsOnly);
      setPromotionItems(promotionsOnly);
    };

    loadHomeMedia();
    return () => {
      mounted = false;
    };
  }, []);

  useEffect(() => {
    let mounted = true;
    const loadHomeProducts = async () => {
      try {
        const data = await listProducts({ ordering: '-created_at', page_size: 8 });
        const source = Array.isArray(data) ? data : (data?.results || data?.products || data?.items || []);
        const normalized = (source || []).map((item, index) => ({
          ...item,
          id: item?.id ?? item?.product_id ?? item?.productId ?? `h-${index}`,
          name: item?.name || item?.title || item?.product_name || 'منتج',
          price: item?.price ?? item?.base_price ?? item?.final_price ?? 0,
        }));
        if (!mounted) return;
        setHomeProducts(normalized);
      } catch (e) {
        if (__DEV__) {
          console.error('[HomeScreen] products fetch failed', {
            message: e?.message,
            status: e?.response?.status,
            data: e?.response?.data,
          });
        }
        if (!mounted) return;
        setHomeProducts([]);
      }
    };
    loadHomeProducts();
    return () => {
      mounted = false;
    };
  }, []);

  const heroAd = adItems.find((item) => {
    const p = String(item?.__placement || '');
    return p.includes('hero') || p.includes('top');
  });
  const midPageAd = adItems.find((item) => {
    const p = String(item?.__placement || '');
    return p.includes('middle') || p.includes('mid');
  });
  const heroSlotAds = heroAd ? [heroAd, ...adItems.filter((item) => item?.id !== heroAd?.id && String(item?.__placement || '').includes('hero'))] : [];
  const midSlotAds = midPageAd ? [midPageAd, ...adItems.filter((item) => item?.id !== midPageAd?.id && String(item?.__placement || '').includes('mid'))] : [];
  const promotions = promotionItems.slice(0, 10);
  const openProductsList = ({ type, listTitle, extra = {}, ...rest }) => {
    navigation.navigate('ProductsList', { type, listTitle, ...extra, ...rest });
  };
  const requestLogin = ({ next }) => {
    setPendingNext(next || { name: 'Root', params: { screen: 'Home' } });
    setLoginSheetVisible(true);
  };

  useFocusEffect(
    React.useCallback(() => {
      refreshCartCount();
    }, [refreshCartCount])
  );

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView
        contentContainerStyle={styles.content}
        showsVerticalScrollIndicator={false}
        alwaysBounceVertical
        scrollEventThrottle={16}
        keyboardShouldPersistTaps="handled"
      >
      <Animated.View style={[styles.header, styles.fadeUp(headerAnim)]}>
        <TouchableOpacity onPress={() => navigation.navigate('Cart')} style={styles.iconButton}>
          <Ionicons name="cart-outline" size={20} color={theme.colors.textPrimary} />
          {cartCount > 0 ? (
            <View style={styles.cartBadge}>
              <Text style={styles.cartBadgeText}>{cartCount > 99 ? '99+' : String(cartCount)}</Text>
            </View>
          ) : null}
        </TouchableOpacity>
        <Text style={styles.headerTitle}>دار DAAR</Text>
      </Animated.View>

      <Animated.View style={[styles.searchBar, styles.fadeUp(searchAnim)]}>
        <TextInput
          value={query}
          onChangeText={setQuery}
          placeholder="ابحث عن منتج..."
          placeholderTextColor={theme.colors.textSecondary}
          style={styles.searchInput}
        />
        <Ionicons name="search" size={18} color={theme.colors.textSecondary} />
      </Animated.View>

      {!accessToken ? (
        <View style={styles.guestBanner}>
          <Text style={styles.guestBannerText}>أهلاً بك! سجل دخولك لتجربة تسوق أفضل</Text>
          <TouchableOpacity onPress={() => requestLogin({ next: { name: 'Root', params: { screen: 'Home' } } })}>
            <Text style={styles.guestBannerLink}>Login</Text>
          </TouchableOpacity>
        </View>
      ) : null}

      <Animated.View style={styles.fadeUp(adAnim)}>
        <AdSlider
          ads={heroSlotAds}
          badgeText="Sponsored"
          intervalMs={5000}
          placeholderTitle="Coming Soon"
          placeholderSubtitle="عرض داخلي قريباً"
        />
      </Animated.View>

      <Animated.View style={styles.fadeUp(offersAnim)}>
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>وصل حديثاً</Text>
          <TouchableOpacity onPress={() => openProductsList({ type: 'new_arrivals', filterType: 'new_arrival', listTitle: 'وصل حديثاً' })}>
            <Text style={styles.sectionLink}>عرض الكل</Text>
          </TouchableOpacity>
        </View>
        <View style={styles.offerCard}>
          <Text style={styles.offerTitle}>اكتشف المنتجات الجديدة</Text>
        </View>
        <TouchableOpacity onPress={() => openProductsList({ type: 'new_arrivals', filterType: 'new_arrival', listTitle: 'وصل حديثاً' })}>
          <Text style={styles.offerLink}>عرض المنتجات</Text>
        </TouchableOpacity>
      </Animated.View>

      <Animated.View style={styles.fadeUp(categoriesAnim)}>
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>الأقسام</Text>
          <TouchableOpacity onPress={() => navigation.navigate('AllCategories', { listTitle: 'كل الأقسام' })}>
            <Text style={styles.sectionLink}>عرض الكل</Text>
          </TouchableOpacity>
        </View>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.chipsRow}>
          {['رجالي', 'نسائي', 'أطفال', 'كوزمتك', 'عطور', 'عرض الكل'].map((label) => (
            <TouchableOpacity
              key={label}
              style={[styles.chip, label === 'عرض الكل' && styles.chipActive]}
              onPress={() => {
                if (label === 'عرض الكل') {
                  navigation.navigate('AllCategories', { listTitle: 'كل الأقسام' });
                  return;
                }
                openProductsList({
                  type: 'category',
                  listTitle: label,
                  extra: {
                    categoryId: CATEGORY_MAP[label] || null,
                    categoryLabel: label,
                  },
                });
              }}
            >
              <Text style={[styles.chipText, label === 'عرض الكل' && styles.chipTextActive]}>{label}</Text>
            </TouchableOpacity>
          ))}
        </ScrollView>
      </Animated.View>

      <Animated.View style={styles.fadeUp(flashAnim)}>
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>عروض فلاش</Text>
          <TouchableOpacity onPress={() => openProductsList({ type: 'flash_sales', filterType: 'flash_sale', listTitle: 'عروض فلاش' })}>
            <Text style={styles.sectionLink}>عرض الكل</Text>
          </TouchableOpacity>
        </View>
        <View style={styles.flashCard}>
          <Text style={styles.flashTitle}>عرض فلاش</Text>
          <TouchableOpacity onPress={() => openProductsList({ type: 'flash_sales', filterType: 'flash_sale', listTitle: 'عروض فلاش' })}>
            <Text style={styles.flashLink}>عرض العروض</Text>
          </TouchableOpacity>
        </View>
      </Animated.View>

      <Animated.View style={styles.fadeUp(adAnim)}>
        <PromoBannerGrid
          items={promotions}
          title="بنرات ترويجية"
          emptyTitle="عرض داخلي قريباً"
          onPressItem={() => openProductsList({ type: 'promotion_banners', listTitle: 'بنرات ترويجية' })}
        />
      </Animated.View>

      <Animated.View style={styles.fadeUp(searchAnim)}>
        <AdSlider
          ads={midSlotAds}
          badgeText="Ad"
          intervalMs={5000}
          placeholderTitle="Coming Soon"
          placeholderSubtitle="عروض جديدة قريباً"
        />
      </Animated.View>

      <Animated.View style={styles.fadeUp(categoriesAnim)}>
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>المنتجات</Text>
          <TouchableOpacity onPress={() => openProductsList({ type: 'all_products', listTitle: 'كل المنتجات' })}>
            <Text style={styles.sectionLink}>عرض الكل</Text>
          </TouchableOpacity>
        </View>
        <View style={styles.productsGrid}>
          {homeProducts.map((item) => (
            <View key={item.id} style={styles.productCard}>
              <ProductCard
                product={item}
                addToCart={() => {
                  if (!accessToken) {
                    requestLogin({ next: { name: 'ProductDetail', params: { productId: item.id } } });
                    return;
                  }
                  navigation.navigate('Cart');
                }}
              />
            </View>
          ))}
        </View>
      </Animated.View>

      <View style={{ height: theme.spacing.xl }} />
      </ScrollView>
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
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: theme.colors.background,
  },
  content: {
    paddingHorizontal: 16,
    paddingTop: theme.spacing.lg,
    paddingBottom: theme.spacing.xl * 2,
  },
  fadeUp: (anim) => ({
    opacity: anim,
    transform: [{ translateY: anim.interpolate({ inputRange: [0, 1], outputRange: [18, 0] }) }],
  }),
  header: {
    flexDirection: 'row-reverse',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: theme.spacing.lg,
  },
  headerTitle: {
    color: theme.colors.textPrimary,
    fontFamily: theme.typography.fontBold,
    fontSize: theme.typography.sizes.lg,
  },
  iconButton: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: theme.colors.surface,
    alignItems: 'center',
    justifyContent: 'center',
    position: 'relative',
  },
  cartBadge: {
    position: 'absolute',
    top: -6,
    right: -6,
    minWidth: 16,
    height: 16,
    borderRadius: 8,
    paddingHorizontal: 4,
    backgroundColor: theme.colors.danger,
    alignItems: 'center',
    justifyContent: 'center',
  },
  cartBadgeText: {
    color: '#fff',
    fontFamily: theme.typography.fontBold,
    fontSize: 9,
  },
  searchBar: {
    flexDirection: 'row-reverse',
    alignItems: 'center',
    backgroundColor: theme.colors.surfaceAlt,
    borderRadius: theme.radius.lg,
    borderWidth: 1,
    borderColor: theme.colors.cardBorder,
    paddingHorizontal: theme.spacing.md,
    paddingVertical: theme.spacing.sm,
    marginBottom: theme.spacing.lg,
  },
  searchInput: {
    flex: 1,
    color: theme.colors.textPrimary,
    fontFamily: theme.typography.fontRegular,
    fontSize: theme.typography.sizes.md,
    textAlign: I18nManager.isRTL ? 'right' : 'left',
  },
  guestBanner: {
    marginBottom: theme.spacing.lg,
    paddingVertical: theme.spacing.sm,
    paddingHorizontal: theme.spacing.md,
    borderRadius: theme.radius.md,
    borderWidth: 1,
    borderColor: theme.colors.cardBorder,
    backgroundColor: theme.colors.surface,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  guestBannerText: {
    color: theme.colors.textSecondary,
    fontFamily: theme.typography.fontRegular,
    fontSize: theme.typography.sizes.sm,
  },
  guestBannerLink: {
    color: theme.colors.accent,
    fontFamily: theme.typography.fontBold,
    fontSize: theme.typography.sizes.sm,
  },
  sectionHeader: {
    flexDirection: 'row-reverse',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: theme.spacing.sm,
  },
  sectionTitle: {
    color: theme.colors.textPrimary,
    fontFamily: theme.typography.fontBold,
    fontSize: theme.typography.sizes.lg,
  },
  sectionLink: {
    color: theme.colors.accent,
    fontFamily: theme.typography.fontRegular,
    fontSize: theme.typography.sizes.sm,
  },
  offerCard: {
    backgroundColor: theme.colors.surface,
    borderRadius: theme.radius.lg,
    borderWidth: 1,
    borderColor: theme.colors.cardBorder,
    height: 120,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: theme.spacing.sm,
  },
  offerTitle: {
    color: theme.colors.textSecondary,
    fontFamily: theme.typography.fontBold,
    fontSize: theme.typography.sizes.md,
  },
  offerLink: {
    color: theme.colors.textSecondary,
    fontFamily: theme.typography.fontRegular,
    fontSize: theme.typography.sizes.sm,
    textAlign: I18nManager.isRTL ? 'right' : 'left',
    marginBottom: theme.spacing.lg,
  },
  chipsRow: {
    paddingVertical: theme.spacing.sm,
    paddingRight: I18nManager.isRTL ? 0 : theme.spacing.sm,
    paddingLeft: I18nManager.isRTL ? theme.spacing.sm : 0,
  },
  chip: {
    backgroundColor: theme.colors.surface,
    borderWidth: 1,
    borderColor: theme.colors.cardBorder,
    borderRadius: 20,
    paddingHorizontal: theme.spacing.md,
    paddingVertical: theme.spacing.sm,
    marginLeft: theme.spacing.sm,
  },
  chipActive: {
    backgroundColor: theme.colors.accent,
    borderColor: theme.colors.accent,
  },
  chipText: {
    color: theme.colors.textPrimary,
    fontFamily: theme.typography.fontRegular,
    fontSize: theme.typography.sizes.sm,
  },
  chipTextActive: {
    color: theme.colors.textPrimary,
    fontFamily: theme.typography.fontBold,
  },
  flashCard: {
    backgroundColor: theme.colors.surfaceAlt,
    borderRadius: theme.radius.lg,
    borderWidth: 1,
    borderColor: theme.colors.cardBorder,
    padding: theme.spacing.md,
    flexDirection: 'row-reverse',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: theme.spacing.lg,
  },
  flashTitle: {
    color: theme.colors.textPrimary,
    fontFamily: theme.typography.fontBold,
    fontSize: theme.typography.sizes.md,
  },
  flashLink: {
    color: theme.colors.accent,
    fontFamily: theme.typography.fontRegular,
    fontSize: theme.typography.sizes.sm,
  },
  productsGrid: {
    flexDirection: 'row-reverse',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    marginBottom: theme.spacing.lg,
  },
  productCard: {
    width: (width - 16 * 2 - theme.spacing.md) / 2,
    marginBottom: theme.spacing.md,
  },
});

export default HomeScreen;
