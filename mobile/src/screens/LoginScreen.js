import React, { useEffect, useMemo, useRef, useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, ActivityIndicator, I18nManager, Animated, StyleSheet, KeyboardAvoidingView, Platform, ScrollView, Alert, Linking } from 'react-native';
import { addToCart, addCartItemVariant } from '../api';
import theme from '../theme';
import { useAuth } from '../auth/AuthContext';
import { LinearGradient } from 'expo-linear-gradient';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { SafeAreaView } from 'react-native-safe-area-context';
import { normalizeIraqiPhone, isValidIraqiPhone } from '../utils/phone';
import { GOOGLE_OAUTH_START_URL, LOGIN_URL, GOOGLE_ANDROID_CLIENT_ID, GOOGLE_IOS_CLIENT_ID } from '../api/config';

export default function LoginScreen({ navigation, route }) {
  const [phone, setPhone] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [errorPhone, setErrorPhone] = useState('');
  const [errorPwd, setErrorPwd] = useState('');
  const [showPwd, setShowPwd] = useState(false);
  const [focusPhone, setFocusPhone] = useState(false);
  const [focusPwd, setFocusPwd] = useState(false);
  const fade = useRef(new Animated.Value(0)).current;
  const slide = useRef(new Animated.Value(20)).current;
  const { login: loginUser } = useAuth();

  useEffect(() => {
    Animated.parallel([
      Animated.timing(fade, { toValue: 1, duration: 300, useNativeDriver: true }),
      Animated.timing(slide, { toValue: 0, duration: 300, useNativeDriver: true }),
    ]).start();
  }, []);

  const validatePhone = (value) => {
    const normalized = normalizeIraqiPhone(value);
    if (!normalized) return 'يرجى إدخال رقم الهاتف';
    if (!isValidIraqiPhone(normalized)) return 'رقم الهاتف غير صحيح';
    return '';
  };

  const validatePassword = (value) => {
    if (!value) return 'يرجى إدخال كلمة المرور';
    if (value.length < 6) return 'كلمة المرور يجب أن تكون 6 أحرف على الأقل';
    return '';
  };

  const isDisabled = useMemo(() => loading || !phone || !password, [loading, phone, password]);

  const onSubmit = async () => {
    const normalizedPhone = normalizeIraqiPhone(phone);
    const phoneErr = validatePhone(normalizedPhone);
    const pwdErr = validatePassword(password);
    setErrorPhone(phoneErr);
    setErrorPwd(pwdErr);
    if (phoneErr || pwdErr) return;
    setLoading(true);
    try {
      await loginUser(normalizedPhone, password);
      const next = route?.params?.next;
      if (next?.action === 'add_to_cart') {
        try {
          if (next?.variant_id) {
            await addCartItemVariant({ product_id: next.product_id, variant_id: next.variant_id, quantity: next.quantity || 1, size: next.size });
          } else {
            await addToCart(next.product_id, next.variant_id, next.quantity || 1);
          }
          if (next?.returnTo?.name) {
            navigation.replace(next.returnTo.name, next.returnTo.params || {});
            return;
          }
          navigation.replace('Root');
          return;
        } catch (e) {
          if (__DEV__) {
            console.error('[Login] deferred add_to_cart failed', {
              message: e?.message,
              status: e?.response?.status,
              data: e?.response?.data,
              next,
            });
          }
        }
      } else if (next?.name) {
        navigation.replace(next.name, next.params || {});
        return;
      }
      navigation.replace('Root');
    } catch (e) {
      setErrorPwd('خطأ في رقم الهاتف أو كلمة المرور');
    } finally {
      setLoading(false);
    }
  };

  const onGoogleLogin = async () => {
    const oauthConfigured = !!(GOOGLE_ANDROID_CLIENT_ID || GOOGLE_IOS_CLIENT_ID);
    const target = GOOGLE_OAUTH_START_URL || LOGIN_URL;
    if (!oauthConfigured && !target) {
      Alert.alert('Google Login', 'Google OAuth غير مهيأ حالياً');
      return;
    }
    try {
      await Linking.openURL(target);
    } catch {
      Alert.alert('Google Login', 'تعذر فتح تسجيل الدخول بواسطة Google');
    }
  };

  return (
    <LinearGradient colors={['#0c1b33', '#081226']} style={styles.gradient}>
      <SafeAreaView style={styles.safe}>
        <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : undefined} style={styles.safe}>
          <ScrollView contentContainerStyle={styles.scrollContent} keyboardShouldPersistTaps="handled">
            <Animated.View style={[styles.container, { transform: [{ translateY: slide }], opacity: fade }]}>
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
              <View style={styles.brandWrap}>
                <View style={styles.logoCircle}>
                  <Text style={styles.logoText}>دار</Text>
                </View>
                <Text style={styles.welcome}>أهلاً بعودتك</Text>
                <Text style={styles.subtitle}>سجّل دخولك برقم الهاتف للمتابعة</Text>
              </View>

              <View style={styles.fieldBlock}>
                <View style={[styles.inputRow, focusPhone && styles.inputRowFocused]}>
                  <MaterialCommunityIcons name="phone-outline" size={20} color="rgba(255,255,255,0.85)" />
                  <TextInput
                    placeholder="07xxxxxxxxx"
                    placeholderTextColor="rgba(255,255,255,0.6)"
                    value={phone}
                    onChangeText={(value) => {
                      const normalized = normalizeIraqiPhone(value);
                      setPhone(normalized);
                      if (errorPhone) setErrorPhone(validatePhone(normalized));
                    }}
                    keyboardType="number-pad"
                    maxLength={11}
                    onFocus={() => setFocusPhone(true)}
                    onBlur={() => {
                      setFocusPhone(false);
                      setErrorPhone(validatePhone(phone));
                    }}
                    style={styles.input}
                  />
                </View>
                {errorPhone ? <Text style={styles.errorText}>{errorPhone}</Text> : null}
              </View>

              <View style={styles.fieldBlock}>
                <View style={[styles.inputRow, focusPwd && styles.inputRowFocused]}>
                  <MaterialCommunityIcons name="lock-outline" size={20} color="rgba(255,255,255,0.85)" />
                  <TextInput
                    placeholder="كلمة المرور"
                    placeholderTextColor="rgba(255,255,255,0.6)"
                    value={password}
                    onChangeText={(value) => {
                      setPassword(value);
                      if (errorPwd) setErrorPwd(validatePassword(value));
                    }}
                    secureTextEntry={!showPwd}
                    onFocus={() => setFocusPwd(true)}
                    onBlur={() => {
                      setFocusPwd(false);
                      setErrorPwd(validatePassword(password));
                    }}
                    style={styles.input}
                  />
                  <TouchableOpacity onPress={() => setShowPwd((v) => !v)} style={styles.eyeBtn}>
                    <MaterialCommunityIcons name={showPwd ? 'eye-off-outline' : 'eye-outline'} size={20} color="rgba(255,255,255,0.85)" />
                  </TouchableOpacity>
                </View>
                {errorPwd ? <Text style={styles.errorText}>{errorPwd}</Text> : null}
              </View>

              <TouchableOpacity disabled={isDisabled} onPress={onSubmit} style={[styles.actionButton, styles.loginButton, isDisabled && styles.loginButtonDisabled]}>
                {loading ? <ActivityIndicator color="#000" /> : <Text style={styles.loginButtonText}>تسجيل الدخول</Text>}
              </TouchableOpacity>

              <View style={styles.linksRow}>
                <TouchableOpacity onPress={() => navigation.navigate('Register')}>
                  <Text style={styles.linkPrimary}>إنشاء حساب جديد</Text>
                </TouchableOpacity>
                <TouchableOpacity onPress={() => {}}>
                  <Text style={styles.linkMuted}>نسيت كلمة المرور؟</Text>
                </TouchableOpacity>
              </View>

              <View style={styles.separatorRow}>
                <View style={styles.separatorLine} />
                <Text style={styles.separatorText}>أو</Text>
                <View style={styles.separatorLine} />
              </View>
              <TouchableOpacity onPress={onGoogleLogin} style={[styles.actionButton, styles.googleButton]}>
                <MaterialCommunityIcons name="google" size={20} color="#DB4437" />
                <Text style={styles.googleText}>تسجيل بواسطة Google</Text>
              </TouchableOpacity>
            </Animated.View>
          </ScrollView>
        </KeyboardAvoidingView>
      </SafeAreaView>
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
  scrollContent: {
    flexGrow: 1,
  },
  container: {
    flex: 1,
    padding: theme.spacing.lg,
  },
  brandWrap: {
    alignItems: 'center',
    marginTop: theme.spacing.xl,
    marginBottom: theme.spacing.xl,
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
  },
  backButtonText: {
    color: '#fff',
    fontFamily: theme.typography.fontBold,
    fontSize: theme.typography.sizes.sm,
  },
  logoCircle: {
    width: 72,
    height: 72,
    borderRadius: 36,
    backgroundColor: 'rgba(255,255,255,0.06)',
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.12)',
  },
  logoText: {
    color: '#fff',
    fontSize: theme.typography.sizes.xl,
    fontFamily: theme.typography.fontBold,
  },
  welcome: {
    marginTop: theme.spacing.md,
    color: '#fff',
    fontFamily: theme.typography.fontBold,
    fontSize: theme.typography.sizes.lg,
  },
  subtitle: {
    marginTop: theme.spacing.xs,
    color: 'rgba(255,255,255,0.72)',
    fontFamily: theme.typography.fontRegular,
    textAlign: 'center',
  },
  fieldBlock: {
    marginBottom: theme.spacing.md,
  },
  inputRow: {
    flexDirection: 'row',
    alignItems: 'center',
    borderRadius: 14,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.14)',
    backgroundColor: 'rgba(255,255,255,0.06)',
    paddingHorizontal: theme.spacing.lg,
    paddingVertical: 12,
    ...theme.shadows.card,
  },
  inputRowFocused: {
    borderColor: theme.colors.accent,
  },
  input: {
    flex: 1,
    marginStart: theme.spacing.md,
    color: '#fff',
    paddingVertical: 4,
    textAlign: I18nManager.isRTL ? 'right' : 'left',
    fontFamily: theme.typography.fontRegular,
  },
  eyeBtn: {
    paddingHorizontal: theme.spacing.sm,
    paddingVertical: theme.spacing.xs,
  },
  errorText: {
    color: theme.colors.danger,
    marginTop: theme.spacing.xs,
    fontFamily: theme.typography.fontRegular,
    textAlign: I18nManager.isRTL ? 'right' : 'left',
  },
  actionButton: {
    width: '100%',
    minHeight: 52,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  loginButton: {
    marginTop: theme.spacing.sm,
    backgroundColor: theme.colors.accent,
    ...theme.shadows.appBar,
  },
  loginButtonDisabled: {
    backgroundColor: 'rgba(255,255,255,0.25)',
  },
  loginButtonText: {
    color: '#000',
    fontFamily: theme.typography.fontBold,
    fontSize: theme.typography.sizes.md,
  },
  linksRow: {
    marginTop: theme.spacing.md,
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  linkPrimary: {
    color: theme.colors.accent,
    fontFamily: theme.typography.fontBold,
  },
  linkMuted: {
    color: 'rgba(255,255,255,0.72)',
    fontFamily: theme.typography.fontRegular,
  },
  separatorRow: {
    marginTop: theme.spacing.lg,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
  },
  separatorLine: {
    height: 1,
    flex: 1,
    backgroundColor: 'rgba(255,255,255,0.2)',
  },
  separatorText: {
    marginHorizontal: theme.spacing.sm,
    color: 'rgba(255,255,255,0.72)',
    fontFamily: theme.typography.fontRegular,
  },
  googleButton: {
    marginTop: theme.spacing.md,
    backgroundColor: '#ffffff',
    flexDirection: 'row',
    justifyContent: 'center',
  },
  googleText: {
    marginStart: theme.spacing.sm,
    color: '#000',
    fontFamily: theme.typography.fontBold,
  },
});
