import React, { useEffect, useState, useCallback } from 'react';
import { View, Text, FlatList, Image, TouchableOpacity, I18nManager, Dimensions } from 'react-native';
import theme from '../theme';
import { listHomeTopBanners } from '../api';

function BannerItem({ item, width = 300, height = 150 }) {
  const [imgLoaded, setImgLoaded] = useState(false);
  const [imgError, setImgError] = useState(false);
  return (
    <View style={{ paddingHorizontal: theme.spacing.md, flex: 1 }}>
      <View style={{ width, height, borderRadius: theme.radius.lg, backgroundColor: theme.colors.surface, borderWidth: 1, borderColor: theme.colors.cardBorder, alignItems: 'center', justifyContent: 'center', ...theme.shadows.card, overflow: 'hidden' }}>
        {item.image && !imgError ? (
          <Image
            source={{ uri: item.image }}
            style={{ width, height, borderRadius: theme.radius.lg }}
            onLoadEnd={() => { setImgLoaded(true); }}
            onError={() => { setImgError(true); setImgLoaded(true); }}
          />
        ) : (
          <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center' }}>
            <Text style={{ color: theme.colors.textPrimary, fontFamily: theme.typography.fontBold }}>{item.title || 'إعلان'}</Text>
          </View>
        )}
      </View>
      <Text style={{ fontFamily: theme.typography.fontBold, marginTop: theme.spacing.sm, color: theme.colors.textPrimary, textAlign: I18nManager.isRTL ? 'right' : 'left' }}>{item.title}</Text>
      {item.description ? (
        <Text style={{ color: theme.colors.textSecondary, fontFamily: theme.typography.fontRegular, textAlign: I18nManager.isRTL ? 'right' : 'left' }}>{item.description}</Text>
      ) : null}
    </View>
  );
}

export default function BannerWidget() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [banners, setBanners] = useState([]);
  const screenW = Dimensions.get('window').width;
  const cardW = Math.floor((screenW - (theme.spacing.lg * 2) - theme.spacing.md) / 2); // 2 columns

  const fetchBanners = useCallback(async () => {
    console.log('banner_fetch_start');
    setLoading(true);
    setError('');
    try {
      const arr = await listHomeTopBanners();
      setBanners(arr);
      console.log('banner_fetch_success', arr.length);
    } catch (e) {
      console.log('banner_fetch_fail', e?.message || e);
      setError('تعذر تحميل الإعلانات');
      setBanners([]);
    } finally {
      setLoading(false);
      console.log('banner_fetch_end');
    }
  }, []);

  useEffect(() => {
    fetchBanners();
  }, [fetchBanners]);

  if (loading) {
    return (
      <View style={{ paddingHorizontal: theme.spacing.lg, paddingTop: theme.spacing.lg }}>
        <View style={{ width: 300, height: 150, borderRadius: theme.radius.lg, backgroundColor: theme.colors.surface, borderWidth: 1, borderColor: theme.colors.cardBorder, alignItems: 'center', justifyContent: 'center', ...theme.shadows.card }}>
          <Text style={{ color: theme.colors.textSecondary, fontFamily: theme.typography.fontRegular }}>جاري تحميل الإعلانات...</Text>
        </View>
      </View>
    );
  }

  if (error || banners.length === 0) {
    return (
      <View style={{ paddingHorizontal: theme.spacing.lg, paddingTop: theme.spacing.lg }}>
        <View style={{ width: 300, height: 150, borderRadius: theme.radius.lg, backgroundColor: theme.colors.surface, borderWidth: 1, borderColor: theme.colors.cardBorder, alignItems: 'center', justifyContent: 'center', ...theme.shadows.card }}>
          <Text style={{ color: theme.colors.textSecondary, fontFamily: theme.typography.fontRegular }}>لا توجد عروض حالياً</Text>
        </View>
      </View>
    );
  }

  // Grid of 2 panels per row
  return (
    <View>
      <View style={{ paddingHorizontal: theme.spacing.lg, paddingTop: theme.spacing.lg, flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
        <Text style={{ fontSize: theme.typography.sizes.lg, fontFamily: theme.typography.fontBold, color: theme.colors.textPrimary, textAlign: I18nManager.isRTL ? 'right' : 'left' }}>
          العروض ({banners.length})
        </Text>
      </View>
      {console.log('banner_render_grid', banners.length)}
      <FlatList
        data={banners}
        keyExtractor={(it) => String(it.id)}
        numColumns={2}
        columnWrapperStyle={{ paddingHorizontal: theme.spacing.lg }}
        showsVerticalScrollIndicator={false}
        renderItem={({ item }) => <BannerItem item={item} width={cardW} height={150} />}
      />
    </View>
  );
}
