import client from './client';
import { API_BASE_URL } from './config';
import { saveTokens } from '../auth/tokenStorage';
import { normalizeIraqiPhone } from '../utils/phone';
import AsyncStorage from '@react-native-async-storage/async-storage';

const CART_CACHE_KEY = 'daar_cart_cache_v1';

function asCartArray(data) {
  return Array.isArray(data) ? data : (data?.items || data?.results || []);
}

function asAddressArray(data) {
  if (Array.isArray(data)) return data;
  if (Array.isArray(data?.results)) return data.results;
  if (Array.isArray(data?.items)) return data.items;
  if (Array.isArray(data?.addresses)) return data.addresses;
  return [];
}

async function readLocalCart() {
  try {
    const raw = await AsyncStorage.getItem(CART_CACHE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

async function writeLocalCart(items) {
  try {
    await AsyncStorage.setItem(CART_CACHE_KEY, JSON.stringify(Array.isArray(items) ? items : []));
  } catch {}
}

async function cacheFromServerData(data) {
  const arr = asCartArray(data);
  if (arr.length) {
    await writeLocalCart(arr);
  }
}

async function upsertLocalCartItem({ product_id, variant_id = null, quantity = 1, size, product_snapshot }) {
  const q = Number(quantity);
  const qty = Number.isFinite(q) && q > 0 ? q : 1;
  const pid = Number(product_id);
  if (!Number.isFinite(pid) || pid <= 0) return readLocalCart();
  const current = await readLocalCart();
  const idx = current.findIndex(
    (it) => Number(it?.product?.id) === pid && Number(it?.variant?.id || it?.variant_id || 0) === Number(variant_id || 0)
  );
  if (idx >= 0) {
    const old = current[idx];
    current[idx] = { ...old, quantity: Number(old?.quantity || 0) + qty };
  } else {
    current.unshift({
      id: `local-${pid}-${variant_id || 'none'}`,
      quantity: qty,
      variant_id: variant_id || null,
      variant_text: size ? `المقاس: ${size}` : '',
      product: {
        id: pid,
        name: product_snapshot?.name || 'منتج',
        base_price: Number(product_snapshot?.base_price ?? product_snapshot?.price ?? 0),
        main_image: product_snapshot?.main_image || null,
      },
      variant: variant_id ? { id: variant_id } : null,
    });
  }
  await writeLocalCart(current);
  return current;
}

async function updateLocalCartItem(id, quantity) {
  const q = Number(quantity);
  const qty = Number.isFinite(q) && q > 0 ? q : 1;
  const current = await readLocalCart();
  const next = current.map((it) => (String(it?.id) === String(id) ? { ...it, quantity: qty } : it));
  await writeLocalCart(next);
  return next;
}

async function removeLocalCartItem(id) {
  const current = await readLocalCart();
  const next = current.filter((it) => String(it?.id) !== String(id));
  await writeLocalCart(next);
  return next;
}

export async function login(identifier, password) {
  const payload = { password };
  const id = (identifier || '').trim();
  const normalizedPhone = normalizeIraqiPhone(id);
  const phoneLike = normalizedPhone && normalizedPhone.startsWith('07') && normalizedPhone.length === 11;
  payload.username = phoneLike ? normalizedPhone : id;
  payload.phone = phoneLike ? normalizedPhone : id;
  if (id.includes('@')) payload.email = id;
  let r;
  try {
    r = await client.post('/api/auth/login/', payload);
  } catch (e) {
    const data = e?.response?.data || {};
    const msg =
      data?.message ||
      data?.detail ||
      data?.error ||
      e?.response?.data?.detail ||
      e?.response?.data?.error ||
      e?.response?.data?.message ||
      'بيانات الدخول غير صحيحة أو تعذر الاتصال';
    const err = new Error(String(msg));
    err.code = String(data?.error || data?.code || '');
    err.payload = data;
    throw err;
  }
  const { access, refresh, user } = r.data || {};
  if (access && refresh) {
    await saveTokens({ access, refresh });
  }
  return user;
}

export async function logout() {
  await client.post('/api/auth/logout/');
}

export async function register(payload) {
  const body = { ...payload };
  let r;
  const extractMsg = (data, status) => {
    if (!data) return '';
    if (typeof data === 'string') return data;
    if (data.detail) return String(data.detail);
    if (data.error) return String(data.error);
    if (data.message) return String(data.message);
    if (typeof data === 'object') {
      const parts = [];
      Object.keys(data).forEach((k) => {
        const v = data[k];
        if (Array.isArray(v) && v.length) parts.push(String(v[0]));
        else if (typeof v === 'string') parts.push(String(v));
      });
      return parts.join('، ');
    }
    return '';
  };
  try {
    r = await client.post('/api/auth/register/', body);
  } catch (e1) {
    const s1 = e1?.response?.status;
    const d1 = e1?.response?.data;
    if (s1 === 404) {
      try {
        r = await client.post('/api/auth/signup/', body);
      } catch (e2) {
        const s2 = e2?.response?.status;
        if (s2 === 404) {
          try {
            r = await client.post('/api/users/', body);
          } catch (e3) {
            const msg = extractMsg(e3?.response?.data, e3?.response?.status) || 'فشل التسجيل. الرجاء التحقق من الحقول.';
            throw new Error(String(msg));
          }
        } else {
          const msg = extractMsg(e2?.response?.data, s2) || 'فشل التسجيل. الرجاء التحقق من الحقول.';
          throw new Error(String(msg));
        }
      }
    } else {
      const msg = extractMsg(d1, s1) || (s1 === 409 ? 'اسم المستخدم أو البريد مستخدم مسبقًا' : 'فشل التسجيل. الرجاء التحقق من الحقول.');
      throw new Error(String(msg));
    }
  }
  const data = r.data || {};
  const { access, refresh, user } = data;
  if (access && refresh) {
    await saveTokens({ access, refresh });
  }
  return data?.requires_verification ? data : user;
}

export async function verifyRegistration(payload = {}) {
  const r = await client.post('/api/auth/verify_registration/', payload);
  const { access, refresh, user } = r.data || {};
  if (access && refresh) {
    await saveTokens({ access, refresh });
  }
  return user || null;
}

export async function resendVerification(payload = {}) {
  const r = await client.post('/api/auth/resend_verification/', payload);
  return r.data;
}

export async function requestPasswordReset(payload = {}) {
  const r = await client.post('/api/auth/forgot_password_request/', payload);
  return r.data;
}

export async function confirmPasswordReset(payload = {}) {
  const r = await client.post('/api/auth/forgot_password_confirm/', payload);
  return r.data;
}

export async function me() {
  const r = await client.get('/api/auth/me/');
  return r.data;
}

export async function updateMe(payload = {}) {
  const r = await client.patch('/api/auth/me/', payload);
  return r.data;
}

export async function listStores(params = {}) {
  const r = await client.get('/api/stores/', { params });
  return r.data;
}

export async function getStore(id) {
  const r = await client.get(`/api/stores/${id}/`);
  return r.data;
}

export async function listStoreProducts(id, params = {}) {
  const r = await client.get(`/api/stores/${id}/products/`, { params });
  return r.data;
}

export async function listTopStores(params = {}) {
  try {
    const r = await client.get('/api/stores/top/', { params });
    return r.data;
  } catch {
    const all = await listStores(params);
    const arr = Array.isArray(all) ? all : (all.results || []);
    return arr.slice(0, 10);
  }
}

export async function productVariantPrice(id, color, size) {
  const r = await client.get(`/api/products/${id}/variant-price/`, { params: { color, size } });
  return r.data;
}

export async function listCategories() {
  try {
    const r = await client.get('/api/categories');
    console.log('[API] GET /api/categories status=', r.status, 'dataLen=', Array.isArray(r.data) ? r.data.length : (r.data?.results?.length || 0));
    return r.data;
  } catch (e) {
    const base = (API_BASE_URL || '').replace(/\/+$/, '');
    const path = '/api/categories';
    const full = `${base}${path}`;
    console.log('[API] AXIOS NetworkError for', full, 'message=', e?.message);
    try {
      const resp = await fetch(full, { method: 'GET' });
      const ct = resp.headers.get('content-type') || '';
      const ok = resp.ok;
      console.log('[API] FETCH fallback status=', resp.status, 'ok=', ok, 'ct=', ct);
      const data = ct.includes('application/json') ? await resp.json() : await resp.text();
      return data;
    } catch (fe) {
      console.log('[API] FETCH fallback failed', fe?.message || fe);
      throw e;
    }
  }
}

export async function listBanners() {
  const r = await client.get('/api/banners');
  const data = r.data;
  const arr = Array.isArray(data) ? data : (data.results || data.banners || []);
  console.log('[API] GET /api/banners status=', r.status, 'len=', arr.length);
  return arr;
}

export async function listBannersByPlacement(placement) {
  const p = String(placement || '').trim();
  const val = p.toUpperCase();
  const map = { HOME_TOP: 'home_top', HOME_MIDDLE: 'home_middle', HOME_BOTTOM: 'home_bottom' };
  const q = map[val] ? map[val] : (p || 'home_top');
  const r = await client.get('/api/banners', { params: { placement: q } });
  const data = r.data;
  const arr = Array.isArray(data) ? data : (data.results || data.banners || []);
  console.log('[API] GET /api/banners placement=', q, 'status=', r.status, 'len=', arr.length);
  return arr;
}

export async function listHomeTopBanners() {
  try {
    const r = await client.get('/api/banners/home-top/');
    const data = r.data;
    const arr = Array.isArray(data) ? data : (data.results || data.banners || []);
    console.log('[API] GET /api/banners/home-top/ status=', r.status, 'len=', arr.length);
    return arr;
  } catch (e) {
    console.log('[API] GET /api/banners/home-top/ fail', e?.message || e);
    const bn = await listBanners();
    return bn?.banners || (Array.isArray(bn) ? bn : (bn.results || []));
  }
}

export async function listAds(params = {}) {
  try {
    const r = await client.get('/api/advertisements/', { params });
    const data = r.data;
    const arr = Array.isArray(data) ? data : (data.results || data.ads || []);
    console.log('[API] GET /api/advertisements status=', r.status, 'len=', arr.length, 'params=', params);
    if (arr.length) return arr;
  } catch (e) {
    console.log('[API] GET /api/advertisements fail', e?.message || e);
  }
  try {
    const r = await client.get('/api/ads/', { params });
    const data = r.data;
    const arr = Array.isArray(data) ? data : (data.results || data.ads || []);
    console.log('[API] GET /api/ads status=', r.status, 'len=', arr.length, 'params=', params);
    return arr;
  } catch (e) {
    console.log('[API] GET /api/ads fail', e?.message || e);
    return [];
  }
}

export async function getCart() {
  try {
    const r = await client.get('/api/cart/');
    await cacheFromServerData(r.data);
    return r.data;
  } catch (e) {
    if (__DEV__) {
      const st = e?.response?.status;
      if (st !== 500) {
        console.log('[API] GET /api/cart/ failed', {
          message: e?.message,
          status: st,
          data: e?.response?.data,
        });
      }
    }
    const status = e?.response?.status;
    if (status === 401 || status === 403) throw e;
    if (status !== 404) {
      const local = await readLocalCart();
      return local;
    }
    try {
      const fallback = await client.get('/api/cart');
      await cacheFromServerData(fallback.data);
      return fallback.data;
    } catch {
      const local = await readLocalCart();
      return local;
    }
  }
}

export async function addToCart(product_id, variant_id, quantity = 1) {
  const payload = { product_id, quantity };
  if (variant_id) payload.variant_id = variant_id;
  try {
    const r = await client.post('/api/cart/', payload);
    await upsertLocalCartItem({ product_id, variant_id, quantity });
    return r.data;
  } catch (e) {
    const status = e?.response?.status;
    if (status === 401 || status === 403 || status === 409 || status === 400) throw e;
    const local = await upsertLocalCartItem({ product_id, variant_id, quantity });
    return local;
  }
}

export async function updateCartItem(id, quantity) {
  try {
    const r = await client.patch(`/api/cart/${id}/`, { quantity });
    await updateLocalCartItem(id, quantity);
    return r.data;
  } catch (e) {
    const status = e?.response?.status;
    if (status === 401 || status === 403 || status === 404) throw e;
    const local = await updateLocalCartItem(id, quantity);
    return local;
  }
}

export async function removeCartItem(id) {
  const idStr = String(id || '');
  if (!idStr) return [];
  if (idStr.startsWith('local-')) {
    return await removeLocalCartItem(idStr);
  }
  try {
    const r = await client.delete(`/api/cart/${idStr}/`);
    await removeLocalCartItem(idStr);
    return r.data;
  } catch (e) {
    const status = e?.response?.status;
    if (status === 401 || status === 403) throw e;
    if (status === 404) {
      return await removeLocalCartItem(idStr);
    }
    const local = await removeLocalCartItem(idStr);
    return local;
  }
}

export async function clearCartAfterCheckout(items = []) {
  const ids = new Set();
  for (const it of (Array.isArray(items) ? items : [])) {
    if (it?.id !== undefined && it?.id !== null) ids.add(String(it.id));
  }
  try {
    const latest = await getCart();
    const latestArr = Array.isArray(latest) ? latest : (latest?.items || latest?.results || []);
    for (const it of latestArr) {
      if (it?.id !== undefined && it?.id !== null) ids.add(String(it.id));
    }
  } catch {}
  for (const id of ids) {
    try {
      await removeCartItem(id);
    } catch {}
  }
  await writeLocalCart([]);
  return [];
}

export async function addCartItemVariant({ product_id, variant_id, qty = 1, quantity, size, product_snapshot }) {
  const normalizedQty = Number(quantity ?? qty ?? 1);
  const payload = {
    product_id,
    quantity: Number.isFinite(normalizedQty) && normalizedQty > 0 ? normalizedQty : 1,
  };
  if (variant_id) payload.variant_id = variant_id;
  if (size) payload.size = size;
  try {
    const r = await client.post('/api/cart/', payload);
    await upsertLocalCartItem({
      product_id,
      variant_id,
      quantity: payload.quantity,
      size,
      product_snapshot,
    });
    console.log('[CART] add', payload, 'status=', r.status);
    return r.data;
  } catch (e) {
    const status = e?.response?.status;
    if (status === 401 || status === 403 || status === 409 || status === 400) throw e;
    const local = await upsertLocalCartItem({
      product_id,
      variant_id,
      quantity: payload.quantity,
      size,
      product_snapshot,
    });
    if (__DEV__) {
      console.log('[CART] add fallback local', {
        status,
        message: e?.message,
        payload,
      });
    }
    return local;
  }
}

export async function listProducts(params = {}) {
  const p = { ...(params || {}) };
  if (p.limit && !p.page_size) p.page_size = p.limit;
  if (!p.limit && !p.page_size) p.page_size = 50;
  try {
    const r = await client.get('/api/products/', { params: p });
    console.log('[API] GET /api/products status=', r.status, 'params=', p, 'data.count=', Array.isArray(r.data) ? r.data.length : (r.data?.results?.length || 0));
    if (__DEV__) {
      const sample = Array.isArray(r.data) ? r.data.slice(0, 2) : (r.data?.results || []).slice(0, 2);
      console.log('[API] GET /api/products sample=', sample);
    }
    return r.data;
  } catch (e) {
    console.error('[API] GET /api/products failed', {
      message: e?.message,
      status: e?.response?.status,
      data: e?.response?.data,
      params: p,
    });
    throw e;
  }
}

export async function getProduct(id) {
  const r = await client.get(`/api/products/${id}/`);
  return r.data;
}

export async function devSeed() {
  const r = await client.post('/api/dev/seed');
  console.log('[API] POST /api/dev/seed status=', r.status, 'data=', r.data);
  return r.data;
}

export async function listOrders(params = {}) {
  const r = await client.get('/api/orders/', { params });
  return r.data;
}

export async function getOrder(id) {
  const r = await client.get(`/api/orders/${id}/`);
  return r.data;
}

export async function listAddresses() {
  const r = await client.get('/api/addresses/');
  return asAddressArray(r.data);
}

export async function createAddress(payload) {
  const endpoints = ['/api/addresses/', '/api/addresses'];
  let lastError = null;
  for (let i = 0; i < 3; i += 1) {
    for (const endpoint of endpoints) {
      try {
        const r = await client.post(endpoint, payload);
        return r.data;
      } catch (e) {
        lastError = e;
        const status = e?.response?.status;
        const code = e?.code;
        const retryable =
          status === 502 ||
          status === 503 ||
          status === 504 ||
          code === 'ECONNABORTED' ||
          code === 'ERR_NETWORK';
        if (!retryable) {
          throw e;
        }
        if (__DEV__) {
          console.log('[API] createAddress retryable failure', {
            endpoint,
            attempt: i + 1,
            status,
            code,
            message: e?.message,
          });
        }
      }
    }
    await new Promise((resolve) => setTimeout(resolve, 600 * (i + 1)));
  }
  throw lastError;
}

export async function updateAddress(id, payload) {
  const r = await client.patch(`/api/addresses/${id}/`, payload);
  return r.data;
}

export async function deleteAddress(id) {
  const r = await client.delete(`/api/addresses/${id}/`);
  return r.data;
}

export async function reverseGeocodeAddress({ lat, lng }) {
  const r = await client.get('/api/addresses/reverse-geocode/', { params: { lat, lng } });
  if (__DEV__) {
    console.log('[API] GET /api/addresses/reverse-geocode/ params=', { lat, lng });
    console.log('[API] GET /api/addresses/reverse-geocode/ response=', r.data);
  }
  return r.data;
}

export async function createOrder(payload) {
  const r = await client.post('/api/orders/', payload);
  return r.data;
}
