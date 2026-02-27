import React, { useEffect, useState } from 'react';
import { View, Text, TouchableOpacity, FlatList, Image, I18nManager } from 'react-native';
import theme from '../theme';
import { getStore, listStoreProducts } from '../api';

const tabs = ['Products', 'Offers', 'Info', 'Reviews'];

export default function StoreDetailScreen({ route }) {
  const { id } = route.params || {};
  const [store, setStore] = useState(null);
  const [active, setActive] = useState('Products');
  const [products, setProducts] = useState([]);

  useEffect(() => {
    (async () => {
      try {
        const s = await getStore(id);
        setStore(s);
      } catch {}
      try {
        const pr = await listStoreProducts(id, { limit: 20 });
        const arr = Array.isArray(pr) ? pr : (pr.results || []);
        setProducts(arr);
      } catch {
        setProducts([]);
      }
    })();
  }, [id]);

  return (
    <View style={{ flex: 1, backgroundColor: theme.colors.background }}>
      <View style={{ padding: theme.spacing.lg, borderBottomWidth: 1, borderColor: theme.colors.border }}>
        <Text style={{ color: theme.colors.textPrimary, fontFamily: theme.typography.fontBold, fontSize: theme.typography.sizes.lg, textAlign: I18nManager.isRTL ? 'right' : 'left' }}>
          {store?.name || 'المتجر'}
        </Text>
        <Text style={{ color: theme.colors.textSecondary, fontFamily: theme.typography.fontRegular, marginTop: theme.spacing.xs, textAlign: I18nManager.isRTL ? 'right' : 'left' }}>
          تقييم: {store?.store_rating ?? 0}
        </Text>
      </View>

      <View style={{ flexDirection: 'row', padding: theme.spacing.lg }}>
        {tabs.map(t => (
          <TouchableOpacity
            key={t}
            onPress={() => setActive(t)}
            style={{
              marginRight: theme.spacing.md,
              paddingHorizontal: theme.spacing.md,
              paddingVertical: theme.spacing.xs,
              borderRadius: theme.radius.md,
              borderWidth: 1,
              borderColor: active === t ? theme.colors.accent : theme.colors.cardBorder,
              backgroundColor: theme.colors.surface,
            }}
          >
            <Text style={{ color: active === t ? theme.colors.accent : theme.colors.textPrimary, fontFamily: theme.typography.fontRegular }}>{t}</Text>
          </TouchableOpacity>
        ))}
      </View>

      {active === 'Products' && (
        <FlatList
          data={products}
          keyExtractor={(it) => String(it.id)}
          numColumns={2}
          contentContainerStyle={{ padding: theme.spacing.lg }}
          columnWrapperStyle={{ justifyContent: 'space-between' }}
          renderItem={({ item }) => (
            <View style={{ width: '48%', marginBottom: theme.spacing.lg, borderWidth: 1, borderColor: theme.colors.cardBorder, borderRadius: theme.radius.lg, backgroundColor: theme.colors.surface, ...theme.shadows.card }}>
              {item.main_image?.image_url ? <Image source={{ uri: item.main_image.image_url }} style={{ width: '100%', height: 120, borderTopLeftRadius: theme.radius.lg, borderTopRightRadius: theme.radius.lg }} /> : null}
              <View style={{ padding: theme.spacing.md }}>
                <Text numberOfLines={2} style={{ color: theme.colors.textPrimary, fontFamily: theme.typography.fontBold, textAlign: I18nManager.isRTL ? 'right' : 'left' }}>{item.name}</Text>
                <Text style={{ color: theme.colors.textSecondary, fontFamily: theme.typography.fontRegular, marginTop: theme.spacing.xs, textAlign: I18nManager.isRTL ? 'right' : 'left' }}>{item.base_price}</Text>
              </View>
            </View>
          )}
          ListEmptyComponent={
            <View style={{ padding: theme.spacing.lg, alignItems: 'center' }}>
              <Text style={{ color: theme.colors.textSecondary, fontFamily: theme.typography.fontRegular }}>لا توجد منتجات.</Text>
            </View>
          }
        />
      )}

      {active === 'Offers' && (
        <View style={{ padding: theme.spacing.lg }}>
          <Text style={{ color: theme.colors.textSecondary, fontFamily: theme.typography.fontRegular }}>عروض المتجر ستظهر هنا.</Text>
        </View>
      )}
      {active === 'Info' && (
        <View style={{ padding: theme.spacing.lg }}>
          <Text style={{ color: theme.colors.textSecondary, fontFamily: theme.typography.fontRegular }}>{store?.description || 'لا توجد معلومات.'}</Text>
        </View>
      )}
      {active === 'Reviews' && (
        <View style={{ padding: theme.spacing.lg }}>
          <Text style={{ color: theme.colors.textSecondary, fontFamily: theme.typography.fontRegular }}>المراجعات ستظهر هنا.</Text>
        </View>
      )}
    </View>
  );
}
