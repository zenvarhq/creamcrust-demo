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
})();
