import client from './client';
import { API_BASE_URL } from '../config';
import { saveTokens } from '../auth/tokenStorage';

export async function login(identifier, password) {
  const payload = { password };
  const id = (identifier || '').trim();
  payload.username = id;
  if (id.includes('@')) payload.email = id;
  let r;
  try {
    r = await client.post('/api/auth/login/', payload);
  } catch (e) {
    const msg =
      e?.response?.data?.detail ||
      e?.response?.data?.error ||
      e?.response?.data?.message ||
      'بيانات الدخول غير صحيحة أو تعذر الاتصال';
    throw new Error(String(msg));
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
  const { access, refresh, user } = r.data || {};
  if (access && refresh) {
    await saveTokens({ access, refresh });
  }
  return user;
}

export async function me() {
  const r = await client.get('/api/auth/me/');
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
  const r = await client.get('/api/categories');
  console.log('[API] GET /api/categories status=', r.status, 'data=', r.data);
  return r.data;
}

export async function listBanners() {
  const r = await client.get('/api/banners');
  console.log('[API] GET /api/banners status=', r.status, 'data=', r.data);
  return r.data;
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
    const r = await client.get('/api/ads/', { params });
    return r.data;
  } catch {
    const bn = await listBanners();
    return bn;
  }
}

export async function getCart() {
  const r = await client.get('/api/cart/');
  return r.data;
}

export async function addToCart(product_id, variant_id, quantity = 1) {
  const payload = { product_id, quantity };
  if (variant_id) payload.variant_id = variant_id;
  const r = await client.post('/api/cart/', payload);
  return r.data;
}

export async function updateCartItem(id, quantity) {
  const r = await client.patch(`/api/cart/${id}/`, { quantity });
  return r.data;
}

export async function removeCartItem(id) {
  const r = await client.delete(`/api/cart/${id}/`);
  return r.data;
}

export async function addCartItemVariant({ variant_id, qty = 1, size }) {
  const payload = { variant_id, qty };
  if (size) payload.size = size;
  const r = await client.post('/api/cart/items', payload);
  console.log('[CART] add', payload, 'status=', r.status);
  return r.data;
}

export async function listProducts(params = {}) {
  const r = await client.get('/api/products/', { params });
  console.log('[API] GET /api/products status=', r.status, 'params=', params, 'data.count=', Array.isArray(r.data) ? r.data.length : (r.data?.results?.length || 0));
  return r.data;
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
