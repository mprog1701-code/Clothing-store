import React, { useEffect, useState } from 'react';
import { View, Text, Image, TouchableOpacity, Linking, FlatList, Dimensions, I18nManager } from 'react-native';
import theme from '../theme';
import { listBannersByPlacement } from '../api';

export default function BannerPlacement({ placement = 'HOME_MIDDLE', onNavigate }) {
  const [items, setItems] = useState([]);
  const screenW = Dimensions.get('window').width;
  const cardW = Math.floor((screenW - (theme.spacing.lg * 2) - theme.spacing.md) / 2);
  useEffect(() => {
    (async () => {
      console.log('banner_placement_fetch_start', placement);
      try {
        const arr = await listBannersByPlacement(placement);
        setItems(Array.isArray(arr) ? arr : []);
        console.log('banner_placement_fetch_success', placement, arr?.length || 0);
      } catch (e) {
        console.log('banner_placement_fetch_fail', placement, e?.message || e);
        setItems([]);
      } finally {
        console.log('banner_placement_fetch_end', placement);
      }
    })();
  }, [placement]);

  if (!items || items.length === 0) {
    return null;
  }

  const handlePress = (b) => {
    const type = b.linkType || b.type;
    const value = b.linkValue || b.value || b.url;
    if (type === 'product' && value) {
      onNavigate && onNavigate('ProductDetail', { id: value });
    } else if (type === 'store' && value) {
      onNavigate && onNavigate('StoreDetail', { id: value });
    } else if (type === 'url' && value) {
      Linking.openURL(value);
    }
  };

  return (
    <View>
      <View style={{ paddingHorizontal: theme.spacing.lg, paddingTop: theme.spacing.lg, flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
        <Text style={{ fontSize: theme.typography.sizes.lg, fontFamily: theme.typography.fontBold, color: theme.colors.textPrimary, textAlign: I18nManager.isRTL ? 'right' : 'left' }}>
          بنرات
        </Text>
      </View>
      <FlatList
        data={items}
        keyExtractor={(it) => String(it.id)}
        numColumns={2}
        columnWrapperStyle={{ paddingHorizontal: theme.spacing.lg }}
        showsVerticalScrollIndicator={false}
        renderItem={({ item }) => (
          <TouchableOpacity onPress={() => handlePress(item)} style={{ width: cardW }}>
            <View style={{ marginBottom: theme.spacing.md, marginRight: theme.spacing.md, height: 150, borderRadius: theme.radius.lg, backgroundColor: theme.colors.surface, borderWidth: 1, borderColor: theme.colors.cardBorder, alignItems: 'center', justifyContent: 'center', ...theme.shadows.card, overflow: 'hidden' }}>
              {item.image ? (
                <Image source={{ uri: item.image }} style={{ width: '100%', height: '100%' }} />
              ) : (
                <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center' }}>
                  <Text style={{ color: theme.colors.textPrimary, fontFamily: theme.typography.fontBold }}>{item.title || 'بنر'}</Text>
                </View>
              )}
            </View>
          </TouchableOpacity>
        )}
      />
    </View>
  );
}
