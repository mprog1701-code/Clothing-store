import React, { useEffect, useState } from 'react';
import { View, Text, Image, TouchableOpacity, Linking, FlatList, Dimensions } from 'react-native';
import theme from '../theme';
import { listAds } from '../api';

export default function AdBannerSlot({ position = 'slot1', onNavigate }) {
  const [ads, setAds] = useState([]);
  const screenW = Dimensions.get('window').width;
  const slideW = Math.floor(screenW - (theme.spacing.lg * 2));
  useEffect(() => {
    (async () => {
      console.log('adslot_fetch_start', position);
      try {
        const resp = await listAds({ position });
        const arr = Array.isArray(resp) ? resp : (resp.results || resp.ads || []);
        setAds(arr || []);
        console.log('adslot_fetch_success', position, arr?.length || 0);
      } catch (e) {
        console.log('adslot_fetch_fail', position, e?.message || e);
        setAds([]);
      } finally {
        console.log('adslot_fetch_end', position);
      }
    })();
  }, [position]);

  if (!ads || ads.length === 0) {
    return (
      <View style={{ height: 180, marginHorizontal: theme.spacing.lg, marginTop: theme.spacing.md, borderRadius: theme.radius.lg, borderWidth: 1, borderColor: theme.colors.cardBorder, backgroundColor: theme.colors.surface, alignItems: 'center', justifyContent: 'center' }}>
        <Text style={{ color: theme.colors.textSecondary, fontFamily: theme.typography.fontRegular }}>مساحة إعلانية</Text>
      </View>
    );
  }

  const handlePress = (item) => {
    const type = item.linkType || item.type;
    const value = item.linkValue || item.value || item.url;
    if (type === 'product' && value) {
      onNavigate && onNavigate('ProductDetail', { id: value });
    } else if (type === 'store' && value) {
      onNavigate && onNavigate('StoreDetail', { id: value });
    } else if (type === 'url' && value) {
      Linking.openURL(value);
    }
  };

  return (
    <View style={{ marginHorizontal: theme.spacing.lg, marginTop: theme.spacing.md }}>
      <FlatList
        data={ads}
        keyExtractor={(it) => String(it.id)}
        horizontal
        pagingEnabled
        showsHorizontalScrollIndicator={false}
        renderItem={({ item }) => (
          <TouchableOpacity onPress={() => handlePress(item)} style={{ width: slideW }}>
            <View style={{ height: 180, borderRadius: theme.radius.lg, borderWidth: 1, borderColor: theme.colors.cardBorder, backgroundColor: theme.colors.surface, ...theme.shadows.card, overflow: 'hidden' }}>
              {item.image ? (
                <Image source={{ uri: item.image }} style={{ width: '100%', height: '100%' }} />
              ) : (
                <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center' }}>
                  <Text style={{ color: theme.colors.textPrimary, fontFamily: theme.typography.fontBold }}>{item.title || 'إعلان'}</Text>
                </View>
              )}
            </View>
          </TouchableOpacity>
        )}
      />
    </View>
  );
}
