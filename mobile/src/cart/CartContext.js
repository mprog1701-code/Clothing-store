import React, { createContext, useCallback, useContext, useMemo, useState } from 'react';
import { getCart } from '../api';
import { useAuth } from '../auth/AuthContext';

const CartCtx = createContext({
  cartCount: 0,
  setCartCount: () => {},
  refreshCartCount: async () => {},
  addToCartCount: () => {},
});

export function CartProvider({ children }) {
  const { accessToken } = useAuth();
  const [cartCount, setCartCount] = useState(0);

  const refreshCartCount = useCallback(async () => {
    if (!accessToken) {
      setCartCount(0);
      return 0;
    }
    try {
      const data = await getCart();
      const arr = Array.isArray(data) ? data : (data.items || data.results || []);
      const next = arr.reduce((sum, it) => sum + Number(it?.quantity || 0), 0);
      setCartCount(next);
      return next;
    } catch {
      return 0;
    }
  }, [accessToken]);

  const addToCartCount = useCallback((qty = 1) => {
    const n = Number(qty);
    if (!Number.isFinite(n) || n <= 0) return;
    setCartCount((prev) => prev + n);
  }, []);

  const value = useMemo(
    () => ({ cartCount, setCartCount, refreshCartCount, addToCartCount }),
    [cartCount, refreshCartCount, addToCartCount]
  );

  return <CartCtx.Provider value={value}>{children}</CartCtx.Provider>;
}

export function useCart() {
  return useContext(CartCtx);
}
