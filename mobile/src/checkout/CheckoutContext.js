import React, { createContext, useContext, useMemo, useState } from 'react';

const CheckoutCtx = createContext({
  selectedAddressId: null,
  selectedAddress: null,
  setSelectedAddress: () => {},
  clearSelectedAddress: () => {},
});

export function CheckoutProvider({ children }) {
  const [selectedAddressId, setSelectedAddressId] = useState(null);
  const [selectedAddress, setSelectedAddressState] = useState(null);

  const setSelectedAddress = (address) => {
    if (!address || !address.id) {
      setSelectedAddressId(null);
      setSelectedAddressState(null);
      return;
    }
    setSelectedAddressId(address.id);
    setSelectedAddressState(address);
  };

  const clearSelectedAddress = () => {
    setSelectedAddressId(null);
    setSelectedAddressState(null);
  };

  const value = useMemo(
    () => ({
      selectedAddressId,
      selectedAddress,
      setSelectedAddress,
      clearSelectedAddress,
    }),
    [selectedAddressId, selectedAddress]
  );

  return <CheckoutCtx.Provider value={value}>{children}</CheckoutCtx.Provider>;
}

export function useCheckout() {
  return useContext(CheckoutCtx);
}
