// Global Mobile App UI Transformation Completed
import React, { useEffect, useState, useCallback } from 'react';
import {
  ScrollView,
  View,
  Text,
  Image,
  TouchableOpacity,
  Dimensions,
  StyleSheet,
  ActivityIndicator,
  RefreshControl,
  TextInput,
  Alert,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { COLORS } from '../constants/Colors';
import ProductCard from '../components/ProductCard';
import { listProducts, listCategories, listAds, addToCart } from '../api';

const { width } = Dimensions.get('window');

const HomeScreen = ({ navigation }) => {
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [banners, setBanners] = useState([]);
  const [email, setEmail] = useState('');

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
      Alert.alert('تمت الإضافة', `تم إضافة ${product.name} إلى السلة بنجاح!`);
    } catch (error) {
      console.error('Error adding to cart:', error);
      Alert.alert('خطأ', 'يرجى تسجيل الدخول لإضافة المنتجات إلى السلة');
    }
  };

  const handleSubscribe = () => {
    if (!email || !email.includes('@')) {
      Alert.alert('خطأ', 'يرجى إدخال بريد إلكتروني صحيح');
      return;
    }
    Alert.alert('نجاح', 'تم الاشتراك في النشرة البريدية بنجاح!');
    setEmail('');
  };

  if (loading && !refreshing) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={COLORS.primary} />
      </View>
    );
  }

  return (
    <ScrollView 
      style={styles.container}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={COLORS.primary} />
      }
    >
      {/* Hero Banner */}
      <View style={styles.heroSection}>
        <LinearGradient
          colors={[COLORS.gradientStart, COLORS.gradientEnd]}
          style={styles.heroBanner}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 1 }}
        >
          <Text style={styles.heroTitle}>أفضل الماركات العالمية</Text>
          <Text style={styles.heroSubtitle}>في العراق</Text>
          <Text style={styles.heroDescription}>
            تسوق من أفضل المحلات العراقية مع ضمان الجودة والتوصيل
          </Text>
          
          <TouchableOpacity 
            style={styles.heroCTA}
            onPress={() => navigation.navigate('Search')}
          >
            <Text style={styles.heroCTAText}>ابدأ التسوق الآن</Text>
            <Ionicons name="arrow-back" size={20} color="#fff" />
          </TouchableOpacity>
        </LinearGradient>
      </View>

      {/* Flash Sale Banner */}
      <View style={styles.flashSale}>
        <LinearGradient
          colors={['#ff6b6b', '#ee5a6f']}
          style={styles.flashBanner}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 0 }}
        >
          <View style={styles.flashContent}>
            <Ionicons name="flash" size={24} color="#fff" />
            <Text style={styles.flashText}>تخفيضات اليوم - خصم حتى 50%</Text>
          </View>
          <Text style={styles.flashTimer}>⏰ 12:45:32</Text>
        </LinearGradient>
      </View>

      {/* Categories */}
      <View style={styles.section}>
        <SectionHeader title="تسوق حسب القسم" onPress={() => navigation.navigate('Categories')} />
        
        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={{ paddingRight: 15 }}>
          <CategoryCard icon="👔" title="رجالي" gradient={['#667eea', '#764ba2']} onPress={() => navigation.navigate('Products', { category: 'men' })} />
          <CategoryCard icon="👗" title="نسائي" gradient={['#f093fb', '#f5576c']} onPress={() => navigation.navigate('Products', { category: 'women' })} />
          <CategoryCard icon="👶" title="أطفال" gradient={['#4facfe', '#00f2fe']} onPress={() => navigation.navigate('Products', { category: 'kids' })} />
          <CategoryCard icon="💄" title="كوزمتك" gradient={['#43e97b', '#38f9d7']} onPress={() => navigation.navigate('Products', { category: 'cosmetics' })} />
          <CategoryCard icon="👟" title="أحذية" gradient={['#fa709a', '#fee140']} onPress={() => navigation.navigate('Products', { category: 'shoes' })} />
          <CategoryCard icon="⌚" title="ساعات" gradient={['#30cfd0', '#330867']} onPress={() => navigation.navigate('Products', { category: 'watches' })} />
        </ScrollView>
      </View>

      {/* Ad Banner 1 */}
      <TouchableOpacity style={styles.adBanner}>
        <Image
          source={{ uri: banners[0]?.image || 'https://placehold.co/800x200/e94560/ffffff?text=Ad+Banner' }}
          style={styles.adImage}
        />
        <View style={styles.adOverlay}>
          <Text style={styles.adText}>عرض خاص - خصم 30%</Text>
          <Text style={styles.adSubtext}>على جميع الملابس النسائية</Text>
        </View>
      </TouchableOpacity>

      {/* Brands Grid */}
      <View style={styles.section}>
        <SectionHeader title="الماركات العالمية" onPress={() => {}} />
        <View style={styles.brandsGrid}>
          <BrandLogo name="ZARA" icon="shirt-outline" />
          <BrandLogo name="NIKE" icon="footsteps-outline" />
          <BrandLogo name="ADIDAS" icon="briefcase-outline" />
          <BrandLogo name="GUCCI" icon="glasses-outline" />
          <BrandLogo name="CHANEL" icon="flask-outline" />
          <BrandLogo name="H&M" icon="body-outline" />
        </View>
      </View>

      {/* Featured Products */}
      <View style={styles.section}>
        <SectionHeader 
          title="المنتجات المميزة" 
          onPress={() => navigation.navigate('Products', { mode: 'featured' })} 
        />
        
        <View style={styles.productsGrid}>
          {products.slice(0, 4).map(item => (
            <ProductCard 
              key={item.id}
              product={item}
              addToCart={handleAddToCart}
            />
          ))}
        </View>
      </View>

      {/* Ad Banner 2 */}
      <TouchableOpacity style={styles.adBanner}>
        <LinearGradient
          colors={[COLORS.gradientStart, COLORS.gradientEnd]}
          style={styles.gradientAd}
        >
          <Text style={styles.adTitle}>🎁 عرض محدود</Text>
          <Text style={styles.adDesc}>اشترِ 2 واحصل على 1 مجاناً</Text>
          <View style={styles.adButton}>
            <Text style={styles.adButtonText}>تسوق الآن</Text>
          </View>
        </LinearGradient>
      </TouchableOpacity>

      {/* New Arrivals */}
      <View style={styles.section}>
        <SectionHeader title="وصل حديثاً" onPress={() => navigation.navigate('Products', { mode: 'all' })} />
        
        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={{ paddingRight: 15 }}>
          {products.slice(4, 10).map(item => (
            <View key={item.id} style={{ marginLeft: 15 }}>
              <ProductCard 
                product={item}
                addToCart={handleAddToCart}
              />
            </View>
          ))}
        </ScrollView>
      </View>

      {/* Newsletter */}
      <View style={styles.newsletter}>
        <LinearGradient
          colors={[COLORS.dark, COLORS.surface]}
          style={styles.newsletterGradient}
        >
          <Ionicons name="mail" size={40} color={COLORS.primary} />
          <Text style={styles.newsletterTitle}>اشترك في نشرتنا البريدية</Text>
          <Text style={styles.newsletterText}>احصل على عروض حصرية وخصومات خاصة</Text>
          
          <View style={styles.newsletterInput}>
            <TextInput 
              placeholder="البريد الإلكتروني"
              placeholderTextColor="#666"
              style={styles.input}
              value={email}
              onChangeText={setEmail}
              keyboardType="email-address"
              autoCapitalize="none"
            />
            <LinearGradient
              colors={[COLORS.gradientStart, COLORS.gradientEnd]}
              style={styles.subscribeBtn}
            >
              <TouchableOpacity style={styles.subscribeBtnTouch} onPress={handleSubscribe}>
                <Text style={styles.subscribeBtnText}>اشتراك</Text>
              </TouchableOpacity>
            </LinearGradient>
          </View>
        </LinearGradient>
      </View>

      <View style={{ height: 30 }} />
    </ScrollView>
  );
};

// Sub-components

const SectionHeader = ({ title, onPress }) => (
  <View style={styles.sectionHeader}>
    <Text style={styles.sectionTitle}>{title}</Text>
    <TouchableOpacity onPress={onPress}>
      <Text style={styles.seeAll}>عرض الكل ←</Text>
    </TouchableOpacity>
  </View>
);

const CategoryCard = ({ icon, title, gradient, onPress }) => (
  <TouchableOpacity style={styles.categoryCard} onPress={onPress}>
    <LinearGradient
      colors={gradient}
      style={styles.categoryGradient}
    >
      <Text style={styles.categoryIcon}>{icon}</Text>
      <Text style={styles.categoryTitle}>{title}</Text>
    </LinearGradient>
  </TouchableOpacity>
);

const BrandLogo = ({ name, icon }) => (
  <TouchableOpacity style={styles.brandItem}>
    <View style={styles.brandIconContainer}>
      <Ionicons name={icon} size={24} color={COLORS.primary} />
    </View>
    <Text style={styles.brandName}>{name}</Text>
  </TouchableOpacity>
);

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.dark,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: COLORS.dark,
  },
  
  // Hero Section
  heroSection: {
    height: 300,
    marginBottom: 20,
  },
  heroBanner: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
    borderBottomLeftRadius: 30,
    borderBottomRightRadius: 30,
  },
  heroTitle: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#fff',
    textAlign: 'center',
    marginBottom: 10,
  },
  heroSubtitle: {
    fontSize: 24,
    color: '#fff',
    marginBottom: 10,
  },
  heroDescription: {
    fontSize: 16,
    color: '#fff',
    textAlign: 'center',
    opacity: 0.9,
    marginBottom: 20,
    paddingHorizontal: 20,
  },
  heroCTA: {
    flexDirection: 'row-reverse',
    alignItems: 'center',
    backgroundColor: 'rgba(255,255,255,0.2)',
    paddingHorizontal: 30,
    paddingVertical: 12,
    borderRadius: 25,
    gap: 10,
  },
  heroCTAText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  
  // Flash Sale
  flashSale: {
    marginHorizontal: 15,
    marginBottom: 20,
    borderRadius: 15,
    overflow: 'hidden',
  },
  flashBanner: {
    flexDirection: 'row-reverse',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 15,
  },
  flashContent: {
    flexDirection: 'row-reverse',
    alignItems: 'center',
    gap: 10,
  },
  flashText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: 'bold',
  },
  flashTimer: {
    color: '#fff',
    fontSize: 14,
    fontWeight: 'bold',
  },
  
  // Section
  section: {
    marginBottom: 25,
  },
  sectionHeader: {
    flexDirection: 'row-reverse',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 15,
    marginBottom: 15,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#fff',
  },
  seeAll: {
    fontSize: 14,
    color: COLORS.primary,
  },
  
  // Category Card
  categoryCard: {
    marginLeft: 15,
    borderRadius: 15,
    overflow: 'hidden',
  },
  categoryGradient: {
    width: 100,
    height: 120,
    justifyContent: 'center',
    alignItems: 'center',
    gap: 10,
  },
  categoryIcon: {
    fontSize: 40,
  },
  categoryTitle: {
    color: '#fff',
    fontSize: 14,
    fontWeight: 'bold',
  },
  
  // Brands Grid
  brandsGrid: {
    flexDirection: 'row-reverse',
    flexWrap: 'wrap',
    paddingHorizontal: 15,
    justifyContent: 'space-between',
  },
  brandItem: {
    width: (width - 60) / 3,
    alignItems: 'center',
    marginBottom: 15,
    backgroundColor: COLORS.card,
    paddingVertical: 15,
    borderRadius: 15,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.05)',
  },
  brandIconContainer: {
    width: 50,
    height: 50,
    borderRadius: 25,
    backgroundColor: 'rgba(233, 69, 96, 0.1)',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 8,
  },
  brandName: {
    color: COLORS.text,
    fontSize: 12,
    fontWeight: 'bold',
  },

  // Ad Banner
  adBanner: {
    marginHorizontal: 15,
    marginBottom: 20,
    borderRadius: 15,
    overflow: 'hidden',
    height: 150,
  },
  adImage: {
    width: '100%',
    height: '100%',
  },
  adOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0,0,0,0.3)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  adText: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 5,
  },
  adSubtext: {
    fontSize: 16,
    color: '#fff',
  },
  gradientAd: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  adTitle: {
    fontSize: 22,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 5,
  },
  adDesc: {
    fontSize: 16,
    color: '#fff',
    marginBottom: 15,
  },
  adButton: {
    backgroundColor: '#fff',
    paddingHorizontal: 25,
    paddingVertical: 8,
    borderRadius: 20,
  },
  adButtonText: {
    color: COLORS.primary,
    fontWeight: 'bold',
  },
  
  // Products Grid
  productsGrid: {
    flexDirection: 'row-reverse',
    flexWrap: 'wrap',
    paddingHorizontal: 15,
    justifyContent: 'space-between',
  },

  // Newsletter
  newsletter: {
    marginHorizontal: 15,
    borderRadius: 20,
    overflow: 'hidden',
    marginTop: 20,
  },
  newsletterGradient: {
    padding: 30,
    alignItems: 'center',
  },
  newsletterTitle: {
    color: '#fff',
    fontSize: 20,
    fontWeight: 'bold',
    marginTop: 15,
    marginBottom: 10,
  },
  newsletterText: {
    color: COLORS.textSecondary,
    textAlign: 'center',
    marginBottom: 20,
  },
  newsletterInput: {
    flexDirection: 'row-reverse',
    backgroundColor: 'rgba(255,255,255,0.05)',
    borderRadius: 30,
    padding: 5,
    width: '100%',
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.1)',
  },
  input: {
    flex: 1,
    paddingHorizontal: 20,
    color: '#fff',
    textAlign: 'right',
  },
  subscribeBtn: {
    borderRadius: 25,
    overflow: 'hidden',
  },
  subscribeBtnTouch: {
    paddingHorizontal: 25,
    paddingVertical: 10,
  },
  subscribeBtnText: {
    color: '#fff',
    fontWeight: 'bold',
  }
});

export default HomeScreen;
