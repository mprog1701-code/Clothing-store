import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, ActivityIndicator, Alert, I18nManager, StyleSheet, KeyboardAvoidingView, Platform, ScrollView } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { firebaseResetPassword, sendPhoneOtp, verifyPhoneOtp, confirmPasswordReset } from '../api';
import theme from '../theme';
import { normalizeIraqiPhone } from '../utils/phone';

export default function ForgotPasswordScreen({ navigation }) {
  const [identifier, setIdentifier] = useState('');
  const [code, setCode] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [requested, setRequested] = useState(false);
  const [legacyOtpMode, setLegacyOtpMode] = useState(false);
  const [resetTicket, setResetTicket] = useState('');
  const normalizeIdentifier = (value) => normalizeIraqiPhone(String(value || '').trim());

  const onRequest = async () => {
    const normalizedIdentifier = normalizeIdentifier(identifier);
    if (!normalizedIdentifier) {
      Alert.alert('تنبيه', 'يرجى إدخال رقم هاتف صحيح');
      return;
    }
    setLoading(true);
    try {
      const res = await sendPhoneOtp({ phone: normalizedIdentifier, purpose: 'reset' });
      setLegacyOtpMode(Boolean(res?.legacy));
      setResetTicket(String(res?.reset_ticket || ''));
      setRequested(true);
      Alert.alert('تم', 'تم إرسال رمز التحقق إلى رقم الهاتف');
    } catch (e) {
      const code = String(e?.code || e?.payload?.code || e?.response?.data?.code || '');
      const raw = String(e?.response?.data?.error || e?.message || 'تعذر إرسال رمز Firebase');
      const normalizedRaw = String(raw || '');
      const message = normalizedRaw === 'INFOBIP_INSUFFICIENT_BALANCE'
        ? 'رصيد الرسائل غير كافٍ في مزود الرسائل'
        : normalizedRaw === 'INFOBIP_INVALID_NUMBER'
          ? 'رقم الهاتف غير صالح للإرسال'
          : normalizedRaw === 'INFOBIP_CONFIG_MISSING'
            ? 'إعدادات Infobip غير مكتملة على الخادم'
            : normalizedRaw === 'INFOBIP_TEMPLATE_MISSING'
              ? 'قالب واتساب غير مُعد بشكل صحيح في Infobip'
              : normalizedRaw === 'INFOBIP_UNREACHABLE'
                ? 'تعذر الاتصال بمزود الرسائل. حاول لاحقًا'
                : normalizedRaw === 'INFOBIP_HTTP_ERROR'
                  ? 'مزود الرسائل رفض الطلب. تحقق من الإعدادات'
          : code === 'PHONE_INVALID'
            ? 'يرجى إدخال رقم هاتف صحيح'
            : normalizedRaw;
      Alert.alert('خطأ', message);
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
      if (legacyOtpMode) {
        await confirmPasswordReset({
          identifier: normalizedIdentifier,
          phone: normalizedIdentifier,
          code: code.trim(),
          new_password: newPassword.trim(),
          reset_ticket: resetTicket || undefined,
        });
        Alert.alert('تم', 'تم تغيير كلمة المرور بنجاح');
        navigation.goBack();
        return;
      }
      const verifyResult = await verifyPhoneOtp({ phone: normalizedIdentifier, purpose: 'reset', otp_code: code.trim() });
      const token = String(verifyResult?.verification_token || '');
      if (!token) {
        Alert.alert('خطأ', 'تعذر التحقق من الرمز');
        setLoading(false);
        return;
      }
      await firebaseResetPassword({ verification_token: token, new_password: newPassword.trim(), phone: normalizedIdentifier });
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
            <Text style={styles.subtitle}>أدخل رقم الهاتف ثم رمز التحقق لإعادة تعيين كلمة المرور</Text>
            <TextInput
              value={identifier}
              onChangeText={setIdentifier}
              placeholder="رقم الهاتف"
              placeholderTextColor="rgba(255,255,255,0.6)"
              style={styles.input}
              keyboardType="number-pad"
              maxLength={11}
            />
            <TouchableOpacity onPress={onRequest} disabled={loading} style={styles.button}>
              {loading ? <ActivityIndicator color="#000" /> : <Text style={styles.buttonText}>إرسال رمز التحقق</Text>}
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
