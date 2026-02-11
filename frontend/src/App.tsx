import { useEffect, useMemo, useState } from 'react'

const API = 'http://localhost:8000/api'
const workChips = ['Meeting', 'Customer', 'Enablement', 'Collateral', 'Internal', 'Learning', 'Admin']
const playChips = ['GCVE', 'GDC', 'GKE', 'Vertex', 'FinOps', 'AI Readiness', 'Other']

type Account = { id: number; name: string }
type Deal = { id: number; account_id: number; name: string; stage: string }

export function App() {
  const [tab, setTab] = useState<'Home'|'Deals'|'Search'|'Reports'|'Settings'>('Home')
  const [accounts, setAccounts] = useState<Account[]>([])
  const [deals, setDeals] = useState<Deal[]>([])
  const [home, setHome] = useState<any>(null)
  const [query, setQuery] = useState('')
  const [search, setSearch] = useState<any>(null)

  const [note, setNote] = useState('')
  const [title, setTitle] = useState('Quick log')
  const [type, setType] = useState('Meeting')
  const [play, setPlay] = useState('Other')
  const [accountId, setAccountId] = useState<number | ''>('')
  const [dealId, setDealId] = useState<number | ''>('')
  const [duration, setDuration] = useState(15)
  const [outcomes, setOutcomes] = useState<string[]>([])
  const [weekly, setWeekly] = useState<any>(null)
  const [monthly, setMonthly] = useState<any>(null)

  useEffect(() => { init() }, [])
  useEffect(() => { fetchHome() }, [])

  async function init() {
    await fetch(`${API}/init`, { method: 'POST' })
    const [a, d] = await Promise.all([fetch(`${API}/accounts`).then(r => r.json()), fetch(`${API}/deals`).then(r => r.json())])
    setAccounts(a); setDeals(d)
  }

  async function fetchHome() { setHome(await fetch(`${API}/home`).then(r => r.json())) }

  const filteredDeals = useMemo(() => deals.filter(d => !accountId || d.account_id === accountId), [deals, accountId])

  async function saveEntry() {
    const payload = { type: type.toLowerCase(), title, raw_note: `[${play}] ${note}`, account_id: accountId || null, deal_id: dealId || null, duration_min: duration }
    const res = await fetch(`${API}/entries`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) }).then(r => r.json())
    setOutcomes(res.outcomes || [])
    setNote('')
    fetchHome()
  }

  async function generateWeekly() {
    const data = await fetch(`${API}/generate/weekly`, { method: 'POST' }).then(r => r.json())
    setWeekly(data)
    await navigator.clipboard.writeText(`Teams:\n${data.teams}\n\nEmail:\n${data.email_subject}\n${data.email_body}\n\nSlides:\n${data.slide_bullets}`)
  }

  async function generateMonthly() {
    const data = await fetch(`${API}/generate/monthly`, { method: 'POST' }).then(r => r.json())
    setMonthly(data)
    await navigator.clipboard.writeText(`Teams:\n${data.teams}\n\nEmail:\n${data.email_subject}\n${data.email_body}\n\nSlides:\n${data.slide_bullets}`)
  }

  async function generateSlides() {
    const data = await fetch(`${API}/generate/slides`, { method: 'POST' }).then(r => r.json())
    await navigator.clipboard.writeText(data.slide_bullets)
    alert('Slide bullets copied')
  }

  async function doSearch() { setSearch(await fetch(`${API}/search?q=${encodeURIComponent(query)}`).then(r => r.json())) }

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.ctrlKey && e.key === 'Enter' && tab === 'Home') { e.preventDefault(); saveEntry() }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  })

  return <div className="app">
    <h1>Local-First Worklog</h1>
    <div className="tabs">{['Home', 'Deals', 'Search', 'Reports', 'Settings'].map(t => <button key={t} className={tab===t?'active':''} onClick={() => setTab(t as any)}>{t}</button>)}</div>

    {tab === 'Home' && <div className="grid">
      <section className="card">
        <h2>Quick Capture</h2>
        <input value={title} onChange={e => setTitle(e.target.value)} placeholder="Title" />
        <textarea value={note} onChange={e => setNote(e.target.value)} placeholder="What did you do? (Ctrl+Enter to save)" rows={5} />
        <div className="chips">{workChips.map(ch => <button key={ch} onClick={() => setType(ch)} className={type===ch?'chip active':'chip'}>{ch}</button>)}</div>
        <div className="chips">{playChips.map(ch => <button key={ch} onClick={() => setPlay(ch)} className={play===ch?'chip active':'chip'}>{ch}</button>)}</div>
        <div className="row">
          <select value={accountId} onChange={e => setAccountId(e.target.value ? Number(e.target.value) : '')}><option value="">Account (optional)</option>{accounts.map(a => <option key={a.id} value={a.id}>{a.name}</option>)}</select>
          <select value={dealId} onChange={e => setDealId(e.target.value ? Number(e.target.value) : '')}><option value="">Deal (optional)</option>{filteredDeals.map(d => <option key={d.id} value={d.id}>{d.name}</option>)}</select>
        </div>
        <div className="chips">{[5,15,30,60].map(d => <button key={d} onClick={() => setDuration(d)} className={duration===d?'chip active':'chip'}>{d}</button>)}</div>
        <button className="primary" onClick={saveEntry}>Save</button>
        {!!outcomes.length && <div><h3>Suggested Outcomes</h3><ul>{outcomes.map((o, i) => <li key={i}>{o} <button>Edit</button> <button>Accept</button></li>)}</ul></div>}
      </section>

      <section className="card">
        <h2>Today at a glance</h2>
        <ul>
          <li>Time logged: {home?.today?.time_logged ?? 0} min</li>
          <li># entries: {home?.today?.entries ?? 0}</li>
          <li># accounts touched: {home?.today?.accounts_touched ?? 0}</li>
          <li># deals touched: {home?.today?.deals_touched ?? 0}</li>
          <li>Follow-ups due: {home?.today?.followups_due ?? 0}</li>
        </ul>
        <h3>Due this week</h3>
        <ul>{home?.due_this_week?.followups?.map((f: any) => <li key={f.id}>{f.title} ({f.due_date})</li>)}</ul>
        <ul>{home?.due_this_week?.deals?.map((d: any) => <li key={d.id}>{d.name}: {d.next_step} ({d.next_step_date})</li>)}</ul>
      </section>

      <section className="card full">
        <h2>One-click Generation</h2>
        <div className="row">
          <button className="primary" onClick={generateWeekly}>Generate Weekly Update</button>
          <button className="primary" onClick={generateMonthly}>Generate Monthly Summary</button>
          <button className="primary" onClick={generateSlides}>Generate Slide Bullets</button>
        </div>
        {weekly && <pre>{weekly.teams}</pre>}
        {monthly && <pre>{monthly.teams}</pre>}
      </section>
    </div>}

    {tab === 'Deals' && <section className="card"><h2>Deals (lightweight)</h2><ul>{deals.map(d => <li key={d.id}>{d.name} — {d.stage}</li>)}</ul></section>}
    {tab === 'Search' && <section className="card"><h2>Search</h2><div className="row"><input value={query} onChange={e => setQuery(e.target.value)} /><button onClick={doSearch}>Search</button></div><pre>{JSON.stringify(search, null, 2)}</pre></section>}
    {tab === 'Reports' && <section className="card"><h2>Reports & Exports</h2><ul>
      <li><a href={`${API}/export/weekly/md`} target="_blank">Export Weekly Markdown</a></li>
      <li><a href={`${API}/export/weekly/pdf`} target="_blank">Export Weekly PDF</a></li>
      <li><a href={`${API}/export/monthly/md`} target="_blank">Export Monthly Markdown</a></li>
      <li><a href={`${API}/export/monthly/pdf`} target="_blank">Export Monthly PDF</a></li>
      <li><a href={`${API}/export/entries/csv`} target="_blank">Export Entries CSV</a></li>
      <li><a href={`${API}/export/deals/csv`} target="_blank">Export Deals CSV</a></li>
      <li><a href={`${API}/export/assets/csv`} target="_blank">Export Assets CSV</a></li>
    </ul></section>}
    {tab === 'Settings' && <section className="card"><h2>Settings</h2><p>Template/rules/cadence schedule are editable via backend tables and defaults seeded.</p></section>}
  </div>
}
