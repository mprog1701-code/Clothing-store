import React from 'react';
import { View, Text, TouchableOpacity } from 'react-native';
import theme from '../theme';

export default function SizeSelector({ sizes, selectedSize, onSelect }) {
  return (
    <View style={{ paddingHorizontal: theme.spacing.lg, paddingVertical: theme.spacing.md, flexDirection: 'row', flexWrap: 'wrap' }}>
      {sizes.map((s) => {
        const active = s.value === selectedSize;
        const disabled = s.in_stock === false;
        return (
          <TouchableOpacity
            key={s.value}
            disabled={disabled}
            onPress={() => onSelect(s.value)}
            style={{
              paddingHorizontal: theme.spacing.md,
              paddingVertical: theme.spacing.sm,
              marginRight: theme.spacing.sm,
              marginBottom: theme.spacing.sm,
              borderRadius: theme.radius.md,
              borderWidth: 1,
              borderColor: active ? theme.colors.accent : theme.colors.cardBorder,
              backgroundColor: disabled ? theme.colors.surfaceAlt : theme.colors.surface,
            }}
          >
            <Text style={{ color: theme.colors.textPrimary, fontFamily: theme.typography.fontRegular }}>{s.value}</Text>
          </TouchableOpacity>
        );
      })}
    </View>
  );
}
