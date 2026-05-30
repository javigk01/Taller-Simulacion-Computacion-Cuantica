import { useEffect, useState } from 'react'
import { getCuentas, createCuenta, deactivateCuenta, type Cuenta } from '../api'

function fmt(n: number) {
  return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(n)
}

function fmtAcct(num: string) {
  return num.replace(/(.{4})/g, '$1 ').trim()
}

export default function CuentasPage() {
  const [cuentas, setCuentas] = useState<Cuenta[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [titular, setTitular] = useState('')
  const [saldo, setSaldo] = useState('')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  const load = () => {
    setLoading(true)
    getCuentas()
      .then(setCuentas)
      .catch(() => setError('No se pudo conectar con el Transaction Service'))
      .finally(() => setLoading(false))
  }

  useEffect(load, [])

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    setSaving(true)
    setError('')
    try {
      await createCuenta(titular, parseFloat(saldo) || 0)
      setTitular('')
      setSaldo('')
      setShowForm(false)
      load()
    } catch (err: any) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  const handleDeactivate = async (id: number) => {
    if (!confirm('¿Desactivar esta cuenta?')) return
    try {
      await deactivateCuenta(id)
      load()
    } catch (err: any) {
      setError(err.message)
    }
  }

  return (
    <div className="slide-in">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-white">Cuentas Bancarias</h1>
          <p className="text-slate-400 text-sm mt-1">
            {cuentas.filter(c => c.estado === 'ACTIVA').length} activas · {cuentas.length} total
          </p>
        </div>
        <button
          onClick={() => setShowForm(v => !v)}
          className="flex items-center gap-2 px-4 py-2.5 bg-purple-600 hover:bg-purple-500 text-white rounded-xl font-medium text-sm transition-colors shadow-lg shadow-purple-900/40"
        >
          <span className="text-lg leading-none">+</span> Nueva Cuenta
        </button>
      </div>

      {/* Error */}
      {error && (
        <div className="mb-4 p-3 bg-red-950/50 border border-red-800 text-red-300 rounded-xl text-sm">
          {error}
        </div>
      )}

      {/* Create form */}
      {showForm && (
        <form
          onSubmit={handleCreate}
          className="mb-8 p-5 bg-slate-900 border border-slate-700 rounded-2xl slide-in"
        >
          <h2 className="font-semibold text-white mb-4">Nueva Cuenta</h2>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-xs text-slate-400 mb-1.5 block">Titular</label>
              <input
                value={titular}
                onChange={e => setTitular(e.target.value)}
                placeholder="Nombre completo"
                required
                className="w-full bg-slate-800 border border-slate-700 text-white rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:border-purple-500"
              />
            </div>
            <div>
              <label className="text-xs text-slate-400 mb-1.5 block">Saldo inicial (COP)</label>
              <input
                value={saldo}
                onChange={e => setSaldo(e.target.value)}
                type="number"
                min="0"
                placeholder="0"
                className="w-full bg-slate-800 border border-slate-700 text-white rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:border-purple-500"
              />
            </div>
          </div>
          <div className="flex gap-3 mt-4">
            <button
              type="submit"
              disabled={saving}
              className="px-4 py-2 bg-purple-600 hover:bg-purple-500 disabled:opacity-50 text-white rounded-lg text-sm font-medium transition-colors"
            >
              {saving ? 'Creando...' : 'Crear cuenta'}
            </button>
            <button
              type="button"
              onClick={() => setShowForm(false)}
              className="px-4 py-2 text-slate-400 hover:text-white bg-slate-800 hover:bg-slate-700 rounded-lg text-sm transition-colors"
            >
              Cancelar
            </button>
          </div>
        </form>
      )}

      {/* Loading */}
      {loading && (
        <div className="grid grid-cols-3 gap-4">
          {[1, 2, 3].map(i => (
            <div key={i} className="h-44 bg-slate-900 rounded-2xl animate-pulse border border-slate-800" />
          ))}
        </div>
      )}

      {/* Cards grid */}
      {!loading && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {cuentas.map(c => (
            <AccountCard key={c.id} cuenta={c} onDeactivate={handleDeactivate} />
          ))}
          {cuentas.length === 0 && (
            <div className="col-span-3 py-16 text-center text-slate-500">
              No hay cuentas. Crea la primera usando el botón de arriba.
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function AccountCard({ cuenta, onDeactivate }: { cuenta: Cuenta; onDeactivate: (id: number) => void }) {
  const active = cuenta.estado === 'ACTIVA'
  return (
    <div className={`relative p-5 rounded-2xl border transition-all ${
      active
        ? 'bg-slate-900 border-slate-700 hover:border-purple-700'
        : 'bg-slate-900/40 border-slate-800 opacity-60'
    }`}>
      {/* Status badge */}
      <div className="flex items-center justify-between mb-4">
        <span className={`text-xs font-medium px-2.5 py-1 rounded-full ${
          active ? 'bg-emerald-950 text-emerald-400 border border-emerald-900' : 'bg-slate-800 text-slate-500 border border-slate-700'
        }`}>
          {active ? '● ACTIVA' : '○ INACTIVA'}
        </span>
        <span className="text-xs text-slate-600 font-mono">#{cuenta.id}</span>
      </div>

      {/* Account number */}
      <p className="font-mono text-sm text-slate-400 tracking-widest mb-1">
        {fmtAcct(cuenta.numero_cuenta)}
      </p>

      {/* Holder */}
      <p className="font-semibold text-white text-base mb-3">{cuenta.titular}</p>

      {/* Balance */}
      <div className="py-3 border-t border-slate-800">
        <p className="text-xs text-slate-500 mb-0.5">Saldo disponible</p>
        <p className="text-2xl font-bold text-white">{fmt(cuenta.saldo)}</p>
      </div>

      {/* Actions */}
      {active && (
        <button
          onClick={() => onDeactivate(cuenta.id)}
          className="mt-3 w-full py-2 text-xs text-slate-500 hover:text-red-400 hover:bg-red-950/30 rounded-lg transition-colors border border-slate-800 hover:border-red-900"
        >
          Desactivar cuenta
        </button>
      )}
    </div>
  )
}
