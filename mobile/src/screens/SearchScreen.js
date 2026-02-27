import React, { useState } from 'react';
import { View, Text, TextInput, Button, I18nManager } from 'react-native';
import theme from '../theme';

export default function SearchScreen() {
  const [q, setQ] = useState('');
  return (
    <View style={{ flex: 1, backgroundColor: theme.colors.background, padding: theme.spacing.lg }}>
      <Text style={{ color: theme.colors.textPrimary, fontFamily: theme.typography.fontBold, fontSize: theme.typography.sizes.lg, textAlign: I18nManager.isRTL ? 'right' : 'left' }}>
        البحث
      </Text>
      <View style={{ flexDirection: 'row', alignItems: 'center', backgroundColor: theme.colors.surfaceAlt, borderRadius: theme.radius.lg, borderWidth: 1, borderColor: theme.colors.cardBorder, paddingHorizontal: theme.spacing.md, paddingVertical: theme.spacing.sm, marginTop: theme.spacing.md }}>
        <Text style={{ color: theme.colors.textSecondary, marginRight: theme.spacing.sm }}>🔍</Text>
        <TextInput
          value={q}
          onChangeText={setQ}
          placeholder="ابحث هنا..."
          placeholderTextColor={theme.colors.textSecondary}
          style={{ flex: 1, color: theme.colors.textPrimary, fontFamily: theme.typography.fontRegular, fontSize: theme.typography.sizes.md, textAlign: I18nManager.isRTL ? 'right' : 'left' }}
        />
      </View>
      <Button title="بحث" onPress={() => {}} />
    </View>
  );
}
