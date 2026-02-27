import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { View, Text, TextInput, Button, ActivityIndicator, I18nManager, TouchableOpacity, StatusBar, FlatList, Pressable, Alert } from 'react-native';
import { getProduct, addCartItemVariant } from '../api';
import theme from '../theme';
import { useAuth } from '../auth/AuthContext';
import ImageCarousel from '../components/ImageCarousel';
import ColorSelector from '../components/ColorSelector';
import SizeSelector from '../components/SizeSelector';
import LoginRequiredSheet from '../components/LoginRequiredSheet';
import { Image as ExpoImage } from 'expo-image';
import { SafeAreaView } from 'react-native-safe-area-context';

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
  const { accessToken } = useAuth();
  const [carouselIndex, setCarouselIndex] = useState(0);
  const [descExpanded, setDescExpanded] = useState(false);

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
      const firstVariant = (p?.variants || [])[0] || null;
      setSelectedVariantId(firstVariant ? firstVariant.id : null);
      if (firstVariant) {
        setColor(firstVariant.color_name || '');
        const firstSize = (firstVariant.sizes || [])[0]?.value || null;
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

  const selectedVariant = useMemo(() => {
    const arr = product?.variants || [];
    return arr.find((v) => v.id === selectedVariantId) || null;
  }, [product, selectedVariantId]);

  const getVariantImages = useCallback((v, p) => {
    const vi = v?.images || v?.imageUrls || [];
    if (Array.isArray(vi) && vi.length) return vi.map((x) => (typeof x === 'string' ? { url: x } : x));
    const pi = p?.images || p?.imageUrls || [];
    return Array.isArray(pi) ? pi.map((x) => (typeof x === 'string' ? { url: x } : x)) : [];
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

  const imagesForSelected = useMemo(() => getVariantImages(selectedVariant, product), [getVariantImages, selectedVariant, product]);
  const priceDisplay = useMemo(() => getVariantPrice(selectedVariant, product), [getVariantPrice, selectedVariant, product]);
  const canAdd = useMemo(() => {
    if (!selectedVariant) return false;
    if (!isVariantInStock(selectedVariant)) return false;
    const needsSize = Array.isArray(selectedVariant?.sizes) && selectedVariant.sizes.length > 0;
    if (needsSize && !size) return false;
    return true;
  }, [selectedVariant, size, isVariantInStock]);

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
    const variantId = selectedVariant?.id;
    const qtyNum = qty || 1;
    const sizeVal = size || (selectedVariant?.sizes || [])[0]?.value || null;
    if (!variantId) return;
    if (!accessToken) {
      setSheetVisible(true);
      return;
    }
    try {
      const data = await addCartItemVariant({ variant_id: variantId, qty: qtyNum, size: sizeVal });
      navigation.navigate('Cart');
    } catch {}
  };

  const content = (
    <View>
      <View style={{ paddingHorizontal: theme.spacing.lg, paddingTop: theme.spacing.md, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' }}>
        <Text style={{ fontFamily: theme.typography.fontBold, fontSize: theme.typography.sizes.md, color: theme.colors.textPrimary, textAlign: I18nManager.isRTL ? 'right' : 'left' }}>{product?.name}</Text>
        <View style={{ flexDirection: 'row' }}>
          <TouchableOpacity style={{ marginHorizontal: theme.spacing.xs }}>
            <Text style={{ color: theme.colors.textSecondary }}>♡</Text>
          </TouchableOpacity>
        </View>
      </View>
      <ImageCarousel images={imagesForSelected} onIndexChange={setCarouselIndex} flatListRef={carouselRef} />
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
      <ColorSelector variants={product?.variants || []} selectedId={selectedVariantId} onSelect={onSelectVariant} />
      <SizeSelector sizes={selectedVariant?.sizes || []} selectedSize={size} onSelect={setSize} />
      <View style={{ paddingHorizontal: theme.spacing.lg }}>
        <Text numberOfLines={descExpanded ? undefined : 3} style={{ color: theme.colors.textSecondary, fontFamily: theme.typography.fontRegular, textAlign: I18nManager.isRTL ? 'right' : 'left' }}>{product?.description}</Text>
        <Pressable onPress={() => setDescExpanded((v) => !v)} style={{ marginTop: theme.spacing.xs }}>
          <Text style={{ color: theme.colors.accent, fontFamily: theme.typography.fontBold }}>{descExpanded ? 'إخفاء' : 'عرض المزيد'}</Text>
        </Pressable>
      </View>
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
              <Text style={{ fontFamily: theme.typography.fontBold, color: theme.colors.textPrimary }}>{priceDisplay}</Text>
              <TouchableOpacity
                onPress={() => {
                  if (!canAdd) {
                    Alert.alert('تنبيه', 'اختر اللون/المقاس');
                    return;
                  }
                  onAddToCart();
                }}
                disabled={!canAdd}
                style={{
                  paddingVertical: theme.spacing.md,
                  paddingHorizontal: theme.spacing.lg,
                  borderRadius: theme.radius.lg,
                  backgroundColor: !canAdd ? theme.colors.surfaceAlt : theme.colors.accent,
                }}
              >
                <Text style={{ color: '#000', fontFamily: theme.typography.fontBold }}>{isVariantInStock(selectedVariant) ? 'أضف للسلة' : 'غير متوفر'}</Text>
              </TouchableOpacity>
            </View>
          </View>
        </>
      )}
      <LoginRequiredSheet
        visible={sheetVisible}
        onLogin={() => {
          setSheetVisible(false);
          const variantId = selectedVariant?.id;
          const qtyNum = qty || 1;
          const sizeVal = size || (selectedVariant?.sizes || [])[0]?.value || null;
          navigation.navigate('Login', { next: { action: 'add_to_cart', variant_id: variantId, quantity: qtyNum, size: sizeVal } });
        }}
        onClose={() => setSheetVisible(false)}
      />
    </SafeAreaView>
  );
}
