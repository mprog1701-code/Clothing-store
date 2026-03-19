import React from 'react';
import { SafeAreaView } from 'react-native-safe-area-context';
import { View, Text, TouchableOpacity, Linking, I18nManager } from 'react-native';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import theme from '../theme';

function Row({ icon, title, subtitle, onPress }) {
  return (
    <TouchableOpacity
      onPress={onPress}
      style={{ marginTop: theme.spacing.md, borderRadius: theme.radius.md, borderWidth: 1, borderColor: theme.colors.cardBorder, backgroundColor: theme.colors.surface, padding: theme.spacing.md, flexDirection: 'row', alignItems: 'center' }}
    >
      <MaterialCommunityIcons name={icon} size={22} color={theme.colors.textPrimary} />
      <View style={{ marginStart: theme.spacing.md, flex: 1 }}>
        <Text style={{ color: theme.colors.textPrimary, fontFamily: theme.typography.fontBold, textAlign: I18nManager.isRTL ? 'right' : 'left' }}>{title}</Text>
        <Text style={{ color: theme.colors.textSecondary, fontFamily: theme.typography.fontRegular, marginTop: 2, textAlign: I18nManager.isRTL ? 'right' : 'left' }}>{subtitle}</Text>
      </View>
      <MaterialCommunityIcons name="chevron-left" size={22} color={theme.colors.textSecondary} />
    </TouchableOpacity>
  );
}

export default function SupportScreen() {
  const openLink = async (url) => {
    try {
      await Linking.openURL(url);
    } catch {}
  };

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: theme.colors.background }}>
      <View style={{ paddingHorizontal: 16, paddingTop: theme.spacing.md }}>
        <Text style={{ color: theme.colors.textPrimary, fontFamily: theme.typography.fontBold, fontSize: theme.typography.sizes.lg, textAlign: I18nManager.isRTL ? 'right' : 'left' }}>الدعم والمساعدة</Text>
        <Text style={{ color: theme.colors.textSecondary, fontFamily: theme.typography.fontRegular, marginTop: 4, textAlign: I18nManager.isRTL ? 'right' : 'left' }}>اختر وسيلة التواصل المناسبة وسنخدمك بأسرع وقت</Text>
        <Row
          icon="whatsapp"
          title="واتساب الدعم"
          subtitle="تواصل مباشر مع فريق الخدمة"
          onPress={() => openLink('https://wa.me/9647700000000')}
        />
        <Row
          icon="email-outline"
          title="البريد الإلكتروني"
          subtitle="support@clothingstore.iq"
          onPress={() => openLink('mailto:support@clothingstore.iq')}
        />
        <Row
          icon="phone-outline"
          title="اتصال هاتفي"
          subtitle="+964 770 000 0000"
          onPress={() => openLink('tel:+9647700000000')}
        />
      </View>
    </SafeAreaView>
  );
}
