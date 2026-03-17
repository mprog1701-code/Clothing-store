import React from 'react';
import { View, Text, Pressable, StyleSheet, I18nManager } from 'react-native';
import { Image } from 'expo-image';
import { Ionicons } from '@expo/vector-icons';
import { useNavigation } from '@react-navigation/native';
import theme from '../theme';

const FALLBACK_IMAGE = 'https://placehold.co/600x600?text=Product';

function toIQD(value) {
  const number = Number(value || 0);
  if (!Number.isFinite(number)) return '0';
  return number.toLocaleString('en-US');
}

export default function ProductCard({ product, addToCart, style }) {
  const navigation = useNavigation();
  const productId = product?.id;
  const title = product?.name || product?.title || 'منتج';
  const price = product?.price ?? product?.base_price ?? product?.final_price ?? 0;
  const oldPrice = product?.oldPrice ?? product?.old_price ?? null;
  const rating = Number(product?.rating || 0);
  const imageUri = product?.image || product?.image_url || product?.thumbnail || FALLBACK_IMAGE;

  const openDetails = () => {
    if (!productId) return;
    navigation.navigate('ProductDetail', { productId });
  };

  return (
    <Pressable onPress={openDetails} style={[styles.card, style]}>
      <View style={styles.imageWrap}>
        <Image source={{ uri: imageUri }} style={styles.image} contentFit="cover" transition={200} cachePolicy="memory-disk" />
        {(product?.badge || product?.is_new) ? (
          <View style={styles.badge}>
            <Text style={styles.badgeText}>{product?.badge || 'جديد'}</Text>
          </View>
        ) : null}
        <Pressable
          onPress={(event) => {
            event.stopPropagation();
            if (addToCart) addToCart(product);
          }}
          hitSlop={8}
          style={styles.cartIconBtn}
        >
          <Ionicons name="cart-outline" size={18} color={theme.colors.textPrimary} />
        </Pressable>
      </View>

      <View style={styles.info}>
        <Text style={styles.title} numberOfLines={2}>{title}</Text>
        <View style={styles.metaRow}>
          <Text style={styles.price}>{toIQD(price)} د.ع</Text>
          <View style={styles.ratingWrap}>
            <Ionicons name="star" size={13} color="#FFD700" />
            <Text style={styles.ratingText}>{rating > 0 ? rating.toFixed(1) : '—'}</Text>
          </View>
        </View>
        {oldPrice ? <Text style={styles.oldPrice}>{toIQD(oldPrice)} د.ع</Text> : null}
      </View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  card: {
    width: '100%',
    backgroundColor: theme.colors.surface,
    borderRadius: theme.radius.lg,
    borderWidth: 1,
    borderColor: theme.colors.cardBorder,
    overflow: 'hidden',
    ...theme.shadows.card,
  },
  imageWrap: {
    position: 'relative',
    height: 170,
    backgroundColor: theme.colors.surfaceAlt,
  },
  image: {
    width: '100%',
    height: '100%',
  },
  badge: {
    position: 'absolute',
    top: 10,
    right: 10,
    backgroundColor: theme.colors.accent,
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 100,
  },
  badgeText: {
    color: theme.colors.textPrimary,
    fontFamily: theme.typography.fontBold,
    fontSize: theme.typography.sizes.xs,
  },
  cartIconBtn: {
    position: 'absolute',
    bottom: 10,
    left: 10,
    width: 34,
    height: 34,
    borderRadius: 17,
    backgroundColor: 'rgba(15,15,35,0.85)',
    borderWidth: 1,
    borderColor: theme.colors.cardBorder,
    alignItems: 'center',
    justifyContent: 'center',
  },
  info: {
    paddingHorizontal: 10,
    paddingVertical: 10,
  },
  title: {
    color: theme.colors.textPrimary,
    fontFamily: theme.typography.fontBold,
    fontSize: theme.typography.sizes.md,
    textAlign: I18nManager.isRTL ? 'right' : 'left',
    minHeight: 42,
  },
  metaRow: {
    marginTop: 8,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  price: {
    color: theme.colors.accent,
    fontFamily: theme.typography.fontBold,
    fontSize: theme.typography.sizes.md,
  },
  oldPrice: {
    marginTop: 3,
    color: theme.colors.textSecondary,
    fontFamily: theme.typography.fontRegular,
    fontSize: theme.typography.sizes.xs,
    textDecorationLine: 'line-through',
    textAlign: I18nManager.isRTL ? 'right' : 'left',
  },
  ratingWrap: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  ratingText: {
    color: theme.colors.textSecondary,
    fontFamily: theme.typography.fontRegular,
    fontSize: theme.typography.sizes.xs,
  },
});
