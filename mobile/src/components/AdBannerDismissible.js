import React, { useEffect, useState } from 'react';
import { View, Image, Text, TouchableOpacity, Linking } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import theme from '../theme';
import { listAds, listBanners } from '../api';

export default function AdBannerDismissible({ position = 'stores-hero' }) {
  const [ad, setAd] = useState(null);
  const [show, setShow] = useState(false);
  useEffect(() => {
    let active = true;
    const run = async () => {
      try {
        const key = `ad_dismissed_until_${position}`;
        const untilStr = await AsyncStorage.getItem(key);
        const until = untilStr ? parseInt(untilStr, 10) : 0;
        const now = Date.now();
        if (until && now < until) {
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
  }, [position]);

  if (!show) return null;
  return (
    <View style={{ marginTop: theme.spacing.md }}>
      <View style={{ flexDirection: 'row', justifyContent: 'flex-end' }}>
        <TouchableOpacity
          onPress={async () => {
            try {
              const key = `ad_dismissed_until_${position}`;
              const until = Date.now() + 24 * 60 * 60 * 1000;
              await AsyncStorage.setItem(key, String(until));
            } catch {}
            setShow(false);
          }}
          style={{ paddingHorizontal: theme.spacing.md, paddingVertical: theme.spacing.xs, borderRadius: theme.radius.md, backgroundColor: theme.colors.surface, borderWidth: 1, borderColor: theme.colors.cardBorder }}
        >
          <Text style={{ color: theme.colors.textPrimary, fontFamily: theme.typography.fontBold }}>إغلاق ✕</Text>
        </TouchableOpacity>
      </View>
      <TouchableOpacity
        onPress={() => {
          const value = ad?.link || ad?.linkValue || ad?.value || ad?.url;
          if (value) {
            Linking.openURL(value);
          }
        }}
        style={{ marginTop: theme.spacing.xs }}
      >
        <View style={{ height: 180, borderRadius: theme.radius.lg, borderWidth: 1, borderColor: theme.colors.cardBorder, backgroundColor: theme.colors.surface, ...theme.shadows.card, overflow: 'hidden' }}>
          {ad?.image_url || ad?.image ? (
            <Image source={{ uri: ad?.image_url || ad?.image }} style={{ width: '100%', height: '100%' }} />
          ) : (
            <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center' }}>
              <Text style={{ color: theme.colors.textPrimary, fontFamily: theme.typography.fontBold }}>{ad?.title || 'إعلان'}</Text>
            </View>
          )}
        </View>
      </TouchableOpacity>
    </View>
  );
}
