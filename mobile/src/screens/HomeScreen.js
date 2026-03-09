import React, { useEffect, useRef, useState } from 'react';
import { ScrollView, View, Text, TouchableOpacity, StyleSheet, TextInput, I18nManager, Animated } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import theme from '../theme';

const HomeScreen = ({ navigation }) => {
  const [query, setQuery] = useState('');
  const headerAnim = useRef(new Animated.Value(0)).current;
  const searchAnim = useRef(new Animated.Value(0)).current;
  const adAnim = useRef(new Animated.Value(0)).current;
  const offersAnim = useRef(new Animated.Value(0)).current;
  const categoriesAnim = useRef(new Animated.Value(0)).current;
  const flashAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.stagger(120, [
      Animated.timing(headerAnim, { toValue: 1, duration: 420, useNativeDriver: true }),
      Animated.timing(searchAnim, { toValue: 1, duration: 420, useNativeDriver: true }),
      Animated.timing(adAnim, { toValue: 1, duration: 420, useNativeDriver: true }),
      Animated.timing(offersAnim, { toValue: 1, duration: 420, useNativeDriver: true }),
      Animated.timing(categoriesAnim, { toValue: 1, duration: 420, useNativeDriver: true }),
      Animated.timing(flashAnim, { toValue: 1, duration: 420, useNativeDriver: true }),
    ]).start();
  }, [adAnim, categoriesAnim, flashAnim, headerAnim, offersAnim, searchAnim]);

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      showsVerticalScrollIndicator={false}
      alwaysBounceVertical
      scrollEventThrottle={16}
      keyboardShouldPersistTaps="handled"
    >
      <Animated.View style={[styles.header, styles.fadeUp(headerAnim)]}>
        <TouchableOpacity onPress={() => navigation.navigate('Cart')} style={styles.iconButton}>
          <Ionicons name="cart-outline" size={20} color={theme.colors.textPrimary} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>دار الأزياء</Text>
      </Animated.View>

      <Animated.View style={[styles.searchBar, styles.fadeUp(searchAnim)]}>
        <TextInput
          value={query}
          onChangeText={setQuery}
          placeholder="ابحث عن منتج..."
          placeholderTextColor={theme.colors.textSecondary}
          style={styles.searchInput}
        />
        <Ionicons name="search" size={18} color={theme.colors.textSecondary} />
      </Animated.View>

      <Animated.View style={[styles.adSlot, styles.fadeUp(adAnim)]}>
        <Text style={styles.adText}>مساحة إعلانية</Text>
      </Animated.View>

      <Animated.View style={styles.fadeUp(offersAnim)}>
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>العروض (1)</Text>
          <TouchableOpacity onPress={() => navigation.navigate('Products', { mode: 'offers', title: 'العروض' })}>
            <Text style={styles.sectionLink}>عرض الكل</Text>
          </TouchableOpacity>
        </View>
        <View style={styles.offerCard}>
          <Text style={styles.offerTitle}>عرض العروض</Text>
        </View>
        <Text style={styles.offerLink}>عرض العروض</Text>
      </Animated.View>

      <Animated.View style={styles.fadeUp(categoriesAnim)}>
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>الأقسام</Text>
          <TouchableOpacity onPress={() => navigation.navigate('Products', { mode: 'categories', title: 'الأقسام' })}>
            <Text style={styles.sectionLink}>عرض الكل</Text>
          </TouchableOpacity>
        </View>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.chipsRow}>
          {['رجالي', 'نسائي', 'أطفال', 'كوزمتك', 'عطور', 'عرض الكل'].map((label) => (
            <TouchableOpacity
              key={label}
              style={[styles.chip, label === 'عرض الكل' && styles.chipActive]}
              onPress={() =>
                navigation.navigate('Products', {
                  mode: 'category',
                  categoryLabel: label,
                  title: label,
                })
              }
            >
              <Text style={[styles.chipText, label === 'عرض الكل' && styles.chipTextActive]}>{label}</Text>
            </TouchableOpacity>
          ))}
        </ScrollView>
      </Animated.View>

      <Animated.View style={styles.fadeUp(flashAnim)}>
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>عروض فلاش</Text>
          <TouchableOpacity onPress={() => navigation.navigate('Products', { mode: 'flash', title: 'عروض فلاش' })}>
            <Text style={styles.sectionLink}>عرض الكل</Text>
          </TouchableOpacity>
        </View>
        <View style={styles.flashCard}>
          <Text style={styles.flashTitle}>عرض فلاش</Text>
          <TouchableOpacity onPress={() => navigation.navigate('Products', { mode: 'flash', title: 'عروض فلاش' })}>
            <Text style={styles.flashLink}>عرض العروض</Text>
          </TouchableOpacity>
        </View>
      </Animated.View>

      <View style={{ height: theme.spacing.xl }} />
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: theme.colors.background,
  },
  content: {
    paddingHorizontal: theme.spacing.lg,
    paddingTop: theme.spacing.lg,
    paddingBottom: theme.spacing.xl * 2,
  },
  fadeUp: (anim) => ({
    opacity: anim,
    transform: [{ translateY: anim.interpolate({ inputRange: [0, 1], outputRange: [18, 0] }) }],
  }),
  header: {
    flexDirection: 'row-reverse',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: theme.spacing.lg,
  },
  headerTitle: {
    color: theme.colors.textPrimary,
    fontFamily: theme.typography.fontBold,
    fontSize: theme.typography.sizes.lg,
  },
  iconButton: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: theme.colors.surface,
    alignItems: 'center',
    justifyContent: 'center',
  },
  searchBar: {
    flexDirection: 'row-reverse',
    alignItems: 'center',
    backgroundColor: theme.colors.surfaceAlt,
    borderRadius: theme.radius.lg,
    borderWidth: 1,
    borderColor: theme.colors.cardBorder,
    paddingHorizontal: theme.spacing.md,
    paddingVertical: theme.spacing.sm,
    marginBottom: theme.spacing.lg,
  },
  searchInput: {
    flex: 1,
    color: theme.colors.textPrimary,
    fontFamily: theme.typography.fontRegular,
    fontSize: theme.typography.sizes.md,
    textAlign: I18nManager.isRTL ? 'right' : 'left',
  },
  adSlot: {
    height: 140,
    backgroundColor: theme.colors.surface,
    borderRadius: theme.radius.lg,
    borderWidth: 1,
    borderColor: theme.colors.cardBorder,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: theme.spacing.lg,
  },
  adText: {
    color: theme.colors.textSecondary,
    fontFamily: theme.typography.fontRegular,
    fontSize: theme.typography.sizes.md,
  },
  sectionHeader: {
    flexDirection: 'row-reverse',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: theme.spacing.sm,
  },
  sectionTitle: {
    color: theme.colors.textPrimary,
    fontFamily: theme.typography.fontBold,
    fontSize: theme.typography.sizes.lg,
  },
  sectionLink: {
    color: theme.colors.accent,
    fontFamily: theme.typography.fontRegular,
    fontSize: theme.typography.sizes.sm,
  },
  offerCard: {
    backgroundColor: theme.colors.surface,
    borderRadius: theme.radius.lg,
    borderWidth: 1,
    borderColor: theme.colors.cardBorder,
    height: 120,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: theme.spacing.sm,
  },
  offerTitle: {
    color: theme.colors.textSecondary,
    fontFamily: theme.typography.fontBold,
    fontSize: theme.typography.sizes.md,
  },
  offerLink: {
    color: theme.colors.textSecondary,
    fontFamily: theme.typography.fontRegular,
    fontSize: theme.typography.sizes.sm,
    textAlign: I18nManager.isRTL ? 'right' : 'left',
    marginBottom: theme.spacing.lg,
  },
  chipsRow: {
    paddingVertical: theme.spacing.sm,
    paddingRight: I18nManager.isRTL ? 0 : theme.spacing.sm,
    paddingLeft: I18nManager.isRTL ? theme.spacing.sm : 0,
  },
  chip: {
    backgroundColor: theme.colors.surface,
    borderWidth: 1,
    borderColor: theme.colors.cardBorder,
    borderRadius: 20,
    paddingHorizontal: theme.spacing.md,
    paddingVertical: theme.spacing.sm,
    marginLeft: theme.spacing.sm,
  },
  chipActive: {
    backgroundColor: theme.colors.accent,
    borderColor: theme.colors.accent,
  },
  chipText: {
    color: theme.colors.textPrimary,
    fontFamily: theme.typography.fontRegular,
    fontSize: theme.typography.sizes.sm,
  },
  chipTextActive: {
    color: theme.colors.textPrimary,
    fontFamily: theme.typography.fontBold,
  },
  flashCard: {
    backgroundColor: theme.colors.surfaceAlt,
    borderRadius: theme.radius.lg,
    borderWidth: 1,
    borderColor: theme.colors.cardBorder,
    padding: theme.spacing.md,
    flexDirection: 'row-reverse',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: theme.spacing.lg,
  },
  flashTitle: {
    color: theme.colors.textPrimary,
    fontFamily: theme.typography.fontBold,
    fontSize: theme.typography.sizes.md,
  },
  flashLink: {
    color: theme.colors.accent,
    fontFamily: theme.typography.fontRegular,
    fontSize: theme.typography.sizes.sm,
  },
});

export default HomeScreen;
