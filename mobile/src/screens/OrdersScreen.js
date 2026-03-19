import React, { useEffect, useMemo, useState } from 'react';
import { View, Text, FlatList, TouchableOpacity, ActivityIndicator, RefreshControl, I18nManager } from 'react-native';
import theme from '../theme';
import { listOrders } from '../api';

const tabs = [
  { key: 'all', label: 'الكل' },
  { key: 'pending', label: 'قيد المعالجة' },
  { key: 'accepted', label: 'تم القبول' },
  { key: 'preparing', label: 'جاري التجهيز' },
  { key: 'on_the_way', label: 'قيد التوصيل' },
  { key: 'delivered', label: 'مكتمل' },
  { key: 'canceled', label: 'ملغي' },
];

function normalizeStatus(rawStatus) {
  const s = String(rawStatus || '').toLowerCase();
  if (s === 'processing') return 'preparing';
  if (s === 'shipped') return 'on_the_way';
  if (s === 'cancelled') return 'canceled';
  return s;
}

function formatDateLabel(value) {
  const d = value ? new Date(value) : null;
  if (!d || Number.isNaN(d.getTime())) return '';
  try {
    return new Intl.DateTimeFormat('ar-IQ', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    }).format(d);
  } catch {
    return String(value || '');
  }
}

function toIQD(value) {
  const n = Number(value || 0);
  if (!Number.isFinite(n)) return '0';
  return n.toLocaleString('en-US');
}

function StatusBadge({ status }) {
  const map = {
    pending: theme.colors.accent,
    accepted: theme.colors.accentAlt,
    preparing: theme.colors.accentAlt,
    on_the_way: '#3B82F6',
    delivered: theme.colors.success,
    canceled: theme.colors.danger,
  };
  const text = {
    pending: 'قيد المعالجة',
    accepted: 'تم القبول',
    preparing: 'جاري التجهيز',
    on_the_way: 'قيد التوصيل',
    delivered: 'مكتمل',
    canceled: 'ملغي',
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
    return orders.filter(o => normalizeStatus(o.status) === active);
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
    const created = formatDateLabel(item.created_at || item.created || '');
    const total = item.total_amount ?? item.total_price ?? item.total ?? 0;
    const count = item.items_count ?? (Array.isArray(item.items) ? item.items.reduce((sum, it) => sum + Number(it?.quantity || 0), 0) : 0);
    const status = normalizeStatus(item.status);
    return (
      <View style={{ padding: theme.spacing.md, borderBottomWidth: 1, borderColor: theme.colors.cardBorder, backgroundColor: theme.colors.surface }}>
        <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
          <Text style={{ color: theme.colors.textPrimary, fontFamily: theme.typography.fontBold }}>#{item.id}</Text>
          <StatusBadge status={status} />
        </View>
        <Text style={{ color: theme.colors.textSecondary, fontFamily: theme.typography.fontRegular, marginTop: 4, textAlign: I18nManager.isRTL ? 'right' : 'left' }}>{created || '-'}</Text>
        <Text style={{ color: theme.colors.textPrimary, fontFamily: theme.typography.fontBold, marginTop: 4, textAlign: I18nManager.isRTL ? 'right' : 'left' }}>
          الإجمالي: {toIQD(total)} د.ع • الكمية: {count} {storeName ? `• متجر: ${storeName}` : ''}
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
