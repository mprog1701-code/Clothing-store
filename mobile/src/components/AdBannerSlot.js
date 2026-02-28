import React, { useEffect, useState } from 'react';
import { View, Text, Image, TouchableOpacity, Linking } from 'react-native';
import theme from '../theme';
import { listBannersByPlacement } from '../api';

export default function AdBannerSlot({ position = 'slot1', onNavigate }) {
  const [ad, setAd] = useState(null);
  useEffect(() => {
    (async () => {
      console.log('adslot_fetch_start', position);
      try {
        const placement =
          position === 'slot1' ? 'HOME_MIDDLE' :
          position === 'slot2' ? 'HOME_BOTTOM' : 'HOME_TOP';
        const arr = await listBannersByPlacement(placement);
        setAd(arr && arr[0]);
        console.log('adslot_fetch_success', placement, arr?.length || 0);
      } catch (e) {
        console.log('adslot_fetch_fail', position, e?.message || e);
        setAd(null);
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
