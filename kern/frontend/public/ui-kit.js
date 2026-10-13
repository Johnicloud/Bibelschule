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

  function subjectId() {
    return new URLSearchParams(location.search).get('subject') || ''
  }

  return { call, el, renderList, subjectId }
})()
