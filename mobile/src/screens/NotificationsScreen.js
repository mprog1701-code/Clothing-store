import React from 'react';
import { SafeAreaView } from 'react-native-safe-area-context';
import { View } from 'react-native';
import theme from '../theme';
import EmptyState from '../components/EmptyState';

export default function NotificationsScreen() {
  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: theme.colors.background }}>
      <View style={{ flex: 1, justifyContent: 'center' }}>
        <EmptyState
          icon="bell-outline"
          title="لا توجد إشعارات جديدة"
          subtitle="عند توفر تحديثات على طلباتك ستظهر هنا"
        />
      </View>
    </SafeAreaView>
  );
}
