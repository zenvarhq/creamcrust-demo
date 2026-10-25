/* Deliberate original-art fallback; no attempt to disguise a missing photograph. */
(() => {
  const siteRoot = new URL('../../', document.currentScript.src);
  const fallback = image => {
    if(image.dataset.fallbackApplied==='true')return;
    image.dataset.fallbackApplied='true';image.removeAttribute('srcset');
    image.src=new URL((image.dataset.fallback||'assets/art/hero-fallback.svg').replace(/^\//,''),siteRoot).href;
    image.alt='Original ZENVAR concept artwork; illustrative photograph unavailable';
    image.classList.add('media-fallback');
  };
  document.addEventListener('error',event=>{if(event.target instanceof HTMLImageElement)fallback(event.target);},true);
  document.addEventListener('DOMContentLoaded',()=>document.querySelectorAll('img[data-fallback]').forEach(image=>{if(image.complete&&!image.naturalWidth)fallback(image);}));
  // Keep Tab navigation inside an open viewer; Escape remains native.
  document.addEventListener('keydown',event=>{
    if(event.key!=='Tab')return;
    const dialog=document.querySelector('dialog[open]');if(!dialog)return;
    const controls=[...dialog.querySelectorAll('a[href],button:not([disabled]),input:not([disabled]),select:not([disabled]),textarea:not([disabled]),[tabindex]:not([tabindex="-1"])')].filter(element=>element.getClientRects().length);
    const first=controls[0],last=controls[controls.length-1];if(!first)return;
    const outside=!dialog.contains(document.activeElement);
    if(event.shiftKey&&(document.activeElement===first||outside)){event.preventDefault();last.focus();}
    else if(!event.shiftKey&&(document.activeElement===last||outside)){event.preventDefault();first.focus();}
  });
})();
