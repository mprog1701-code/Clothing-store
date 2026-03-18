import React, { useMemo } from 'react';
import { View, Text, Pressable } from 'react-native';
import theme from '../theme';

export default function ColorSelector({ variants, selectedId, onSelect }) {
  const normalize = (s) => String(s || '').trim().toLowerCase();
  const colorHexForName = (name) => {
    const key = normalize(name);
    const M = {
      'أسود': '#000000',
      'ابيض': '#ffffff',
      'أبيض': '#ffffff',
      'احمر': '#ff3b30',
      'أحمر': '#ff3b30',
      'أزرق': '#007aff',
      'ازرق': '#007aff',
      'أخضر': '#34c759',
      'اخضر': '#34c759',
      'رمادي': '#8e8e93',
      'زهري': '#ff2d55',
      'وردي': '#ff2d55',
      'بنفسجي': '#af52de',
      'بني': '#795548',
      'بيج': '#f5f5dc',
      'ذهبي': '#d4af37',
      'فضي': '#c0c0c0',
      'أزرق داكن': '#003366',
      'كحلي': '#003366',
    };
    return M[key] || '';
  };
  const selectedVar = variants.find((v) => v.id === selectedId);
  const selectedKey =
    (selectedVar?.color_key || normalize(selectedVar?.color_name) || normalize(selectedVar?.color) || '__unknown__').trim();
  const colors = useMemo(() => {
    const byKey = new Map();
    let hasUnknown = false;
    for (const v of variants) {
      const key = (v.color_key || normalize(v.color_name) || normalize(v.color) || '').trim();
      if (!key) {
        hasUnknown = true;
        continue;
      }
      if (!byKey.has(key)) byKey.set(key, v);
    }
    if (hasUnknown && !byKey.has('__unknown__')) {
      const any = variants[0];
      if (any) {
        byKey.set('__unknown__', { ...any, color_key: '__unknown__', color_name: 'غير محدد' });
      }
    }
    return Array.from(byKey.values());
  }, [variants]);
  return (
    <View style={{ paddingHorizontal: theme.spacing.lg, paddingVertical: theme.spacing.xs }}>
      <View style={{ flexDirection: 'row', flexWrap: 'wrap' }}>
        {colors.map((v) => {
          const key = (v.color_key || normalize(v.color_name) || normalize(v.color) || '__unknown__').trim();
          const active = key && key === selectedKey;
          const bg =
            v.color_hex ||
            colorHexForName(v.color_name || v.color) ||
            theme.colors.surfaceAlt;
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
                backgroundColor: bg,
                borderWidth: active ? 2 : 1,
                borderColor: active ? theme.colors.accent : theme.colors.cardBorder,
              }}
            />
          );
        })}
      </View>
      {selectedVar?.color_name || selectedVar?.color ? (
        <Text style={{ marginTop: theme.spacing.xs, color: theme.colors.textPrimary, fontFamily: theme.typography.fontRegular }}>
          {selectedVar?.color_name || selectedVar?.color}
        </Text>
      ) : null}
    </View>
  );
}
