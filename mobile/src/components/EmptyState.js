import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import theme from '../theme';

export default function EmptyState({
  icon = 'information-outline',
  title = 'لا توجد بيانات',
  subtitle = '',
  ctaLabel = '',
  onPress,
}) {
  return (
    <View style={styles.container}>
      <View style={styles.iconWrap}>
        <MaterialCommunityIcons name={icon} size={36} color={theme.colors.accentAlt} />
      </View>
      <Text style={styles.title}>{title}</Text>
      {!!subtitle && <Text style={styles.subtitle}>{subtitle}</Text>}
      {!!ctaLabel && !!onPress && (
        <TouchableOpacity onPress={onPress} style={styles.cta}>
          <Text style={styles.ctaText}>{ctaLabel}</Text>
        </TouchableOpacity>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 28,
    paddingHorizontal: 20,
  },
  iconWrap: {
    width: 66,
    height: 66,
    borderRadius: 33,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: theme.colors.surfaceAlt,
    borderWidth: 1,
    borderColor: theme.colors.cardBorder,
    marginBottom: 12,
  },
  title: {
    color: theme.colors.textPrimary,
    fontFamily: theme.typography.fontBold,
    fontSize: theme.typography.sizes.md,
    textAlign: 'center',
  },
  subtitle: {
    marginTop: 6,
    color: theme.colors.textSecondary,
    fontFamily: theme.typography.fontRegular,
    fontSize: theme.typography.sizes.sm,
    textAlign: 'center',
  },
  cta: {
    marginTop: 14,
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: theme.radius.md,
    backgroundColor: theme.colors.accent,
  },
  ctaText: {
    color: '#000',
    fontFamily: theme.typography.fontBold,
    fontSize: theme.typography.sizes.sm,
  },
});
