let currentPage = 1
const PAGE_SIZE = 20
let activeFilters = { type1: '', type2: '', heavy: false }
let typeIcons = {}
let descriptionCache = {}

// ── Helpers ────────────────────────────────────────────────────────────────

function filterParams() {
  const params = new URLSearchParams()
  if (activeFilters.type1) params.append('type1', activeFilters.type1)
  if (activeFilters.type2) params.append('type2', activeFilters.type2)
  if (activeFilters.heavy) params.append('heavy', 'true')
  return params
}

function typeBadge(t) {
  if (typeIcons[t]) {
    return `<img src="${typeIcons[t]}" alt="${t}" title="${t}" class="w-8 h-8 object-contain shrink-0" />`
  }
  return `<span class="inline-flex items-center text-xs font-medium px-2 py-0.5 rounded-full bg-gray-100 text-gray-700">${t}</span>`
}

function spriteImg(src, alt, classes = 'w-16 h-16 object-contain shrink-0') {
  return src
    ? `<img src="${src}" alt="${alt}" class="${classes} cursor-pointer hover:scale-110 transition-transform" onclick="openPokemonModal('${alt}', '${src}')" title="Clicca per la descrizione" />`
    : `<div class="w-16 h-16 shrink-0 bg-gray-100 rounded-lg"></div>`
}

// ── Pokémon list ───────────────────────────────────────────────────────────

async function fetchPokemon(page = 1) {
  const params = filterParams()
  params.set('page', page)
  params.set('size', PAGE_SIZE)
  const res = await fetch(`/api/pokemon/?${params}`)
  if (!res.ok) throw new Error('Failed to fetch')
  return res.json()
}

async function loadPage(page) {
  const tbody = document.getElementById('pokemon-tbody')
  const cards = document.getElementById('pokemon-cards')
  tbody.innerHTML = `<tr><td colspan="7" class="text-center py-10 text-gray-400">Loading...</td></tr>`
  cards.innerHTML = `<div class="text-center py-10 text-gray-400 text-sm">Loading...</div>`

  try {
    const result = await fetchPokemon(page)
    currentPage = result.page
    renderTable(result)
    renderCards(result)
    renderPagination(result)
  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="7" class="text-center py-10 text-red-400">Error loading data.</td></tr>`
    cards.innerHTML = `<div class="text-center py-10 text-red-400 text-sm">Error loading data.</div>`
  }
}

function renderTable(result) {
  const tbody = document.getElementById('pokemon-tbody')
  const entries = Object.entries(result.data)
  if (entries.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" class="text-center py-10 text-gray-400">No Pokémon found.</td></tr>`
    return
  }
  tbody.innerHTML = entries.map(([name, data]) => {
    const types  = data.types.map(typeBadge).join(' ')
    const weight = (data.weight / 10).toFixed(1)
    const height = (data.height / 10).toFixed(1)
    return `
      <tr class="border-b hover:bg-gray-50 transition">
        <td class="px-4 py-2">${spriteImg(data.sprite, name)}</td>
        <td class="px-4 py-2 font-medium capitalize">${name}</td>
        <td class="px-4 py-2"><div class="flex flex-wrap gap-1">${types}</div></td>
        <td class="px-4 py-2">${weight}</td>
        <td class="px-4 py-2">${height}</td>
        <td class="px-4 py-2">${data.base_experience ?? 'N/A'}</td>
        <td class="px-4 py-2 text-right">
          <button onclick="deletePokemon('${name}')"
            class="text-xs text-red-500 hover:text-red-700 border border-red-200 hover:border-red-400 px-3 py-1 rounded-lg transition active:scale-95">
            Delete
          </button>
        </td>
      </tr>`
  }).join('')
}

function renderCards(result) {
  const cards = document.getElementById('pokemon-cards')
  const entries = Object.entries(result.data)
  if (entries.length === 0) {
    cards.innerHTML = `<div class="text-center py-10 text-gray-400 text-sm">No Pokémon found.</div>`
    return
  }
  cards.innerHTML = entries.map(([name, data]) => {
    const types  = data.types.map(typeBadge).join(' ')
    const weight = (data.weight / 10).toFixed(1)
    const height = (data.height / 10).toFixed(1)
    return `
      <div class="flex items-center gap-3 px-4 py-3">
        ${spriteImg(data.sprite, name)}
        <div class="flex-1 min-w-0">
          <p class="font-medium capitalize text-sm">${name}</p>
          <div class="flex flex-wrap gap-1 mt-1">${types}</div>
          <p class="text-xs text-gray-500 mt-1">${weight} kg · ${height} m · ${data.base_experience ?? 'N/A'} XP</p>
        </div>
        <button onclick="deletePokemon('${name}')"
          class="shrink-0 text-xs text-red-500 border border-red-200 px-2 py-1 rounded-lg active:scale-95">
          Delete
        </button>
      </div>`
  }).join('')
}

function renderPagination(result) {
  document.getElementById('pagination-info').textContent =
    `Page ${result.page} of ${result.pages} — ${result.total} Pokémon`
  document.getElementById('btn-prev').disabled = result.page <= 1
  document.getElementById('btn-next').disabled = result.page >= result.pages
}

function changePage(delta) { loadPage(currentPage + delta) }

// ── Statistics ─────────────────────────────────────────────────────────────

async function loadStats() {
  const params = filterParams()
  try {
    const [avgRes, topRes, typesRes] = await Promise.all([
      fetch(`/api/stats/averages?${params}`),
      fetch(`/api/stats/top-experience?${params}`),
      fetch(`/api/stats/types-count?${params}`),
    ])
    const avg   = await avgRes.json()
    const top   = await topRes.json()
    const types = await typesRes.json()
    renderStats(avg, top, types)
  } catch (e) {
    console.error('Error loading stats:', e)
  }
}

function renderStats(avg, top, types) {
  document.getElementById('stat-total').textContent  = avg.total
  document.getElementById('stat-weight').textContent = `${avg.avg_weight_kg} kg`
  document.getElementById('stat-height').textContent = `${avg.avg_height_m} m`

  const topSection = document.getElementById('stat-top')
  if (top.name) {
    const badges = top.types.map(typeBadge).join(' ')
    topSection.innerHTML = `
      <div class="flex items-center gap-3">
        ${spriteImg(top.sprite, top.name)}
        <div>
          <p class="font-medium capitalize text-sm">${top.name}</p>
          <div class="flex gap-1 mt-0.5">${badges}</div>
        </div>
        <span class="ml-auto text-sm font-semibold text-amber-600">${top.base_experience} XP</span>
      </div>`
  } else {
    topSection.innerHTML = `<p class="text-sm text-gray-400">No data</p>`
  }

  document.getElementById('stat-types').innerHTML = Object.entries(types.data).map(([t, count]) => {
    const icon = typeIcons[t]
      ? `<img src="${typeIcons[t]}" alt="${t}" title="${t}" class="w-8 h-8 object-contain shrink-0" />`
      : `<span class="text-xs text-gray-500 capitalize">${t}</span>`
    return `
      <div class="flex items-center gap-1.5 bg-gray-50 rounded-lg px-2 py-1">
        ${icon}
        <span class="text-xs font-medium text-gray-700">${count}</span>
      </div>`
  }).join('')
}

// ── Actions ────────────────────────────────────────────────────────────────

function applyFilters() {
  activeFilters = {
    type1: document.getElementById('type1').value,
    type2: document.getElementById('type2').value,
    heavy: document.getElementById('heavy').checked,
  }
  currentPage = 1
  loadPage(1)
  loadStats()
}

async function deletePokemon(name) {
  const res = await fetch(`/api/pokemon/${name}`, { method: 'DELETE' })
  if (res.ok) {
    loadPage(currentPage)
    loadStats()
  }
}

async function restoreAll() {
  const res = await fetch('/api/pokemon/restore', { method: 'POST' })
  if (res.ok) {
    loadPage(1)
    loadStats()
  }
}

// ── Modale & Streaming ─────────────────────────────────────────────────────

async function openPokemonModal(name, spriteSrc) {
  document.body.classList.add('overflow-hidden');

  const modal = document.getElementById('pokemon-modal')
  const title = document.getElementById('modal-title')
  const sprite = document.getElementById('modal-sprite')
  const desc = document.getElementById('modal-description')
  const loading = document.getElementById('modal-loading')

  title.textContent = name
  sprite.src = spriteSrc
  sprite.alt = name
  modal.classList.remove('hidden')

  if (descriptionCache[name]) {
    desc.textContent = descriptionCache[name]
    loading.classList.add('hidden')
    return
  }

  desc.textContent = ''
  loading.classList.remove('hidden')

  try {
    const response = await fetch(`/api/pokemon/${name}/description`)
    if (!response.ok) throw new Error('Errore nella risposta del server')

    const reader = response.body.getReader()
    const decoder = new TextDecoder('utf-8')
    let fullText = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      const chunk = decoder.decode(value, { stream: true })
      fullText += chunk

      if (title.textContent === name) {
        desc.textContent = fullText
      }
    }

    descriptionCache[name] = fullText

  } catch (error) {
    console.error('Errore nel fetch della descrizione:', error)
    if (title.textContent === name) {
      desc.textContent = "Impossibile caricare la descrizione al momento."
    }
  } finally {
    if (title.textContent === name) {
      loading.classList.add('hidden')
    }
  }
}

function closePokemonModal() {
  document.getElementById('pokemon-modal').classList.add('hidden')
  document.body.classList.remove('overflow-hidden');
}

// ── Type selects ───────────────────────────────────────────────────────────

async function populateTypeSelects() {
  try {
    const res = await fetch('/api/pokemon/types')
    if (!res.ok) return
    const result = await res.json()
    typeIcons = result.data
    const types = Object.keys(result.data).sort()
    ;['type1', 'type2'].forEach(id => {
      const sel = document.getElementById(id)
      types.forEach(t => {
        const opt = document.createElement('option')
        opt.value = t
        opt.textContent = t.charAt(0).toUpperCase() + t.slice(1)
        sel.appendChild(opt)
      })
    })
  } catch (err) {
    console.error('Error loading types:', err)
  }
}

// ── Init ───────────────────────────────────────────────────────────────────

populateTypeSelects().then(() => {
  loadPage(1)
  loadStats()
})