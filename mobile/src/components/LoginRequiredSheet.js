import React from 'react';
import { View, Text, Modal, TouchableOpacity } from 'react-native';
import theme from '../theme';

export default function LoginRequiredSheet({ visible, onLogin, onClose }) {
  return (
    <Modal visible={visible} animationType="slide" transparent>
      <View style={{ flex: 1, justifyContent: 'flex-end', backgroundColor: 'rgba(0,0,0,0.4)' }}>
        <View style={{ padding: theme.spacing.lg, borderTopLeftRadius: theme.radius.xl, borderTopRightRadius: theme.radius.xl, backgroundColor: theme.colors.surface }}>
          <Text style={{ color: theme.colors.textPrimary, fontFamily: theme.typography.fontBold, fontSize: theme.typography.sizes.md, textAlign: 'center' }}>لإكمال الطلب لازم تسجّل دخول</Text>
          <View style={{ marginTop: theme.spacing.md }}>
            <TouchableOpacity onPress={onLogin} style={{ paddingVertical: theme.spacing.md, borderRadius: theme.radius.lg, backgroundColor: theme.colors.accent, alignItems: 'center' }}>
              <Text style={{ color: '#000', fontFamily: theme.typography.fontBold }}>تسجيل الدخول</Text>
            </TouchableOpacity>
            <TouchableOpacity onPress={onClose} style={{ paddingVertical: theme.spacing.md, borderRadius: theme.radius.lg, alignItems: 'center', marginTop: theme.spacing.sm }}>
              <Text style={{ color: theme.colors.textSecondary, fontFamily: theme.typography.fontRegular }}>متابعة التصفح</Text>
            </TouchableOpacity>
          </View>
        </View>
      </View>
    </Modal>
  );
}
