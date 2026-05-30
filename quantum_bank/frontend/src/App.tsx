import { useState } from 'react'
import CuentasPage from './pages/CuentasPage'
import TransaccionesPage from './pages/TransaccionesPage'
import QKDLabPage from './pages/QKDLabPage'

type Tab = 'cuentas' | 'transferencias' | 'qkd'

const TABS: { id: Tab; label: string; icon: string }[] = [
  { id: 'cuentas',        label: 'Cuentas',        icon: '🏦' },
  { id: 'transferencias', label: 'Transferencias',  icon: '💸' },
  { id: 'qkd',            label: 'QKD Lab',         icon: '⚛️'  },
]

export default function App() {
  const [tab, setTab] = useState<Tab>('cuentas')

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      {/* ── Navbar ─────────────────────────────────────────────────────── */}
      <header className="sticky top-0 z-50 border-b border-slate-800 bg-slate-950/90 backdrop-blur-md">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          {/* Logo */}
          <div className="flex items-center gap-3">
            <div className="relative w-9 h-9 rounded-xl bg-gradient-to-br from-purple-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-purple-900/50">
              <span className="text-white font-bold text-base">Q</span>
            </div>
            <div>
              <span className="font-bold text-white text-lg tracking-tight">QuantumBank</span>
              <span className="ml-2 text-xs text-purple-400 font-mono bg-purple-950/60 px-2 py-0.5 rounded-full">
                BB84 QKD
              </span>
            </div>
          </div>

          {/* Tabs */}
          <nav className="flex gap-1 bg-slate-900 p-1 rounded-xl border border-slate-800">
            {TABS.map(t => (
              <button
                key={t.id}
                onClick={() => setTab(t.id)}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-150 ${
                  tab === t.id
                    ? 'bg-purple-600 text-white shadow-md shadow-purple-900/50'
                    : 'text-slate-400 hover:text-white hover:bg-slate-800'
                }`}
              >
                <span>{t.icon}</span>
                {t.label}
              </button>
            ))}
          </nav>

          {/* Status badges */}
          <div className="flex items-center gap-3 text-xs font-mono">
            <StatusDot label="txn :8000" />
            <StatusDot label="qkd :8001" color="blue" />
          </div>
        </div>
      </header>

      {/* ── Page content ───────────────────────────────────────────────── */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        {tab === 'cuentas'        && <CuentasPage />}
        {tab === 'transferencias' && <TransaccionesPage />}
        {tab === 'qkd'            && <QKDLabPage />}
      </main>
    </div>
  )
}

function StatusDot({ label, color = 'emerald' }: { label: string; color?: string }) {
  const dot = color === 'blue' ? 'bg-blue-400' : 'bg-emerald-400'
  const ring = color === 'blue' ? 'bg-blue-400/30' : 'bg-emerald-400/30'
  return (
    <div className="flex items-center gap-1.5 text-slate-500">
      <span className={`relative flex w-2 h-2`}>
        <span className={`animate-ping absolute inline-flex h-full w-full rounded-full ${ring}`} />
        <span className={`relative inline-flex rounded-full w-2 h-2 ${dot}`} />
      </span>
      {label}
    </div>
  )
}
