(function(){
  var Rail = window.TalabatRailTabs = window.TalabatRailTabs || {};
  function normalizeNumber(val){
    var n = parseFloat(val);
    return isNaN(n) ? 0 : n;
  }
  function isNewItem(item){
    var raw = item.dataset.createdAt;
    if(!raw) return false;
    var t = Date.parse(raw);
    if(isNaN(t)) return false;
    var days = (Date.now() - t) / 86400000;
    return days <= 30;
  }
  function prepareItems(items){
    items.forEach(function(it){
      if(it.dataset.createdAt){
        it.dataset.isNew = isNewItem(it) ? '1' : '0';
      }
      if(!it.dataset.isNew) it.dataset.isNew = '0';
      if(!it.dataset.discount) it.dataset.discount = '0';
    });
  }
  function filterItems(items, tab){
    if(tab === 'discount') return items.filter(function(it){ return it.dataset.discount === '1'; });
    if(tab === 'new') return items.filter(function(it){ return it.dataset.isNew === '1'; });
    return items.slice();
  }
  function roundRobin(items, tab){
    var groups = {};
    items.forEach(function(it){
      var key = it.dataset.storeId || 'all';
      if(!groups[key]) groups[key] = [];
      groups[key].push(it);
    });
    var keys = Object.keys(groups);
    keys.forEach(function(k){
      var list = groups[k];
      if(tab === 'best'){
        list.sort(function(a,b){ return normalizeNumber(b.dataset.sold) - normalizeNumber(a.dataset.sold); });
      } else if(tab === 'price'){
        list.sort(function(a,b){ return normalizeNumber(a.dataset.price) - normalizeNumber(b.dataset.price); });
      } else if(tab === 'new'){
        list.sort(function(a,b){
          var ta = Date.parse(a.dataset.createdAt || '') || 0;
          var tb = Date.parse(b.dataset.createdAt || '') || 0;
          return tb - ta;
        });
      }
    });
    var out = [];
    var remaining = true;
    while(remaining){
      remaining = false;
      for(var i=0;i<keys.length;i++){
        var key = keys[i];
        if(groups[key].length){
          out.push(groups[key].shift());
          remaining = true;
        }
      }
    }
    return out;
  }
  function applyTab(state){
    var filtered = filterItems(state.allItems, state.tab);
    var ordered = roundRobin(filtered, state.tab);
    state.scroller.innerHTML = '';
    ordered.forEach(function(it){
      state.scroller.appendChild(it);
    });
    setPos(state.scroller, 0, true);
  }
  function getPos(scroller){
    var dir = getComputedStyle(scroller).direction;
    var left = scroller.scrollLeft;
    if(dir === 'rtl'){
      if(left < 0) return -left;
      var max = scroller.scrollWidth - scroller.clientWidth;
      return max - left;
    }
    return left;
  }
  function setPos(scroller, val, smooth){
    var max = scroller.scrollWidth - scroller.clientWidth;
    var target = Math.max(0, Math.min(val, max));
    var dir = getComputedStyle(scroller).direction;
    if(dir === 'rtl'){
      if(scroller.scrollLeft < 0){
        if(smooth){ scroller.scrollTo({left: -target, behavior:'smooth'}); }
        else { scroller.scrollLeft = -target; }
      } else {
        if(smooth){ scroller.scrollTo({left: max - target, behavior:'smooth'}); }
        else { scroller.scrollLeft = max - target; }
      }
    } else {
      if(smooth){ scroller.scrollTo({left: target, behavior:'smooth'}); }
      else { scroller.scrollLeft = target; }
    }
  }
  function tickAuto(state, now){
    if(!state.scroller || !state.scroller.isConnected){
      stopAuto(state);
      return;
    }
    if(state.pausedUntil && now < state.pausedUntil){
      state.scroller.__rafId = requestAnimationFrame(function(t){ tickAuto(state, t); });
      return;
    }
    var max = state.scroller.scrollWidth - state.scroller.clientWidth;
    if(max > 0){
      if(!state.animating && now >= state.nextStepAt){
        var step = state.scroller.clientWidth || 1;
        var next = getPos(state.scroller) + step;
        if(next >= max - 2) next = 0;
        state.animating = true;
        state.animStart = now;
        state.animFrom = getPos(state.scroller);
        state.animTo = next;
      }
      if(state.animating){
        var t = Math.min(1, (now - state.animStart) / state.animMs);
        var eased = 1 - Math.pow(1 - t, 3);
        var pos = state.animFrom + (state.animTo - state.animFrom) * eased;
        setPos(state.scroller, pos, false);
        if(t >= 1){
          state.animating = false;
          state.nextStepAt = now + state.stepMs;
        }
      }
    } else {
      state.nextStepAt = now + state.stepMs;
    }
    state.scroller.__rafId = requestAnimationFrame(function(t){ tickAuto(state, t); });
  }
  function startAuto(state){
    if(state.scroller.__rafId) return;
    var now = performance.now();
    state.nextStepAt = now + state.stepMs;
    state.animating = false;
    state.scroller.__rafId = requestAnimationFrame(function(t){ tickAuto(state, t); });
  }
  function stopAuto(state){
    if(state.scroller && state.scroller.__rafId){
      cancelAnimationFrame(state.scroller.__rafId);
      state.scroller.__rafId = null;
    }
  }
  function scheduleResume(state){
    if(state.idleTimer){
      clearTimeout(state.idleTimer);
    }
    state.pausedUntil = performance.now() + 3000;
    state.idleTimer = setTimeout(function(){
      startAuto(state);
    }, 3000);
  }
  function bindInteractions(state){
    var scroller = state.scroller;
    ['touchstart','pointerdown','mousedown','wheel','scroll'].forEach(function(evt){
      scroller.addEventListener(evt, function(){
        stopAuto(state);
        scheduleResume(state);
      }, {passive:true});
    });
  }
  function bindTabs(state){
    state.tabs.forEach(function(btn){
      btn.addEventListener('click', function(){
        state.tabs.forEach(function(b){ b.classList.remove('active'); });
        btn.classList.add('active');
        state.tab = btn.getAttribute('data-tab') || 'best';
        applyTab(state);
        stopAuto(state);
        scheduleResume(state);
      });
    });
  }
  function init(){
    var rail = document.querySelector('.mobile-product-rail');
    if(!rail) return;
    if(window.innerWidth > 768) return;
    if(rail.dataset.inited === '1') return;
    var scroller = rail.querySelector('.rail-scroller');
    var tabs = Array.prototype.slice.call(rail.querySelectorAll('.rail-tab'));
    if(!scroller || !tabs.length) return;
    var items = Array.prototype.slice.call(scroller.querySelectorAll('.rail-item'));
    if(!items.length) return;
    prepareItems(items);
    rail.dataset.inited = '1';
    var state = {
      rail: rail,
      scroller: scroller,
      tabs: tabs,
      allItems: items,
      tab: 'best',
      idleTimer: null,
      pausedUntil: 0,
      stepMs: 3500,
      animMs: 450,
      animating: false,
      animStart: 0,
      animFrom: 0,
      animTo: 0,
      nextStepAt: 0
    };
    applyTab(state);
    bindTabs(state);
    bindInteractions(state);
    startAuto(state);
    Rail.state = state;
    if(!Rail._visibilityBound){
      Rail._visibilityBound = true;
      document.addEventListener('visibilitychange', function(){
        var s = Rail.state;
        if(!s) return;
        if(document.hidden){
          stopAuto(s);
        } else {
          startAuto(s);
        }
      });
      window.addEventListener('pageshow', function(){
        var s = Rail.state;
        if(s) startAuto(s);
      });
    }
  }
  if(document.readyState === 'loading'){
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
