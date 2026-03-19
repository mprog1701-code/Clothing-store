import React, { useEffect, useState } from 'react';
import { View, Text, FlatList, ActivityIndicator, I18nManager } from 'react-native';
import theme from '../theme';
import { getOrder } from '../api';

function formatAddressValue(value) {
  if (!value) return '';
  if (typeof value === 'string') return value.trim();
  if (typeof value === 'object') {
    const formatted = String(value.formatted_address || '').trim();
    if (formatted) return formatted;
    const line = [value.city, value.area, value.street, value.details]
      .map((x) => String(x || '').trim())
      .filter(Boolean)
      .join(' - ');
    if (line) return line;
    const lat = Number(value.latitude);
    const lng = Number(value.longitude);
    if (Number.isFinite(lat) && Number.isFinite(lng)) {
      return `${lat.toFixed(6)}, ${lng.toFixed(6)}`;
    }
  }
  return '';
}

function StatusBadge({ status }) {
  const map = {
    pending: theme.colors.accent,
    processing: theme.colors.accentAlt,
    shipped: '#3B82F6',
    delivered: theme.colors.success,
    cancelled: theme.colors.danger,
  };
  const text = {
    pending: 'قيد المعالجة',
    processing: 'جاري التجهيز',
    shipped: 'قيد التوصيل',
    delivered: 'مكتمل',
    cancelled: 'ملغي',
  }[status] || 'غير معروف';
  const bg = map[status] || theme.colors.surfaceAlt;
  return (
    <View style={{ paddingHorizontal: theme.spacing.sm, paddingVertical: 4, borderRadius: theme.radius.md, backgroundColor: bg }}>
      <Text style={{ color: '#000', fontFamily: theme.typography.fontBold }}>{text}</Text>
    </View>
  );
}

export default function OrderDetailScreen({ route }) {
  const { id } = route.params || {};
  const [loading, setLoading] = useState(true);
  const [order, setOrder] = useState(null);
  const load = async () => {
    setLoading(true);
    try {
      const data = await getOrder(id);
      setOrder(data);
    } finally {
      setLoading(false);
    }
  };
  useEffect(() => { load(); }, [id]);

  if (loading || !order) {
    return (
      <View style={{ flex: 1, backgroundColor: theme.colors.background, alignItems: 'center', justifyContent: 'center' }}>
        <ActivityIndicator />
        <Text style={{ marginTop: 8, color: theme.colors.textSecondary, fontFamily: theme.typography.fontRegular }}>جاري تحميل تفاصيل الطلب...</Text>
      </View>
    );
  }

  const items = Array.isArray(order.items) ? order.items : [];
  const status = (order.status || '').toLowerCase();
  const address = formatAddressValue(order.shipping_address || order.address || null);

  const Header = (
    <View style={{ padding: theme.spacing.lg, borderBottomWidth: 1, borderColor: theme.colors.cardBorder, backgroundColor: theme.colors.surface }}>
      <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
        <Text style={{ color: theme.colors.textPrimary, fontFamily: theme.typography.fontBold, fontSize: theme.typography.sizes.lg }}>طلب رقم #{order.id}</Text>
        <StatusBadge status={status} />
      </View>
      <View style={{ marginTop: theme.spacing.md }}>
        <Text style={{ color: theme.colors.textSecondary, fontFamily: theme.typography.fontRegular, textAlign: I18nManager.isRTL ? 'right' : 'left' }}>{order.created_at || ''}</Text>
      </View>
      <View style={{ marginTop: theme.spacing.lg }}>
        <Text style={{ color: theme.colors.textPrimary, fontFamily: theme.typography.fontBold }}>المسار</Text>
        <View style={{ marginTop: theme.spacing.sm }}>
          {['تم الإنشاء', 'المعالجة', 'الشحن', 'التسليم'].map((s, i) => (
            <View key={i} style={{ flexDirection: 'row', alignItems: 'center', marginBottom: theme.spacing.xs }}>
              <View style={{ width: 10, height: 10, borderRadius: 5, backgroundColor: i <= ['pending','processing','shipped','delivered'].indexOf(status) ? theme.colors.accent : theme.colors.surfaceAlt }} />
              <Text style={{ marginStart: theme.spacing.sm, color: theme.colors.textPrimary, fontFamily: theme.typography.fontRegular }}>{s}</Text>
            </View>
          ))}
        </View>
      </View>
      {address ? (
        <View style={{ marginTop: theme.spacing.lg }}>
          <Text style={{ color: theme.colors.textPrimary, fontFamily: theme.typography.fontBold }}>عنوان التوصيل</Text>
          <Text style={{ marginTop: theme.spacing.xs, color: theme.colors.textSecondary, fontFamily: theme.typography.fontRegular, textAlign: I18nManager.isRTL ? 'right' : 'left' }}>
            {address}
          </Text>
        </View>
      ) : null}
    </View>
  );

  const Row = ({ item }) => (
    <View style={{ padding: theme.spacing.md, borderBottomWidth: 1, borderColor: theme.colors.cardBorder, backgroundColor: theme.colors.surface }}>
      <Text style={{ color: theme.colors.textPrimary, fontFamily: theme.typography.fontBold, textAlign: I18nManager.isRTL ? 'right' : 'left' }}>{item.product?.name || 'منتج'}</Text>
      <Text style={{ color: theme.colors.textSecondary, fontFamily: theme.typography.fontRegular, marginTop: 4, textAlign: I18nManager.isRTL ? 'right' : 'left' }}>
        {item.variant_text || ''} • كمية: {item.quantity ?? 0} • سعر: {item.price ?? item.product?.base_price ?? '-'}
      </Text>
    </View>
  );

  return (
    <View style={{ flex: 1, backgroundColor: theme.colors.background }}>
      <FlatList
        data={items}
        keyExtractor={(it, idx) => String(it.id || idx)}
        ListHeaderComponent={Header}
        renderItem={Row}
        removeClippedSubviews
        initialNumToRender={10}
        windowSize={7}
        ListEmptyComponent={
          <View style={{ padding: theme.spacing.lg, alignItems: 'center' }}>
            <Text style={{ color: theme.colors.textSecondary, fontFamily: theme.typography.fontRegular }}>لا توجد عناصر في هذا الطلب.</Text>
          </View>
        }
      />
    </View>
  );
}
