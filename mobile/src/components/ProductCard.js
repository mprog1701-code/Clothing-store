import React from 'react';
import { View, Text, Image, TouchableOpacity, StyleSheet, Dimensions } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Colors } from '../constants/Colors';
import { Ionicons } from '@expo/vector-icons';
import { useNavigation } from '@react-navigation/native';

const { width } = Dimensions.get('window');
const cardWidth = (width - 40) / 2;

const ProductCard = ({ product, addToCart }) => {
  const navigation = useNavigation();

  return (
    <View style={styles.card}>
      <TouchableOpacity 
        activeOpacity={0.9}
        onPress={() => navigation.navigate('ProductDetail', { productId: product.id })}
      >
        <Image 
          source={
            product.image 
              ? { uri: product.image } 
              : { uri: 'https://placehold.co/400x400?text=Product' }
          } 
          style={styles.image} 
        />
        
        {/* Badge */}
        {product.is_new && (
          <LinearGradient
            colors={[Colors.primaryStart, Colors.primaryEnd]}
            style={styles.badge}
          >
            <Text style={styles.badgeText}>جديد</Text>
          </LinearGradient>
        )}

        <View style={styles.content}>
          <Text numberOfLines={1} style={styles.name}>{product.name}</Text>
          <Text style={styles.price}>{product.price?.toLocaleString()} د.ع</Text>
          
          <View style={styles.buttons}>
            <TouchableOpacity 
              style={styles.detailsBtn}
              onPress={() => navigation.navigate('ProductDetail', { productId: product.id })}
            >
              <Text style={styles.detailsBtnText}>تفاصيل</Text>
            </TouchableOpacity>
            
            <TouchableOpacity 
              activeOpacity={0.8}
              onPress={() => addToCart && addToCart(product)}
              style={styles.cartBtnWrapper}
            >
              <LinearGradient
                colors={[Colors.primaryStart, Colors.primaryEnd]}
                style={styles.cartBtn}
              >
                <Ionicons name="cart-outline" size={18} color="#fff" />
              </LinearGradient>
            </TouchableOpacity>
          </View>
        </View>
      </TouchableOpacity>
    </View>
  );
};

const styles = StyleSheet.create({
  card: {
    backgroundColor: Colors.card,
    borderRadius: 15,
    overflow: 'hidden',
    marginBottom: 15,
    width: cardWidth,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 5,
    marginHorizontal: 5,
  },
  image: {
    width: '100%',
    height: 180,
    resizeMode: 'cover',
  },
  badge: {
    position: 'absolute',
    top: 10,
    right: 10,
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 20,
  },
  badgeText: {
    color: '#fff',
    fontWeight: 'bold',
    fontSize: 10,
  },
  content: {
    padding: 12,
  },
  name: {
    fontSize: 14,
    fontWeight: 'bold',
    color: Colors.textPrimary,
    marginBottom: 5,
    textAlign: 'right',
  },
  price: {
    fontSize: 16,
    fontWeight: 'bold',
    color: Colors.primaryStart,
    marginBottom: 10,
    textAlign: 'right',
  },
  buttons: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: 8,
  },
  detailsBtn: {
    flex: 2,
    paddingVertical: 8,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: Colors.primaryStart,
    alignItems: 'center',
  },
  detailsBtnText: {
    color: Colors.primaryStart,
    fontWeight: 'bold',
    fontSize: 12,
  },
  cartBtnWrapper: {
    flex: 1,
  },
  cartBtn: {
    paddingVertical: 8,
    borderRadius: 20,
    alignItems: 'center',
    justifyContent: 'center',
  },
});

export default ProductCard;
