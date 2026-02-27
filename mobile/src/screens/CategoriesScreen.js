import React, { useEffect, useState } from 'react';
import { View, Text, FlatList, TouchableOpacity, ActivityIndicator, RefreshControl, I18nManager } from 'react-native';
import { listCategories } from '../api';
import theme from '../theme';

export default function CategoriesScreen({ navigation }) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState('');

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
      <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center', backgroundColor: theme.colors.background }}>
        <ActivityIndicator />
      </View>
    );
  }
  if (error) {
    return (
      <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center', backgroundColor: theme.colors.background }}>
        <Text style={{ color: theme.colors.textSecondary }}>{error}</Text>
      </View>
    );
  }

  return (
    <FlatList
      data={items}
      keyExtractor={(item) => String(item.id)}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
      renderItem={({ item }) => (
        <TouchableOpacity
          onPress={() => navigation.navigate('Products', { mode: 'category', categoryId: item.id })}
          style={{ padding: theme.spacing.md, borderBottomWidth: 1, borderColor: theme.colors.cardBorder, backgroundColor: theme.colors.background }}
        >
          <Text style={{ fontFamily: theme.typography.fontBold, color: theme.colors.textPrimary, textAlign: I18nManager.isRTL ? 'right' : 'left' }}>{item.name}</Text>
        </TouchableOpacity>
      )}
    />
  );
}
