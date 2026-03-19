import React, { createContext, useCallback, useContext, useMemo, useState } from 'react';

const CheckoutCtx = createContext({
  selectedAddressId: null,
  selectedAddress: null,
  setSelectedAddress: () => {},
  clearSelectedAddress: () => {},
});

export function CheckoutProvider({ children }) {
  const [selectedAddressId, setSelectedAddressId] = useState(null);
  const [selectedAddress, setSelectedAddressState] = useState(null);

  const setSelectedAddress = useCallback((address) => {
    if (!address || !address.id) {
      setSelectedAddressId(null);
      setSelectedAddressState(null);
      return;
    }
    setSelectedAddressId((prev) => (prev === address.id ? prev : address.id));
    setSelectedAddressState((prev) => {
      if (
        prev &&
        prev.id === address.id &&
        prev.city === address.city &&
        prev.area === address.area &&
        prev.street === address.street &&
        prev.formatted_address === address.formatted_address
      ) {
        return prev;
      }
      return address;
    });
  }, []);

  const clearSelectedAddress = useCallback(() => {
    setSelectedAddressId((prev) => (prev == null ? prev : null));
    setSelectedAddressState((prev) => (prev == null ? prev : null));
  }, []);

  const value = useMemo(
    () => ({
      selectedAddressId,
      selectedAddress,
      setSelectedAddress,
      clearSelectedAddress,
    }),
    [clearSelectedAddress, selectedAddress, selectedAddressId, setSelectedAddress]
  );

  return <CheckoutCtx.Provider value={value}>{children}</CheckoutCtx.Provider>;
}

export function useCheckout() {
  return useContext(CheckoutCtx);
}
