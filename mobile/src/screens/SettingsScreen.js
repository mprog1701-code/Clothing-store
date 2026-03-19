import React, { useEffect, useState } from 'react';
import { View, Text, I18nManager, Switch, TouchableOpacity, Alert, Linking } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import theme from '../theme';

const SETTINGS_KEY = 'daar_app_settings_v1';

function Row({ title, subtitle, rightNode, onPress }) {
  const content = (
    <View style={{ marginTop: theme.spacing.md, borderRadius: theme.radius.md, borderWidth: 1, borderColor: theme.colors.cardBorder, backgroundColor: theme.colors.surface, padding: theme.spacing.md, flexDirection: 'row', alignItems: 'center' }}>
      <View style={{ flex: 1 }}>
        <Text style={{ color: theme.colors.textPrimary, fontFamily: theme.typography.fontBold, textAlign: I18nManager.isRTL ? 'right' : 'left' }}>{title}</Text>
        {!!subtitle && <Text style={{ marginTop: 4, color: theme.colors.textSecondary, fontFamily: theme.typography.fontRegular, textAlign: I18nManager.isRTL ? 'right' : 'left' }}>{subtitle}</Text>}
      </View>
      {rightNode}
    </View>
  );
  if (!onPress) return content;
  return <TouchableOpacity onPress={onPress}>{content}</TouchableOpacity>;
}

export default function SettingsScreen() {
  const [notificationsEnabled, setNotificationsEnabled] = useState(true);
  const [productAlertsEnabled, setProductAlertsEnabled] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const raw = await AsyncStorage.getItem(SETTINGS_KEY);
        const parsed = raw ? JSON.parse(raw) : {};
        setNotificationsEnabled(parsed?.notificationsEnabled !== false);
        setProductAlertsEnabled(parsed?.productAlertsEnabled !== false);
      } catch {}
    })();
  }, []);

  const saveSettings = async (next) => {
    try {
      await AsyncStorage.setItem(SETTINGS_KEY, JSON.stringify(next));
    } catch {}
  };

  const onToggleNotifications = async (value) => {
    setNotificationsEnabled(value);
    await saveSettings({ notificationsEnabled: value, productAlertsEnabled });
  };

  const onToggleProductAlerts = async (value) => {
    setProductAlertsEnabled(value);
    await saveSettings({ notificationsEnabled, productAlertsEnabled: value });
  };

  const clearLocalSettings = async () => {
    try {
      await AsyncStorage.removeItem(SETTINGS_KEY);
      setNotificationsEnabled(true);
      setProductAlertsEnabled(true);
      Alert.alert('تم', 'تمت إعادة الإعدادات للوضع الافتراضي');
    } catch {
      Alert.alert('خطأ', 'تعذر إعادة الإعدادات');
    }
  };

  const openPrivacy = async () => {
    try {
      await Linking.openURL('https://clothing-store-production-4387.up.railway.app/privacy/');
    } catch {
      Alert.alert('تنبيه', 'تعذر فتح رابط الخصوصية حالياً');
    }
  };

  return (
    <View style={{ flex: 1, backgroundColor: theme.colors.background, padding: theme.spacing.lg }}>
      <Text style={{ color: theme.colors.textPrimary, fontFamily: theme.typography.fontBold, fontSize: theme.typography.sizes.lg, textAlign: I18nManager.isRTL ? 'right' : 'left' }}>الإعدادات</Text>
      <Row
        title="إشعارات الطلبات"
        subtitle="تحديثات حالة الطلب بعد الشراء"
        rightNode={<Switch value={notificationsEnabled} onValueChange={onToggleNotifications} trackColor={{ true: theme.colors.accent, false: theme.colors.surfaceAlt }} />}
      />
      <Row
        title="تنبيهات المنتجات والعروض"
        subtitle="العروض الجديدة وتحديثات المتاجر"
        rightNode={<Switch value={productAlertsEnabled} onValueChange={onToggleProductAlerts} trackColor={{ true: theme.colors.accent, false: theme.colors.surfaceAlt }} />}
      />
      <Row
        title="سياسة الخصوصية"
        subtitle="عرض سياسة الخصوصية الخاصة بالتطبيق"
        rightNode={<Text style={{ color: theme.colors.accent, fontFamily: theme.typography.fontBold }}>فتح</Text>}
        onPress={openPrivacy}
      />
      <Row
        title="إعادة ضبط الإعدادات"
        subtitle="إرجاع إعدادات التطبيق للوضع الافتراضي"
        rightNode={<Text style={{ color: theme.colors.danger, fontFamily: theme.typography.fontBold }}>إعادة</Text>}
        onPress={clearLocalSettings}
      />
    </View>
  );
}
