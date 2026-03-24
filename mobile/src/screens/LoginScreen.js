import React, { useEffect, useMemo, useRef, useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, ActivityIndicator, I18nManager, Animated, StyleSheet, KeyboardAvoidingView, Platform, ScrollView, Alert } from 'react-native';
import { addToCart, addCartItemVariant } from '../api';
import theme from '../theme';
import { useAuth } from '../auth/AuthContext';
import { LinearGradient } from 'expo-linear-gradient';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Image as ExpoImage } from 'expo-image';
import { normalizeIraqiPhone, isValidIraqiPhone } from '../utils/phone';

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
      const code = String(e?.code || e?.payload?.error || '');
      if (code === 'ACCOUNT_NOT_VERIFIED') {
        const payload = e?.payload || {};
        navigation.navigate('VerifyAccount', {
          phone: payload?.phone || normalizedPhone,
          email: payload?.email || '',
          debugCode: payload?.debug_code || '',
        });
      } else {
        setErrorPwd('خطأ في رقم الهاتف أو كلمة المرور');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <LinearGradient colors={['#0c1b33', '#081226']} style={styles.gradient}>
      <SafeAreaView style={styles.safe}>
        <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : 'height'} keyboardVerticalOffset={Platform.OS === 'ios' ? 0 : 24} style={styles.safe}>
          <ScrollView contentContainerStyle={styles.scrollContent} keyboardShouldPersistTaps="handled" keyboardDismissMode="on-drag">
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
                <ExpoImage source={require('../../assets/daar-logo.png')} style={styles.logoImage} contentFit="contain" transition={0} />
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
                <TouchableOpacity onPress={() => navigation.navigate('ForgotPassword')}>
                  <Text style={styles.linkMuted}>نسيت كلمة المرور؟</Text>
                </TouchableOpacity>
              </View>
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
    paddingBottom: theme.spacing.xl * 3,
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
  logoImage: {
    width: 86,
    height: 86,
    borderRadius: 43,
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
});
