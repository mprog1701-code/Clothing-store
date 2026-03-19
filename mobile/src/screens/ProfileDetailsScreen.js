import React, { useEffect, useState } from 'react';
import { View, Text, I18nManager, ActivityIndicator, TouchableOpacity, RefreshControl, ScrollView } from 'react-native';
import theme from '../theme';
import { me } from '../api';
import EmptyState from '../components/EmptyState';

function Field({ label, value }) {
  return (
    <View style={{ marginTop: theme.spacing.md, borderRadius: theme.radius.md, borderWidth: 1, borderColor: theme.colors.cardBorder, backgroundColor: theme.colors.surface, padding: theme.spacing.md }}>
      <Text style={{ color: theme.colors.textSecondary, fontFamily: theme.typography.fontRegular, textAlign: I18nManager.isRTL ? 'right' : 'left' }}>{label}</Text>
      <Text style={{ marginTop: 4, color: theme.colors.textPrimary, fontFamily: theme.typography.fontBold, textAlign: I18nManager.isRTL ? 'right' : 'left' }}>{value || '-'}</Text>
    </View>
  );
}

export default function ProfileDetailsScreen({ navigation }) {
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [user, setUser] = useState(null);
  const [error, setError] = useState('');

  const load = async () => {
    setError('');
    try {
      const u = await me();
      setUser(u || null);
    } catch {
      setUser(null);
      setError('تعذر تحميل بيانات الملف الشخصي');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const onRefresh = async () => {
    setRefreshing(true);
    await load();
    setRefreshing(false);
  };

  if (loading) {
    return (
      <View style={{ flex: 1, backgroundColor: theme.colors.background, alignItems: 'center', justifyContent: 'center' }}>
        <ActivityIndicator />
      </View>
    );
  }

  if (!user) {
    return (
      <View style={{ flex: 1, backgroundColor: theme.colors.background, justifyContent: 'center' }}>
        <EmptyState icon="account-alert-outline" title="الملف الشخصي غير متاح" subtitle={error || 'تعذر تحميل البيانات'} ctaLabel="إعادة المحاولة" onPress={load} />
      </View>
    );
  }

  return (
    <ScrollView
      style={{ flex: 1, backgroundColor: theme.colors.background }}
      contentContainerStyle={{ padding: theme.spacing.lg, paddingBottom: theme.spacing.xl }}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
    >
      <Text style={{ color: theme.colors.textPrimary, fontFamily: theme.typography.fontBold, fontSize: theme.typography.sizes.lg, textAlign: I18nManager.isRTL ? 'right' : 'left' }}>تفاصيل الحساب</Text>
      <Field label="الاسم" value={user?.name || [user?.first_name, user?.last_name].filter(Boolean).join(' ') || user?.username} />
      <Field label="اسم المستخدم" value={user?.username} />
      <Field label="رقم الهاتف" value={user?.phone} />
      <Field label="البريد الإلكتروني" value={user?.email} />
      <Field label="المدينة" value={user?.city} />
      <Field label="الدور" value={user?.role} />
      <TouchableOpacity onPress={() => navigation.navigate('EditProfile')} style={{ marginTop: theme.spacing.lg, paddingVertical: theme.spacing.md, borderRadius: theme.radius.lg, backgroundColor: theme.colors.accent, alignItems: 'center' }}>
        <Text style={{ color: '#000', fontFamily: theme.typography.fontBold }}>تعديل الملف الشخصي</Text>
      </TouchableOpacity>
    </ScrollView>
  );
}
