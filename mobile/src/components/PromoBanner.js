import React from 'react';
import { View, Text, Pressable, StyleSheet } from 'react-native';
import { Image } from 'expo-image';
import theme from '../theme';

function mediaOf(item) {
  return item?.image_url || item?.image || item?.banner_image || '';
}

export default function PromoBanner({ item, onPress }) {
  const media = mediaOf(item);
  return (
    <Pressable onPress={() => onPress && onPress(item)} style={styles.card}>
      {media ? (
        <Image source={{ uri: media }} style={styles.image} contentFit="cover" transition={150} cachePolicy="memory-disk" />
      ) : (
        <View style={styles.placeholder}>
          <Text style={styles.placeholderText}>Promotion</Text>
        </View>
      )}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  card: {
    width: '48%',
    aspectRatio: 1,
    borderRadius: theme.radius.lg,
    borderWidth: 1,
    borderColor: theme.colors.cardBorder,
    overflow: 'hidden',
    backgroundColor: theme.colors.surface,
    marginBottom: theme.spacing.md,
  },
  image: {
    width: '100%',
    height: '100%',
  },
  placeholder: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: theme.colors.surfaceAlt,
  },
  placeholderText: {
    color: theme.colors.textSecondary,
    fontFamily: theme.typography.fontRegular,
    fontSize: theme.typography.sizes.sm,
  },
});
