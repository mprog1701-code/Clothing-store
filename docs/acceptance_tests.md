# Acceptance Tests

This document lists 25 acceptance tests grouped by feature area. Each test specifies Steps, Inputs, Expected UI result, and Expected API status + code.

## Cart & Variants (8)

1) Add product with variants without variantId
- Steps: Logged-in user clicks Add to Cart on a product that has variants, without selecting a variant.
- Inputs: POST /cart/items with { productId, quantity }.
- Expected UI result: Toast shows “الرجاء اختيار النسخة/المقاس”. Cart count unchanged.
- Expected API status + code: 400, VARIANT_REQUIRED.

2) Add variant that is out of stock
- Steps: Logged-in user selects a variant with stock_qty = 0 and adds to cart.
- Inputs: POST /cart/items with { productId, variantId, quantity: 1 }.
- Expected UI result: Toast shows “النسخة غير متوفرة”. Cart count unchanged.
- Expected API status + code: 409, OUT_OF_STOCK.

3) Add variant with quantity exceeding stock
- Steps: Logged-in user selects a variant with stock_qty = N and requests quantity N+1.
- Inputs: POST /cart/items with { productId, variantId, quantity: N+1 }.
- Expected UI result: Toast shows “الكمية غير كافية”. Cart count unchanged.
- Expected API status + code: 409, INSUFFICIENT_STOCK.

4) Increase quantity beyond stock for existing cart item
- Steps: Logged-in user adds a variant to cart, then re-adds to increase quantity over available stock.
- Inputs: Sequential POST /cart/items with same { productId, variantId } causing new_qty > stock.
- Expected UI result: Toast shows “الكمية غير كافية”. Quantity not increased.
- Expected API status + code: 409, INSUFFICIENT_STOCK.

5) Add with invalid productId format
- Steps: Logged-in user calls API with non-integer productId.
- Inputs: POST /cart/items with { productId: "abc" }.
- Expected UI result: Toast shows failure. Cart unchanged.
- Expected API status + code: 400, INVALID_PRODUCT.

6) Add with product not found
- Steps: Logged-in user calls API with productId that does not exist.
- Inputs: POST /cart/items with { productId: 999999 }.
- Expected UI result: Toast shows failure. Cart unchanged.
- Expected API status + code: 404, PRODUCT_NOT_FOUND.

7) Add with invalid variant relationship
- Steps: Logged-in user selects a variantId that does not belong to the given product.
- Inputs: POST /cart/items with { productId: A, variantId: of other product }.
- Expected UI result: Toast shows failure. Cart unchanged.
- Expected API status + code: 400, INVALID_VARIANT.

8) Add to cart requires authentication
- Steps: Guest tries to add any product to cart.
- Inputs: POST /cart/items with any payload.
- Expected UI result: Redirect to login or toast “يرجى تسجيل الدخول”.
- Expected API status + code: 401, UNAUTHORIZED.

## Stock & Checkout (7)

1) Checkout fails due to stock changes (AJAX)
- Steps: Logged-in user proceeds to checkout and submits confirmation (AJAX) while a variant is now out-of-stock or insufficient.
- Inputs: POST /checkout/ (XHR) with address_id; session cart contains an item exceeding stock.
- Expected UI result: Stock Fail modal opens listing failed items; user stays on checkout/cart.
- Expected API status + code: 409, CHECKOUT_STOCK_FAILED.

2) Checkout across multiple stores is blocked
- Steps: Logged-in user has items from Store A in cart and attempts to checkout after adding Store B items.
- Inputs: POST /checkout/ (XHR) with address_id; session cart spans multiple stores.
- Expected UI result: Error message “لا يمكن الطلب من متاجر مختلفة”.
- Expected API status + code: 409, MULTI_STORE_NOT_ALLOWED.

3) Successful checkout (AJAX)
- Steps: Logged-in user completes checkout with valid address and sufficient stock.
- Inputs: POST /checkout/ (XHR) with address_id.
- Expected UI result: Redirect to order detail page.
- Expected API status + code: 200, ok: true (JSON body contains order_id).

4) Authenticated user missing address selection
- Steps: Logged-in user submits checkout without selecting or providing address.
- Inputs: POST /checkout/ (form) missing address_id and guest fields.
- Expected UI result: Error message prompting address selection; remain on checkout.
- Expected API status + code: 200, HTML response (no JSON code).

5) Guest checkout invalid phone
- Steps: Guest fills checkout form with phone not matching ^07\d{9}$.
- Inputs: POST /checkout/ (form) with invalid guest_phone.
- Expected UI result: Error message “يرجى إدخال رقم عراقي صالح…”.
- Expected API status + code: 200, HTML response (no JSON code).

6) Apply valid coupon reduces totals
- Steps: User enters coupon code (e.g., WELCOME10) on step 3.
- Inputs: POST /checkout/apply-coupon/ with { code: "WELCOME10" }.
- Expected UI result: Discount label appears; grand total reduced.
- Expected API status + code: 200, success: true.

7) Apply invalid coupon
- Steps: User enters unknown coupon code.
- Inputs: POST /checkout/apply-coupon/ with { code: "INVALID" }.
- Expected UI result: Message “الكوبون غير صالح”.
- Expected API status + code: 400, invalid_code.

## Multi-Store (5)

1) Add second product from different store
- Steps: Logged-in user adds item from Store A, then tries to add from Store B.
- Inputs: Two POST /cart/items requests.
- Expected UI result: Modal offers to clear cart or cancel; cart not mixed.
- Expected API status + code: 409, MULTI_STORE_NOT_ALLOWED.

2) Clear cart then add from another store succeeds
- Steps: User clears cart via UI, then adds item from Store B.
- Inputs: DELETE /cart/clear/ then POST /cart/items.
- Expected UI result: Cart cleared; new item added; badge updated.
- Expected API status + code: 200, success: true (clear); 200, ok: true (add).

3) Checkout rejects mixed-store cart (AJAX)
- Steps: User attempts checkout with items from multiple stores.
- Inputs: POST /checkout/ (XHR) with address_id.
- Expected UI result: Error message; stay on cart.
- Expected API status + code: 409, MULTI_STORE_NOT_ALLOWED.

4) Cart store detection from existing item works
- Steps: User adds item without variants, then re-adds; store inference remains consistent.
- Inputs: POST /cart/items for same product twice.
- Expected UI result: Quantity increases; no store mismatch.
- Expected API status + code: 200, ok: true.

5) Pending add flow after clear
- Steps: When multi-store modal appears, user clicks “مسح السلة” then auto-add of pending item.
- Inputs: DELETE /cart/clear/ followed by POST /cart/items.
- Expected UI result: Modal closes; item from new store added.
- Expected API status + code: 200, success: true (clear); 200, ok: true (add).

## Security & Authorization (3)

1) Add to cart requires login
- Steps: Guest attempts to add any item.
- Inputs: POST /cart/items.
- Expected UI result: Redirect to login or toast warning.
- Expected API status + code: 401, UNAUTHORIZED.

2) Order detail IDOR prevention (authenticated)
- Steps: User B attempts to view order that belongs to User A.
- Inputs: GET /my/orders/{order_id} as User B.
- Expected UI result: Error message “ليس لديك صلاحية…”; redirected to order list.
- Expected API status + code: 302 redirect (HTML; no JSON code).

3) Remove from cart requires login (AJAX)
- Steps: Guest clicks remove in cart.
- Inputs: POST /cart/remove/{index} with XHR header.
- Expected UI result: Toast “يرجى تسجيل الدخول”.
- Expected API status + code: 401, UNAUTHORIZED.

## Admin Feature Flags (2)

1) Bank transfer option disabled by feature flag
- Steps: Admin disables feature flag bank_transfer; user opens checkout step 2.
- Inputs: FeatureFlag(key="bank_transfer", enabled=False).
- Expected UI result: Bank transfer radio is disabled with “قريباً”.
- Expected API status + code: N/A (UI-only; context includes features.bank_transfer=false).

2) Card payment option disabled by feature flag
- Steps: Admin disables feature flag card_payment; user opens checkout step 2.
- Inputs: FeatureFlag(key="card_payment", enabled=False).
- Expected UI result: Card payment radio is disabled with “قريباً”.
- Expected API status + code: N/A (UI-only; context includes features.card_payment=false).

---

References
- Cart endpoints: [urls.py](file:///c:/Users/k/talabat/core/urls.py#L24-L47)
- Checkout template behaviors: [checkout.html](file:///c:/Users/k/talabat/core/templates/orders/checkout.html#L311-L355)
- Cart JSON view: [views.py:cart_items_json](file:///c:/Users/k/talabat/core/views.py#L708-L807)
- Checkout stock failure: [views.py:checkout](file:///c:/Users/k/talabat/core/views.py#L968-L1005)
- Coupon API: [views.py:apply_coupon_json](file:///c:/Users/k/talabat/core/views.py#L1105-L1216)
- Order detail authorization: [views.py:order_detail](file:///c:/Users/k/talabat/core/views.py#L1230-L1266)
- Feature flags context: [context_processors.py](file:///c:/Users/k/talabat/core/context_processors.py#L5-L19)
