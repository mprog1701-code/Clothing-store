import React from 'react';
import { View, Text, Image, Pressable, StyleSheet } from 'react-native';
import { COLORS } from '../theme/colors';

export default function ProductCard({ product, onPress }) {
  const priceText = product?.price ? `${Number(product.price).toLocaleString()} د.ع` : '';
  return (
    <Pressable style={styles.card} onPress={onPress}>
      <Image
        source={{ uri: product?.image || 'https://placehold.co/300x300/e94560/ffffff?text=Product' }}
        style={styles.image}
      />
      <View style={styles.info}>
        <Text style={styles.name} numberOfLines={1}>
          {product?.name || 'منتج مميز'}
        </Text>
        <Text style={styles.price}>{priceText}</Text>
      </View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: COLORS.surface,
    borderRadius: 15,
    overflow: 'hidden',
    marginBottom: 12,
  },
  image: {
    width: '100%',
    height: 180,
  },
  info: {
    padding: 12,
  },
  name: {
    color: COLORS.text,
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 6,
  },
  price: {
    color: COLORS.primary,
    fontSize: 16,
    fontWeight: 'bold',
  },
});
