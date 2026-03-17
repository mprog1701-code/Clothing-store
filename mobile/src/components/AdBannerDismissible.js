import React, { useEffect, useState } from 'react';
import { View, Text, TouchableOpacity, Linking, StyleSheet } from 'react-native';
import { Image } from 'expo-image';
import { Ionicons } from '@expo/vector-icons';
import theme from '../theme';
import { listAds, listBanners } from '../api';

const dismissedInSession = new Set();

export default function AdBannerDismissible({ position = 'stores-hero', onDismiss }) {
  const [ad, setAd] = useState(null);
  const [show, setShow] = useState(false);

  useEffect(() => {
    let active = true;
    const run = async () => {
      try {
        if (dismissedInSession.has(position)) {
          setShow(false);
          return;
        }
        try {
          const r = await listAds({ position });
          const arr = Array.isArray(r) ? r : (r.results || r.ads || []);
          const first = arr && arr[0];
          if (active) {
            setAd(first || null);
            setShow(!!first);
          }
        } catch {
          const bn = await listBanners();
          const first = (bn.banners || [])[0] || null;
          if (active) {
            setAd(first);
            setShow(!!first);
          }
        }
      } catch {
        setShow(false);
      }
    };
    run();
    return () => { active = false; };
  }, [position, onDismiss]);

  if (!show) return null;

  const dismiss = () => {
    dismissedInSession.add(position);
    setShow(false);
    if (onDismiss) onDismiss();
  };

  return (
    <View style={styles.wrap}>
      <TouchableOpacity
        onPress={() => {
          const value = ad?.link || ad?.linkValue || ad?.value || ad?.url;
          if (value) {
            Linking.openURL(value);
          }
        }}
        style={styles.pressable}
      >
        <View style={styles.card}>
          <TouchableOpacity onPress={dismiss} style={styles.closeButton} hitSlop={8}>
            <Ionicons name="close" size={16} color={theme.colors.textPrimary} />
          </TouchableOpacity>
          {ad?.image_url || ad?.image ? (
            <Image source={{ uri: ad?.image_url || ad?.image }} style={styles.image} contentFit="cover" transition={150} cachePolicy="memory-disk" />
          ) : (
            <View style={styles.placeholder}>
              <Text style={styles.placeholderText}>{ad?.title || 'إعلان'}</Text>
            </View>
          )}
        </View>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: {
    marginTop: theme.spacing.md,
  },
  pressable: {
    marginTop: theme.spacing.xs,
  },
  card: {
    height: 180,
    borderRadius: theme.radius.lg,
    borderWidth: 1,
    borderColor: theme.colors.cardBorder,
    backgroundColor: theme.colors.surface,
    overflow: 'hidden',
    ...theme.shadows.card,
  },
  image: {
    width: '100%',
    height: '100%',
  },
  placeholder: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  placeholderText: {
    color: theme.colors.textPrimary,
    fontFamily: theme.typography.fontBold,
  },
  closeButton: {
    position: 'absolute',
    top: 10,
    right: 10,
    zIndex: 2,
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: 'rgba(15,15,35,0.82)',
    borderWidth: 1,
    borderColor: theme.colors.cardBorder,
    alignItems: 'center',
    justifyContent: 'center',
  },
});
