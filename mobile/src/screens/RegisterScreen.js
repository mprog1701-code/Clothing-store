import React, { useMemo, useRef, useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, ActivityIndicator, I18nManager, StyleSheet, KeyboardAvoidingView, Platform, ScrollView, Modal } from 'react-native';
import theme from '../theme';
import { useAuth } from '../auth/AuthContext';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { normalizeIraqiPhone, isValidIraqiPhone } from '../utils/phone';
import { FirebaseRecaptchaVerifierModal } from 'expo-firebase-recaptcha';
import { signInWithPhoneNumber } from 'firebase/auth';
import { firebaseAuth, firebaseConfig, ensureFirebasePhoneAuthReady } from '../firebase';

const IRAQI_CITIES = [
  'بغداد',
  'البصرة',
  'أربيل',
  'النجف',
  'كربلاء',
  'الموصل',
  'السليمانية',
  'الناصرية',
  'الحلة',
  'ديالى',
];

export default function RegisterScreen({ navigation }) {
  const { register: registerUser } = useAuth();
  const [fullName, setFullName] = useState('');
  const [phone, setPhone] = useState('');
  const [email, setEmail] = useState('');
  const [city, setCity] = useState(IRAQI_CITIES[0]);
  const [password, setPassword] = useState('');
  const [passwordConfirm, setPasswordConfirm] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showPasswordConfirm, setShowPasswordConfirm] = useState(false);
  const [loading, setLoading] = useState(false);
  const [cityModalOpen, setCityModalOpen] = useState(false);
  const [errors, setErrors] = useState({});
  const [otpStep, setOtpStep] = useState(false);
  const [otpCode, setOtpCode] = useState('');
  const [confirmationResult, setConfirmationResult] = useState(null);
  const recaptchaVerifier = useRef(null);

  const validators = {
    fullName: (value) => {
      if (!value.trim()) return 'يرجى إدخال الاسم الكامل';
      if (value.trim().length < 3) return 'الاسم الكامل قصير جداً';
      return '';
    },
    phone: (value) => {
      if (!value) return 'يرجى إدخال رقم الهاتف';
      if (!isValidIraqiPhone(value)) return 'رقم الهاتف غير صحيح';
      return '';
    },
    email: (value) => {
      const v = String(value || '').trim();
      if (!v) return 'يرجى إدخال البريد الإلكتروني';
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v)) return 'صيغة البريد الإلكتروني غير صحيحة';
      return '';
    },
    city: (value) => (!value ? 'يرجى اختيار المدينة' : ''),
    password: (value) => {
      if (!value) return 'يرجى إدخال كلمة المرور';
      if (value.length < 6) return 'كلمة المرور يجب أن تكون 6 أحرف على الأقل';
      return '';
    },
    passwordConfirm: (value) => {
      if (!value) return 'يرجى تأكيد كلمة المرور';
      if (value !== password) return 'كلمتا المرور غير متطابقتين';
      return '';
    },
    otpCode: (value) => {
      if (!otpStep) return '';
      if (!/^\d{6}$/.test(String(value || ''))) return 'رمز التحقق يجب أن يكون 6 أرقام';
      return '';
    },
  };

  const validateField = (name, value) => validators[name]?.(value) || '';

  const validateAll = () => {
    const next = {
      fullName: validateField('fullName', fullName),
      phone: validateField('phone', phone),
      email: validateField('email', email),
      city: validateField('city', city),
      password: validateField('password', password),
      passwordConfirm: validateField('passwordConfirm', passwordConfirm),
      otpCode: validateField('otpCode', otpCode),
    };
    setErrors(next);
    return !Object.values(next).some(Boolean);
  };

  const disabled = useMemo(() => {
    const baseValid = !validateField('fullName', fullName) &&
      !validateField('phone', phone) &&
      !validateField('email', email) &&
      !validateField('city', city) &&
      !validateField('password', password) &&
      !validateField('passwordConfirm', passwordConfirm);
    if (!baseValid) return true;
    if (otpStep && !!validateField('otpCode', otpCode)) return true;
    return loading;
  }, [city, email, fullName, loading, otpCode, otpStep, password, passwordConfirm, phone]);

  const onSubmit = async () => {
    if (!validateAll()) return;
    setLoading(true);
    try {
      await ensureFirebasePhoneAuthReady();
      const normalizedPhone = normalizeIraqiPhone(phone);
      const e164 = `+964${String(normalizedPhone || '').replace(/^0/, '')}`;
      if (!otpStep) {
        const confirmation = await signInWithPhoneNumber(firebaseAuth(), e164, recaptchaVerifier.current);
        setConfirmationResult(confirmation);
        setOtpStep(true);
        setErrors((prev) => ({ ...prev, form: 'تم إرسال رمز التحقق من Firebase إلى رقم الهاتف' }));
      } else {
        if (!confirmationResult) {
          throw new Error('OTP_SESSION_MISSING');
        }
        const cred = await confirmationResult.confirm(otpCode.trim());
        const idToken = await cred.user.getIdToken(true);
        await registerUser({
          id_token: idToken,
          phone: normalizedPhone,
          email: email.trim().toLowerCase(),
          city,
          full_name: fullName.trim(),
          password,
          password_confirm: passwordConfirm,
        });
        navigation.reset({
          index: 0,
          routes: [{ name: 'Root' }],
        });
      }
    } catch (e) {
      const code = String(e?.code || e?.payload?.code || e?.response?.data?.code || '');
      const rawError = e?.payload?.message || e?.payload?.error || e?.response?.data?.error || e?.response?.data?.detail || e?.message || 'فشل التحقق عبر Firebase';
      const normalizedRawError = String(rawError || '');
      const msg = code === 'PHONE_ALREADY_HAS_ACCOUNT'
        ? 'رقم الهاتف مرتبط بحساب عميل بالفعل، استخدم تسجيل الدخول'
        : code === 'auth/invalid-app-credential'
          ? 'فشل تهيئة Firebase Phone Auth. تأكد من إضافة SHA-1 وSHA-256 لتطبيق Android في Firebase.'
          : code === 'auth/captcha-check-failed'
            ? 'فشل تحقق reCAPTCHA. أعد المحاولة وتأكد من اتصال الإنترنت.'
            : code === 'auth/web-storage-unsupported'
              ? 'بيئة التطبيق لا تدعم متطلبات Firebase web storage. استخدم نسخة Dev Client محدثة.'
        : normalizedRawError === 'FIREBASE_CONFIG_INVALID'
          ? 'إعدادات Firebase غير مكتملة على التطبيق'
          : normalizedRawError === 'FIREBASE_WEB_APP_ID_MISSING'
            ? 'Firebase Web App ID مفقود. أضف EXPO_PUBLIC_FIREBASE_WEB_APP_ID من إعدادات Web App في Firebase.'
            : normalizedRawError === 'FIREBASE_WEB_APP_NOT_CONFIGURED'
              ? 'مشروع Firebase لا يحتوي Web App فعّال على authDomain الحالي. أنشئ Web App واستخدم إعداداته.'
              : normalizedRawError === 'FIREBASE_AUTH_DOMAIN_UNREACHABLE'
                ? 'تعذر الوصول إلى Firebase authDomain. تحقق من الإنترنت وقيمة authDomain.'
                : normalizedRawError;
      setErrors((prev) => ({ ...prev, form: msg }));
    } finally {
      setLoading(false);
    }
  };
  return (
    <LinearGradient colors={['#0c1b33', '#081226']} style={styles.gradient}>
      <SafeAreaView style={styles.safe}>
        <FirebaseRecaptchaVerifierModal ref={recaptchaVerifier} firebaseConfig={firebaseConfig} attemptInvisibleVerification={Platform.OS !== 'ios'} />
        <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : 'height'} keyboardVerticalOffset={Platform.OS === 'ios' ? 0 : 24} style={styles.safe}>
          <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled" keyboardDismissMode="on-drag">
            <TouchableOpacity
              onPress={() => {
                if (navigation.canGoBack()) navigation.goBack();
                else navigation.navigate('Root');
              }}
              style={styles.backButton}
            >
              <MaterialCommunityIcons name="arrow-right" size={20} color="#fff" />
              <Text style={styles.backButtonText}>رجوع</Text>
            </TouchableOpacity>
            <Text style={styles.title}>إنشاء حساب جديد</Text>
            <Text style={styles.subtitle}>سجل الآن باستخدام رقم الهاتف</Text>

            {errors.form ? <Text style={styles.errorText}>{errors.form}</Text> : null}

            <View style={styles.fieldWrap}>
              <Text style={styles.label}>الاسم الكامل</Text>
              <TextInput
                placeholder="الاسم الكامل"
                placeholderTextColor="rgba(255,255,255,0.6)"
                value={fullName}
                onChangeText={(value) => {
                  setFullName(value);
                  if (errors.fullName) setErrors((prev) => ({ ...prev, fullName: validateField('fullName', value) }));
                }}
                onBlur={() => setErrors((prev) => ({ ...prev, fullName: validateField('fullName', fullName) }))}
                style={styles.input}
              />
              {errors.fullName ? <Text style={styles.errorText}>{errors.fullName}</Text> : null}
            </View>

            <View style={styles.fieldWrap}>
              <Text style={styles.label}>رقم الهاتف</Text>
              <TextInput
                placeholder="07xxxxxxxxx"
                placeholderTextColor="rgba(255,255,255,0.6)"
                value={phone}
                onChangeText={(value) => {
                  const normalized = normalizeIraqiPhone(value);
                  setPhone(normalized);
                  if (errors.phone) setErrors((prev) => ({ ...prev, phone: validateField('phone', normalized) }));
                }}
                keyboardType="number-pad"
                maxLength={11}
                style={styles.input}
                onBlur={() => setErrors((prev) => ({ ...prev, phone: validateField('phone', phone) }))}
              />
              {errors.phone ? <Text style={styles.errorText}>{errors.phone}</Text> : null}
            </View>

            <View style={styles.fieldWrap}>
              <Text style={styles.label}>البريد الإلكتروني</Text>
              <TextInput
                placeholder="name@example.com"
                placeholderTextColor="rgba(255,255,255,0.6)"
                value={email}
                onChangeText={(value) => {
                  setEmail(value);
                  if (errors.email) setErrors((prev) => ({ ...prev, email: validateField('email', value) }));
                }}
                keyboardType="email-address"
                autoCapitalize="none"
                style={styles.input}
                onBlur={() => setErrors((prev) => ({ ...prev, email: validateField('email', email) }))}
              />
              {errors.email ? <Text style={styles.errorText}>{errors.email}</Text> : null}
            </View>

            <View style={styles.fieldWrap}>
              <Text style={styles.label}>المدينة</Text>
              <TouchableOpacity onPress={() => setCityModalOpen(true)} style={styles.selectInput}>
                <Text style={styles.selectText}>{city || 'اختر المدينة'}</Text>
                <MaterialCommunityIcons name="chevron-down" size={20} color={theme.colors.textSecondary} />
              </TouchableOpacity>
              {errors.city ? <Text style={styles.errorText}>{errors.city}</Text> : null}
            </View>

            <View style={styles.fieldWrap}>
              <Text style={styles.label}>كلمة المرور</Text>
              <View style={styles.passwordRow}>
                <TextInput
                  placeholder="••••••"
                  placeholderTextColor="rgba(255,255,255,0.6)"
                  value={password}
                  onChangeText={(value) => {
                    setPassword(value);
                    if (errors.password) setErrors((prev) => ({ ...prev, password: validateField('password', value) }));
                    if (errors.passwordConfirm) setErrors((prev) => ({ ...prev, passwordConfirm: validateField('passwordConfirm', passwordConfirm) }));
                  }}
                  secureTextEntry={!showPassword}
                  style={styles.passwordInput}
                  onBlur={() => setErrors((prev) => ({ ...prev, password: validateField('password', password) }))}
                />
                <TouchableOpacity onPress={() => setShowPassword((v) => !v)} style={styles.eyeBtn}>
                  <MaterialCommunityIcons name={showPassword ? 'eye-off-outline' : 'eye-outline'} size={20} color="rgba(255,255,255,0.85)" />
                </TouchableOpacity>
              </View>
              {errors.password ? <Text style={styles.errorText}>{errors.password}</Text> : null}
            </View>

            <View style={styles.fieldWrap}>
              <Text style={styles.label}>تأكيد كلمة المرور</Text>
              <View style={styles.passwordRow}>
                <TextInput
                  placeholder="••••••"
                  placeholderTextColor="rgba(255,255,255,0.6)"
                  value={passwordConfirm}
                  onChangeText={(value) => {
                    setPasswordConfirm(value);
                    if (errors.passwordConfirm) setErrors((prev) => ({ ...prev, passwordConfirm: validateField('passwordConfirm', value) }));
                  }}
                  secureTextEntry={!showPasswordConfirm}
                  style={styles.passwordInput}
                  onBlur={() => setErrors((prev) => ({ ...prev, passwordConfirm: validateField('passwordConfirm', passwordConfirm) }))}
                />
                <TouchableOpacity onPress={() => setShowPasswordConfirm((v) => !v)} style={styles.eyeBtn}>
                  <MaterialCommunityIcons name={showPasswordConfirm ? 'eye-off-outline' : 'eye-outline'} size={20} color="rgba(255,255,255,0.85)" />
                </TouchableOpacity>
              </View>
              {errors.passwordConfirm ? <Text style={styles.errorText}>{errors.passwordConfirm}</Text> : null}
            </View>

            {otpStep ? (
              <View style={styles.fieldWrap}>
                <Text style={styles.label}>رمز التحقق (OTP)</Text>
                <TextInput
                  placeholder="ادخل 6 أرقام"
                  placeholderTextColor="rgba(255,255,255,0.6)"
                  value={otpCode}
                  onChangeText={(value) => {
                    const digits = String(value || '').replace(/\D/g, '').slice(0, 6);
                    setOtpCode(digits);
                    if (errors.otpCode) setErrors((prev) => ({ ...prev, otpCode: validateField('otpCode', digits) }));
                  }}
                  keyboardType="number-pad"
                  maxLength={6}
                  style={styles.input}
                  onBlur={() => setErrors((prev) => ({ ...prev, otpCode: validateField('otpCode', otpCode) }))}
                />
                {errors.otpCode ? <Text style={styles.errorText}>{errors.otpCode}</Text> : null}
              </View>
            ) : null}

            <TouchableOpacity disabled={disabled} onPress={onSubmit} style={[styles.registerBtn, disabled && styles.registerBtnDisabled]}>
              {loading ? <ActivityIndicator color="#000" /> : <Text style={styles.registerBtnText}>{otpStep ? 'تأكيد Firebase وإكمال التسجيل' : 'إرسال رمز Firebase'}</Text>}
            </TouchableOpacity>

            <TouchableOpacity onPress={() => navigation.navigate('Login')} style={styles.loginLinkWrap}>
              <Text style={styles.loginLink}>لديك حساب بالفعل؟ تسجيل الدخول</Text>
            </TouchableOpacity>
          </ScrollView>
        </KeyboardAvoidingView>
      </SafeAreaView>

      <Modal visible={cityModalOpen} transparent animationType="fade" onRequestClose={() => setCityModalOpen(false)}>
        <View style={styles.modalBackdrop}>
          <View style={styles.modalCard}>
            <Text style={styles.modalTitle}>اختر المدينة</Text>
            <ScrollView style={{ maxHeight: 280 }}>
              {IRAQI_CITIES.map((item) => (
                <TouchableOpacity
                  key={item}
                  onPress={() => {
                    setCity(item);
                    setCityModalOpen(false);
                    setErrors((prev) => ({ ...prev, city: '' }));
                  }}
                  style={styles.cityOption}
                >
                  <Text style={styles.cityOptionText}>{item}</Text>
                </TouchableOpacity>
              ))}
            </ScrollView>
            <TouchableOpacity onPress={() => setCityModalOpen(false)} style={styles.closeModalBtn}>
              <Text style={styles.closeModalText}>إغلاق</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  gradient: {
    flex: 1,
  },
  safe: {
    flex: 1,
  },
  content: {
    padding: theme.spacing.lg,
    paddingBottom: theme.spacing.xl * 4,
  },
  title: {
    color: theme.colors.textPrimary,
    fontFamily: theme.typography.fontBold,
    fontSize: theme.typography.sizes.h2,
    marginBottom: theme.spacing.xs,
    textAlign: I18nManager.isRTL ? 'right' : 'left',
  },
  backButton: {
    alignSelf: 'flex-start',
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingVertical: 8,
    paddingHorizontal: 10,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.22)',
    backgroundColor: 'rgba(255,255,255,0.08)',
    marginBottom: theme.spacing.md,
  },
  backButtonText: {
    color: '#fff',
    fontFamily: theme.typography.fontBold,
    fontSize: theme.typography.sizes.sm,
  },
  subtitle: {
    color: theme.colors.textSecondary,
    fontFamily: theme.typography.fontRegular,
    marginBottom: theme.spacing.lg,
    textAlign: I18nManager.isRTL ? 'right' : 'left',
  },
  fieldWrap: {
    marginBottom: theme.spacing.md,
  },
  label: {
    color: theme.colors.textPrimary,
    marginBottom: theme.spacing.xs,
    fontFamily: theme.typography.fontRegular,
    textAlign: I18nManager.isRTL ? 'right' : 'left',
  },
  input: {
    borderWidth: 1,
    borderColor: theme.colors.cardBorder,
    backgroundColor: 'rgba(255,255,255,0.06)',
    paddingHorizontal: theme.spacing.md,
    paddingVertical: 14,
    borderRadius: theme.radius.md,
    color: theme.colors.textPrimary,
    fontFamily: theme.typography.fontRegular,
    textAlign: I18nManager.isRTL ? 'right' : 'left',
  },
  passwordRow: {
    borderWidth: 1,
    borderColor: theme.colors.cardBorder,
    backgroundColor: 'rgba(255,255,255,0.06)',
    borderRadius: theme.radius.md,
    flexDirection: 'row',
    alignItems: 'center',
    paddingStart: theme.spacing.md,
  },
  passwordInput: {
    flex: 1,
    color: theme.colors.textPrimary,
    paddingVertical: 14,
    textAlign: I18nManager.isRTL ? 'right' : 'left',
    fontFamily: theme.typography.fontRegular,
  },
  eyeBtn: {
    paddingHorizontal: theme.spacing.md,
    paddingVertical: theme.spacing.sm,
  },
  selectInput: {
    borderWidth: 1,
    borderColor: theme.colors.cardBorder,
    backgroundColor: 'rgba(255,255,255,0.06)',
    paddingHorizontal: theme.spacing.md,
    paddingVertical: 14,
    borderRadius: theme.radius.md,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  selectText: {
    color: theme.colors.textPrimary,
    fontFamily: theme.typography.fontRegular,
  },
  errorText: {
    marginTop: theme.spacing.xs,
    color: theme.colors.danger,
    fontFamily: theme.typography.fontRegular,
    textAlign: I18nManager.isRTL ? 'right' : 'left',
  },
  registerBtn: {
    marginTop: theme.spacing.md,
    minHeight: 52,
    borderRadius: 12,
    backgroundColor: theme.colors.accent,
    width: '100%',
    alignItems: 'center',
    justifyContent: 'center',
    ...theme.shadows.appBar,
  },
  registerBtnDisabled: {
    backgroundColor: 'rgba(255,255,255,0.25)',
  },
  registerBtnText: {
    color: '#000',
    fontFamily: theme.typography.fontBold,
    fontSize: theme.typography.sizes.md,
  },
  loginLinkWrap: {
    marginTop: theme.spacing.md,
    alignItems: 'center',
  },
  loginLink: {
    color: theme.colors.accent,
    fontFamily: theme.typography.fontBold,
  },
  modalBackdrop: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.55)',
    justifyContent: 'center',
    padding: theme.spacing.lg,
  },
  modalCard: {
    borderRadius: theme.radius.lg,
    backgroundColor: theme.colors.surface,
    borderWidth: 1,
    borderColor: theme.colors.cardBorder,
    padding: theme.spacing.lg,
  },
  modalTitle: {
    color: theme.colors.textPrimary,
    fontFamily: theme.typography.fontBold,
    fontSize: theme.typography.sizes.md,
    marginBottom: theme.spacing.md,
    textAlign: I18nManager.isRTL ? 'right' : 'left',
  },
  cityOption: {
    paddingVertical: theme.spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: theme.colors.border,
  },
  cityOptionText: {
    color: theme.colors.textPrimary,
    fontFamily: theme.typography.fontRegular,
    textAlign: I18nManager.isRTL ? 'right' : 'left',
  },
  closeModalBtn: {
    marginTop: theme.spacing.md,
    alignSelf: 'center',
    paddingHorizontal: theme.spacing.lg,
    paddingVertical: theme.spacing.sm,
    borderRadius: theme.radius.md,
    backgroundColor: theme.colors.surfaceAlt,
  },
  closeModalText: {
    color: theme.colors.textPrimary,
    fontFamily: theme.typography.fontBold,
  },
});
