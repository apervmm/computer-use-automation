(() => {
    const isVisible = (el) => el.offsetParent !== null;
  
    const hasStructuralChildren = (el) => {
      return Array.from(el.children).some(child =>
        !['BR', 'SPAN', 'B', 'I', 'EM', 'STRONG'].includes(child.tagName)
      );
    };
  
    const safeText = (node) => {
      if (!node || hasStructuralChildren(node)) return '';
      return node.innerText?.trim() || '';
    };
  
    const nearbyText = (el) => {
      let node = el.previousElementSibling;
      for (let i = 0; i < 2 && node; i++, node = node.previousElementSibling) {
        const text = safeText(node);
        if (text) return text;
      }
      let ancestor = el.parentElement;
      for (let level = 0; level < 2 && ancestor; level++, ancestor = ancestor.parentElement) {
        let prev = ancestor.previousElementSibling;
        for (let i = 0; i < 2 && prev; i++, prev = prev.previousElementSibling) {
          const text = safeText(prev);
          if (text) return text;
        }
      }
      const parentCell = el.closest('td');
      if (parentCell) {
        const text = safeText(parentCell.previousElementSibling);
        if (text) return text;
      }
      return '';
    };
  
    const nameOf = (el) => {
      return el.getAttribute('aria-label')
          || (el.id && document.querySelector(`label[for="${el.id}"]`)?.innerText.trim())
          || el.placeholder
          || el.value
          || nearbyText(el)
          || (!hasStructuralChildren(el) ? el.innerText?.trim() : '')
          || '';
    };
  
    const roleOf = (el) => {
      const tag = el.tagName.toLowerCase();
      if (tag === 'a') return 'link';
      if (tag === 'button') return 'button';
      if (tag === 'select') return 'combobox';
      if (tag === 'input') {
        const t = (el.type || 'text').toLowerCase();
        return (t === 'submit' || t === 'button') ? 'button' : 'textbox';
      }
      return 'other';
    };
  
    return Array.from(document.querySelectorAll('a, button, input, select'))
      .filter(isVisible)
      .filter(el => !hasStructuralChildren(el))
      .map(el => ({ role: roleOf(el), name: (nameOf(el) || '').trim() }))
      .filter(item => item.name);
  })();