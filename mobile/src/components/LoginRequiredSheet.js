import React from 'react';
import { View, Text, Modal, TouchableOpacity, StyleSheet } from 'react-native';
import theme from '../theme';

export default function LoginRequiredSheet({
  visible,
  onLogin,
  onClose,
  message = 'سجل دخولك الآن لتتمكن من إتمام الطلب والتمتع بمميزات دار!',
  buttonLabel = 'تسجيل دخول',
}) {
  return (
    <Modal visible={visible} animationType="slide" transparent statusBarTranslucent>
      <View style={styles.backdrop}>
        <View style={styles.sheet}>
          <View style={styles.handle} />
          <Text style={styles.title}>الدخول مطلوب</Text>
          <Text style={styles.message}>{message}</Text>
          <View style={styles.actions}>
            <TouchableOpacity onPress={onLogin} style={styles.loginButton}>
              <Text style={styles.loginButtonText}>{buttonLabel}</Text>
            </TouchableOpacity>
            <TouchableOpacity onPress={onClose} style={styles.closeButton}>
              <Text style={styles.closeText}>متابعة التصفح</Text>
            </TouchableOpacity>
          </View>
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  backdrop: {
    flex: 1,
    justifyContent: 'flex-end',
    backgroundColor: 'rgba(0,0,0,0.45)',
  },
  sheet: {
    padding: theme.spacing.lg,
    borderTopLeftRadius: theme.radius.lg,
    borderTopRightRadius: theme.radius.lg,
    backgroundColor: theme.colors.surface,
    borderTopWidth: 1,
    borderLeftWidth: 1,
    borderRightWidth: 1,
    borderColor: theme.colors.cardBorder,
  },
  handle: {
    width: 48,
    height: 4,
    borderRadius: 2,
    alignSelf: 'center',
    backgroundColor: theme.colors.cardBorder,
    marginBottom: theme.spacing.md,
  },
  title: {
    color: theme.colors.textPrimary,
    fontFamily: theme.typography.fontBold,
    fontSize: theme.typography.sizes.md,
    textAlign: 'center',
  },
  message: {
    marginTop: theme.spacing.sm,
    color: theme.colors.textSecondary,
    fontFamily: theme.typography.fontRegular,
    fontSize: theme.typography.sizes.sm,
    textAlign: 'center',
    lineHeight: 21,
  },
  actions: {
    marginTop: theme.spacing.md,
  },
  loginButton: {
    paddingVertical: theme.spacing.md,
    borderRadius: theme.radius.lg,
    backgroundColor: theme.colors.accent,
    alignItems: 'center',
    ...theme.shadows.appBar,
  },
  loginButtonText: {
    color: '#000',
    fontFamily: theme.typography.fontBold,
    fontSize: theme.typography.sizes.md,
  },
  closeButton: {
    paddingVertical: theme.spacing.md,
    borderRadius: theme.radius.lg,
    alignItems: 'center',
    marginTop: theme.spacing.sm,
  },
  closeText: {
    color: theme.colors.textSecondary,
    fontFamily: theme.typography.fontRegular,
  },
});
