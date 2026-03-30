import React, { useRef, useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, ActivityIndicator, Alert, I18nManager, StyleSheet, KeyboardAvoidingView, Platform, ScrollView } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { firebaseResetPassword } from '../api';
import theme from '../theme';
import { normalizeIraqiPhone } from '../utils/phone';
import { FirebaseRecaptchaVerifierModal } from 'expo-firebase-recaptcha';
import { signInWithPhoneNumber } from 'firebase/auth';
import { firebaseAuth, firebaseConfig, ensureFirebasePhoneAuthReady } from '../firebase';

export default function ForgotPasswordScreen({ navigation }) {
  const [identifier, setIdentifier] = useState('');
  const [code, setCode] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [requested, setRequested] = useState(false);
  const [confirmationResult, setConfirmationResult] = useState(null);
  const recaptchaVerifier = useRef(null);
  const normalizeIdentifier = (value) => normalizeIraqiPhone(String(value || '').trim());

  const onRequest = async () => {
    const normalizedIdentifier = normalizeIdentifier(identifier);
    if (!normalizedIdentifier) {
      Alert.alert('تنبيه', 'يرجى إدخال رقم هاتف صحيح');
      return;
    }
    setLoading(true);
    try {
      await ensureFirebasePhoneAuthReady();
      const e164 = `+964${String(normalizedIdentifier).replace(/^0/, '')}`;
      const confirmation = await signInWithPhoneNumber(firebaseAuth(), e164, recaptchaVerifier.current);
      setConfirmationResult(confirmation);
      setRequested(true);
      Alert.alert('تم', 'تم إرسال رمز Firebase إلى رقم الهاتف');
    } catch (e) {
      const code = String(e?.code || e?.payload?.code || e?.response?.data?.code || '');
      const raw = String(e?.response?.data?.error || e?.message || 'تعذر إرسال رمز Firebase');
      const normalizedRaw = String(raw || '');
      const message = raw === 'FIREBASE_CONFIG_INVALID'
        ? 'إعدادات Firebase غير مكتملة على التطبيق'
        : code === 'auth/invalid-app-credential'
          ? 'فشل تهيئة Firebase Phone Auth. تأكد من إضافة SHA-1 وSHA-256 لتطبيق Android في Firebase.'
          : code === 'auth/captcha-check-failed'
            ? 'فشل تحقق reCAPTCHA. أعد المحاولة وتأكد من اتصال الإنترنت.'
            : code === 'auth/web-storage-unsupported'
              ? 'بيئة التطبيق لا تدعم متطلبات Firebase web storage. استخدم نسخة Dev Client محدثة.'
        : normalizedRaw === 'FIREBASE_WEB_APP_ID_MISSING'
          ? 'Firebase Web App ID مفقود. أضف EXPO_PUBLIC_FIREBASE_WEB_APP_ID من إعدادات Web App في Firebase.'
          : normalizedRaw === 'FIREBASE_WEB_APP_NOT_CONFIGURED'
            ? 'مشروع Firebase لا يحتوي Web App فعّال على authDomain الحالي. أنشئ Web App واستخدم إعداداته.'
            : normalizedRaw === 'FIREBASE_AUTH_DOMAIN_UNREACHABLE'
              ? 'تعذر الوصول إلى Firebase authDomain. تحقق من الإنترنت وقيمة authDomain.'
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
      if (!confirmationResult) {
        Alert.alert('تنبيه', 'يرجى طلب رمز Firebase أولاً');
        setLoading(false);
        return;
      }
      const cred = await confirmationResult.confirm(code.trim());
      const idToken = await cred.user.getIdToken(true);
      await firebaseResetPassword({ id_token: idToken, new_password: newPassword.trim(), phone: normalizedIdentifier });
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
        <FirebaseRecaptchaVerifierModal ref={recaptchaVerifier} firebaseConfig={firebaseConfig} attemptInvisibleVerification={Platform.OS !== 'ios'} />
        <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : 'height'} keyboardVerticalOffset={Platform.OS === 'ios' ? 0 : 24} style={{ flex: 1 }}>
          <ScrollView contentContainerStyle={{ padding: theme.spacing.lg, paddingBottom: theme.spacing.xl * 4 }} keyboardShouldPersistTaps="handled" keyboardDismissMode="on-drag">
            <Text style={styles.title}>استعادة كلمة المرور</Text>
            <Text style={styles.subtitle}>تحقق عبر Firebase ثم أدخل كلمة المرور الجديدة</Text>
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
              {loading ? <ActivityIndicator color="#000" /> : <Text style={styles.buttonText}>إرسال رمز Firebase</Text>}
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
