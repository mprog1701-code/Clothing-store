import React from 'react';
import { View, Text, Image, StyleSheet, ScrollView } from 'react-native';
import { Button } from 'react-native-paper';
import { COLORS } from '../theme/colors';

export default function ProductDetailScreen({ route, navigation }) {
  const product = route?.params?.product || {};
  const title = product.name || 'تفاصيل المنتج';
  const price = product.price ? `${Number(product.price).toLocaleString()} د.ع` : '';
  const image = product.image || 'https://placehold.co/600x600/8b2f97/ffffff?text=Product';

  return (
    <ScrollView style={styles.container}>
      <Image source={{ uri: image }} style={styles.image} />
      <View style={styles.content}>
        <Text style={styles.title}>{title}</Text>
        <Text style={styles.price}>{price}</Text>
        <Text style={styles.description}>
          منتج أصلي بجودة عالية مع ضمان التوصيل داخل جميع المحافظات.
        </Text>
        <Button mode="contained" onPress={() => navigation.navigate('Cart')} style={styles.button}>
          إضافة إلى السلة
        </Button>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  image: {
    width: '100%',
    height: 320,
  },
  content: {
    padding: 16,
  },
  title: {
    color: COLORS.text,
    fontSize: 22,
    fontWeight: 'bold',
    marginBottom: 8,
  },
  price: {
    color: COLORS.primary,
    fontSize: 20,
    fontWeight: 'bold',
    marginBottom: 12,
  },
  description: {
    color: COLORS.textSecondary,
    fontSize: 14,
    lineHeight: 22,
    marginBottom: 16,
  },
  button: {
    backgroundColor: COLORS.primary,
  },
});
