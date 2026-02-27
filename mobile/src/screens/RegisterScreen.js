import React, { useState } from 'react';
import { View, Text, TextInput, Button, Alert } from 'react-native';
import { register } from '../api';
import theme from '../theme';

export default function RegisterScreen({ navigation }) {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [city, setCity] = useState('');
  const [fullName, setFullName] = useState('');
  const [password, setPassword] = useState('');
  const [passwordConfirm, setPasswordConfirm] = useState('');
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const onSubmit = async () => {
    setLoading(true);
    setErrorMsg('');
    const u = (username || '').trim();
    const em = (email || '').trim();
    const pw = (password || '').trim();
    const pc = (passwordConfirm || '').trim();
    if (!u || !em || !pw || !pc) {
      setLoading(false);
      setErrorMsg('يرجى ملء جميع الحقول المطلوبة');
      return;
    }
    if (pw.length < 6) {
      setLoading(false);
      setErrorMsg('كلمة المرور يجب أن تكون 6 أحرف على الأقل');
      return;
    }
    if (pw !== pc) {
      setLoading(false);
      setErrorMsg('كلمتا المرور غير متطابقتين');
      return;
    }
    try {
      const payload = {
        username: u,
        email: em,
        phone,
        city,
        full_name: fullName,
        password: pw,
        password_confirm: pc,
      };
      await register(payload);
      Alert.alert('تم', 'تم تسجيل الحساب بنجاح');
      navigation.replace('Login');
    } catch (e) {
      const msg = String(e?.message || 'فشل التسجيل');
      setErrorMsg(msg);
    } finally {
      setLoading(false);
    }
  };
  return (
    <View style={{ flex: 1, padding: theme.spacing.lg, backgroundColor: theme.colors.background }}>
      <Text style={{ fontSize: theme.typography.sizes.md, fontFamily: theme.typography.fontBold, color: theme.colors.textPrimary, marginBottom: theme.spacing.md }}>تسجيل</Text>
      <Text style={{ color: theme.colors.textSecondary, marginBottom: theme.spacing.sm }}>املأ الحقول التالية لإنشاء حساب</Text>
      {errorMsg ? <Text style={{ color: theme.colors.danger, marginBottom: theme.spacing.sm }}>{errorMsg}</Text> : null}
      <Text style={{ color: theme.colors.textPrimary, marginBottom: theme.spacing.xs }}>اسم المستخدم</Text>
      <TextInput placeholder="مثال: superowner" placeholderTextColor="rgba(255,255,255,0.6)" value={username} onChangeText={setUsername} style={{ borderWidth: 1, borderColor: theme.colors.cardBorder, padding: theme.spacing.md, borderRadius: theme.radius.md, marginBottom: theme.spacing.md, color: theme.colors.textPrimary }} />
      <Text style={{ color: theme.colors.textPrimary, marginBottom: theme.spacing.xs }}>البريد الإلكتروني</Text>
      <TextInput placeholder="superowner@example.com" placeholderTextColor="rgba(255,255,255,0.6)" value={email} onChangeText={setEmail} autoCapitalize="none" keyboardType="email-address" style={{ borderWidth: 1, borderColor: theme.colors.cardBorder, padding: theme.spacing.md, borderRadius: theme.radius.md, marginBottom: theme.spacing.md, color: theme.colors.textPrimary }} />
      <Text style={{ color: theme.colors.textPrimary, marginBottom: theme.spacing.xs }}>الاسم الكامل</Text>
      <TextInput placeholder="الاسم الكامل" placeholderTextColor="rgba(255,255,255,0.6)" value={fullName} onChangeText={setFullName} style={{ borderWidth: 1, borderColor: theme.colors.cardBorder, padding: theme.spacing.md, borderRadius: theme.radius.md, marginBottom: theme.spacing.md, color: theme.colors.textPrimary }} />
      <Text style={{ color: theme.colors.textPrimary, marginBottom: theme.spacing.xs }}>المدينة</Text>
      <TextInput placeholder="المدينة" placeholderTextColor="rgba(255,255,255,0.6)" value={city} onChangeText={setCity} style={{ borderWidth: 1, borderColor: theme.colors.cardBorder, padding: theme.spacing.md, borderRadius: theme.radius.md, marginBottom: theme.spacing.md, color: theme.colors.textPrimary }} />
      <Text style={{ color: theme.colors.textPrimary, marginBottom: theme.spacing.xs }}>رقم الهاتف</Text>
      <TextInput placeholder="05xxxxxxxx" placeholderTextColor="rgba(255,255,255,0.6)" value={phone} onChangeText={setPhone} keyboardType="phone-pad" style={{ borderWidth: 1, borderColor: theme.colors.cardBorder, padding: theme.spacing.md, borderRadius: theme.radius.md, marginBottom: theme.spacing.md, color: theme.colors.textPrimary }} />
      <Text style={{ color: theme.colors.textPrimary, marginBottom: theme.spacing.xs }}>كلمة المرور</Text>
      <TextInput placeholder="•••••••" placeholderTextColor="rgba(255,255,255,0.6)" value={password} onChangeText={setPassword} secureTextEntry style={{ borderWidth: 1, borderColor: theme.colors.cardBorder, padding: theme.spacing.md, borderRadius: theme.radius.md, marginBottom: theme.spacing.md, color: theme.colors.textPrimary }} />
      <Text style={{ color: theme.colors.textPrimary, marginBottom: theme.spacing.xs }}>تأكيد كلمة المرور</Text>
      <TextInput placeholder="أعد كتابة كلمة المرور" placeholderTextColor="rgba(255,255,255,0.6)" value={passwordConfirm} onChangeText={setPasswordConfirm} secureTextEntry style={{ borderWidth: 1, borderColor: theme.colors.cardBorder, padding: theme.spacing.md, borderRadius: theme.radius.md, marginBottom: theme.spacing.md, color: theme.colors.textPrimary }} />
      <Button title={loading ? 'جاري...' : 'تسجيل'} onPress={onSubmit} disabled={loading} />
    </View>
  );
}
