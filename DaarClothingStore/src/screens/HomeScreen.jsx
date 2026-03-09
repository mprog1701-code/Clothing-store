import React from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, Image } from 'react-native';
import { COLORS } from '../theme/colors';
import CategoryCard from '../components/CategoryCard';

const { LinearGradient } = require('expo-linear-gradient');

export default function HomeScreen({ navigation }) {
  return (
    <ScrollView style={styles.container}>
      <LinearGradient colors={[COLORS.primary, COLORS.secondary]} style={styles.hero}>
        <Text style={styles.heroTitle}>أفضل الماركات العالمية</Text>
        <Text style={styles.heroSubtitle}>في العراق</Text>
        <TouchableOpacity style={styles.cta} onPress={() => navigation.navigate('Products')}>
          <Text style={styles.ctaText}>ابدأ التسوق الآن</Text>
        </TouchableOpacity>
      </LinearGradient>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>تسوق حسب القسم</Text>
        <View style={styles.categories}>
          <CategoryCard title="رجالي" icon="👔" />
          <CategoryCard title="نسائي" icon="👗" />
          <CategoryCard title="أطفال" icon="👶" />
        </View>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>المنتجات المميزة</Text>
        <TouchableOpacity
          style={styles.productCard}
          onPress={() => navigation.navigate('ProductDetail')}
        >
          <Image
            source={{ uri: 'https://placehold.co/300x300/e94560/ffffff?text=Product' }}
            style={styles.productImage}
          />
          <View style={styles.productInfo}>
            <Text style={styles.productName}>قميص نسائي عصري</Text>
            <Text style={styles.productPrice}>45,000 د.ع</Text>
          </View>
        </TouchableOpacity>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  hero: {
    height: 300,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  heroTitle: {
    fontSize: 32,
    fontWeight: 'bold',
    color: COLORS.text,
    marginBottom: 10,
  },
  heroSubtitle: {
    fontSize: 24,
    color: COLORS.text,
    marginBottom: 20,
  },
  cta: {
    backgroundColor: 'rgba(255,255,255,0.2)',
    paddingHorizontal: 30,
    paddingVertical: 15,
    borderRadius: 25,
  },
  ctaText: {
    color: COLORS.text,
    fontSize: 16,
    fontWeight: 'bold',
  },
  section: {
    padding: 15,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: COLORS.text,
    marginBottom: 15,
  },
  categories: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  productCard: {
    backgroundColor: COLORS.surface,
    borderRadius: 15,
    overflow: 'hidden',
  },
  productImage: {
    width: '100%',
    height: 200,
  },
  productInfo: {
    padding: 15,
  },
  productName: {
    color: COLORS.text,
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 5,
  },
  productPrice: {
    color: COLORS.primary,
    fontSize: 20,
    fontWeight: 'bold',
  },
});
