import React, { useEffect, useState } from 'react';
import { View, Text, FlatList, TouchableOpacity, ActivityIndicator, Image, Button, Alert, I18nManager, Linking, Dimensions } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { listCategories, listProducts, listStores, devSeed, addToCart, listAds, getCart } from '../api';
import { useAuth } from '../auth/AuthContext';
import theme from '../theme';
import SearchBar from '../components/SearchBar';
import AdBannerSlot from '../components/AdBannerSlot';
import BannerPlacement from '../components/BannerPlacement';
import BannerWidget from '../components/BannerWidget';

export default function HomeScreen({ navigation }) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [categories, setCategories] = useState([]);
  const [products, setProducts] = useState([]);
  const [stores, setStores] = useState([]);
  const [search, setSearch] = useState('');
  const [heroAd, setHeroAd] = useState(null);
  const [showHero, setShowHero] = useState(false);
  const [searchResults, setSearchResults] = useState([]);
  const [cartCount, setCartCount] = useState(0);
  const { accessToken } = useAuth();
  const screenW = Dimensions.get('window').width;
  const productCardW = Math.floor((screenW - (theme.spacing.lg * 2) - theme.spacing.md) / 2);
  const PREVIEW_LIMIT = 6;

  const load = async () => {
    setLoading(true);
    setError('');
    try {
      const cats = await listCategories();
      const pr = await listProducts({ limit: 50 });
      const st = await listStores({ limit: 20 });
      // Load hero ad with dismissal check
      try {
        const untilStr = await AsyncStorage.getItem('home_ad_dismissed_until');
        const until = untilStr ? parseInt(untilStr, 10) : 0;
        const now = Date.now();
        if (!until || now >= until) {
          try {
            const ads = await listAds({ position: 'hero' });
            const arr = Array.isArray(ads) ? ads : (ads.results || ads.ads || []);
            const ad = arr && arr[0];
            setHeroAd(ad || null);
            setShowHero(!!ad);
            console.log('[Hero] ads result', Array.isArray(arr) ? arr.length : 0, 'showHero=', !!ad);
          } catch {
            try {
              const bnResp = await import('../api').then(m => m.listBanners());
              const arr = bnResp?.banners || [];
              const fb = arr[0] || null;
              setHeroAd(fb);
              setShowHero(!!fb);
              console.log('[Hero] fallback banners', arr.length, 'showHero=', !!fb);
            } catch {
              setHeroAd(null);
              setShowHero(false);
              console.log('[Hero] no data for hero, showHero=false');
            }
          }
        } else {
          setShowHero(false);
          console.log('[Hero] dismissed until', until);
        }
      } catch {
        setShowHero(false);
        console.log('[Hero] error reading dismissal, showHero=false');
      }
      const catItems = cats.categories || [];
      const prItems = Array.isArray(pr) ? pr : (pr.results || []);
      const stItems = Array.isArray(st) ? st : (st.results || []);
      console.log('[Home] categories.len=', catItems.length, 'products.len=', prItems.length, 'stores.len=', stItems.length);
      setCategories(catItems);
      setProducts(prItems);
      setStores(stItems);
      if (accessToken) {
        try {
          const c = await getCart();
          const arr = Array.isArray(c) ? c : (c.items || c.results || []);
          setCartCount((arr || []).length);
        } catch {}
      } else {
        setCartCount(0);
      }
      if (prItems.length === 0) {
        console.log('[Home] Empty data detected, triggering dev seed...');
        try {
          await devSeed();
          const pr2 = await listProducts({ limit: 20 });
          setProducts(Array.isArray(pr2) ? pr2 : (pr2.results || []));
        } catch (se) {
          console.log('[Home] dev seed failed:', se?.message || se);
        }
      }
      try {
        const [topList, midList, botList] = await Promise.all([
          import('../api').then(m => m.listBannersByPlacement('HOME_TOP')),
          import('../api').then(m => m.listBannersByPlacement('HOME_MIDDLE')),
          import('../api').then(m => m.listBannersByPlacement('HOME_BOTTOM')),
        ]);
        const topBanner = (Array.isArray(topList) ? topList : [])[0] || null;
        const midBanner = (Array.isArray(midList) ? midList : [])[0] || null;
        const botBanner = (Array.isArray(botList) ? botList : [])[0] || null;
        console.log('TOP', topBanner?.id, 'MID', midBanner?.id, 'BOT', botBanner?.id);
      } catch {}
    } catch (e) {
      console.log('[Home] load error:', e?.message || e);
      setError('تعذر تحميل البيانات. تحقق من الاتصال أو السيرفر.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  useEffect(() => {
    const q = (search || '').trim();
    let active = true;
    const run = async () => {
      if (!q) {
        setSearchResults([]);
        return;
      }
      try {
        const r = await listProducts({ search: q, limit: 6 });
        const arr = Array.isArray(r) ? r : (r.results || []);
        if (active) setSearchResults(arr);
      } catch {
        if (active) setSearchResults([]);
      }
    };
    run();
    return () => { active = false; };
  }, [search]);
  if (loading) {
    return (
      <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center', backgroundColor: theme.colors.background }}>
        <ActivityIndicator />
        <Text style={{ marginTop: 8, textAlign: 'center', color: theme.colors.textSecondary, fontFamily: theme.typography.fontRegular }}>جاري تحميل المحتوى...</Text>
      </View>
    );
  }

  if (error) {
    return (
      <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center', padding: 16, backgroundColor: theme.colors.background }}>
        <Text style={{ color: theme.colors.danger, marginBottom: 12, textAlign: 'center', fontFamily: theme.typography.fontRegular }}>{error}</Text>
        <Button title="إعادة المحاولة" onPress={load} />
      </View>
    );
  }

  const isEmpty = (categories.length === 0) && (products.length === 0);
  const ListHeader = () => {
    const topStores = stores.slice(0, PREVIEW_LIMIT);
    const flashDeals = products.filter(p => (p.discount_price || 0) > 0).slice(0, PREVIEW_LIMIT);
    const recommended = products.slice(0, PREVIEW_LIMIT);
    return (
    <View style={{ backgroundColor: theme.colors.background }}>
      {/* AppBar */}
      <SafeAreaView edges={['top']} style={{ backgroundColor: theme.colors.surface }}>
      <View style={{ height: 60, paddingHorizontal: theme.spacing.lg, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', borderBottomWidth: 1, borderColor: theme.colors.border, ...theme.shadows.appBar }}>
        <Text style={{ color: theme.colors.textPrimary, fontFamily: theme.typography.fontBold, fontSize: theme.typography.sizes.lg, textAlign: I18nManager.isRTL ? 'right' : 'left' }}>دار الأزياء</Text>
        <View style={{ flexDirection: 'row', alignItems: 'center' }}>
          <Text style={{ color: theme.colors.textSecondary, fontFamily: theme.typography.fontRegular, fontSize: theme.typography.sizes.md }}>🛒</Text>
          {cartCount > 0 ? (
            <View style={{ marginLeft: 6, paddingHorizontal: 6, paddingVertical: 2, borderRadius: 12, backgroundColor: theme.colors.accent }}>
              <Text style={{ color: '#000', fontFamily: theme.typography.fontBold }}>{cartCount}</Text>
            </View>
          ) : null}
        </View>
      </View>
      </SafeAreaView>

      {/* Ad Hero with dismiss */}
      {showHero && (
        <View style={{ marginHorizontal: theme.spacing.lg, marginTop: theme.spacing.md }}>
          <View style={{ flexDirection: 'row', justifyContent: 'flex-end' }}>
            <TouchableOpacity
              onPress={async () => {
                try {
                  const until = Date.now() + 24 * 60 * 60 * 1000;
                  await AsyncStorage.setItem('home_ad_dismissed_until', String(until));
                } catch {}
                setShowHero(false);
              }}
              style={{ paddingHorizontal: theme.spacing.md, paddingVertical: theme.spacing.xs, borderRadius: theme.radius.md, backgroundColor: theme.colors.surface, borderWidth: 1, borderColor: theme.colors.cardBorder }}
            >
              <Text style={{ color: theme.colors.textPrimary, fontFamily: theme.typography.fontBold }}>إغلاق ✕</Text>
            </TouchableOpacity>
          </View>
          <TouchableOpacity
            onPress={() => {
              const type = heroAd?.linkType || heroAd?.type;
              const value = heroAd?.linkValue || heroAd?.value || heroAd?.url;
              if (type === 'product' && value) {
                navigation.navigate('ProductDetail', { productId: value });
              } else if (type === 'store' && value) {
                navigation.navigate('StoreDetail', { id: value });
              } else if (type === 'url' && value) {
                Linking.openURL(value);
              }
            }}
            style={{ marginTop: theme.spacing.xs }}
          >
            <View style={{ height: 200, borderRadius: theme.radius.lg, borderWidth: 1, borderColor: theme.colors.cardBorder, backgroundColor: theme.colors.surface, ...theme.shadows.card, overflow: 'hidden' }}>
              {heroAd?.image ? (
                <Image source={{ uri: heroAd.image }} style={{ width: '100%', height: '100%' }} />
              ) : (
                <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center' }}>
                  <Text style={{ color: theme.colors.textPrimary, fontFamily: theme.typography.fontBold }}>{heroAd?.title || 'إعلان'}</Text>
                </View>
              )}
            </View>
          </TouchableOpacity>
        </View>
      )}

      <View style={{ paddingHorizontal: theme.spacing.lg, paddingTop: theme.spacing.md }}>
        <SearchBar initial={search} onChange={setSearch} placeholder="ابحث عن منتج..." debounce={400} />
      </View>

      {search?.trim() ? (
        <>
          <View style={{ paddingHorizontal: theme.spacing.lg, paddingTop: theme.spacing.md, flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
            <Text style={{ fontSize: theme.typography.sizes.lg, fontFamily: theme.typography.fontBold, color: theme.colors.textPrimary, textAlign: I18nManager.isRTL ? 'right' : 'left' }}>نتائج سريعة</Text>
            <TouchableOpacity onPress={() => navigation.navigate('Products', { mode: 'search', q: search })}>
              <Text style={{ color: theme.colors.accent, fontFamily: theme.typography.fontBold }}>عرض الكل</Text>
            </TouchableOpacity>
          </View>
          <FlatList
            horizontal
            data={searchResults}
            keyExtractor={(it) => String(it.id)}
            showsHorizontalScrollIndicator={false}
            contentContainerStyle={{ paddingHorizontal: theme.spacing.lg }}
            renderItem={({ item }) => (
              <View style={{ width: 220, marginRight: theme.spacing.md, borderWidth: 1, borderColor: theme.colors.cardBorder, borderRadius: theme.radius.lg, backgroundColor: theme.colors.surface, ...theme.shadows.card }}>
                {item.main_image?.image_url ? <Image source={{ uri: item.main_image.image_url }} style={{ width: 220, height: 110, borderTopLeftRadius: theme.radius.lg, borderTopRightRadius: theme.radius.lg }} /> : null}
                <View style={{ padding: theme.spacing.md }}>
                  <Text numberOfLines={1} style={{ fontFamily: theme.typography.fontBold, color: theme.colors.textPrimary }}>{item.name}</Text>
                  <Text style={{ color: theme.colors.textSecondary, fontFamily: theme.typography.fontRegular }}>{item.base_price}</Text>
                </View>
              </View>
            )}
            ListEmptyComponent={
              <View style={{ paddingHorizontal: theme.spacing.lg }}>
                <Text style={{ color: theme.colors.textSecondary, fontFamily: theme.typography.fontRegular }}>لا نتائج حالياً</Text>
              </View>
            }
          />
        </>
      ) : null}

      {showHero && (
        <View style={{ marginHorizontal: theme.spacing.lg, marginTop: theme.spacing.md }}>
          <View style={{ flexDirection: 'row', justifyContent: 'flex-end' }}>
            <TouchableOpacity
              onPress={async () => {
                try {
                  const until = Date.now() + 24 * 60 * 60 * 1000;
                  await AsyncStorage.setItem('home_ad_dismissed_until', String(until));
                } catch {}
                setShowHero(false);
              }}
              style={{ paddingHorizontal: theme.spacing.md, paddingVertical: theme.spacing.xs, borderRadius: theme.radius.md, backgroundColor: theme.colors.surface, borderWidth: 1, borderColor: theme.colors.cardBorder }}
            >
              <Text style={{ color: theme.colors.textPrimary, fontFamily: theme.typography.fontBold }}>إغلاق ✕</Text>
            </TouchableOpacity>
          </View>
          <TouchableOpacity
            onPress={() => {
              const type = heroAd?.linkType || heroAd?.type;
              const value = heroAd?.linkValue || heroAd?.value || heroAd?.url;
              if (type === 'product' && value) {
                navigation.navigate('ProductDetail', { productId: value });
              } else if (type === 'store' && value) {
                navigation.navigate('StoreDetail', { id: value });
              } else if (type === 'url' && value) {
                Linking.openURL(value);
              }
            }}
            style={{ marginTop: theme.spacing.xs }}
          >
            <View style={{ height: 200, borderRadius: theme.radius.lg, borderWidth: 1, borderColor: theme.colors.cardBorder, backgroundColor: theme.colors.surface, ...theme.shadows.card, overflow: 'hidden' }}>
              {heroAd?.image ? (
                <Image source={{ uri: heroAd.image }} style={{ width: '100%', height: '100%' }} />
              ) : (
                <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center' }}>
                  <Text style={{ color: theme.colors.textPrimary, fontFamily: theme.typography.fontBold }}>{heroAd?.title || 'إعلان'}</Text>
                </View>
              )}
            </View>
          </TouchableOpacity>
        </View>
      )}
      {/* Ad Slot 1 */}
      <AdBannerSlot position="slot1" onNavigate={(name, params) => navigation.navigate(name, params)} />

      {/* Banners (HOME_TOP) */}
      <BannerWidget />

      {/* Categories horizontal */}
      <View style={{ paddingHorizontal: theme.spacing.lg, paddingTop: theme.spacing.lg, flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
        <Text style={{ fontSize: theme.typography.sizes.lg, fontFamily: theme.typography.fontBold, color: theme.colors.textPrimary, textAlign: I18nManager.isRTL ? 'right' : 'left' }}>الأقسام</Text>
        <TouchableOpacity onPress={() => navigation.navigate('Categories')}>
          <Text style={{ color: theme.colors.accent, fontFamily: theme.typography.fontBold }}>عرض الكل</Text>
        </TouchableOpacity>
      </View>
      <FlatList
        horizontal
        data={categories}
        keyExtractor={(it) => String(it.key)}
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={{ paddingHorizontal: theme.spacing.lg }}
        renderItem={({ item }) => (
          <TouchableOpacity
            onPress={() => navigation.navigate('Products', { mode: 'category', categoryId: item.key })}
            style={{ paddingHorizontal: theme.spacing.md, paddingVertical: theme.spacing.sm, marginRight: theme.spacing.sm, borderWidth: 1, borderColor: theme.colors.cardBorder, borderRadius: theme.radius.md, backgroundColor: theme.colors.surface }}
          >
            <Text style={{ color: theme.colors.textPrimary, fontFamily: theme.typography.fontRegular }}>{item.label}</Text>
          </TouchableOpacity>
        )}
      />

      {/* Flash Deals */}
      <View style={{ paddingHorizontal: theme.spacing.lg, paddingTop: theme.spacing.lg, flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
        <Text style={{ fontSize: theme.typography.sizes.lg, fontFamily: theme.typography.fontBold, color: theme.colors.textPrimary }}>عروض فلاش</Text>
        <TouchableOpacity onPress={() => navigation.navigate('Products', { mode: 'all' })}>
          <Text style={{ color: theme.colors.accent, fontFamily: theme.typography.fontBold }}>عرض الكل</Text>
        </TouchableOpacity>
      </View>
      <FlatList
        horizontal
        data={flashDeals}
        keyExtractor={(it) => String(it.id)}
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={{ paddingHorizontal: theme.spacing.lg }}
        renderItem={({ item }) => (
          <View style={{ width: 220, marginRight: theme.spacing.md, borderWidth: 1, borderColor: theme.colors.cardBorder, borderRadius: theme.radius.lg, backgroundColor: theme.colors.surface, ...theme.shadows.card }}>
            {item.main_image?.url || item.main_image?.image_url ? (
              <Image
                source={{ uri: item.main_image.url || item.main_image.image_url }}
                style={{ width: 220, height: 110, borderTopLeftRadius: theme.radius.lg, borderTopRightRadius: theme.radius.lg }}
              />
            ) : null}
            <View style={{ padding: theme.spacing.md }}>
              <Text numberOfLines={1} style={{ fontFamily: theme.typography.fontBold, color: theme.colors.textPrimary }}>{item.name}</Text>
              <Text style={{ color: theme.colors.textSecondary, fontFamily: theme.typography.fontRegular }}>
                {item.discount_price ? `${item.discount_price} (خصم)` : item.base_price}
              </Text>
            </View>
          </View>
        )}
      />

      {/* Banner Middle */}
      <BannerPlacement placement="HOME_MIDDLE" onNavigate={(name, params) => navigation.navigate(name, params)} />

      {/* Ad Slot 2 */}
      <AdBannerSlot position="slot2" onNavigate={(name, params) => navigation.navigate(name, params)} />

      {/* Banner Bottom */}
      <BannerPlacement placement="HOME_BOTTOM" onNavigate={(name, params) => navigation.navigate(name, params)} />

      {/* Top Stores */}
      <View style={{ paddingHorizontal: theme.spacing.lg, paddingTop: theme.spacing.lg, flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
        <Text style={{ fontSize: theme.typography.sizes.lg, fontFamily: theme.typography.fontBold, color: theme.colors.textPrimary }}>أفضل المتاجر</Text>
        <TouchableOpacity onPress={() => navigation.navigate('Stores')}>
          <Text style={{ color: theme.colors.accent, fontFamily: theme.typography.fontBold }}>عرض الكل</Text>
        </TouchableOpacity>
      </View>
      <FlatList
        horizontal
        data={topStores}
        keyExtractor={(it) => String(it.id)}
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={{ paddingHorizontal: theme.spacing.lg }}
        renderItem={({ item: s }) => (
          <TouchableOpacity onPress={() => navigation.navigate('StoreDetail', { id: s.id })} style={{ width: 220, marginRight: theme.spacing.md }}>
            <View style={{ height: 110, borderRadius: theme.radius.lg, backgroundColor: theme.colors.surface, borderWidth: 1, borderColor: theme.colors.cardBorder, alignItems: 'center', justifyContent: 'center', ...theme.shadows.card }}>
              {s.logo ? <Image source={{ uri: s.logo }} style={{ width: 220, height: 110, borderRadius: theme.radius.lg }} /> : <Text style={{ color: theme.colors.textPrimary, fontFamily: theme.typography.fontBold }}>{s.name}</Text>}
            </View>
            <Text style={{ fontFamily: theme.typography.fontBold, marginTop: theme.spacing.sm, color: theme.colors.textPrimary, textAlign: I18nManager.isRTL ? 'right' : 'left' }}>{s.name}</Text>
            <Text style={{ color: theme.colors.textSecondary, fontFamily: theme.typography.fontRegular, textAlign: I18nManager.isRTL ? 'right' : 'left' }}>تقييم: {s.store_rating ?? 0}</Text>
          </TouchableOpacity>
        )}
      />

      {/* New Arrivals title for grid below */}
      <View style={{ paddingHorizontal: theme.spacing.lg, paddingTop: theme.spacing.lg, flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
        <Text style={{ fontSize: theme.typography.sizes.lg, fontFamily: theme.typography.fontBold, color: theme.colors.textPrimary }}>وصل حديثًا</Text>
        <TouchableOpacity onPress={() => navigation.navigate('Products', { mode: 'all' })}>
          <Text style={{ color: theme.colors.accent, fontFamily: theme.typography.fontBold }}>عرض الكل</Text>
        </TouchableOpacity>
      </View>

      {/* Recommended */}
      <View style={{ paddingHorizontal: theme.spacing.lg, paddingTop: theme.spacing.lg, flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
        <Text style={{ fontSize: theme.typography.sizes.lg, fontFamily: theme.typography.fontBold, color: theme.colors.textPrimary }}>مقترح لك</Text>
        <TouchableOpacity onPress={() => navigation.navigate('Products', { mode: 'all' })}>
          <Text style={{ color: theme.colors.accent, fontFamily: theme.typography.fontBold }}>عرض الكل</Text>
        </TouchableOpacity>
      </View>
      <FlatList
        horizontal
        data={recommended}
        keyExtractor={(it) => String(it.id)}
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={{ paddingHorizontal: theme.spacing.lg }}
        renderItem={({ item }) => (
          <View style={{ width: 220, marginRight: theme.spacing.md, borderWidth: 1, borderColor: theme.colors.cardBorder, borderRadius: theme.radius.lg, backgroundColor: theme.colors.surface, ...theme.shadows.card }}>
            {item.main_image?.image_url ? <Image source={{ uri: item.main_image.image_url }} style={{ width: 220, height: 110, borderTopLeftRadius: theme.radius.lg, borderTopRightRadius: theme.radius.lg }} /> : null}
            <View style={{ padding: theme.spacing.md }}>
              <Text numberOfLines={1} style={{ fontFamily: theme.typography.fontBold, color: theme.colors.textPrimary }}>{item.name}</Text>
              <Text style={{ color: theme.colors.textSecondary, fontFamily: theme.typography.fontRegular }}>{item.base_price}</Text>
            </View>
          </View>
        )}
      />
      
    </View>
  ); };

  if (isEmpty) {
    return (
      <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center', padding: 16 }}>
        <Text style={{ marginBottom: 12, textAlign: 'center' }}>لا توجد بيانات للعرض حالياً.</Text>
        <Button title="إنشاء بيانات تجريبية" onPress={async () => { await devSeed(); await load(); }} />
      </View>
    );
  }

  const newArrivals = products.slice(0, 6);
  return (
    <FlatList
      data={newArrivals}
      keyExtractor={(it) => String(it.id)}
      style={{ backgroundColor: theme.colors.background }}
      numColumns={2}
      columnWrapperStyle={{ paddingHorizontal: theme.spacing.lg }}
      
      ListHeaderComponent={<ListHeader />}
      
      onScroll={(ev) => {
        try {
          console.log('[Home] scroll y=', ev.nativeEvent.contentOffset?.y ?? 0);
        } catch {}
      }}
      contentContainerStyle={{ paddingBottom: 100 }}
      renderItem={({ item }) => (
        <View style={{ flex: 1, margin: theme.spacing.sm, borderWidth: 1, borderColor: theme.colors.cardBorder, borderRadius: theme.radius.lg, backgroundColor: theme.colors.surface, ...theme.shadows.card }}>
          {item.main_image?.url || item.main_image?.image_url ? (
            <Image
              source={{ uri: item.main_image.url || item.main_image.image_url }}
              style={{ width: '100%', height: 160, borderTopLeftRadius: theme.radius.lg, borderTopRightRadius: theme.radius.lg }}
            />
          ) : null}
          <View style={{ padding: theme.spacing.md }}>
            <Text numberOfLines={2} style={{ fontFamily: theme.typography.fontBold, color: theme.colors.textPrimary, textAlign: I18nManager.isRTL ? 'right' : 'left' }}>{item.name}</Text>
            <Text style={{ marginTop: theme.spacing.xs, color: theme.colors.textSecondary, fontFamily: theme.typography.fontRegular, textAlign: I18nManager.isRTL ? 'right' : 'left' }}>{item.base_price}</Text>
            <View style={{ flexDirection: 'row', marginTop: 8 }}>
              <Button color={theme.colors.accent} title="أضف للسلة" onPress={async () => {
                if (!accessToken) {
                  navigation.navigate('Login', { next: { action: 'add_to_cart', product_id: item.id, variant_id: null, quantity: 1, returnTo: 'Home' } });
                  return;
                }
                try {
                  await addToCart(item.id, null, 1);
                  Alert.alert('تم', 'تمت إضافة المنتج إلى السلة');
                  setCartCount((x) => x + 1);
                } catch (e) {
                  Alert.alert('خطأ', 'فشل إضافة المنتج للسلة');
                }
              }} />
              <View style={{ width: 8 }} />
              <Button title="تفاصيل" onPress={() => navigation.navigate('ProductDetail', { productId: item.id })} />
            </View>
          </View>
        </View>
      )}
      ListEmptyComponent={
        <View style={{ padding: 24, alignItems: 'center' }}>
          <Text style={{ marginBottom: 12, textAlign: 'center', color: theme.colors.textPrimary, fontFamily: theme.typography.fontRegular }}>لا توجد منتجات للعرض حالياً.</Text>
          <Button title="إعادة المحاولة" onPress={load} />
        </View>
      }
    />
  );
}
