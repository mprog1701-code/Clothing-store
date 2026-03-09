import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Button } from 'react-native-paper';
import { COLORS } from '../theme/colors';

export default function CartScreen() {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>السلة فارغة حالياً</Text>
      <Text style={styles.subtitle}>ابدأ بإضافة منتجاتك المفضلة</Text>
      <Button mode="contained" style={styles.button}>
        متابعة التسوق
      </Button>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 20,
  },
  title: {
    color: COLORS.text,
    fontSize: 20,
    fontWeight: 'bold',
    marginBottom: 8,
  },
  subtitle: {
    color: COLORS.textSecondary,
    marginBottom: 20,
  },
  button: {
    backgroundColor: COLORS.primary,
  },
});
