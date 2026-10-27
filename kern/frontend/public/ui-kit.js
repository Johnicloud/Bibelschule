// Gemeinsame Helfer für die eigene Oberfläche eines Dienstes (siehe ui-kit.css). Kein Build-Schritt nötig,
// darum reines Browser-JS ohne Module: als <script src="/ui-kit.js"> einbinden, dann steht window.UIKit bereit.
window.UIKit = (() => {
  async function call(method, path, body) {
    const res = await fetch(path, {
      method,
      headers: body ? { 'Content-Type': 'application/json' } : undefined,
      body: body ? JSON.stringify(body) : undefined,
    })
    if (!res.ok) {
      const e = await res.json().catch(() => ({}))
      throw new Error(typeof e.detail === 'string' ? e.detail : 'Etwas ist schiefgelaufen.')
    }
    return res.status === 204 ? null : res.json()
  }

  // Baut ein Element ohne innerHTML (sicher gegenüber fremden Texten): el('span', {class: 'uk-badge'}, 'Text')
  function el(tag, attrs, children) {
    const node = document.createElement(tag)
    for (const [k, v] of Object.entries(attrs || {})) {
      if (k === 'class') node.className = v
      else if (k.startsWith('on') && typeof v === 'function') node.addEventListener(k.slice(2), v)
      else node.setAttribute(k, v)
    }
    for (const child of [].concat(children ?? [])) {
      node.append(child instanceof Node ? child : document.createTextNode(String(child)))
    }
    return node
  }

  // Ersetzt den Inhalt eines Containers durch eine Liste gerenderter Einträge.
  function renderList(container, items, render) {
    container.replaceChildren(...items.map(render))
  }

  // Symbole (Strichzeichnungen wie in der App, siehe AppIcon.vue): UIKit.icon('trash') liefert ein <svg>.
  const ICONS = {
    eye: 'M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12zM12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6z',
    eyeoff: 'M10.7 5.1A10 10 0 0 1 12 5c6.5 0 10 7 10 7a17 17 0 0 1-2.2 3.2M6.6 6.6A17 17 0 0 0 2 12s3.5 7 10 7a9.7 9.7 0 0 0 5.4-1.6M2 2l20 20M9.9 9.9a3 3 0 0 0 4.2 4.2',
    download: 'M12 3v12M7 10l5 5 5-5M5 21h14',
    trash: 'M3 6h18M8 6V4a1 1 0 0 1 1-1h6a1 1 0 0 1 1 1v2M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6M10 11v6M14 11v6',
    scan: 'M3 7V5a2 2 0 0 1 2-2h2M17 3h2a2 2 0 0 1 2 2v2M21 17v2a2 2 0 0 1-2 2h-2M7 21H5a2 2 0 0 1-2-2v-2M7 8h8M7 12h10M7 16h6',
    karten: 'M2 7a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V7zM14 7.5l4.4-1.6a2 2 0 0 1 2.6 1.2l2.7 9.4a2 2 0 0 1-1.2 2.6L18 20.5',
    haken: 'M20 6 9 17l-5-5',
    x: 'M6 6l12 12M18 6 6 18',
    upload: 'M12 15V3M7 8l5-5 5 5M5 21h14',
    uhr: 'M12 6v6l4 2M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18z',
  }
  function icon(name) {
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg')
    for (const [k, v] of Object.entries({ viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': '2',
      'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'aria-hidden': 'true', class: 'uk-icon' })) svg.setAttribute(k, v)
    const pfad = document.createElementNS('http://www.w3.org/2000/svg', 'path')
    pfad.setAttribute('d', ICONS[name] || ICONS.karten)
    svg.appendChild(pfad)
    return svg
  }
  // Nur ein Symbol, der Name steht im Tooltip und für Screenreader (aria-label): setIcon(knopf, 'trash', 'Löschen')
  function setIcon(node, name, label) {
    node.replaceChildren(icon(name))
    node.title = label
    node.setAttribute('aria-label', label)
  }

  function subjectId() {
    return new URLSearchParams(location.search).get('subject') || ''
  }

  return { call, el, renderList, subjectId, icon, setIcon }
})()
