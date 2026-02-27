import React from 'react';
import { View, Text, I18nManager } from 'react-native';
import theme from '../theme';

export default function ProfileDetailsScreen() {
  return (
    <View style={{ flex: 1, backgroundColor: theme.colors.background, padding: theme.spacing.lg }}>
      <Text style={{ color: theme.colors.textPrimary, fontFamily: theme.typography.fontBold, fontSize: theme.typography.sizes.lg, textAlign: I18nManager.isRTL ? 'right' : 'left' }}>تفاصيل الحساب</Text>
      <Text style={{ marginTop: theme.spacing.sm, color: theme.colors.textSecondary, fontFamily: theme.typography.fontRegular, textAlign: I18nManager.isRTL ? 'right' : 'left' }}>
        شاشة Placeholder لعرض تفاصيل الملف الشخصي.
      </Text>
    </View>
  );
}
