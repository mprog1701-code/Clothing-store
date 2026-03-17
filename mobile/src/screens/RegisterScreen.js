import React, { useMemo, useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, ActivityIndicator, I18nManager, StyleSheet, KeyboardAvoidingView, Platform, ScrollView, Modal } from 'react-native';
import theme from '../theme';
import { useAuth } from '../auth/AuthContext';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { normalizeIraqiPhone, isValidIraqiPhone } from '../utils/phone';

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
  const [city, setCity] = useState(IRAQI_CITIES[0]);
  const [password, setPassword] = useState('');
  const [passwordConfirm, setPasswordConfirm] = useState('');
  const [loading, setLoading] = useState(false);
  const [cityModalOpen, setCityModalOpen] = useState(false);
  const [errors, setErrors] = useState({});

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
  };

  const validateField = (name, value) => validators[name]?.(value) || '';

  const validateAll = () => {
    const next = {
      fullName: validateField('fullName', fullName),
      phone: validateField('phone', phone),
      city: validateField('city', city),
      password: validateField('password', password),
      passwordConfirm: validateField('passwordConfirm', passwordConfirm),
    };
    setErrors(next);
    return !Object.values(next).some(Boolean);
  };

  const disabled = useMemo(() => {
    return loading || !fullName || !phone || !city || !password || !passwordConfirm;
  }, [city, fullName, loading, password, passwordConfirm, phone]);

  const onSubmit = async () => {
    if (!validateAll()) return;
    setLoading(true);
    try {
      const payload = {
        phone: normalizeIraqiPhone(phone),
        city,
        full_name: fullName.trim(),
        password,
        password_confirm: passwordConfirm,
      };
      await registerUser(payload);
      navigation.reset({
        index: 0,
        routes: [{ name: 'Root' }],
      });
    } catch (e) {
      const msg = String(e?.message || 'فشل التسجيل');
      setErrors((prev) => ({ ...prev, form: msg }));
    } finally {
      setLoading(false);
    }
  };
  return (
    <LinearGradient colors={['#0c1b33', '#081226']} style={styles.gradient}>
      <SafeAreaView style={styles.safe}>
        <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : undefined} style={styles.safe}>
          <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
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
              <Text style={styles.label}>المدينة</Text>
              <TouchableOpacity onPress={() => setCityModalOpen(true)} style={styles.selectInput}>
                <Text style={styles.selectText}>{city || 'اختر المدينة'}</Text>
                <MaterialCommunityIcons name="chevron-down" size={20} color={theme.colors.textSecondary} />
              </TouchableOpacity>
              {errors.city ? <Text style={styles.errorText}>{errors.city}</Text> : null}
            </View>

            <View style={styles.fieldWrap}>
              <Text style={styles.label}>كلمة المرور</Text>
              <TextInput
                placeholder="••••••"
                placeholderTextColor="rgba(255,255,255,0.6)"
                value={password}
                onChangeText={(value) => {
                  setPassword(value);
                  if (errors.password) setErrors((prev) => ({ ...prev, password: validateField('password', value) }));
                  if (errors.passwordConfirm) setErrors((prev) => ({ ...prev, passwordConfirm: validateField('passwordConfirm', passwordConfirm) }));
                }}
                secureTextEntry
                style={styles.input}
                onBlur={() => setErrors((prev) => ({ ...prev, password: validateField('password', password) }))}
              />
              {errors.password ? <Text style={styles.errorText}>{errors.password}</Text> : null}
            </View>

            <View style={styles.fieldWrap}>
              <Text style={styles.label}>تأكيد كلمة المرور</Text>
              <TextInput
                placeholder="••••••"
                placeholderTextColor="rgba(255,255,255,0.6)"
                value={passwordConfirm}
                onChangeText={(value) => {
                  setPasswordConfirm(value);
                  if (errors.passwordConfirm) setErrors((prev) => ({ ...prev, passwordConfirm: validateField('passwordConfirm', value) }));
                }}
                secureTextEntry
                style={styles.input}
                onBlur={() => setErrors((prev) => ({ ...prev, passwordConfirm: validateField('passwordConfirm', passwordConfirm) }))}
              />
              {errors.passwordConfirm ? <Text style={styles.errorText}>{errors.passwordConfirm}</Text> : null}
            </View>

            <TouchableOpacity disabled={disabled} onPress={onSubmit} style={[styles.registerBtn, disabled && styles.registerBtnDisabled]}>
              {loading ? <ActivityIndicator color="#000" /> : <Text style={styles.registerBtnText}>تسجيل</Text>}
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
    paddingBottom: theme.spacing.xl * 2,
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
