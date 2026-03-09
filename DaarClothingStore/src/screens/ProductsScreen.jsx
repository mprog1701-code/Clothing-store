import React, { useEffect, useState } from 'react';
import { View, Text, FlatList, StyleSheet, ActivityIndicator } from 'react-native';
import { COLORS } from '../theme/colors';
import ProductCard from '../components/ProductCard';
import { getProducts } from '../api/products';

export default function ProductsScreen({ navigation }) {
  const [loading, setLoading] = useState(true);
  const [items, setItems] = useState([]);

  useEffect(() => {
    let mounted = true;
    const load = async () => {
      try {
        const data = await getProducts();
        const list = Array.isArray(data) ? data : data?.results || [];
        if (mounted) setItems(list);
      } catch (_error) {
        if (mounted) setItems([]);
      } finally {
        if (mounted) setLoading(false);
      }
    };
    load();
    return () => {
      mounted = false;
    };
  }, []);

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator color={COLORS.primary} size="large" />
      </View>
    );
  }

  if (!items.length) {
    return (
      <View style={styles.center}>
        <Text style={styles.emptyText}>لا توجد منتجات حالياً</Text>
      </View>
    );
  }

  return (
    <FlatList
      contentContainerStyle={styles.list}
      data={items}
      keyExtractor={(item, index) => String(item.id || index)}
      renderItem={({ item }) => (
        <ProductCard product={item} onPress={() => navigation.navigate('ProductDetail', { product: item })} />
      )}
    />
  );
}

const styles = StyleSheet.create({
  list: {
    padding: 15,
    backgroundColor: COLORS.background,
  },
  center: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: COLORS.background,
  },
  emptyText: {
    color: COLORS.textSecondary,
    fontSize: 16,
  },
});
