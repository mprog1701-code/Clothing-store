import React, { useEffect, useMemo, useRef, useState } from 'react';
import { View, Text, FlatList, Pressable, StyleSheet, Dimensions } from 'react-native';
import { Image } from 'expo-image';
import theme from '../theme';

const { width } = Dimensions.get('window');

function mediaOf(item) {
  return item?.image_url || item?.image || item?.banner_image || '';
}

export default function AdSlider({
  ads = [],
  intervalMs = 5000,
  badgeText = 'Ad',
  placeholderTitle = 'Coming Soon',
  placeholderSubtitle = 'مساحة إعلانية',
  onPressItem,
}) {
  const flatListRef = useRef(null);
  const [activeIndex, setActiveIndex] = useState(0);
  const validAds = useMemo(() => (Array.isArray(ads) ? ads.filter((item) => !!mediaOf(item)) : []), [ads]);
  const slides = validAds.length ? validAds : [{ id: 'ad-placeholder' }];

  useEffect(() => {
    if (slides.length <= 1) return undefined;
    const timer = setInterval(() => {
      setActiveIndex((prev) => {
        const next = (prev + 1) % slides.length;
        flatListRef.current?.scrollToIndex({ index: next, animated: true });
        return next;
      });
    }, intervalMs);
    return () => clearInterval(timer);
  }, [intervalMs, slides.length]);

  return (
    <View style={styles.container}>
      <View style={styles.badge}>
        <Text style={styles.badgeText}>{badgeText}</Text>
      </View>
      <FlatList
        ref={flatListRef}
        data={slides}
        horizontal
        pagingEnabled
        bounces={false}
        keyExtractor={(item, index) => String(item?.id ?? index)}
        showsHorizontalScrollIndicator={false}
        onMomentumScrollEnd={(event) => {
          const index = Math.round(event.nativeEvent.contentOffset.x / (width - 32));
          setActiveIndex(index);
        }}
        renderItem={({ item }) => {
          const media = mediaOf(item);
          if (!media) {
            return (
              <View style={styles.slide}>
                <View style={styles.placeholderWrap}>
                  <Text style={styles.placeholderTitle}>{placeholderTitle}</Text>
                  <Text style={styles.placeholderSubtitle}>{placeholderSubtitle}</Text>
                </View>
              </View>
            );
          }
          return (
            <Pressable style={styles.slide} onPress={() => onPressItem && onPressItem(item)}>
              <Image source={{ uri: media }} style={styles.image} contentFit="cover" transition={180} cachePolicy="memory-disk" />
            </Pressable>
          );
        }}
      />
      <View style={styles.dots}>
        {slides.map((_, index) => (
          <View key={index} style={[styles.dot, index === activeIndex && styles.dotActive]} />
        ))}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    width: '100%',
    height: 170,
    borderRadius: theme.radius.lg,
    borderWidth: 1,
    borderColor: theme.colors.cardBorder,
    overflow: 'hidden',
    backgroundColor: theme.colors.surface,
    marginBottom: theme.spacing.lg,
  },
  slide: {
    width: width - 32,
    height: 170,
    backgroundColor: theme.colors.surface,
  },
  image: {
    width: '100%',
    height: '100%',
  },
  badge: {
    position: 'absolute',
    top: 10,
    right: 10,
    zIndex: 3,
    backgroundColor: 'rgba(15,15,35,0.85)',
    borderWidth: 1,
    borderColor: theme.colors.cardBorder,
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 999,
  },
  badgeText: {
    color: theme.colors.textPrimary,
    fontFamily: theme.typography.fontBold,
    fontSize: theme.typography.sizes.xs,
  },
  dots: {
    position: 'absolute',
    bottom: 10,
    left: 0,
    right: 0,
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    gap: 6,
  },
  dot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: 'rgba(255,255,255,0.45)',
  },
  dotActive: {
    width: 16,
    backgroundColor: theme.colors.accent,
  },
  placeholderWrap: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: theme.colors.surfaceAlt,
  },
  placeholderTitle: {
    color: theme.colors.textPrimary,
    fontFamily: theme.typography.fontBold,
    fontSize: theme.typography.sizes.md,
    marginBottom: 4,
  },
  placeholderSubtitle: {
    color: theme.colors.textSecondary,
    fontFamily: theme.typography.fontRegular,
    fontSize: theme.typography.sizes.sm,
  },
});
