import React, { useEffect, useRef, useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, ActivityIndicator, I18nManager, Animated } from 'react-native';
import { login, addToCart, addCartItemVariant } from '../api';
import theme from '../theme';
import { useAuth } from '../auth/AuthContext';
import { LinearGradient } from 'expo-linear-gradient';
import { MaterialCommunityIcons } from '@expo/vector-icons';

export default function LoginScreen({ navigation, route }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [errorUser, setErrorUser] = useState('');
  const [errorPwd, setErrorPwd] = useState('');
  const [showPwd, setShowPwd] = useState(false);
  const [focusUser, setFocusUser] = useState(false);
  const [focusPwd, setFocusPwd] = useState(false);
  const fade = useRef(new Animated.Value(0)).current;
  const slide = useRef(new Animated.Value(20)).current;
  const { setUser } = useAuth();

  useEffect(() => {
    Animated.parallel([
      Animated.timing(fade, { toValue: 1, duration: 300, useNativeDriver: true }),
      Animated.timing(slide, { toValue: 0, duration: 300, useNativeDriver: true }),
    ]).start();
  }, []);

  const onSubmit = async () => {
    setLoading(true);
    setErrorUser('');
    setErrorPwd('');
    const u = (username || '').trim();
    const p = (password || '').trim();
    let invalid = false;
    if (!u) { setErrorUser('يرجى إدخال اسم المستخدم أو البريد'); invalid = true; }
    if (!p) { setErrorPwd('يرجى إدخال كلمة المرور'); invalid = true; }
    if (p && p.length < 6) { setErrorPwd('كلمة المرور يجب أن تكون 6 أحرف على الأقل'); invalid = true; }
    if (invalid) { setLoading(false); return; }
    try {
      const usr = await login(u, p);
      setUser(usr || null);
      const next = route?.params?.next;
      if (next?.action === 'add_to_cart') {
        try {
          if (next?.variant_id) {
            await addCartItemVariant({ variant_id: next.variant_id, qty: next.quantity || 1, size: next.size });
          } else {
            await addToCart(next.product_id, next.variant_id, next.quantity || 1);
          }
          navigation.goBack();
          navigation.navigate('Cart');
          return;
        } catch {}
      } else if (next?.name) {
        navigation.replace(next.name, next.params || {});
        return;
      }
      navigation.replace('Root');
    } catch (e) {
      const msg = String(e?.message || 'بيانات الدخول غير صحيحة أو تعذر الاتصال');
      setErrorPwd(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <LinearGradient colors={['#0c1b33', '#081226']} style={{ flex: 1 }}>
      <Animated.View style={{ flex: 1, padding: theme.spacing.lg, transform: [{ translateY: slide }], opacity: fade }}>
        <View style={{ alignItems: 'center', marginTop: theme.spacing.xl }}>
          <View style={{ width: 72, height: 72, borderRadius: 36, backgroundColor: 'rgba(255,255,255,0.06)', alignItems: 'center', justifyContent: 'center', borderWidth: 1, borderColor: 'rgba(255,255,255,0.12)' }}>
            <Text style={{ color: '#fff', fontSize: 22, fontFamily: theme.typography.fontBold }}>دار</Text>
          </View>
          <Text style={{ marginTop: theme.spacing.md, color: '#fff', fontFamily: theme.typography.fontBold, fontSize: theme.typography.sizes.lg }}>أهلاً بعودتك</Text>
          <Text style={{ marginTop: theme.spacing.xs, color: 'rgba(255,255,255,0.7)', fontFamily: theme.typography.fontRegular, textAlign: 'center' }}>سجل دخولك للمتابعة وإتمام طلباتك</Text>
        </View>
        <View style={{ marginTop: theme.spacing.xl }}>
          <View style={{ flexDirection: 'row', alignItems: 'center', borderRadius: 14, borderWidth: 1, borderColor: focusUser ? theme.colors.accent : 'rgba(255,255,255,0.14)', backgroundColor: 'rgba(255,255,255,0.06)', paddingHorizontal: theme.spacing.md, paddingVertical: theme.spacing.sm, ...theme.shadows.card }}>
            <MaterialCommunityIcons name="email-outline" size={20} color="rgba(255,255,255,0.8)" />
            <TextInput
              placeholder="اسم المستخدم أو البريد"
              placeholderTextColor="rgba(255,255,255,0.6)"
              value={username}
              onChangeText={setUsername}
              autoCapitalize="none"
              onFocus={() => setFocusUser(true)}
              onBlur={() => setFocusUser(false)}
              style={{ flex: 1, marginStart: theme.spacing.md, color: '#fff' }}
            />
          </View>
          {errorUser ? <Text style={{ color: theme.colors.danger, marginTop: theme.spacing.xs }}>{errorUser}</Text> : null}
        </View>
        <View style={{ marginTop: theme.spacing.md }}>
          <View style={{ flexDirection: 'row', alignItems: 'center', borderRadius: 14, borderWidth: 1, borderColor: focusPwd ? theme.colors.accent : 'rgba(255,255,255,0.14)', backgroundColor: 'rgba(255,255,255,0.06)', paddingHorizontal: theme.spacing.md, paddingVertical: theme.spacing.sm, ...theme.shadows.card }}>
            <MaterialCommunityIcons name="lock-outline" size={20} color="rgba(255,255,255,0.8)" />
            <TextInput
              placeholder="كلمة المرور"
              placeholderTextColor="rgba(255,255,255,0.6)"
              value={password}
              onChangeText={setPassword}
              secureTextEntry={!showPwd}
              onFocus={() => setFocusPwd(true)}
              onBlur={() => setFocusPwd(false)}
              style={{ flex: 1, marginStart: theme.spacing.md, color: '#fff' }}
            />
            <TouchableOpacity onPress={() => setShowPwd(v => !v)} style={{ paddingHorizontal: theme.spacing.sm, paddingVertical: theme.spacing.xs }}>
              <MaterialCommunityIcons name={showPwd ? 'eye-off-outline' : 'eye-outline'} size={20} color="rgba(255,255,255,0.8)" />
            </TouchableOpacity>
          </View>
          {errorPwd ? <Text style={{ color: theme.colors.danger, marginTop: theme.spacing.xs }}>{errorPwd}</Text> : null}
        </View>
        <TouchableOpacity disabled={loading} onPress={onSubmit} style={{ marginTop: theme.spacing.lg, paddingVertical: theme.spacing.md, borderRadius: 18, backgroundColor: loading ? 'rgba(255,255,255,0.2)' : theme.colors.accent, alignItems: 'center', ...theme.shadows.appBar }}>
          {loading ? <ActivityIndicator color="#000" /> : <Text style={{ color: '#000', fontFamily: theme.typography.fontBold }}>دخول</Text>}
        </TouchableOpacity>
        <View style={{ marginTop: theme.spacing.md, flexDirection: 'row', justifyContent: 'space-between' }}>
          <TouchableOpacity onPress={() => navigation.navigate('Register')}>
            <Text style={{ color: theme.colors.accent, fontFamily: theme.typography.fontBold }}>إنشاء حساب</Text>
          </TouchableOpacity>
          <TouchableOpacity onPress={() => {}}>
            <Text style={{ color: 'rgba(255,255,255,0.7)', fontFamily: theme.typography.fontRegular }}>نسيت كلمة المرور؟</Text>
          </TouchableOpacity>
        </View>
        <View style={{ marginTop: theme.spacing.lg, flexDirection: 'row', alignItems: 'center', justifyContent: 'center' }}>
          <View style={{ height: 1, flex: 1, backgroundColor: 'rgba(255,255,255,0.2)' }} />
          <Text style={{ marginHorizontal: theme.spacing.sm, color: 'rgba(255,255,255,0.7)' }}>أو</Text>
          <View style={{ height: 1, flex: 1, backgroundColor: 'rgba(255,255,255,0.2)' }} />
        </View>
        <TouchableOpacity onPress={() => {}} style={{ marginTop: theme.spacing.md, paddingVertical: theme.spacing.sm, borderRadius: 14, backgroundColor: '#ffffff', alignItems: 'center', flexDirection: 'row', justifyContent: 'center' }}>
          <MaterialCommunityIcons name="google" size={20} color="#DB4437" />
          <Text style={{ marginStart: theme.spacing.sm, color: '#000', fontFamily: theme.typography.fontBold }}>تسجيل بواسطة Google</Text>
        </TouchableOpacity>
      </Animated.View>
    </LinearGradient>
  );
}
