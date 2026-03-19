import AsyncStorage from '@react-native-async-storage/async-storage';

const FAVORITES_KEY = 'daar_favorites_v1';

function asArray(value) {
  return Array.isArray(value) ? value : [];
}

export async function getFavorites() {
  try {
    const raw = await AsyncStorage.getItem(FAVORITES_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return asArray(parsed);
  } catch {
    return [];
  }
}

async function writeFavorites(items) {
  try {
    await AsyncStorage.setItem(FAVORITES_KEY, JSON.stringify(asArray(items)));
  } catch {}
}

export async function isFavoriteProduct(productId) {
  const pid = Number(productId);
  if (!Number.isFinite(pid) || pid <= 0) return false;
  const items = await getFavorites();
  return items.some((it) => Number(it?.id) === pid);
}

export async function toggleFavoriteProduct(product) {
  const pid = Number(product?.id);
  if (!Number.isFinite(pid) || pid <= 0) return { liked: false, items: await getFavorites() };
  const items = await getFavorites();
  const idx = items.findIndex((it) => Number(it?.id) === pid);
  if (idx >= 0) {
    const next = items.filter((_, i) => i !== idx);
    await writeFavorites(next);
    return { liked: false, items: next };
  }
  const snapshot = {
    id: pid,
    name: product?.name || product?.title || 'منتج',
    price: Number(product?.price ?? product?.base_price ?? product?.final_price ?? 0),
    image_url: String(product?.image_url || product?.image || product?.main_image?.image_url || product?.main_image?.url || '').trim(),
    created_at: new Date().toISOString(),
  };
  const next = [snapshot, ...items];
  await writeFavorites(next);
  return { liked: true, items: next };
}
