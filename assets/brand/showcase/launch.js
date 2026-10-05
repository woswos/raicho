for (const viewport of document.querySelectorAll('.export-viewport')) {
  const artboard = viewport.firstElementChild;
  const resize = () => {
    const scale = Math.min(1, viewport.clientWidth / artboard.offsetWidth);
    artboard.style.transform = `scale(${scale})`;
    artboard.style.transformOrigin = 'top left';
    viewport.style.height = `${artboard.offsetHeight * scale}px`;
  };
  new ResizeObserver(resize).observe(viewport);
  resize();
}
