import React, { useEffect, useState } from 'react';
import { View, Text, I18nManager, TextInput, TouchableOpacity, ActivityIndicator, Alert, ScrollView } from 'react-native';
import theme from '../theme';
import { me, updateMe } from '../api';

export default function EditProfileScreen({ navigation }) {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [initial, setInitial] = useState({ username: '', firstName: '', lastName: '', email: '', city: '' });
  const [username, setUsername] = useState('');
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [email, setEmail] = useState('');
  const [city, setCity] = useState('');
  const [phone, setPhone] = useState('');

  const load = async () => {
    setLoading(true);
    try {
      const u = await me();
      setUsername(String(u?.username || ''));
      setFirstName(String(u?.first_name || ''));
      setLastName(String(u?.last_name || ''));
      setEmail(String(u?.email || ''));
      setCity(String(u?.city || ''));
      setPhone(String(u?.phone || ''));
      setInitial({
        username: String(u?.username || ''),
        firstName: String(u?.first_name || ''),
        lastName: String(u?.last_name || ''),
        email: String(u?.email || ''),
        city: String(u?.city || ''),
      });
    } catch {
      Alert.alert('خطأ', 'تعذر تحميل بيانات الملف');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const normalized = {
    username: username.trim(),
    firstName: firstName.trim(),
    lastName: lastName.trim(),
    email: email.trim(),
    city: city.trim(),
  };
  const hasChanges =
    normalized.username !== initial.username ||
    normalized.firstName !== initial.firstName ||
    normalized.lastName !== initial.lastName ||
    normalized.email !== initial.email ||
    normalized.city !== initial.city;

  const onSave = async () => {
    if (saving) return;
    if (!normalized.username) {
      Alert.alert('تنبيه', 'اسم المستخدم مطلوب');
      return;
    }
    if (normalized.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(normalized.email)) {
      Alert.alert('تنبيه', 'صيغة البريد الإلكتروني غير صحيحة');
      return;
    }
    if (!hasChanges) {
      Alert.alert('معلومة', 'لا توجد تغييرات للحفظ');
      return;
    }
    setSaving(true);
    try {
      await updateMe({
        username: normalized.username,
        first_name: normalized.firstName,
        last_name: normalized.lastName,
        email: normalized.email,
        city: normalized.city,
      });
      Alert.alert('تم', 'تم تحديث الملف الشخصي بنجاح');
      navigation.goBack();
    } catch (e) {
      const data = e?.response?.data || {};
      const firstError = Object.values(data)?.[0];
      const msg = Array.isArray(firstError) ? firstError[0] : (typeof firstError === 'string' ? firstError : 'تعذر حفظ البيانات');
      Alert.alert('خطأ', String(msg));
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <View style={{ flex: 1, backgroundColor: theme.colors.background, alignItems: 'center', justifyContent: 'center' }}>
        <ActivityIndicator />
      </View>
    );
  }

  const inputStyle = {
    marginTop: theme.spacing.sm,
    borderRadius: theme.radius.md,
    borderWidth: 1,
    borderColor: theme.colors.cardBorder,
    backgroundColor: theme.colors.surface,
    color: theme.colors.textPrimary,
    paddingHorizontal: theme.spacing.md,
    paddingVertical: 10,
    textAlign: I18nManager.isRTL ? 'right' : 'left',
    fontFamily: theme.typography.fontRegular,
  };

  return (
    <ScrollView style={{ flex: 1, backgroundColor: theme.colors.background }} contentContainerStyle={{ padding: theme.spacing.lg, paddingBottom: theme.spacing.xl }}>
      <Text style={{ color: theme.colors.textPrimary, fontFamily: theme.typography.fontBold, fontSize: theme.typography.sizes.lg, textAlign: I18nManager.isRTL ? 'right' : 'left' }}>تعديل الملف</Text>
      <Text style={{ marginTop: 6, color: theme.colors.textSecondary, fontFamily: theme.typography.fontRegular, textAlign: I18nManager.isRTL ? 'right' : 'left' }}>عدّل بيانات حسابك ثم اضغط حفظ</Text>

      <TextInput value={firstName} onChangeText={setFirstName} placeholder="الاسم الأول" placeholderTextColor={theme.colors.textSecondary} style={inputStyle} />
      <TextInput value={lastName} onChangeText={setLastName} placeholder="الاسم الأخير" placeholderTextColor={theme.colors.textSecondary} style={inputStyle} />
      <TextInput value={username} onChangeText={setUsername} placeholder="اسم المستخدم" placeholderTextColor={theme.colors.textSecondary} autoCapitalize="none" style={inputStyle} />
      <TextInput value={email} onChangeText={setEmail} placeholder="البريد الإلكتروني" placeholderTextColor={theme.colors.textSecondary} keyboardType="email-address" autoCapitalize="none" style={inputStyle} />
      <TextInput value={city} onChangeText={setCity} placeholder="المدينة" placeholderTextColor={theme.colors.textSecondary} style={inputStyle} />
      <TextInput value={phone} editable={false} selectTextOnFocus={false} placeholder="رقم الهاتف" placeholderTextColor={theme.colors.textSecondary} style={{ ...inputStyle, opacity: 0.7 }} />

      <TouchableOpacity
        onPress={onSave}
        disabled={saving || !hasChanges}
        style={{ marginTop: theme.spacing.lg, borderRadius: theme.radius.lg, backgroundColor: saving || !hasChanges ? theme.colors.surfaceAlt : theme.colors.accent, paddingVertical: theme.spacing.md, alignItems: 'center' }}
      >
        {saving ? <ActivityIndicator color="#000" /> : <Text style={{ color: '#000', fontFamily: theme.typography.fontBold }}>حفظ التعديلات</Text>}
      </TouchableOpacity>
    </ScrollView>
  );
}
