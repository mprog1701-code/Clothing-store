import React, { useEffect, useState } from 'react';
import { View, Text, Image, TouchableOpacity, Linking } from 'react-native';
import theme from '../theme';
import { listAds, listBanners } from '../api';

export default function AdBannerSlot({ position = 'slot1', onNavigate }) {
  const [ad, setAd] = useState(null);
  useEffect(() => {
    (async () => {
      console.log('adslot_fetch_start', position);
      try {
        const resp = await listAds({ position });
        const arr = Array.isArray(resp) ? resp : (resp.results || resp.ads || []);
        setAd(arr && arr[0]);
        console.log('adslot_fetch_success', position, arr?.length || 0);
      } catch (e) {
        console.log('adslot_fetch_fail_ads', position, e?.message || e);
        try {
          const bn = await listBanners();
          const arr = bn.banners || [];
          setAd(arr[0] || null);
          console.log('adslot_fallback_banners_success', position, arr?.length || 0);
        } catch (e2) {
          console.log('adslot_fallback_banners_fail', position, e2?.message || e2);
          setAd(null);
        }
      } finally {
        console.log('adslot_fetch_end', position);
      }
    })();
  }, [position]);

  if (!ad) {
    return (
      <View style={{ height: 180, marginHorizontal: theme.spacing.lg, marginTop: theme.spacing.md, borderRadius: theme.radius.lg, borderWidth: 1, borderColor: theme.colors.cardBorder, backgroundColor: theme.colors.surface, alignItems: 'center', justifyContent: 'center' }}>
        <Text style={{ color: theme.colors.textSecondary, fontFamily: theme.typography.fontRegular }}>مساحة إعلانية</Text>
      </View>
    );
  }

  const handlePress = () => {
    const type = ad.linkType || ad.type;
    const value = ad.linkValue || ad.value || ad.url;
    if (type === 'product' && value) {
      onNavigate && onNavigate('ProductDetail', { id: value });
    } else if (type === 'store' && value) {
      onNavigate && onNavigate('StoreDetail', { id: value });
    } else if (type === 'url' && value) {
      Linking.openURL(value);
    }
  };

  return (
    <TouchableOpacity onPress={handlePress} style={{ marginHorizontal: theme.spacing.lg, marginTop: theme.spacing.md }}>
      <View style={{ height: 180, borderRadius: theme.radius.lg, borderWidth: 1, borderColor: theme.colors.cardBorder, backgroundColor: theme.colors.surface, ...theme.shadows.card, overflow: 'hidden' }}>
        {ad.image ? (
          <Image
            source={{ uri: ad.image }}
            style={{ width: '100%', height: '100%' }}
            onError={() => {}}
            onLoadEnd={() => {}}
          />
        ) : (
          <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center' }}>
            <Text style={{ color: theme.colors.textPrimary, fontFamily: theme.typography.fontBold }}>{ad.title || 'إعلان'}</Text>
          </View>
        )}
      </View>
    </TouchableOpacity>
  );
}
