import React from 'react';
import { View, Text, I18nManager } from 'react-native';
import theme from '../theme';

export default function EditProfileScreen() {
  return (
    <View style={{ flex: 1, backgroundColor: theme.colors.background, padding: theme.spacing.lg }}>
      <Text style={{ color: theme.colors.textPrimary, fontFamily: theme.typography.fontBold, fontSize: theme.typography.sizes.lg, textAlign: I18nManager.isRTL ? 'right' : 'left' }}>تعديل الملف</Text>
      <Text style={{ marginTop: theme.spacing.sm, color: theme.colors.textSecondary, fontFamily: theme.typography.fontRegular, textAlign: I18nManager.isRTL ? 'right' : 'left' }}>
        شاشة Placeholder لتعديل الملف الشخصي.
      </Text>
    </View>
  );
}
