import React, { useRef } from 'react';
import { View, FlatList, Dimensions } from 'react-native';
import { Image } from 'expo-image';
import theme from '../theme';
import { API_BASE_URL } from '../config';

export default function ImageCarousel({ images, onIndexChange, flatListRef, height }) {
  const width = Dimensions.get('window').width;
  const resolvedHeight = Number(height) > 0 ? Number(height) : Math.round(width * 1.25);
  const ref = flatListRef || useRef(null);
  const resolveUri = (u) => {
    const s = String(u || '').trim();
    if (!s) return '';
    if (/^https?:\/\//i.test(s)) return s;
    const base = String(API_BASE_URL || '').replace(/\/+$/, '');
    if (!base) return s;
    if (s.startsWith('/')) return `${base}${s}`;
    return `${base}/${s}`;
  };
  return (
    <View style={{ width, height: resolvedHeight, backgroundColor: theme.colors.background }}>
      <FlatList
        ref={ref}
        horizontal
        pagingEnabled
        showsHorizontalScrollIndicator={false}
        data={images}
        keyExtractor={(it) => String(resolveUri(it.url || it.image_url || it))}
        renderItem={({ item }) => (
          <View style={{ width, height: resolvedHeight, alignItems: 'center', justifyContent: 'center' }}>
            <Image
              source={{ uri: resolveUri(item.url || item.image_url || item) }}
              style={{ width: width, height: resolvedHeight }}
              contentFit="cover"
              transition={200}
            />
          </View>
        )}
        onMomentumScrollEnd={(e) => {
          const x = e.nativeEvent.contentOffset.x || 0;
          const idx = Math.round(x / width);
          if (onIndexChange) onIndexChange(idx);
        }}
      />
    </View>
  );
}
