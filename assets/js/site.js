document.addEventListener('DOMContentLoaded',()=>{
  const toggle=document.querySelector('.menu-toggle'),nav=document.querySelector('.nav-mobile');
  function closeNav(restore=false){nav?.classList.remove('is-open');toggle?.setAttribute('aria-expanded','false');toggle?.setAttribute('aria-label','Open navigation');if(restore)toggle?.focus();}
  toggle?.addEventListener('click',()=>{const open=nav.classList.toggle('is-open');toggle.setAttribute('aria-expanded',String(open));toggle.setAttribute('aria-label',open?'Close navigation':'Open navigation');});
  document.addEventListener('keydown',e=>{if(e.key==='Escape'&&nav?.classList.contains('is-open'))closeNav(true);});
  nav?.addEventListener('click',e=>{if(e.target.closest('a'))closeNav();});
  document.addEventListener('click',e=>{if(!e.target.closest('.brand-header'))closeNav();});
  matchMedia('(min-width:761px)').addEventListener('change',()=>closeNav());
  const dialog=document.querySelector('.gallery-dialog');
  if(dialog){let opener;document.querySelectorAll('[data-image]').forEach(button=>button.addEventListener('click',()=>{opener=button;const image=dialog.querySelector('img');image.src=button.dataset.image;image.dataset.fallback='/assets/art/hero-fallback.svg';image.dataset.fallbackApplied='false';image.alt=button.dataset.label;dialog.querySelector('p').textContent=button.dataset.label+' · Photo: '+button.dataset.credit+' · Licensed illustration';document.body.style.overflow='hidden';dialog.showModal();dialog.querySelector('.dialog-close').focus();}));dialog.querySelector('.dialog-close').addEventListener('click',()=>dialog.close());dialog.addEventListener('click',e=>{if(e.target===dialog)dialog.close();});dialog.addEventListener('close',()=>{document.body.style.overflow='';opener?.focus();});}
  function syncHighlights(){const data=window.CC?.load();if(!data)return;const hide=window.CC.read('cc_hide_prices_v1')==='1';document.querySelectorAll('[data-featured]').forEach(card=>{const i=data.items.find(i=>i.id===card.dataset.featured);if(!i)return;card.querySelector('h3').textContent=i.name;const edited=window.CREAMCRUST_CATALOG.items.find(x=>x.id===i.id)?.price!==i.price;card.querySelector('.price-text').textContent=hide?'Price pending approval':window.CC.price(i.price)+'*';card.querySelector('.featured-content p').textContent=edited?'Local demo price':i.available===false?'Unavailable in local preview':'Public menu observation';});}
  syncHighlights();window.addEventListener('pageshow',syncHighlights);window.addEventListener('storage',syncHighlights);
});
