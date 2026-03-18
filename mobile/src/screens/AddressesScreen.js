import React, { useCallback, useMemo, useState } from 'react';
import { View, Text, I18nManager, TouchableOpacity, TextInput, ActivityIndicator, FlatList, Alert, Linking } from 'react-native';
import { useFocusEffect } from '@react-navigation/native';
import * as Location from 'expo-location';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import theme from '../theme';
import { createAddress, deleteAddress, listAddresses, reverseGeocodeAddress } from '../api';
import { useAuth } from '../auth/AuthContext';
import { useCheckout } from '../checkout/CheckoutContext';
import LoginRequiredSheet from '../components/LoginRequiredSheet';

let NativeMaps = null;
try {
  NativeMaps = require('react-native-maps');
} catch {}
const MapView = NativeMaps?.default || null;
const Marker = NativeMaps?.Marker || null;
const hasNativeMap = !!MapView && !!Marker;

export default function AddressesScreen({ navigation }) {
  const { accessToken } = useAuth();
  const { selectedAddressId, setSelectedAddress } = useCheckout();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [locating, setLocating] = useState(false);
  const [deletingId, setDeletingId] = useState(null);
  const [sheetVisible, setSheetVisible] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [permissionStatus, setPermissionStatus] = useState('');
  const [error, setError] = useState('');
  const [locationMeta, setLocationMeta] = useState({
    latitude: null,
    longitude: null,
    accuracy_m: null,
    formatted_address: '',
    provider: '',
    provider_place_id: '',
  });
  const [form, setForm] = useState({
    city: '',
    area: '',
    street: '',
    details: '',
  });
  const [mapRegion, setMapRegion] = useState({
    latitude: 33.3152,
    longitude: 44.3661,
    latitudeDelta: 0.01,
    longitudeDelta: 0.01,
  });

  const canSave = useMemo(() => {
    return !!form.city.trim() && !!form.area.trim() && !!form.street.trim() && !saving;
  }, [form, saving]);

  const ensureLocationPermission = useCallback(async () => {
    try {
      const current = await Location.getForegroundPermissionsAsync();
      if (current.status === 'granted') {
        setPermissionStatus('granted');
        return true;
      }
      const req = await Location.requestForegroundPermissionsAsync();
      setPermissionStatus(req.status);
      return req.status === 'granted';
    } catch {
      setPermissionStatus('denied');
      return false;
    }
  }, []);

  const load = useCallback(async () => {
    if (!accessToken) {
      setItems([]);
      setLoading(false);
      return;
    }
    setLoading(true);
    setError('');
    try {
      const arr = await listAddresses();
      setItems(arr || []);
      if (Array.isArray(arr) && arr.length) {
        const selected = arr.find((a) => a.id === selectedAddressId) || arr[0];
        if (selected) setSelectedAddress(selected);
      }
    } catch (e) {
      setError('تعذر تحميل العناوين');
      if (__DEV__) {
        console.log('[Addresses] load failed', {
          message: e?.message,
          status: e?.response?.status,
          data: e?.response?.data,
        });
      }
    } finally {
      setLoading(false);
    }
  }, [accessToken, selectedAddressId, setSelectedAddress]);

  const applyCoordinates = useCallback(async (lat, lng, accuracy = null) => {
    const geo = await reverseGeocodeAddress({ lat, lng });
    setForm((p) => ({
      ...p,
      city: String(geo?.city || p.city || '').trim(),
      area: String(geo?.area || p.area || '').trim(),
      street: String(geo?.street || p.street || '').trim(),
    }));
    setLocationMeta({
      latitude: lat,
      longitude: lng,
      accuracy_m: accuracy,
      formatted_address: String(geo?.formatted || '').trim(),
      provider: String(geo?.provider || '').trim(),
      provider_place_id: String(geo?.provider_place_id || '').trim(),
    });
    setMapRegion((r) => ({ ...r, latitude: lat, longitude: lng }));
  }, []);

  useFocusEffect(
    useCallback(() => {
      load();
      ensureLocationPermission();
    }, [load, ensureLocationPermission])
  );

  const onSave = async () => {
    if (!accessToken) {
      setSheetVisible(true);
      return;
    }
    if (!canSave) return;
    setSaving(true);
    try {
      const payload = {
        city: form.city.trim(),
        area: form.area.trim(),
        street: form.street.trim(),
        details: form.details.trim(),
        latitude: locationMeta.latitude,
        longitude: locationMeta.longitude,
        accuracy_m: locationMeta.accuracy_m,
        formatted_address: locationMeta.formatted_address,
        provider: locationMeta.provider,
        provider_place_id: locationMeta.provider_place_id,
      };
      const created = await createAddress(payload);
      setItems((prev) => [created, ...prev]);
      setSelectedAddress(created);
      setForm({ city: '', area: '', street: '', details: '' });
      setLocationMeta({
        latitude: null,
        longitude: null,
        accuracy_m: null,
        formatted_address: '',
        provider: '',
        provider_place_id: '',
      });
      setShowForm(false);
      Alert.alert('تم', 'تم حفظ العنوان');
    } catch (e) {
      Alert.alert('خطأ', 'تعذر حفظ العنوان');
      if (__DEV__) {
        console.log('[Addresses] create failed', {
          message: e?.message,
          status: e?.response?.status,
          data: e?.response?.data,
        });
      }
    } finally {
      setSaving(false);
    }
  };

  const onDetectByGps = useCallback(async () => {
    if (!accessToken) {
      setSheetVisible(true);
      return;
    }
    if (locating) return;
    setLocating(true);
    try {
      const ok = await ensureLocationPermission();
      if (!ok) {
        Alert.alert('تنبيه', 'يجب منح صلاحية الموقع');
        return;
      }
      const enabled = await Location.hasServicesEnabledAsync();
      if (!enabled) {
        Alert.alert('تنبيه', 'يرجى تفعيل نظام تحديد المواقع (GPS) لتسهيل عملية التوصيل');
        return;
      }
      const pos = await Location.getCurrentPositionAsync({ accuracy: Location.Accuracy.Highest });
      const lat = Number(pos?.coords?.latitude);
      const lng = Number(pos?.coords?.longitude);
      const acc = Number(pos?.coords?.accuracy || 0);
      if (!Number.isFinite(lat) || !Number.isFinite(lng)) {
        Alert.alert('خطأ', 'تعذر قراءة الإحداثيات');
        return;
      }
      await applyCoordinates(lat, lng, Number.isFinite(acc) ? acc : null);
    } catch (e) {
      Alert.alert('خطأ', 'تعذر تحديد الموقع حالياً');
      if (__DEV__) {
        console.log('[Addresses] gps failed', {
          message: e?.message,
          status: e?.response?.status,
          data: e?.response?.data,
        });
      }
    } finally {
      setLocating(false);
    }
  }, [accessToken, applyCoordinates, ensureLocationPermission, locating]);

  const onDelete = async (id) => {
    if (!id) return;
    setDeletingId(id);
    try {
      await deleteAddress(id);
      setItems((prev) => prev.filter((it) => it.id !== id));
    } catch (e) {
      Alert.alert('خطأ', 'تعذر حذف العنوان');
      if (__DEV__) {
        console.log('[Addresses] delete failed', {
          message: e?.message,
          status: e?.response?.status,
          data: e?.response?.data,
          id,
        });
      }
    } finally {
      setDeletingId(null);
    }
  };

  const AddressRow = ({ item }) => {
    const label = [item?.city, item?.area, item?.street].filter(Boolean).join(' - ');
    const hint = String(item?.details || '').toLowerCase();
    const icon = hint.includes('work') || hint.includes('عمل') ? 'briefcase-outline' : 'home-outline';
    const active = item?.id === selectedAddressId;
    return (
      <TouchableOpacity
        onPress={() => setSelectedAddress(item)}
        style={{
          marginTop: theme.spacing.sm,
          backgroundColor: active ? 'rgba(233,69,96,0.18)' : theme.colors.surface,
          borderWidth: 1,
          borderColor: active ? theme.colors.accent : theme.colors.cardBorder,
          borderRadius: theme.radius.lg,
          padding: theme.spacing.md,
        }}
      >
        <View style={{ flexDirection: 'row', alignItems: 'center' }}>
          <MaterialCommunityIcons name={icon} size={20} color={theme.colors.textPrimary} />
          <Text style={{ marginHorizontal: 8, flex: 1, color: theme.colors.textPrimary, fontFamily: theme.typography.fontBold, textAlign: I18nManager.isRTL ? 'right' : 'left' }}>{label || 'عنوان'}</Text>
          <MaterialCommunityIcons name={active ? 'check-circle' : 'circle-outline'} size={20} color={active ? theme.colors.accent : theme.colors.textSecondary} />
        </View>
        {item?.details ? <Text style={{ marginTop: 4, color: theme.colors.textSecondary, fontFamily: theme.typography.fontRegular, textAlign: I18nManager.isRTL ? 'right' : 'left' }}>{item.details}</Text> : null}
        <TouchableOpacity
          onPress={() => onDelete(item.id)}
          disabled={deletingId === item.id}
          style={{ marginTop: theme.spacing.sm, alignSelf: I18nManager.isRTL ? 'flex-start' : 'flex-end', paddingVertical: 6, paddingHorizontal: 12, borderRadius: theme.radius.md, borderWidth: 1, borderColor: theme.colors.cardBorder, backgroundColor: theme.colors.surfaceAlt }}
        >
          {deletingId === item.id ? <ActivityIndicator size="small" /> : <Text style={{ color: theme.colors.danger, fontFamily: theme.typography.fontBold }}>حذف</Text>}
        </TouchableOpacity>
      </TouchableOpacity>
    );
  };

  return (
    <View style={{ flex: 1, backgroundColor: theme.colors.background }}>
      <FlatList
        data={items}
        keyExtractor={(it) => String(it.id)}
        contentContainerStyle={{ padding: theme.spacing.lg, paddingBottom: 180 }}
        ListHeaderComponent={
          <View>
            <Text style={{ color: theme.colors.textPrimary, fontFamily: theme.typography.fontBold, fontSize: theme.typography.sizes.lg, textAlign: I18nManager.isRTL ? 'right' : 'left' }}>عنوان التوصيل</Text>
            {permissionStatus === 'denied' ? (
              <Text style={{ marginTop: 6, color: theme.colors.danger, fontFamily: theme.typography.fontBold, textAlign: I18nManager.isRTL ? 'right' : 'left' }}>
                يرجى تفعيل نظام تحديد المواقع (GPS) لتسهيل عملية التوصيل
              </Text>
            ) : null}
            {!accessToken ? (
              <TouchableOpacity onPress={() => setSheetVisible(true)} style={{ marginTop: theme.spacing.md, borderWidth: 1, borderColor: theme.colors.cardBorder, borderRadius: theme.radius.md, backgroundColor: theme.colors.surface, padding: theme.spacing.md }}>
                <Text style={{ color: theme.colors.textSecondary, fontFamily: theme.typography.fontRegular, textAlign: I18nManager.isRTL ? 'right' : 'left' }}>سجل الدخول لإدارة العناوين</Text>
              </TouchableOpacity>
            ) : showForm ? (
              <View style={{ marginTop: theme.spacing.md, borderWidth: 1, borderColor: theme.colors.cardBorder, borderRadius: theme.radius.md, backgroundColor: theme.colors.surface, padding: theme.spacing.md }}>
                <Text style={{ color: theme.colors.textPrimary, fontFamily: theme.typography.fontBold, textAlign: I18nManager.isRTL ? 'right' : 'left' }}>إضافة عنوان جديد</Text>
                <TextInput
                  value={form.city}
                  onChangeText={(v) => setForm((p) => ({ ...p, city: v }))}
                  placeholder="المدينة"
                  placeholderTextColor={theme.colors.textSecondary}
                  style={{ color: theme.colors.textPrimary, fontFamily: theme.typography.fontRegular, borderBottomWidth: 1, borderColor: theme.colors.cardBorder, paddingVertical: 8 }}
                />
                <TextInput
                  value={form.area}
                  onChangeText={(v) => setForm((p) => ({ ...p, area: v }))}
                  placeholder="المنطقة"
                  placeholderTextColor={theme.colors.textSecondary}
                  style={{ color: theme.colors.textPrimary, fontFamily: theme.typography.fontRegular, borderBottomWidth: 1, borderColor: theme.colors.cardBorder, paddingVertical: 8, marginTop: 8 }}
                />
                <TextInput
                  value={form.street}
                  onChangeText={(v) => setForm((p) => ({ ...p, street: v }))}
                  placeholder="الشارع"
                  placeholderTextColor={theme.colors.textSecondary}
                  style={{ color: theme.colors.textPrimary, fontFamily: theme.typography.fontRegular, borderBottomWidth: 1, borderColor: theme.colors.cardBorder, paddingVertical: 8, marginTop: 8 }}
                />
                <TextInput
                  value={form.details}
                  onChangeText={(v) => setForm((p) => ({ ...p, details: v }))}
                  placeholder="تفاصيل إضافية"
                  placeholderTextColor={theme.colors.textSecondary}
                  style={{ color: theme.colors.textPrimary, fontFamily: theme.typography.fontRegular, paddingVertical: 8, marginTop: 8 }}
                />
                <TouchableOpacity onPress={onDetectByGps} disabled={locating} style={{ marginTop: theme.spacing.sm, borderRadius: theme.radius.md, borderWidth: 1, borderColor: theme.colors.cardBorder, backgroundColor: theme.colors.surfaceAlt, paddingVertical: theme.spacing.sm, alignItems: 'center' }}>
                  {locating ? (
                    <ActivityIndicator size="small" />
                  ) : (
                    <View style={{ flexDirection: 'row', alignItems: 'center' }}>
                      <MaterialCommunityIcons name="crosshairs-gps" size={18} color={theme.colors.textPrimary} />
                      <Text style={{ marginHorizontal: 6, color: theme.colors.textPrimary, fontFamily: theme.typography.fontBold }}>Detect my location</Text>
                    </View>
                  )}
                </TouchableOpacity>
                {hasNativeMap ? (
                  <View style={{ marginTop: theme.spacing.sm, borderRadius: theme.radius.md, overflow: 'hidden', borderWidth: 1, borderColor: theme.colors.cardBorder }}>
                    <MapView
                      style={{ width: '100%', height: 180 }}
                      provider="google"
                      region={mapRegion}
                      onLongPress={(e) => {
                        const lat = Number(e?.nativeEvent?.coordinate?.latitude);
                        const lng = Number(e?.nativeEvent?.coordinate?.longitude);
                        if (Number.isFinite(lat) && Number.isFinite(lng)) applyCoordinates(lat, lng, null);
                      }}
                    >
                      {Number.isFinite(locationMeta.latitude) && Number.isFinite(locationMeta.longitude) ? (
                        <Marker
                          coordinate={{ latitude: locationMeta.latitude, longitude: locationMeta.longitude }}
                          draggable
                          onDragEnd={(e) => {
                            const lat = Number(e?.nativeEvent?.coordinate?.latitude);
                            const lng = Number(e?.nativeEvent?.coordinate?.longitude);
                            if (Number.isFinite(lat) && Number.isFinite(lng)) applyCoordinates(lat, lng, null);
                          }}
                        />
                      ) : null}
                    </MapView>
                  </View>
                ) : (
                  <View style={{ marginTop: theme.spacing.sm, borderRadius: theme.radius.md, borderWidth: 1, borderColor: theme.colors.cardBorder, backgroundColor: theme.colors.surfaceAlt, padding: theme.spacing.md }}>
                    <Text style={{ color: theme.colors.textSecondary, fontFamily: theme.typography.fontRegular, textAlign: I18nManager.isRTL ? 'right' : 'left' }}>
                      الخريطة المصغرة تحتاج نسخة تطبيق مبنية من جديد
                    </Text>
                    <TouchableOpacity
                      onPress={() => {
                        const lat = Number(locationMeta.latitude);
                        const lng = Number(locationMeta.longitude);
                        if (Number.isFinite(lat) && Number.isFinite(lng)) {
                          Linking.openURL(`https://www.google.com/maps?q=${lat},${lng}`);
                        }
                      }}
                      style={{ marginTop: theme.spacing.sm, borderRadius: theme.radius.md, borderWidth: 1, borderColor: theme.colors.cardBorder, paddingVertical: theme.spacing.sm, alignItems: 'center' }}
                    >
                      <Text style={{ color: theme.colors.textPrimary, fontFamily: theme.typography.fontBold }}>فتح الموقع في Google Maps</Text>
                    </TouchableOpacity>
                  </View>
                )}
                {locationMeta.formatted_address ? (
                  <Text style={{ marginTop: 6, color: theme.colors.textSecondary, fontFamily: theme.typography.fontRegular, textAlign: I18nManager.isRTL ? 'right' : 'left' }}>
                    {locationMeta.formatted_address}
                  </Text>
                ) : null}
                <TouchableOpacity onPress={onSave} disabled={!canSave} style={{ marginTop: theme.spacing.md, borderRadius: theme.radius.lg, backgroundColor: canSave ? theme.colors.accent : theme.colors.surfaceAlt, paddingVertical: theme.spacing.md, alignItems: 'center' }}>
                  {saving ? <ActivityIndicator color="#000" /> : <Text style={{ color: '#000', fontFamily: theme.typography.fontBold }}>حفظ العنوان</Text>}
                </TouchableOpacity>
                <TouchableOpacity onPress={() => setShowForm(false)} style={{ marginTop: theme.spacing.sm, borderRadius: theme.radius.md, borderWidth: 1, borderColor: theme.colors.cardBorder, paddingVertical: theme.spacing.sm, alignItems: 'center' }}>
                  <Text style={{ color: theme.colors.textSecondary, fontFamily: theme.typography.fontBold }}>إلغاء</Text>
                </TouchableOpacity>
              </View>
            ) : null}
            {error ? <Text style={{ marginTop: theme.spacing.sm, color: theme.colors.danger, fontFamily: theme.typography.fontBold, textAlign: I18nManager.isRTL ? 'right' : 'left' }}>{error}</Text> : null}
            <Text style={{ marginTop: theme.spacing.lg, color: theme.colors.textPrimary, fontFamily: theme.typography.fontBold, fontSize: theme.typography.sizes.md, textAlign: I18nManager.isRTL ? 'right' : 'left' }}>العناوين المحفوظة</Text>
          </View>
        }
        renderItem={AddressRow}
        ListEmptyComponent={
          loading ? (
            <View style={{ marginTop: theme.spacing.lg, alignItems: 'center' }}>
              <ActivityIndicator />
            </View>
          ) : (
            <View style={{ marginTop: theme.spacing.lg, alignItems: 'center' }}>
              <Text style={{ color: theme.colors.textSecondary, fontFamily: theme.typography.fontRegular }}>لا توجد عناوين بعد</Text>
            </View>
          )
        }
      />
      {accessToken ? (
        <View style={{ position: 'absolute', left: 0, right: 0, bottom: 0, paddingHorizontal: theme.spacing.lg, paddingTop: theme.spacing.sm, paddingBottom: theme.spacing.lg, borderTopWidth: 1, borderColor: theme.colors.cardBorder, backgroundColor: theme.colors.surface }}>
          <TouchableOpacity onPress={() => setShowForm((v) => !v)} style={{ borderRadius: theme.radius.lg, backgroundColor: theme.colors.accent, paddingVertical: theme.spacing.md, alignItems: 'center' }}>
            <Text style={{ color: '#000', fontFamily: theme.typography.fontBold }}>{showForm ? 'إخفاء إضافة عنوان' : 'إضافة عنوان جديد'}</Text>
          </TouchableOpacity>
        </View>
      ) : null}
      <LoginRequiredSheet
        visible={sheetVisible}
        onClose={() => setSheetVisible(false)}
        onLogin={() => {
          setSheetVisible(false);
          navigation.replace('Login', { next: { name: 'Addresses' } });
        }}
      />
    </View>
  );
}
