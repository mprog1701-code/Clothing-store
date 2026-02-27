import React, { useEffect, useState, useCallback } from 'react';
import { View, Text, FlatList, Image, TouchableOpacity, I18nManager } from 'react-native';
import theme from '../theme';
import { listHomeTopBanners } from '../api';

function BannerItem({ item }) {
  const [imgLoaded, setImgLoaded] = useState(false);
  const [imgError, setImgError] = useState(false);
  return (
    <View style={{ paddingHorizontal: theme.spacing.md }}>
      <View style={{ width: 300, height: 150, borderRadius: theme.radius.lg, backgroundColor: theme.colors.surface, borderWidth: 1, borderColor: theme.colors.cardBorder, alignItems: 'center', justifyContent: 'center', ...theme.shadows.card, overflow: 'hidden' }}>
        {item.image && !imgError ? (
          <Image
            source={{ uri: item.image }}
            style={{ width: 300, height: 150, borderRadius: theme.radius.lg }}
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

  return (
    <View>
      <View style={{ paddingHorizontal: theme.spacing.lg, paddingTop: theme.spacing.lg, flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
        <Text style={{ fontSize: theme.typography.sizes.lg, fontFamily: theme.typography.fontBold, color: theme.colors.textPrimary, textAlign: I18nManager.isRTL ? 'right' : 'left' }}>
          العروض ({banners.length})
        </Text>
      </View>
      {console.log('banner_render_list', banners.length)}
      <FlatList
        horizontal
        data={banners}
        keyExtractor={(it) => String(it.id)}
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={{ paddingHorizontal: theme.spacing.lg }}
        renderItem={({ item }) => <BannerItem item={item} />}
      />
    </View>
  );
}
