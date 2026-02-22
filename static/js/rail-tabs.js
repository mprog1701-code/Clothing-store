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
    state.scroller.scrollTo({left: 0});
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
  function setPos(scroller, val){
    var max = scroller.scrollWidth - scroller.clientWidth;
    var target = Math.max(0, Math.min(val, max));
    var dir = getComputedStyle(scroller).direction;
    if(dir === 'rtl'){
      if(scroller.scrollLeft < 0){
        scroller.scrollTo({left: -target, behavior:'smooth'});
      } else {
        scroller.scrollTo({left: max - target, behavior:'smooth'});
      }
    } else {
      scroller.scrollTo({left: target, behavior:'smooth'});
    }
  }
  function startAuto(state){
    if(state.timer) return;
    state.timer = setInterval(function(){
      var max = state.scroller.scrollWidth - state.scroller.clientWidth;
      if(max <= 0) return;
      var step = state.scroller.clientWidth || 1;
      var next = getPos(state.scroller) + step;
      if(next >= max - 2) next = 0;
      setPos(state.scroller, next);
    }, 3500);
  }
  function stopAuto(state){
    if(state.timer){
      clearInterval(state.timer);
      state.timer = null;
    }
  }
  function scheduleResume(state){
    if(state.idleTimer){
      clearTimeout(state.idleTimer);
    }
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
    var scroller = rail.querySelector('.rail-scroller');
    var tabs = Array.prototype.slice.call(rail.querySelectorAll('.rail-tab'));
    if(!scroller || !tabs.length) return;
    var items = Array.prototype.slice.call(scroller.querySelectorAll('.rail-item'));
    if(!items.length) return;
    prepareItems(items);
    var state = {
      rail: rail,
      scroller: scroller,
      tabs: tabs,
      allItems: items,
      tab: 'best',
      timer: null,
      idleTimer: null
    };
    applyTab(state);
    bindTabs(state);
    bindInteractions(state);
    startAuto(state);
    Rail.state = state;
  }
  if(document.readyState === 'loading'){
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
