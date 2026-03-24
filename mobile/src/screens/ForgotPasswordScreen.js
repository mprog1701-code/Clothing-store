import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, ActivityIndicator, Alert, I18nManager, StyleSheet, KeyboardAvoidingView, Platform, ScrollView } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { requestPasswordReset, confirmPasswordReset } from '../api';
import theme from '../theme';
import { normalizeIraqiPhone } from '../utils/phone';

export default function ForgotPasswordScreen({ navigation }) {
  const [identifier, setIdentifier] = useState('');
  const [code, setCode] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [resetTicket, setResetTicket] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [requested, setRequested] = useState(false);
  const normalizeIdentifier = (value) => {
    const raw = String(value || '').trim();
    if (!raw) return '';
    const normalizedPhone = normalizeIraqiPhone(raw);
    if (normalizedPhone) return normalizedPhone;
    return raw.toLowerCase();
  };

  const onRequest = async () => {
    const normalizedIdentifier = normalizeIdentifier(identifier);
    if (!normalizedIdentifier) {
      Alert.alert('تنبيه', 'يرجى إدخال رقم الهاتف أو البريد الإلكتروني');
      return;
    }
    setLoading(true);
    try {
      const res = await requestPasswordReset({ identifier: normalizedIdentifier });
      setRequested(true);
      setResetTicket(String(res?.reset_ticket || ''));
      const deliveredCode = String(res?.debug_code || res?.reset_code || '').trim();
      if (deliveredCode) {
        setCode(deliveredCode);
        Alert.alert('تم', `رمز الاسترجاع: ${deliveredCode}`);
      } else {
        Alert.alert('تم', String(res?.message || 'إذا كانت البيانات صحيحة تم إرسال رمز الاسترجاع'));
      }
    } catch (e) {
      Alert.alert('خطأ', String(e?.response?.data?.error || 'تعذر إرسال رمز الاسترجاع'));
    } finally {
      setLoading(false);
    }
  };

  const onConfirm = async () => {
    const normalizedIdentifier = normalizeIdentifier(identifier);
    if (!normalizedIdentifier || !code.trim() || !newPassword.trim()) {
      Alert.alert('تنبيه', 'يرجى تعبئة جميع الحقول');
      return;
    }
    if (newPassword.trim().length < 6) {
      Alert.alert('تنبيه', 'كلمة المرور يجب أن تكون 6 أحرف على الأقل');
      return;
    }
    setLoading(true);
    try {
      let activeTicket = String(resetTicket || '').trim();
      let activeCode = code.trim();
      if (!activeTicket) {
        const bootstrap = await requestPasswordReset({ identifier: normalizedIdentifier });
        activeTicket = String(bootstrap?.reset_ticket || '').trim();
        const deliveredCode = String(bootstrap?.debug_code || bootstrap?.reset_code || '').trim();
        if (deliveredCode) {
          activeCode = deliveredCode;
          setCode(deliveredCode);
        }
        setResetTicket(activeTicket);
      }
      await confirmPasswordReset({ identifier: normalizedIdentifier, code: activeCode, new_password: newPassword.trim(), reset_ticket: activeTicket || undefined });
      Alert.alert('تم', 'تم تغيير كلمة المرور بنجاح');
      navigation.goBack();
    } catch (e) {
      Alert.alert('خطأ', String(e?.response?.data?.error || e?.response?.data?.message || 'تعذر تغيير كلمة المرور'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <LinearGradient colors={['#0c1b33', '#081226']} style={{ flex: 1 }}>
      <SafeAreaView style={{ flex: 1 }}>
        <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : 'height'} keyboardVerticalOffset={Platform.OS === 'ios' ? 0 : 24} style={{ flex: 1 }}>
          <ScrollView contentContainerStyle={{ padding: theme.spacing.lg, paddingBottom: theme.spacing.xl * 4 }} keyboardShouldPersistTaps="handled" keyboardDismissMode="on-drag">
            <Text style={styles.title}>استعادة كلمة المرور</Text>
            <Text style={styles.subtitle}>أدخل رقم الهاتف أو البريد، ثم الرمز وكلمة المرور الجديدة</Text>
            <TextInput
              value={identifier}
              onChangeText={setIdentifier}
              placeholder="رقم الهاتف أو البريد الإلكتروني"
              placeholderTextColor="rgba(255,255,255,0.6)"
              style={styles.input}
              autoCapitalize="none"
              keyboardType="default"
            />
            <TouchableOpacity onPress={onRequest} disabled={loading} style={styles.button}>
              {loading ? <ActivityIndicator color="#000" /> : <Text style={styles.buttonText}>إرسال رمز الاسترجاع</Text>}
            </TouchableOpacity>
            {requested ? (
              <View style={{ marginTop: theme.spacing.lg }}>
                <TextInput
                  value={code}
                  onChangeText={setCode}
                  placeholder="رمز التحقق"
                  placeholderTextColor="rgba(255,255,255,0.6)"
                  style={styles.input}
                  keyboardType="number-pad"
                  maxLength={6}
                />
                <View style={styles.passwordRow}>
                  <TextInput
                    value={newPassword}
                    onChangeText={setNewPassword}
                    placeholder="كلمة المرور الجديدة"
                    placeholderTextColor="rgba(255,255,255,0.6)"
                    style={styles.passwordInput}
                    secureTextEntry={!showPassword}
                  />
                  <TouchableOpacity onPress={() => setShowPassword((v) => !v)} style={styles.eyeBtn}>
                    <MaterialCommunityIcons name={showPassword ? 'eye-off-outline' : 'eye-outline'} size={20} color="rgba(255,255,255,0.85)" />
                  </TouchableOpacity>
                </View>
                <TouchableOpacity onPress={onConfirm} disabled={loading} style={styles.button}>
                  {loading ? <ActivityIndicator color="#000" /> : <Text style={styles.buttonText}>تأكيد تغيير كلمة المرور</Text>}
                </TouchableOpacity>
              </View>
            ) : null}
          </ScrollView>
        </KeyboardAvoidingView>
      </SafeAreaView>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  title: {
    color: '#fff',
    fontFamily: theme.typography.fontBold,
    fontSize: theme.typography.sizes.lg,
    textAlign: I18nManager.isRTL ? 'right' : 'left',
  },
  subtitle: {
    marginTop: theme.spacing.sm,
    color: 'rgba(255,255,255,0.72)',
    fontFamily: theme.typography.fontRegular,
    textAlign: I18nManager.isRTL ? 'right' : 'left',
  },
  input: {
    marginTop: theme.spacing.md,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.2)',
    borderRadius: theme.radius.md,
    backgroundColor: 'rgba(255,255,255,0.06)',
    color: '#fff',
    paddingHorizontal: theme.spacing.md,
    paddingVertical: 12,
    textAlign: I18nManager.isRTL ? 'right' : 'left',
    fontFamily: theme.typography.fontRegular,
  },
  passwordRow: {
    marginTop: theme.spacing.md,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.2)',
    borderRadius: theme.radius.md,
    backgroundColor: 'rgba(255,255,255,0.06)',
    flexDirection: 'row',
    alignItems: 'center',
    paddingStart: theme.spacing.md,
  },
  passwordInput: {
    flex: 1,
    color: '#fff',
    paddingVertical: 12,
    textAlign: I18nManager.isRTL ? 'right' : 'left',
    fontFamily: theme.typography.fontRegular,
  },
  eyeBtn: {
    paddingHorizontal: theme.spacing.md,
    paddingVertical: theme.spacing.sm,
  },
  button: {
    marginTop: theme.spacing.md,
    minHeight: 50,
    borderRadius: theme.radius.md,
    backgroundColor: theme.colors.accent,
    alignItems: 'center',
    justifyContent: 'center',
  },
  buttonText: {
    color: '#000',
    fontFamily: theme.typography.fontBold,
  },
});
