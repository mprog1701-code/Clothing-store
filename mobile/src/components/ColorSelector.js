import React from 'react';
import { View, Text, Pressable } from 'react-native';
import theme from '../theme';

export default function ColorSelector({ variants, selectedId, onSelect }) {
  return (
    <View style={{ paddingHorizontal: theme.spacing.lg, paddingVertical: theme.spacing.md }}>
      <View style={{ flexDirection: 'row', flexWrap: 'wrap' }}>
        {variants.map((v) => {
          const active = v.id === selectedId;
          return (
            <Pressable
              key={v.id}
              onPress={() => onSelect(v)}
              style={{
                width: 36,
                height: 36,
                borderRadius: 18,
                marginRight: theme.spacing.sm,
                marginBottom: theme.spacing.sm,
                backgroundColor: v.color_hex || '#ccc',
                borderWidth: active ? 2 : 1,
                borderColor: active ? theme.colors.accent : theme.colors.cardBorder,
              }}
            />
          );
        })}
      </View>
      {variants.find((vv) => vv.id === selectedId)?.color_name ? (
        <Text style={{ marginTop: theme.spacing.xs, color: theme.colors.textPrimary, fontFamily: theme.typography.fontRegular }}>
          {variants.find((vv) => vv.id === selectedId)?.color_name}
        </Text>
      ) : null}
    </View>
  );
}
