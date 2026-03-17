import React from 'react';
import { View, Text, StyleSheet, ScrollView } from 'react-native';
import PromoBanner from './PromoBanner';
import theme from '../theme';

export default function PromoBannerGrid({
  items = [],
  title = 'Promotions',
  emptyTitle = 'Coming Soon',
  onPressItem,
}) {
  const list = Array.isArray(items) ? items : [];
  return (
    <View>
      <Text style={styles.title}>{title}</Text>
      {list.length ? (
        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.row}>
          {list.map((item, index) => (
            <PromoBanner key={String(item?.id ?? index)} item={item} onPress={onPressItem} />
          ))}
        </ScrollView>
      ) : (
        <View style={styles.emptyCard}>
          <Text style={styles.emptyText}>{emptyTitle}</Text>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  title: {
    color: theme.colors.textPrimary,
    fontFamily: theme.typography.fontBold,
    fontSize: theme.typography.sizes.lg,
    marginBottom: theme.spacing.sm,
    textAlign: 'right',
  },
  row: {
    paddingBottom: theme.spacing.sm,
  },
  emptyCard: {
    borderRadius: theme.radius.lg,
    borderWidth: 1,
    borderColor: theme.colors.cardBorder,
    backgroundColor: theme.colors.surfaceAlt,
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: 100,
    marginBottom: theme.spacing.lg,
  },
  emptyText: {
    color: theme.colors.textSecondary,
    fontFamily: theme.typography.fontRegular,
  },
});
