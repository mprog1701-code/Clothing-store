import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, ActivityIndicator, Alert, I18nManager, StyleSheet } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import { verifyRegistration, resendVerification } from '../api';
import theme from '../theme';

export default function VerifyAccountScreen({ navigation, route }) {
  const phone = String(route?.params?.phone || '');
  const email = String(route?.params?.email || '');
  const debugCode = route?.params?.debugCode ? String(route.params.debugCode) : '';
  const [code, setCode] = useState(debugCode);
  const [loading, setLoading] = useState(false);

  const onVerify = async () => {
    if (!phone || !code.trim()) {
      Alert.alert('تنبيه', 'يرجى إدخال رمز التفعيل');
      return;
    }
    setLoading(true);
    try {
      await verifyRegistration({ phone, code: code.trim() });
      Alert.alert('تم', 'تم تفعيل الحساب بنجاح');
      navigation.reset({ index: 0, routes: [{ name: 'Root' }] });
    } catch (e) {
      Alert.alert('خطأ', String(e?.response?.data?.error || 'تعذر تفعيل الحساب'));
    } finally {
      setLoading(false);
    }
  };

  const onResend = async () => {
    if (!phone) return;
    setLoading(true);
    try {
      const res = await resendVerification({ phone });
      if (res?.debug_code) {
        setCode(String(res.debug_code));
      }
      Alert.alert('تم', 'تم إرسال رمز جديد إلى البريد الإلكتروني');
    } catch (e) {
      Alert.alert('خطأ', String(e?.response?.data?.error || 'تعذر إعادة إرسال الرمز'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <LinearGradient colors={['#0c1b33', '#081226']} style={{ flex: 1 }}>
      <SafeAreaView style={{ flex: 1, padding: theme.spacing.lg }}>
        <Text style={styles.title}>تفعيل الحساب</Text>
        <Text style={styles.subtitle}>أدخل رمز التفعيل المرسل إلى {email || 'بريدك الإلكتروني'}</Text>
        <TextInput
          value={phone}
          editable={false}
          style={[styles.input, { opacity: 0.7 }]}
        />
        <TextInput
          value={code}
          onChangeText={setCode}
          placeholder="رمز التفعيل"
          placeholderTextColor="rgba(255,255,255,0.6)"
          style={styles.input}
          keyboardType="number-pad"
          maxLength={6}
        />
        <TouchableOpacity onPress={onVerify} disabled={loading} style={styles.button}>
          {loading ? <ActivityIndicator color="#000" /> : <Text style={styles.buttonText}>تفعيل الحساب</Text>}
        </TouchableOpacity>
        <TouchableOpacity onPress={onResend} disabled={loading} style={styles.secondaryButton}>
          <Text style={styles.secondaryText}>إعادة إرسال الرمز</Text>
        </TouchableOpacity>
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
  secondaryButton: {
    marginTop: theme.spacing.md,
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: theme.spacing.sm,
  },
  secondaryText: {
    color: theme.colors.accent,
    fontFamily: theme.typography.fontBold,
  },
});
