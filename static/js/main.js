document.addEventListener('DOMContentLoaded', function(){
  var searchInput = document.querySelector('#globalSearchInput');
  var searchBtn = document.querySelector('#globalSearchBtn');
  function submitSearch(){
    var q = (searchInput && searchInput.value || '').trim();
    if(!q) return;
    window.location.assign('/products/?q='+encodeURIComponent(q));
  }
  if(searchBtn) searchBtn.addEventListener('click', submitSearch);
  if(searchInput) searchInput.addEventListener('keydown', function(e){ if(e.key === 'Enter'){ submitSearch(); } });
  var addButtons = document.querySelectorAll('[data-add-to-cart]');
  addButtons.forEach(function(btn){
    btn.addEventListener('click', function(){
      var pid = parseInt(btn.getAttribute('data-product-id')||'0')||0;
      var vid = btn.getAttribute('data-variant-id');
      var qty = parseInt(btn.getAttribute('data-qty')||'1')||1;
      try{
        var icon = document.querySelector('.global-bottom-nav .bi-cart');
        if(icon){ icon.classList.add('add-to-cart-anim'); setTimeout(function(){ icon.classList.remove('add-to-cart-anim'); }, 600); }
      }catch(e){}
      try{ addToCart(pid, vid?parseInt(vid):null, qty); }catch(e){}
    });
  });
  document.querySelectorAll('a[href^="#"]').forEach(function(a){
    a.addEventListener('click', function(e){
      var target = document.querySelector(a.getAttribute('href'));
      if(target){
        e.preventDefault();
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  });
});

// --- Moved from base.html ---

// From base.html - Announcements
function openAnnouncements(){
    window.location.assign('/announcements/');
}

// From base.html - Translations
(function(){
    window.i18n = {
        ar: {
            nav_home: 'الرئيسية',
            nav_stores: 'المتاجر',
            nav_cart: 'السلة',
            nav_account: 'حسابي',
            account_language: 'اللغة',
            account_theme: 'مظهر التطبيق',
            account_notifications: 'الاشعارات',
            account_services: 'خدماتنا',
            account_about: 'عن شركتنا',
            account_merchant: 'صير تاجر ويانة',
            account_appicon: 'ايقونة التطبيق',
            account_login: 'تسجيل الدخول',
            account_register: 'تسجيل',
            account_logout: 'تسجيل الخروج',
            account_not_signed: 'غير مسجل',
            account_owner_login: 'دخول المالك',
            language_ar: 'العربية',
            language_en: 'English',
            language_ku: 'کوردی',
            theme_dark: 'داكن',
            theme_light: 'فاتح',
            theme_system: 'حسب النظام'
        },
        en: {
            nav_home: 'Home',
            nav_stores: 'Stores',
            nav_cart: 'Cart',
            nav_account: 'Account',
            account_language: 'Language',
            account_theme: 'App Theme',
            account_notifications: 'Notifications',
            account_services: 'Our Services',
            account_about: 'About Us',
            account_merchant: 'Become a Merchant',
            account_appicon: 'App Icon',
            account_login: 'Login',
            account_register: 'Register',
            account_logout: 'Logout',
            account_not_signed: 'Not signed in',
            account_owner_login: 'Owner Login',
            language_ar: 'Arabic',
            language_en: 'English',
            language_ku: 'Kurdî',
            theme_dark: 'Dark',
            theme_light: 'Light',
            theme_system: 'System'
        },
        ku: {
            nav_home: 'سەرەتا',
            nav_stores: 'فرۆشیگا',
            nav_cart: 'سەبەتە',
            nav_account: 'هەژمار',
            account_language: 'زمان',
            account_theme: 'ڕووخەی ئەپ',
            account_notifications: 'ئاگەدارییەکان',
            account_services: 'خزمەتگوزارییەکانمان',
            account_about: 'دەربارەی ئێمە',
            account_merchant: 'بە فرۆشیگار بێ',
            account_appicon: 'نیشانی ئەپلیکەیشن',
            account_login: 'چوونەژورەوە',
            account_register: 'تۆماربوون',
            account_logout: 'دەرچوون',
            account_not_signed: 'تۆمار نەکراوە',
            account_owner_login: 'چوونەژوورەوەی خاوند',
            language_ar: 'عەرەبی',
            language_en: 'ئینگلیزی',
            language_ku: 'کوردی',
            theme_dark: 'تاریک',
            theme_light: 'کاڵ',
            theme_system: 'بە سیستەم'
        }
    };
    
    function applyTranslations(lang){
        const dict=(window.i18n && window.i18n[lang])? window.i18n[lang] : window.i18n['ar'];
        document.querySelectorAll('[data-i18n]').forEach(el=>{
            const k=el.getAttribute('data-i18n');
            if(dict[k]) el.textContent=dict[k];
        });
    }
    
    function applyLanguageFromStorage(){
        let lang='ar';
        try{
            const stored=localStorage.getItem('siteLanguage');
            if(!stored || !window.i18n[stored]){
                localStorage.setItem('siteLanguage','ar');
                lang='ar';
            } else {
                lang=stored;
            }
        }catch(e){ lang='ar'; }
        applyTranslations(lang);
    }
    
    applyLanguageFromStorage();
    
    window.addEventListener('languageChange',function(e){
        const lang=e.detail&&e.detail.lang? e.detail.lang : (localStorage.getItem('siteLanguage')||'ar');
        applyTranslations(lang);
    });
})();

// Cart Functionality
function updateCartCount() {
    const cart = JSON.parse(sessionStorage.getItem('cart') || '[]');
    const count = cart.reduce((sum, item) => sum + item.quantity, 0);
    const cartCountElement = document.getElementById('cart-count');
    if (cartCountElement) {
        cartCountElement.textContent = count;
        cartCountElement.style.display = count > 0 ? 'block' : 'none';
    }
}

function showLoading() {
    const el = document.getElementById('loadingSpinner');
    if(el) el.style.display = 'flex';
}

function hideLoading() {
    const el = document.getElementById('loadingSpinner');
    if(el) el.style.display = 'none';
}

document.addEventListener('DOMContentLoaded', function() {
    updateCartCount();
    hideLoading();
    try{ var h = String(location.hash||''); if(h === '#'){ history.replaceState(null, document.title, location.pathname + location.search); } }catch(e){}
});

function getCsrfToken(){
    const meta = document.querySelector('meta[name="csrf-token"]');
    if (meta && meta.content && meta.content !== 'NOTPROVIDED') return meta.content;
    const m = document.cookie.match(/csrftoken=([^;]+)/);
    return m ? m[1] : '';
}

function addToCart(productId, variantId = null, quantity = 1, storeId = null) {
    showLoading();
    const csrfToken = getCsrfToken();
    const body = { productId: productId, quantity: quantity };
    if (variantId) body.variantId = variantId;
    if (storeId) body.storeId = storeId;
    fetch('/cart/items', {
        method: 'POST',
        credentials: 'same-origin',
        headers: { 'X-CSRFToken': csrfToken, 'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest' },
        body: JSON.stringify(body)
    })
    .then(function(r){ return r.json().then(function(j){ return { ok: r.ok, status: r.status, data: j }; }); })
    .then(function(res){
        if (res.ok && res.data && res.data.ok) {
            try {
                if (typeof res.data.cart_items_count !== 'undefined') {
                    updateCartBadge(parseInt(res.data.cart_items_count || 0));
                }
            } catch(e) {}
            const toast = document.createElement('div');
            toast.className = 'position-fixed top-0 end-0 p-3';
            toast.style.zIndex = '9999';
            toast.innerHTML = `
                <div class="toast show animate__animated animate__slideInRight" role="alert">
                    <div class="toast-header bg-success text-white">
                        <i class="bi bi-check-circle-fill me-2"></i>
                        <strong class="me-auto">تمت الإضافة</strong>
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast"></button>
                    </div>
                    <div class="toast-body">تمت إضافة المنتج إلى السلة بنجاح!</div>
                </div>
            `;
            document.body.appendChild(toast);
            setTimeout(function(){ toast.remove(); }, 6000);
        } else {
            if (res.status === 409 && res.data && res.data.code === 'MULTI_STORE_NOT_ALLOWED') {
                try { window._pendingAdd = { productId: productId, variantId: variantId, quantity: quantity, storeId: storeId, details: res.data }; } catch(e){}
                const modalEl = document.getElementById('multiStoreModal');
                if (modalEl) { new bootstrap.Modal(modalEl).show(); }
                hideLoading();
                return;
            }
            const code = res.data && res.data.code;
            const msgMap = {
                'VARIANT_REQUIRED': 'اختر اللون/القياس قبل الإضافة للسلة.',
                'INVALID_VARIANT': 'الخيار المختار غير صالح. اختر مرة أخرى.',
                'OUT_OF_STOCK': 'المنتج نفد حالياً.',
                'INSUFFICIENT_STOCK': 'الكمية المطلوبة غير متوفرة.',
                'MULTI_STORE_NOT_ALLOWED': 'لا يمكن الجمع بين متاجر مختلفة في سلة واحدة.',
                'CHECKOUT_STOCK_FAILED': 'بعض المنتجات تغير مخزونها. تم تحديث سلتك.'
            };
            const msg = (code && msgMap[code]) ? msgMap[code] : ((res.data && res.data.message) ? res.data.message : 'تعذر إضافة المنتج إلى السلة');
            const toast = document.createElement('div');
            toast.className = 'position-fixed top-0 end-0 p-3';
            toast.style.zIndex = '9999';
            toast.innerHTML = `
                <div class="toast show animate__animated animate__slideInRight" role="alert">
                    <div class="toast-header bg-danger text-white">
                        <i class="bi bi-x-circle-fill me-2"></i>
                        <strong class="me-auto">فشل الإضافة</strong>
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast"></button>
                    </div>
                    <div class="toast-body">${msg}</div>
                </div>
            `;
            document.body.appendChild(toast);
            setTimeout(function(){ toast.remove(); }, 3000);
            if (code === 'VARIANT_REQUIRED' && productId) {
                try { openQuickVariantPicker(productId); } catch(e) {}
            }
        }
        hideLoading();
    })
    .catch(function(){ hideLoading(); });
}

(function(){
    const clearBtn = document.getElementById('msClearBtn');
    const cancelBtn = document.getElementById('msCancelBtn');
    if (clearBtn) {
        clearBtn.addEventListener('click', function(){
            const csrfToken = getCsrfToken();
            fetch('/cart/clear/', { method: 'DELETE', credentials: 'same-origin', headers: { 'X-CSRFToken': csrfToken, 'X-Requested-With': 'XMLHttpRequest' } })
            .then(function(r){ return r.json().then(function(j){ return { ok:r.ok, status:r.status, data:j }; }); })
            .then(function(){
                try{
                    const p = window._pendingAdd || {};
                    const modalEl = document.getElementById('multiStoreModal');
                    if (modalEl) { bootstrap.Modal.getInstance(modalEl)?.hide(); }
                    addToCart(p.productId, p.variantId, p.quantity, p.storeId);
                    window._pendingAdd = null;
                }catch(e){}
            });
        });
    }
    if (cancelBtn) {
        cancelBtn.addEventListener('click', function(){
            try{ window._pendingAdd = null; }catch(e){}
        });
    }
})();

function updateCartBadge(count){
    try{
        const inCartPage = (window.location.pathname || '').startsWith('/cart/');
        const navCart = document.querySelector('.global-bottom-nav a.nav-item[href$="/cart/"]');
        if(!navCart) return;
        const wrap = navCart.querySelector('.nav-icon-wrap') || navCart;
        let badge = wrap.querySelector('.cart-badge');
        if(!badge){
            badge = document.createElement('span');
            badge.className = 'cart-badge';
            wrap.appendChild(badge);
        }
        badge.textContent = String(count);
        badge.style.display = (!inCartPage && count > 0) ? 'flex' : 'none';
    }catch(e){}
}

try{ window.WebUI = { showToast: function(type, text){ var cont=document.createElement('div'); cont.className='position-fixed top-0 end-0 p-3'; cont.style.zIndex='9999'; cont.innerHTML='<div class="toast show" role="alert"><div class="toast-header '+(type==='success'?'bg-success text-white':type==='error'?'bg-danger text-white':'bg-primary text-white')+'"><strong class="me-auto">'+(type==='success'?'تم':'إشعار')+'</strong><button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast"></button></div><div class="toast-body">'+text+'</div></div>'; document.body.appendChild(cont); setTimeout(function(){ cont.remove(); }, 4000); } }; }catch(e){}

// Quick Variant Picker
(function(){
    var qpOverlay = null, qpSheet = null, qpCloseBtn = null;
    var qpColor = null, qpSize = null, qpQty = null, qpAddBtn = null;
    var qpCurrent = { productId: null, storeId: null, variants: [] };
    function ensureQuickPicker(){
        if(qpOverlay) return;
        qpOverlay = document.createElement('div');
        qpOverlay.id = 'qpOverlay';
        qpOverlay.style.cssText = 'position:fixed;inset:0;display:none;align-items:flex-end;z-index:1060;background:rgba(0,0,0,.35)';
        qpSheet = document.createElement('div');
        qpSheet.id = 'qpSheet';
        qpSheet.style.cssText = 'background:#fff;color:#111;width:100%;max-width:540px;margin:0 auto;border-top-left-radius:16px;border-top-right-radius:16px;box-shadow:0 -6px 24px rgba(0,0,0,.2);transform:translateY(100%);transition:transform .18s ease;';
        qpSheet.innerHTML = '<div style="padding:12px 16px;border-bottom:1px solid #eee;display:flex;justify-content:space-between;align-items:center"><strong>اختيار النسخة</strong><button type="button" id="qpClose" class="btn btn-sm btn-outline-secondary">إغلاق</button></div>'+
            '<div style="padding:12px 16px">'+
            '<div class="mb-2"><label class="form-label">اللون</label><select id="qpColor" class="form-select"><option value="">اختر اللون</option></select></div>'+
            '<div class="mb-2"><label class="form-label">المقاس</label><select id="qpSize" class="form-select" disabled><option value="">اختر المقاس</option></select></div>'+
            '<div class="mb-3"><label class="form-label">الكمية</label><input id="qpQty" type="number" class="form-control" value="1" min="1" style="max-width:120px"></div>'+
            '<div class="text-end"><button type="button" id="qpAdd" class="btn btn-primary">أضف للسلة</button></div>'+
            '</div>';
        qpOverlay.appendChild(qpSheet);
        document.body.appendChild(qpOverlay);
        qpCloseBtn = qpSheet.querySelector('#qpClose');
        qpColor = qpSheet.querySelector('#qpColor');
        qpSize = qpSheet.querySelector('#qpSize');
        qpQty = qpSheet.querySelector('#qpQty');
        qpAddBtn = qpSheet.querySelector('#qpAdd');
        qpOverlay.addEventListener('click', function(e){ if(e.target===qpOverlay) closeQuickPicker(); });
        qpCloseBtn.addEventListener('click', closeQuickPicker);
        qpColor.addEventListener('change', updateSizes);
        qpSize.addEventListener('change', function(){
            var opt = qpSize.options[qpSize.selectedIndex];
            var stock = opt ? parseInt(opt.getAttribute('data-stock')||'0') : 0;
            qpQty.value = 1;
            qpQty.max = stock>0 ? stock : 1;
        });
        qpAddBtn.addEventListener('click', function(){
            var color = qpColor.value;
            var size = qpSize.value;
            if(!color || !size) return;
            var v = qpCurrent.variants.find(function(x){ return x.color===color && x.size===size; });
            if(!v || !v.id) return;
            var qty = parseInt(qpQty.value||'1')||1;
            try{ addToCart(qpCurrent.productId, v.id, qty, qpCurrent.storeId); }catch(e){}
            try{ setTimeout(closeQuickPicker, 3000); }catch(e){}
        });
    }
    function openQuickVariantPicker(productId){
        ensureQuickPicker();
        qpCurrent.productId = productId; qpCurrent.storeId = null; qpCurrent.variants = [];
        qpColor.innerHTML = '<option value="">اختر اللون</option>';
        qpSize.innerHTML = '<option value="">اختر المقاس</option>';
        qpSize.disabled = true;
        qpQty.value = 1; qpQty.removeAttribute('max');
        qpOverlay.style.display = 'flex';
        setTimeout(function(){ qpSheet.style.transform = 'translateY(0)'; }, 10);
        fetch('/api/products/'+String(productId)+'/', { credentials:'same-origin' })
        .then(function(r){ return r.json(); })
        .then(function(p){
            try{
                var variants = Array.isArray(p.variants) ? p.variants : [];
                qpCurrent.storeId = (p.store && p.store.id) ? p.store.id : null;
                qpCurrent.variants = variants.map(function(v){ return { id:v.id, color:v.color, size:v.size, stock_qty:parseInt(v.stock_qty||'0'), price:parseFloat(v.price||p.base_price||0) }; });
                var colors = Array.from(new Set(qpCurrent.variants.map(function(v){ return v.color; }).filter(Boolean)));
                colors.forEach(function(c){ var opt=document.createElement('option'); opt.value=c; opt.textContent=c; qpColor.appendChild(opt); });
                var firstWithStock = qpCurrent.variants.find(function(v){ return v.stock_qty>0; });
                if(firstWithStock){ qpColor.value = firstWithStock.color; updateSizes(); }
            }catch(e){}
        }).catch(function(){ });
    }
    function updateSizes(){
        var color = qpColor.value;
        qpSize.innerHTML = '<option value="">اختر المقاس</option>';
        qpSize.disabled = true;
        qpQty.value = 1; qpQty.removeAttribute('max');
        if(!color) return;
        var sizes = qpCurrent.variants.filter(function(v){ return v.color===color; }).map(function(v){ return { size:v.size, id:v.id, stock:v.stock_qty }; });
        sizes.forEach(function(s){ var out = !s.stock || s.stock<=0; var opt=document.createElement('option'); opt.value=s.size; opt.textContent= out ? (s.size+' (غير متاح)') : s.size; opt.setAttribute('data-id', s.id); opt.setAttribute('data-stock', String(s.stock||0)); qpSize.appendChild(opt); });
        qpSize.disabled = sizes.length===0;
        var firstAvail = sizes.find(function(s){ return s.stock>0; });
        if(firstAvail){ qpSize.value = firstAvail.size; qpSize.dispatchEvent(new Event('change')); }
    }
    function closeQuickPicker(){
        try{ qpSheet.style.transform = 'translateY(100%)'; setTimeout(function(){ qpOverlay.style.display='none'; }, 180); }catch(e){ qpOverlay.style.display='none'; }
    }
    window.openQuickVariantPicker = openQuickVariantPicker;
})();

// Theme Toggler
(function(){
    window.toggleAppTheme = function(){
        var html = document.documentElement;
        var current = html.getAttribute('data-theme') || 'dark';
        var next = current === 'dark' ? 'light' : 'dark';
        html.setAttribute('data-theme', next);
        html.setAttribute('data-bs-theme', next);
        if(document.body){
            document.body.classList.remove('theme-light', 'dark-theme');
            document.body.classList.add(next === 'dark' ? 'dark-theme' : 'theme-light');
        }
        try{
            localStorage.setItem('siteTheme', next);
            localStorage.setItem('theme', next);
        }catch(e){}
        window.dispatchEvent(new CustomEvent('themeChange', { detail: { theme: next } }));
        var toast = document.createElement('div');
        toast.className = 'position-fixed bottom-0 start-50 translate-middle-x p-3';
        toast.style.zIndex = '1100';
        toast.innerHTML = '<div class="toast show align-items-center text-white bg-' + (next==='dark'?'dark':'primary') + ' border-0" role="alert" aria-live="assertive" aria-atomic="true"><div class="d-flex"><div class="toast-body">' + (next==='dark' ? 'تم تفعيل الوضع الداكن' : 'تم تفعيل الوضع الفاتح') + '</div><button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button></div></div>';
        document.body.appendChild(toast);
        setTimeout(function(){ toast.remove(); }, 2000);
        return next;
    };
    window.applyCurrentTheme = function(){
        var stored = localStorage.getItem('siteTheme') || localStorage.getItem('theme') || 'dark';
        var html = document.documentElement;
        html.setAttribute('data-theme', stored);
        html.setAttribute('data-bs-theme', stored);
        if(document.body){
            document.body.classList.remove('theme-light', 'dark-theme');
            document.body.classList.add(stored === 'dark' ? 'dark-theme' : 'theme-light');
        }
    };
    if(document.readyState === 'loading'){
        document.addEventListener('DOMContentLoaded', window.applyCurrentTheme);
    } else {
        window.applyCurrentTheme();
    }
})();
