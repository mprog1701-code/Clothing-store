import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { View, Text, TextInput, Button, ActivityIndicator, I18nManager, TouchableOpacity, StatusBar, FlatList, Pressable, Alert } from 'react-native';
import { getProduct, addCartItemVariant } from '../api';
import theme from '../theme';
import { useAuth } from '../auth/AuthContext';
import { useCart } from '../cart/CartContext';
import ImageCarousel from '../components/ImageCarousel';
import ColorSelector from '../components/ColorSelector';
import SizeSelector from '../components/SizeSelector';
import LoginRequiredSheet from '../components/LoginRequiredSheet';
import { Image as ExpoImage } from 'expo-image';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';

export default function ProductDetailScreen({ route, navigation }) {
  const { productId = null } = route.params || {};
  const [product, setProduct] = useState(null);
  const [color, setColor] = useState('');
  const [size, setSize] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedVariantId, setSelectedVariantId] = useState(null);
  const [qty, setQty] = useState(1);
  const [sheetVisible, setSheetVisible] = useState(false);
  const carouselRef = useRef(null);
  const { accessToken, user } = useAuth();
  const { addToCartCount, refreshCartCount } = useCart();
  const [carouselIndex, setCarouselIndex] = useState(0);
  const [descExpanded, setDescExpanded] = useState(false);
  const [liked, setLiked] = useState(false);
  const [toastVisible, setToastVisible] = useState(false);

  const load = async () => {
    setError('');
    if (!productId) {
      setLoading(false);
      setError('معرّف المنتج غير متوفر');
      return;
    }
    try {
      const p = await getProduct(productId);
      setProduct(p);
      const variants = p?.variants || [];
      const images = p?.images || [];
      const pickHasImages = (v) => {
        const vi = v?.images || [];
        if (Array.isArray(vi) && vi.length) return true;
        const ck = String(v?.color_key || '').trim();
        const cn = String(v?.color_name || '').trim().toLowerCase();
        const co = v?.color_obj_id || null;
        const ca = v?.color_attr_id || null;
        const match = Array.isArray(images)
          ? images.some((im) => {
              const imKey = String(im?.color_key || '').trim();
              const imName = String(im?.color_name || '').trim().toLowerCase();
              const imCo = im?.color_obj_id || null;
              const imCa = im?.color_attr_id || null;
              if (ck && imKey && ck === imKey) return true;
              if (cn && imName && cn === imName) return true;
              if (co && imCo && co === imCo) return true;
              if (ca && imCa && ca === imCa) return true;
              return false;
            })
          : false;
        return !!match;
      };
      const initialVariant = variants.find(pickHasImages) || variants[0] || null;
      setSelectedVariantId(initialVariant ? initialVariant.id : null);
      if (initialVariant) {
        setColor(initialVariant.color_name || '');
        const firstSize = (initialVariant.sizes || [])[0]?.value || null;
        setSize(firstSize);
      }
    } catch (e) {
      setError('تعذر تحميل بيانات المنتج');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);
  useEffect(() => {
    if (product) {
      try {
        const imagesLen = Array.isArray(product.images) ? product.images.length : 0;
        const variantsLen = Array.isArray(product.variants) ? product.variants.length : 0;
        const v0ImagesLen = Array.isArray(product.variants?.[0]?.images) ? product.variants[0].images.length : 0;
        console.log('[DIAG] product keys:', Object.keys(product || {}));
        console.log('[DIAG] imagesLen=', imagesLen, 'variantsLen=', variantsLen, 'v0ImagesLen=', v0ImagesLen);
      } catch {}
    }
  }, [product]);

  const selectedVariant = useMemo(() => {
    const arr = product?.variants || [];
    return arr.find((v) => v.id === selectedVariantId) || null;
  }, [product, selectedVariantId]);
  const selectedVariantForSize = useMemo(() => {
    const arr = product?.variants || [];
    if (!selectedVariant) return null;
    const sizeVal = size || (selectedVariant?.sizes || [])[0]?.value || null;
    if (!sizeVal) return selectedVariant;
    const co = selectedVariant?.color_obj_id || null;
    const ca = selectedVariant?.color_attr_id || null;
    const match = arr.find((v) => {
      const sameColor =
        (co && v.color_obj_id === co) ||
        (ca && v.color_attr_id === ca) ||
        (!co && !ca && !(v.color_obj_id || v.color_attr_id));
      const sameSize =
        (typeof v.size === 'string' && v.size === sizeVal) ||
        (typeof v.size_display === 'string' && v.size_display === sizeVal);
      return sameColor && sameSize;
    });
    return match || selectedVariant;
  }, [product, selectedVariant, size]);

  const getVariantImages = useCallback((v, p) => {
    const normalizeToken = (val) =>
      String(val || '')
        .trim()
        .toLowerCase()
        .replace(/[أإآ]/g, 'ا')
        .replace(/ى/g, 'ي')
        .replace(/ة/g, 'ه');
    const asNum = (val) => {
      const n = Number(val);
      return Number.isFinite(n) ? n : null;
    };
    const sameId = (a, b) => {
      const na = asNum(a);
      const nb = asNum(b);
      return na !== null && nb !== null && na === nb;
    };
    const vi = v?.images || [];
    if (Array.isArray(vi) && vi.length) return vi.map((x) => (typeof x === 'string' ? { url: x } : x));
    const pi = p?.images || [];
    const ck = String(v?.color_key || '').trim();
    const cn = normalizeToken(v?.color_name || v?.color);
    const co = v?.color_obj_id || null;
    const ca = v?.color_attr_id || null;
    const cv = v?.id || null;
    const filtered = Array.isArray(pi)
      ? pi.filter((im) => {
          const imKey = String(im?.color_key || '').trim();
          const imName = normalizeToken(im?.color_name);
          const imCo = im?.color_obj_id || null;
          const imCa = im?.color_attr_id || null;
          const imColorId = im?.color_id || null;
          const imVariantId = im?.variant_id || null;
          if (ck && imKey && ck === imKey) return true;
          if (cn && imName && cn === imName) return true;
          if (co && (sameId(co, imCo) || sameId(co, imColorId))) return true;
          if (ca && (sameId(ca, imCa) || sameId(ca, imColorId))) return true;
          if (cv && sameId(cv, imVariantId)) return true;
          return false;
        })
      : [];
    const hasTaggedPool = Array.isArray(pi)
      ? pi.some((im) => {
          const key = String(im?.color_key || '').trim();
          const name = normalizeToken(im?.color_name);
          const cid = im?.color_id ?? im?.color_attr_id ?? im?.color_obj_id;
          return !!key || !!name || cid !== null && cid !== undefined;
        })
      : false;
    let src = filtered;
    const mi = p?.main_image || null;
    const hasMain = mi && (mi.url || mi.image_url);
    if (!src.length && !hasTaggedPool && Array.isArray(pi) && pi.length) {
      src = pi;
    }
    if (!src.length && hasMain && !hasTaggedPool) {
      src = [mi];
    }
    if (__DEV__) {
      try {
        console.log('[PDP] image match', {
          variantId: v?.id || null,
          colorKey: ck || '',
          colorName: cn || '',
          taggedPool: hasTaggedPool,
          filteredCount: filtered.length,
          finalCount: src.length,
        });
      } catch {}
    }
    const mapped = Array.isArray(src) ? src.map((x) => (typeof x === 'string' ? { url: x } : x)) : [];
    const seen = new Set();
    const out = [];
    for (const im of mapped) {
      const u = im.url || im.image_url || String(im);
      const key = String(u).trim();
      if (!key) continue;
      if (seen.has(key)) continue;
      seen.add(key);
      out.push(im);
    }
    return out;
  }, []);

  const getVariantPrice = useCallback((v, p) => {
    return v?.price ?? p?.base_price ?? 0;
  }, []);

  const isVariantInStock = useCallback((v) => {
    if (!v) return false;
    if (typeof v.stock === 'number') return v.stock > 0;
    const sizes = v.sizes || [];
    if (Array.isArray(sizes) && sizes.length) return sizes.some((s) => s.in_stock !== false);
    return true;
  }, []);

  const imagesForSelected = useMemo(
    () => getVariantImages(selectedVariantForSize || selectedVariant, product),
    [getVariantImages, selectedVariantForSize, selectedVariant, product]
  );
  const priceDisplay = useMemo(() => getVariantPrice(selectedVariantForSize || selectedVariant, product), [getVariantPrice, selectedVariantForSize, selectedVariant, product]);
  const canAdd = useMemo(() => {
    if (!selectedVariantForSize) return false;
    const needsSize = Array.isArray(selectedVariant?.sizes) && selectedVariant.sizes.length > 0;
    if (needsSize && !size) return false;
    const qty = Number(selectedVariantForSize?.stock_qty ?? 0);
    return qty > 0;
  }, [selectedVariantForSize, selectedVariant, size]);

  useEffect(() => {
    const preload = async () => {
      const arr = imagesForSelected.slice(0, 3);
      try {
        await Promise.all(arr.map((im) => ExpoImage.prefetch(im.url || im.image_url || im)));
      } catch {}
    };
    preload();
    const idx0 = 0;
    requestAnimationFrame(() => {
      try {
        carouselRef.current?.scrollToIndex({ index: idx0, animated: false });
      } catch {}
    });
  }, [selectedVariantId]);

  const onSelectVariant = async (v) => {
    setSelectedVariantId(v.id);
    const firstSize = (v.sizes || [])[0]?.value || null;
    setSize(firstSize);
    setColor(v.color_name || '');
    console.log('[PDP] local variant switch', v.id);
  };

  const onAddToCart = async () => {
    const variantId = (selectedVariantForSize || selectedVariant)?.id;
    const qtyNum = qty || 1;
    const sizeVal = size || (selectedVariant?.sizes || [])[0]?.value || null;
    if (!variantId) return;
    if (!accessToken) {
      setSheetVisible(true);
      return;
    }
    try {
      await addCartItemVariant({ variant_id: variantId, qty: qtyNum, size: sizeVal, user_id: user?.id });
      addToCartCount(qtyNum);
      refreshCartCount();
      setToastVisible(true);
      setTimeout(() => setToastVisible(false), 1800);
    } catch {}
  };

  const content = (
    <View>
      <View style={{ paddingHorizontal: theme.spacing.lg, paddingTop: theme.spacing.md, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' }}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={{ padding: 6 }}>
          <Ionicons name="arrow-back" size={20} color={theme.colors.textPrimary} />
        </TouchableOpacity>
        <Text style={{ fontFamily: theme.typography.fontBold, fontSize: theme.typography.sizes.md, color: theme.colors.textPrimary, textAlign: I18nManager.isRTL ? 'right' : 'left', flex: 1, marginHorizontal: 8 }}>{product?.name}</Text>
      </View>
      <View style={{ paddingHorizontal: theme.spacing.lg, marginTop: 2, marginBottom: 4 }}>
        <Text style={{ color: theme.colors.textSecondary, fontFamily: theme.typography.fontRegular }}>⭐ {Number(product?.rating || 4.5).toFixed(1)}</Text>
      </View>
      {imagesForSelected.length > 0 ? (
        <View style={{ position: 'relative' }}>
          <ImageCarousel key={`carousel-${selectedVariantId}-${imagesForSelected.length}`} images={imagesForSelected} onIndexChange={setCarouselIndex} flatListRef={carouselRef} />
          <TouchableOpacity
            onPress={() => setLiked((v) => !v)}
            style={{
              position: 'absolute',
              top: 14,
              right: 16,
              width: 38,
              height: 38,
              borderRadius: 19,
              backgroundColor: 'rgba(15,15,35,0.7)',
              borderWidth: 1,
              borderColor: theme.colors.cardBorder,
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <Ionicons name={liked ? 'heart' : 'heart-outline'} size={20} color={liked ? '#FF4D6D' : '#fff'} />
          </TouchableOpacity>
        </View>
      ) : (
        <View style={{ height: 200, alignItems: 'center', justifyContent: 'center', marginHorizontal: theme.spacing.lg, borderWidth: 1, borderColor: theme.colors.cardBorder, borderRadius: theme.radius.lg, backgroundColor: theme.colors.surface }}>
          <Text style={{ color: theme.colors.textSecondary, fontFamily: theme.typography.fontRegular }}>لا توجد صور لهذا اللون</Text>
        </View>
      )}
      <View style={{ alignItems: 'center', justifyContent: 'center', paddingVertical: theme.spacing.sm }}>
        <View style={{ flexDirection: 'row' }}>
          {imagesForSelected.map((_, idx) => (
            <View
              key={idx}
              style={{
                width: 6,
                height: 6,
                borderRadius: 3,
                marginHorizontal: 4,
                backgroundColor: carouselIndex === idx ? theme.colors.accent : theme.colors.cardBorder,
              }}
            />
          ))}
        </View>
      </View>
      <View style={{ paddingHorizontal: theme.spacing.lg }}>
        <Text numberOfLines={descExpanded ? undefined : 3} style={{ color: theme.colors.textSecondary, fontFamily: theme.typography.fontRegular, textAlign: I18nManager.isRTL ? 'right' : 'left', marginTop: 4 }}>{product?.description}</Text>
        <Pressable onPress={() => setDescExpanded((v) => !v)} style={{ marginTop: 4 }}>
          <Text style={{ color: theme.colors.accent, fontFamily: theme.typography.fontBold }}>{descExpanded ? 'إخفاء' : 'عرض المزيد'}</Text>
        </Pressable>
      </View>
      <ColorSelector variants={product?.variants || []} selectedId={selectedVariantId} onSelect={onSelectVariant} />
      <SizeSelector sizes={selectedVariant?.sizes || []} selectedSize={size} onSelect={setSize} />
    </View>
  );

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: theme.colors.background }}>
      <StatusBar barStyle="light-content" backgroundColor={theme.colors.background} />
      {loading ? (
        <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center', backgroundColor: theme.colors.background }}>
          <ActivityIndicator />
        </View>
      ) : error ? (
        <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center', backgroundColor: theme.colors.background }}>
          <Text style={{ color: theme.colors.textSecondary, fontFamily: theme.typography.fontRegular }}>{error}</Text>
          <Button title="إعادة المحاولة" onPress={load} />
        </View>
      ) : (
        <>
          <FlatList data={[{ key: 'content' }]} keyExtractor={(it) => it.key} renderItem={() => content} contentContainerStyle={{ paddingBottom: 96 }} />
          <View style={{ position: 'absolute', bottom: 0, left: 0, right: 0, padding: theme.spacing.lg, backgroundColor: theme.colors.surface, borderTopWidth: 1, borderColor: theme.colors.cardBorder }}>
            <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' }}>
              <Text style={{ fontFamily: theme.typography.fontBold, color: theme.colors.textPrimary, fontSize: theme.typography.sizes.lg }}>{priceDisplay}</Text>
              <TouchableOpacity
                onPress={() => {
                  if (!selectedVariant) {
                    Alert.alert('تنبيه', 'اختر اللون أولاً');
                    return;
                  }
                  if (!canAdd) {
                    Alert.alert('تنبيه', 'المقاس/اللون غير متوفر حالياً');
                    return;
                  }
                  onAddToCart();
                }}
                style={{
                  paddingVertical: theme.spacing.md,
                  paddingHorizontal: theme.spacing.lg,
                  borderRadius: theme.radius.lg,
                  backgroundColor: canAdd ? theme.colors.accent : theme.colors.surfaceAlt,
                }}
              >
                <Text style={{ color: '#000', fontFamily: theme.typography.fontBold }}>{isVariantInStock(selectedVariantForSize || selectedVariant) ? 'أضف للسلة' : 'غير متوفر'}</Text>
              </TouchableOpacity>
            </View>
          </View>
          {toastVisible ? (
            <View style={{ position: 'absolute', bottom: 90, alignSelf: 'center', backgroundColor: 'rgba(25,25,35,0.95)', borderRadius: 14, paddingVertical: 10, paddingHorizontal: 14, borderWidth: 1, borderColor: theme.colors.cardBorder }}>
              <Text style={{ color: '#fff', fontFamily: theme.typography.fontBold }}>تمت إضافة المنتج إلى السلة بنجاح</Text>
            </View>
          ) : null}
        </>
      )}
      <LoginRequiredSheet
        visible={sheetVisible}
        onLogin={() => {
          setSheetVisible(false);
          const variantId = selectedVariant?.id;
          const qtyNum = qty || 1;
          const sizeVal = size || (selectedVariant?.sizes || [])[0]?.value || null;
          navigation.replace('Login', {
            next: {
              action: 'add_to_cart',
              variant_id: variantId,
              quantity: qtyNum,
              size: sizeVal,
              returnTo: { name: 'ProductDetail', params: { productId } },
            },
          });
        }}
        onClose={() => setSheetVisible(false)}
      />
    </SafeAreaView>
  );
}
