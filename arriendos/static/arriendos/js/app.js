/* app.js - Utilidades compartidas: sesión JWT, llamadas a la API, menú, avisos y formato. */
const API = '/api';
const ICONOS = {
  'Movimiento de Tierra': '🚜', 'Trabajo en Altura': '🏗️',
  'Energía y Respaldo': '⚡', 'Obras Civiles y Hormigón': '🧱'
};

/* Manejo de sesión: tokens y rol guardados en localStorage */
const Auth = {
  get access() { return localStorage.getItem('access'); },
  get refresh() { return localStorage.getItem('refresh'); },
  get rol() { return localStorage.getItem('rol'); },
  get username() { return localStorage.getItem('username'); },
  logged() { return !!this.access; },
  save(d) {
    localStorage.setItem('access', d.access);
    localStorage.setItem('refresh', d.refresh);
    localStorage.setItem('rol', d.rol);
    localStorage.setItem('username', d.username);
  },
  clear() { localStorage.clear(); }
};

/* Llamada a la API con renovación automática del access token */
async function api(path, { method = 'GET', body, auth = true, retry = true } = {}) {
  const headers = {};
  const esArchivo = body instanceof FormData;
  if (!esArchivo) headers['Content-Type'] = 'application/json';
  if (auth && Auth.access) headers.Authorization = 'Bearer ' + Auth.access;
  const r = await fetch(API + path, { method, headers, body: body ? (esArchivo ? body : JSON.stringify(body)) : undefined });
  if (r.status === 401 && auth && retry && Auth.refresh) {
    const rr = await fetch(API + '/auth/refresh/', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh: Auth.refresh })
    });
    if (rr.ok) {
      localStorage.setItem('access', (await rr.json()).access);
      return api(path, { method, body, auth, retry: false });
    }
    Auth.clear();
    location.href = '/login/';
    return;
  }
  let data = null;
  try { data = await r.json(); } catch (e) {}
  if (!r.ok) throw data || { detail: 'Error inesperado' };
  return data;
}

/* Convierte un error de la API en texto legible */
function msg(e) {
  if (!e) return 'Error';
  if (e.detail) return e.detail;
  return Object.values(e).flat().join(' ');
}

function toast(texto, tipo = 'ok') {
  const t = document.createElement('div');
  t.className = 'toast ' + (tipo === 'error' ? 'error' : '');
  t.textContent = texto;
  document.getElementById('toasts').appendChild(t);
  setTimeout(() => t.remove(), 3500);
}

const clp = n => '$' + Number(n).toLocaleString('es-CL');
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

/* Exige sesión (y opcionalmente un rol) para ver la página */
function requerir(rol) {
  if (!Auth.logged()) { location.href = '/login/'; return false; }
  if (rol && Auth.rol !== rol) { location.href = '/catalogo/'; return false; }
  return true;
}

/* Menú superior según el rol (ADMIN ve Panel; CLIENTE ve carro y contratos) */
async function construirMenu() {
  let h = '<a href="/catalogo/">▦ Catálogo</a>';
  if (Auth.logged()) {
    h += Auth.rol === 'ADMIN'
      ? '<a href="/panel/">⚙ Panel Admin</a>'
      : '<a href="/mis-contratos/">▤ Mis contratos</a><a href="/carro/" class="cart">🛒<span id="cartN">0</span></a>';
    h += `<span class="who">👤 ${esc(Auth.username)}</span><a href="#" id="salir" class="btn-sm">Salir</a>`;
  } else {
    h += '<a href="/login/">Ingresar</a><a href="/registro/" class="btn-sm">Registrarse</a>';
  }
  document.getElementById('menu').innerHTML = h;
  const s = document.getElementById('salir');
  if (s) s.onclick = async e => {
    e.preventDefault();
    try { await api('/auth/logout/', { method: 'POST', body: { refresh: Auth.refresh } }); } catch (x) {}
    Auth.clear();
    location.href = '/';
  };
  if (Auth.logged() && Auth.rol === 'CLIENTE') {
    try { const c = await api('/carro-arriendo/'); document.getElementById('cartN').textContent = c.items.length; } catch (x) {}
  }
}
document.addEventListener('DOMContentLoaded', construirMenu);

/* Etiqueta de stock con color: verde / ámbar / rojo */
function badgeStock(e) {
  if (e.stock === 0) return '<span class="badge cero">Agotado</span>';
  if (e.stock_bajo) return `<span class="badge bajo">⚠ Quedan ${e.stock}</span>`;
  return `<span class="badge ok">${e.stock} disponibles</span>`;
}
