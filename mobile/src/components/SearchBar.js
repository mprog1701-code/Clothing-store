import React, { useEffect, useState } from 'react';
import { View, Text, TextInput, I18nManager } from 'react-native';
import theme from '../theme';

export default function SearchBar({ initial = '', onChange, placeholder = 'ابحث...', debounce = 300 }) {
  const [q, setQ] = useState(initial);
  useEffect(() => {
    const t = setTimeout(() => {
      onChange && onChange(q);
    }, debounce);
    return () => clearTimeout(t);
  }, [q, debounce, onChange]);
  return (
    <View style={{ flexDirection: 'row', alignItems: 'center', backgroundColor: theme.colors.surfaceAlt, borderRadius: theme.radius.lg, borderWidth: 1, borderColor: theme.colors.cardBorder, paddingHorizontal: theme.spacing.md, paddingVertical: theme.spacing.sm }}>
      <Text style={{ color: theme.colors.textSecondary, marginRight: theme.spacing.sm }}>🔍</Text>
      <TextInput
        value={q}
        onChangeText={setQ}
        placeholder={placeholder}
        placeholderTextColor={theme.colors.textSecondary}
        style={{ flex: 1, color: theme.colors.textPrimary, fontFamily: theme.typography.fontRegular, fontSize: theme.typography.sizes.md, textAlign: I18nManager.isRTL ? 'right' : 'left' }}
      />
    </View>
  );
}
