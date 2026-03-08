import React from 'react';
import { View, Text, Image, TouchableOpacity, StyleSheet, Dimensions } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { COLORS } from '../constants/Colors';
import { Ionicons } from '@expo/vector-icons';
import { useNavigation } from '@react-navigation/native';

const { width } = Dimensions.get('window');

const ProductCard = ({ product, addToCart }) => {
  const navigation = useNavigation();

  return (
    <View style={styles.productCard}>
      {/* Badge */}
      {(product.badge || product.is_new) && (
        <View style={styles.badge}>
          <Text style={styles.badgeText}>{product.badge || 'جديد'}</Text>
        </View>
      )}
      
      {/* Image */}
      <TouchableOpacity 
        activeOpacity={0.9}
        onPress={() => navigation.navigate('ProductDetail', { productId: product.id })}
      >
        <Image 
          source={{ uri: product.image || 'https://placehold.co/400x400?text=Product' }} 
          style={styles.productImage} 
        />
      </TouchableOpacity>
      
      {/* Wishlist */}
      <TouchableOpacity style={styles.wishlist}>
        <Ionicons name="heart-outline" size={20} color={COLORS.primary} />
      </TouchableOpacity>
      
      {/* Info */}
      <View style={styles.productInfo}>
        <Text style={styles.productName} numberOfLines={2}>{product.name}</Text>
        
        {/* Rating & Stock */}
        <View style={styles.metaRow}>
          <View style={styles.rating}>
            <Ionicons name="star" size={14} color={COLORS.gold} />
            <Text style={styles.ratingText}>{product.rating || '5.0'}</Text>
          </View>
          
          {product.inStock !== undefined && (
            <View style={styles.stockInfo}>
              <Ionicons 
                name={product.inStock ? "checkmark-circle" : "close-circle"} 
                size={14} 
                color={product.inStock ? COLORS.success : COLORS.error} 
              />
              <Text style={[styles.stockText, { color: product.inStock ? COLORS.success : COLORS.error }]}>
                {product.inStock ? "متوفر" : "غير متوفر"}
              </Text>
            </View>
          )}
        </View>
        
        {/* Price */}
        <View style={styles.priceRow}>
          <Text style={styles.price}>{product.price?.toLocaleString()} د.ع</Text>
          {product.oldPrice && (
            <Text style={styles.oldPrice}>{product.oldPrice?.toLocaleString()}</Text>
          )}
        </View>
        
        {/* Buttons */}
        <View style={styles.cardActions}>
          <TouchableOpacity 
            style={styles.detailsBtn}
            onPress={() => navigation.navigate('ProductDetail', { productId: product.id })}
          >
            <Text style={styles.detailsBtnText}>تفاصيل</Text>
          </TouchableOpacity>
          
          <TouchableOpacity 
            activeOpacity={0.8}
            onPress={() => addToCart && addToCart(product)}
          >
            <LinearGradient
              colors={[COLORS.gradientStart, COLORS.gradientEnd]}
              style={styles.addBtn}
            >
              <Ionicons name="cart" size={20} color="#fff" />
            </LinearGradient>
          </TouchableOpacity>
        </View>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  productCard: {
    width: (width - 45) / 2,
    backgroundColor: COLORS.card,
    borderRadius: 15,
    marginBottom: 15,
    overflow: 'hidden',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 5,
  },
  badge: {
    position: 'absolute',
    top: 10,
    right: 10,
    backgroundColor: COLORS.primary,
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 10,
    zIndex: 1,
  },
  badgeText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: 'bold',
  },
  wishlist: {
    position: 'absolute',
    top: 10,
    left: 10,
    backgroundColor: '#fff',
    width: 35,
    height: 35,
    borderRadius: 17.5,
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 1,
  },
  productImage: {
    width: '100%',
    height: 180,
    resizeMode: 'cover',
  },
  productInfo: {
    padding: 12,
  },
  productName: {
    fontSize: 14,
    fontWeight: 'bold',
    color: COLORS.text,
    marginBottom: 5,
    textAlign: 'right',
  },
  metaRow: {
    flexDirection: 'row-reverse',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  rating: {
    flexDirection: 'row-reverse',
    alignItems: 'center',
    gap: 5,
  },
  ratingText: {
    color: COLORS.text,
    fontSize: 12,
  },
  stockInfo: {
    flexDirection: 'row-reverse',
    alignItems: 'center',
    gap: 4,
  },
  stockText: {
    fontSize: 11,
    fontWeight: 'bold',
  },
  priceRow: {
    flexDirection: 'row-reverse',
    alignItems: 'center',
    gap: 8,
    marginBottom: 10,
  },
  price: {
    fontSize: 16,
    fontWeight: 'bold',
    color: COLORS.primary,
  },
  oldPrice: {
    fontSize: 12,
    color: COLORS.textMuted,
    textDecorationLine: 'line-through',
  },
  cardActions: {
    flexDirection: 'row-reverse',
    gap: 8,
    alignItems: 'center',
  },
  detailsBtn: {
    flex: 1,
    paddingVertical: 8,
    borderRadius: 20,
    borderWidth: 1.5,
    borderColor: COLORS.primary,
    alignItems: 'center',
  },
  detailsBtnText: {
    color: COLORS.primary,
    fontWeight: 'bold',
    fontSize: 12,
  },
  addBtn: {
    width: 40,
    height: 40,
    borderRadius: 20,
    justifyContent: 'center',
    alignItems: 'center',
  },
});

export default ProductCard;
