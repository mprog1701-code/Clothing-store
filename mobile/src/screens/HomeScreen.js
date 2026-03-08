import React, { useEffect, useState, useCallback } from 'react';
import { 
  View, 
  Text, 
  FlatList, 
  TouchableOpacity, 
  ActivityIndicator, 
  StyleSheet, 
  ScrollView, 
  RefreshControl,
  I18nManager
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
// import Animated, { FadeInDown } from 'react-native-reanimated'; 
import { Ionicons } from '@expo/vector-icons';
import { Colors } from '../constants/Colors';
import ProductCard from '../components/ProductCard';
import BannerCarousel from '../components/BannerCarousel';
import { listProducts, listCategories, listAds, addToCart } from '../api';

const Category = ({ icon, title, onPress }) => (
  <TouchableOpacity style={styles.categoryItem} onPress={onPress}>
    <View style={styles.categoryIcon}>
      <Text style={{ fontSize: 24 }}>{icon}</Text>
    </View>
    <Text style={styles.categoryTitle}>{title}</Text>
  </TouchableOpacity>
);

const SectionTitle = ({ title, onSeeAll }) => (
  <View style={styles.sectionHeader}>
    <Text style={styles.sectionTitle}>{title}</Text>
    <TouchableOpacity onPress={onSeeAll}>
      <Text style={styles.seeAll}>عرض الكل</Text>
    </TouchableOpacity>
  </View>
);

const HomeScreen = ({ navigation }) => {
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [banners, setBanners] = useState([]);

  const loadData = useCallback(async () => {
    try {
      const [productsData, categoriesData, adsData] = await Promise.all([
        listProducts({ limit: 10 }),
        listCategories(),
        listAds({ position: 'hero' })
      ]);

      setProducts(Array.isArray(productsData) ? productsData : (productsData.results || []));
      
      const catArr = Array.isArray(categoriesData) ? categoriesData : (categoriesData.results || []);
      setCategories(catArr);
      
      setBanners(Array.isArray(adsData) ? adsData : (adsData.results || adsData.ads || []));
    } catch (error) {
      console.error('Error loading home data:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const onRefresh = () => {
    setRefreshing(true);
    loadData();
  };

  const handleAddToCart = async (product) => {
    try {
      await addToCart(product.id);
      // You could add a toast here
    } catch (error) {
      console.error('Error adding to cart:', error);
    }
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={Colors.primaryStart} />
      </View>
    );
  }

  return (
    <ScrollView 
      style={styles.container}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={Colors.primaryStart} />
      }
    >
      {/* Hero Banner */}
      <LinearGradient
        colors={[Colors.primaryStart, Colors.primaryEnd]}
        style={styles.hero}
      >
        <View style={styles.heroHeader}>
          <TouchableOpacity onPress={() => navigation.navigate('Search')}>
            <Ionicons name="search" size={24} color="#fff" />
          </TouchableOpacity>
          <Text style={styles.logoText}>DAAR</Text>
          <TouchableOpacity onPress={() => navigation.navigate('Cart')}>
            <Ionicons name="cart-outline" size={24} color="#fff" />
          </TouchableOpacity>
        </View>
        <Text style={styles.heroTitle}>أفضل الماركات العالمية</Text>
        <Text style={styles.heroSubtitle}>في العراق</Text>
      </LinearGradient>

      {/* Banner Carousel or ActivityIndicator */}
      <View style={styles.bannerSection}>
        {loading ? (
          <ActivityIndicator size="large" color={Colors.primaryStart} />
        ) : (
          <BannerCarousel banners={banners} />
        )}
      </View>

      {/* Categories */}
      <View style={styles.categoriesContainer}>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.categoriesScroll}>
          <Category icon="👔" title="رجالي" onPress={() => navigation.navigate('Products', { category: 'men' })} />
          <Category icon="👗" title="نسائي" onPress={() => navigation.navigate('Products', { category: 'women' })} />
          <Category icon="👶" title="أطفال" onPress={() => navigation.navigate('Products', { category: 'kids' })} />
          <Category icon="💄" title="كوزمتك" onPress={() => navigation.navigate('Products', { category: 'cosmetics' })} />
          <Category icon="⌚" title="ساعات" onPress={() => navigation.navigate('Products', { category: 'watches' })} />
        </ScrollView>
      </View>

      {/* Featured Products */}
      <SectionTitle 
        title="المنتجات المميزة" 
        onSeeAll={() => navigation.navigate('Products', { mode: 'featured' })} 
      />
      
      <View style={styles.productsGrid}>
        {products.map((item, index) => (
          <View key={item.id}>
            <ProductCard 
              product={item} 
              addToCart={handleAddToCart}
            />
          </View>
        ))}
      </View>

      <View style={{ height: 30 }} />
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: Colors.background,
  },
  hero: {
    paddingTop: 50,
    paddingBottom: 30,
    paddingHorizontal: 20,
    borderBottomLeftRadius: 30,
    borderBottomRightRadius: 30,
  },
  heroHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20,
  },
  logoText: {
    color: '#fff',
    fontSize: 22,
    fontWeight: 'bold',
    letterSpacing: 2,
  },
  heroTitle: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#fff',
    textAlign: 'center',
    marginTop: 10,
  },
  heroSubtitle: {
    fontSize: 18,
    color: 'rgba(255,255,255,0.8)',
    textAlign: 'center',
    marginTop: 5,
  },
  bannerSection: {
    marginTop: -20,
  },
  categoriesContainer: {
    marginVertical: 20,
  },
  categoriesScroll: {
    paddingHorizontal: 15,
  },
  categoryItem: {
    alignItems: 'center',
    marginHorizontal: 10,
  },
  categoryIcon: {
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: Colors.card,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 8,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.1)',
  },
  categoryTitle: {
    color: Colors.textSecondary,
    fontSize: 12,
    fontWeight: 'bold',
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    marginBottom: 15,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: Colors.textPrimary,
  },
  seeAll: {
    color: Colors.primaryStart,
    fontWeight: 'bold',
  },
  productsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    paddingHorizontal: 10,
    justifyContent: 'space-between',
  },
});

export default HomeScreen;
