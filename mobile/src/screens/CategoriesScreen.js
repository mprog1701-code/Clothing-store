import React, { useEffect, useLayoutEffect, useState } from 'react';
import { View, Text, FlatList, TouchableOpacity, ActivityIndicator, RefreshControl, I18nManager, StyleSheet } from 'react-native';
import { listCategories } from '../api';
import theme from '../theme';
import { SafeAreaView } from 'react-native-safe-area-context';

export default function CategoriesScreen({ navigation, route }) {
  const listTitle = route?.params?.listTitle || 'كل الأقسام';
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState('');

  useLayoutEffect(() => {
    navigation.setOptions({ title: listTitle });
  }, [listTitle, navigation]);

  const load = async () => {
    setError('');
    try {
      const data = await listCategories();
      const arr = Array.isArray(data) ? data : (data.results || []);
      setItems(arr || []);
    } catch (e) {
      setError('تعذر تحميل الأقسام');
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

  if (loading) {
    return (
      <SafeAreaView style={styles.centered}>
        <ActivityIndicator />
      </SafeAreaView>
    );
  }
  if (error) {
    return (
      <SafeAreaView style={styles.centered}>
        <Text style={styles.errorText}>{error}</Text>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <FlatList
        data={items}
        keyExtractor={(item) => String(item.id)}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
        numColumns={2}
        contentContainerStyle={styles.list}
        columnWrapperStyle={styles.row}
        renderItem={({ item }) => (
          <TouchableOpacity
            onPress={() => navigation.navigate('ProductsList', { type: 'category', categoryId: item.id, categoryLabel: item.name, listTitle: item.name })}
            style={styles.card}
          >
            <Text style={styles.cardText}>{item.name}</Text>
          </TouchableOpacity>
        )}
      />
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
  errorText: {
    color: theme.colors.textSecondary,
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
