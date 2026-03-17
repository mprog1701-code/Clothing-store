import React, { useEffect, useLayoutEffect, useMemo, useState } from 'react';
import { View, Text, FlatList, TouchableOpacity, ActivityIndicator, RefreshControl, I18nManager, StyleSheet } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { listCategories } from '../api';
import theme from '../theme';
import EmptyState from '../components/EmptyState';

export default function AllCategoriesScreen({ navigation, route }) {
  const listTitle = route?.params?.listTitle || 'كل الأقسام';
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState('');

  useLayoutEffect(() => {
    navigation.setOptions({ title: listTitle });
  }, [listTitle, navigation]);

  const normalizeCategories = (raw) => {
    const fromApi = Array.isArray(raw)
      ? raw
      : (raw?.categories || raw?.results || raw?.items || []);
    return (fromApi || []).map((item, index) => ({
      id: String(item?.id ?? item?.key ?? item?.value ?? index),
      key: String(item?.key ?? item?.id ?? item?.value ?? ''),
      name: String(item?.name ?? item?.label ?? item?.title ?? 'قسم'),
    }));
  };

  const load = async () => {
    setError('');
    try {
      const data = await listCategories();
      const arr = normalizeCategories(data);
      setItems(arr);
    } catch {
      setError('تعذر تحميل الأقسام');
      setItems([]);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const onRefresh = () => {
    setRefreshing(true);
    load();
  };

  const hasItems = useMemo(() => Array.isArray(items) && items.length > 0, [items]);

  if (loading) {
    return (
      <SafeAreaView style={styles.centered}>
        <ActivityIndicator color={theme.colors.accent} />
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      {!hasItems ? (
        <EmptyState
          icon="grid-outline"
          title="لا توجد أقسام متاحة حالياً"
          subtitle={error || 'تحقق من مصدر بيانات الأقسام ثم أعد المحاولة'}
          ctaLabel="إعادة المحاولة"
          onPress={load}
        />
      ) : (
        <FlatList
          data={items}
          keyExtractor={(item) => item.id}
          refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
          numColumns={2}
          contentContainerStyle={styles.list}
          columnWrapperStyle={styles.row}
          renderItem={({ item }) => (
            <TouchableOpacity
              onPress={() => navigation.navigate('ProductsList', { type: 'category', categoryId: item.key, categoryLabel: item.name, listTitle: item.name })}
              style={styles.card}
            >
              <Text style={styles.cardText}>{item.name}</Text>
            </TouchableOpacity>
          )}
        />
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: theme.colors.background,
  },
  centered: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: theme.colors.background,
  },
  list: {
    paddingHorizontal: 16,
    paddingVertical: theme.spacing.md,
  },
  row: {
    justifyContent: 'space-between',
  },
  card: {
    width: '48%',
    backgroundColor: theme.colors.surface,
    borderWidth: 1,
    borderColor: theme.colors.cardBorder,
    borderRadius: theme.radius.lg,
    paddingVertical: theme.spacing.lg,
    paddingHorizontal: theme.spacing.md,
    marginBottom: theme.spacing.md,
    alignItems: 'center',
    justifyContent: 'center',
  },
  cardText: {
    fontFamily: theme.typography.fontBold,
    color: theme.colors.textPrimary,
    textAlign: I18nManager.isRTL ? 'right' : 'left',
  },
});
