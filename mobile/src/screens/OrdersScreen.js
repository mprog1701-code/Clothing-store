import React, { useEffect, useMemo, useState } from 'react';
import { View, Text, FlatList, TouchableOpacity, ActivityIndicator, RefreshControl, I18nManager } from 'react-native';
import theme from '../theme';
import { listOrders } from '../api';

const tabs = [
  { key: 'all', label: 'الكل' },
  { key: 'pending', label: 'قيد المعالجة' },
  { key: 'processing', label: 'جاري التجهيز' },
  { key: 'shipped', label: 'قيد التوصيل' },
  { key: 'delivered', label: 'مكتمل' },
  { key: 'cancelled', label: 'ملغي' },
];

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

export default function OrdersScreen({ navigation }) {
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState('');
  const [orders, setOrders] = useState([]);
  const [active, setActive] = useState('all');

  const load = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await listOrders();
      const arr = Array.isArray(data) ? data : (data.results || []);
      setOrders(arr);
    } catch (e) {
      setError('تعذر تحميل الطلبات. يرجى تسجيل الدخول أو المحاولة لاحقاً.');
      setOrders([]);
    } finally {
      setLoading(false);
    }
  };

  const refresh = async () => {
    setRefreshing(true);
    try {
      const data = await listOrders();
      const arr = Array.isArray(data) ? data : (data.results || []);
      setOrders(arr);
    } catch {
    } finally {
      setRefreshing(false);
    }
  };

  useEffect(() => { load(); }, []);

  const filtered = useMemo(() => {
    if (active === 'all') return orders;
    return orders.filter(o => (o.status || '').toLowerCase() === active);
  }, [orders, active]);

  const Header = (
    <View style={{ paddingHorizontal: theme.spacing.lg, paddingTop: theme.spacing.lg, paddingBottom: theme.spacing.md, borderBottomWidth: 1, borderColor: theme.colors.border, backgroundColor: theme.colors.surface }}>
      <Text style={{ color: theme.colors.textPrimary, fontFamily: theme.typography.fontBold, fontSize: theme.typography.sizes.lg, textAlign: I18nManager.isRTL ? 'right' : 'left' }}>طلباتي</Text>
      {error ? (
        <View style={{ marginTop: theme.spacing.sm }}>
          <Text style={{ color: theme.colors.danger, fontFamily: theme.typography.fontBold, textAlign: I18nManager.isRTL ? 'right' : 'left' }}>{error}</Text>
        </View>
      ) : null}
      <View style={{ flexDirection: 'row', flexWrap: 'wrap', marginTop: theme.spacing.md }}>
        {tabs.map(t => (
          <TouchableOpacity
            key={t.key}
            onPress={() => setActive(t.key)}
            style={{
              paddingHorizontal: theme.spacing.md,
              paddingVertical: theme.spacing.xs,
              borderRadius: theme.radius.md,
              borderWidth: 1,
              borderColor: active === t.key ? theme.colors.accent : theme.colors.cardBorder,
              backgroundColor: theme.colors.surface,
              marginRight: theme.spacing.sm,
              marginBottom: theme.spacing.sm,
            }}
          >
            <Text style={{ color: active === t.key ? theme.colors.accent : theme.colors.textPrimary, fontFamily: theme.typography.fontRegular }}>{t.label}</Text>
          </TouchableOpacity>
        ))}
      </View>
    </View>
  );

  const Row = ({ item }) => {
    const storeName = item.store?.name || '';
    const created = item.created_at || item.created || '';
    const total = item.total_price ?? item.total ?? 0;
    const count = item.items_count ?? (Array.isArray(item.items) ? item.items.length : 0);
    return (
      <View style={{ padding: theme.spacing.md, borderBottomWidth: 1, borderColor: theme.colors.cardBorder, backgroundColor: theme.colors.surface }}>
        <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
          <Text style={{ color: theme.colors.textPrimary, fontFamily: theme.typography.fontBold }}>#{item.id}</Text>
          <StatusBadge status={(item.status || '').toLowerCase()} />
        </View>
        <Text style={{ color: theme.colors.textSecondary, fontFamily: theme.typography.fontRegular, marginTop: 4, textAlign: I18nManager.isRTL ? 'right' : 'left' }}>{created}</Text>
        <Text style={{ color: theme.colors.textPrimary, fontFamily: theme.typography.fontBold, marginTop: 4, textAlign: I18nManager.isRTL ? 'right' : 'left' }}>
          الإجمالي: {total} • عناصر: {count} {storeName ? `• متجر: ${storeName}` : ''}
        </Text>
        <View style={{ flexDirection: 'row', marginTop: theme.spacing.sm }}>
          <TouchableOpacity onPress={() => navigation.navigate('OrderDetail', { id: item.id })} style={{ paddingVertical: theme.spacing.sm, paddingHorizontal: theme.spacing.md, borderRadius: theme.radius.md, borderWidth: 1, borderColor: theme.colors.cardBorder }}>
            <Text style={{ color: theme.colors.textPrimary, fontFamily: theme.typography.fontBold }}>تفاصيل</Text>
          </TouchableOpacity>
          <View style={{ width: theme.spacing.sm }} />
          <TouchableOpacity onPress={() => {}} style={{ paddingVertical: theme.spacing.sm, paddingHorizontal: theme.spacing.md, borderRadius: theme.radius.md, backgroundColor: theme.colors.accent }}>
            <Text style={{ color: '#000', fontFamily: theme.typography.fontBold }}>إعادة الطلب</Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  };

  if (loading) {
    return (
      <View style={{ flex: 1, backgroundColor: theme.colors.background, alignItems: 'center', justifyContent: 'center' }}>
        <ActivityIndicator />
        <Text style={{ marginTop: 8, color: theme.colors.textSecondary, fontFamily: theme.typography.fontRegular }}>جاري تحميل الطلبات...</Text>
      </View>
    );
  }

  return (
    <View style={{ flex: 1, backgroundColor: theme.colors.background }}>
      <FlatList
        data={filtered}
        keyExtractor={(it) => String(it.id)}
        ListHeaderComponent={Header}
        renderItem={Row}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={refresh} />}
        removeClippedSubviews
        initialNumToRender={10}
        windowSize={7}
        ListEmptyComponent={
          <View style={{ padding: theme.spacing.lg, alignItems: 'center' }}>
            <Text style={{ color: theme.colors.textSecondary, fontFamily: theme.typography.fontRegular }}>لا توجد طلبات حالياً.</Text>
          </View>
        }
      />
    </View>
  );
}
