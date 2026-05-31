import { useEffect, useState } from 'react'
import {
  getCuentas, createCuenta, updateCuenta,
  reactivateCuenta, deactivateCuenta, permanentDeleteCuenta,
  type Cuenta,
} from '../api'

const fmt = (n: number) =>
  new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(n)

const fmtAcct = (num: string) => num.replace(/(.{4})/g, '$1 ').trim()

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
    } catch (err: any) { setError(err.message) }
    finally { setSaving(false) }
  }

  const handleUpdate = async (id: number, nuevoTitular: string) => {
    try { await updateCuenta(id, nuevoTitular); load() }
    catch (err: any) { setError(err.message) }
  }

  const handleReactivate = async (id: number) => {
    try { await reactivateCuenta(id); load() }
    catch (err: any) { setError(err.message) }
  }

  const handleDeactivate = async (id: number) => {
    if (!confirm('¿Desactivar esta cuenta?\nNo podrá usarse para transferencias hasta reactivarla.')) return
    try { await deactivateCuenta(id); load() }
    catch (err: any) { setError(err.message) }
  }

  const handlePermanentDelete = async (id: number, titular: string) => {
    if (!confirm(
      `¿Eliminar permanentemente la cuenta de "${titular}"?\n\n` +
      'Esta acción no se puede deshacer.\n' +
      'El historial de transacciones se conservará como registro de solo lectura.'
    )) return
    try { await permanentDeleteCuenta(id); load() }
    catch (err: any) { setError(err.message) }
  }

  const activas   = cuentas.filter(c => c.estado === 'ACTIVA')
  const inactivas = cuentas.filter(c => c.estado === 'INACTIVA')
  const eliminadas = cuentas.filter(c => c.estado === 'ELIMINADA')

  return (
    <div className="slide-in">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-white">Cuentas Bancarias</h1>
          <p className="text-slate-400 text-sm mt-1">
            {activas.length} activas · {inactivas.length} inactivas · {eliminadas.length} eliminadas
          </p>
        </div>
        <button
          onClick={() => setShowForm(v => !v)}
          className="flex items-center gap-2 px-4 py-2.5 bg-purple-600 hover:bg-purple-500 text-white rounded-xl font-medium text-sm transition-colors shadow-lg shadow-purple-900/40"
        >
          <span className="text-lg leading-none">+</span> Nueva Cuenta
        </button>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-950/50 border border-red-800 text-red-300 rounded-xl text-sm">{error}</div>
      )}

      {/* Create form */}
      {showForm && (
        <form onSubmit={handleCreate} className="mb-8 p-5 bg-slate-900 border border-slate-700 rounded-2xl slide-in">
          <h2 className="font-semibold text-white mb-4">Nueva Cuenta</h2>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-xs text-slate-400 mb-1.5 block">Titular</label>
              <input value={titular} onChange={e => setTitular(e.target.value)}
                placeholder="Nombre completo" required
                className="w-full bg-slate-800 border border-slate-700 text-white rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:border-purple-500" />
            </div>
            <div>
              <label className="text-xs text-slate-400 mb-1.5 block">Saldo inicial (COP)</label>
              <input value={saldo} onChange={e => setSaldo(e.target.value)}
                type="number" min="0" placeholder="0"
                className="w-full bg-slate-800 border border-slate-700 text-white rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:border-purple-500" />
            </div>
          </div>
          <div className="flex gap-3 mt-4">
            <button type="submit" disabled={saving}
              className="px-4 py-2 bg-purple-600 hover:bg-purple-500 disabled:opacity-50 text-white rounded-lg text-sm font-medium">
              {saving ? 'Creando...' : 'Crear cuenta'}
            </button>
            <button type="button" onClick={() => setShowForm(false)}
              className="px-4 py-2 text-slate-400 hover:text-white bg-slate-800 hover:bg-slate-700 rounded-lg text-sm">
              Cancelar
            </button>
          </div>
        </form>
      )}

      {loading && (
        <div className="grid grid-cols-3 gap-4">
          {[1, 2, 3].map(i => <div key={i} className="h-44 bg-slate-900 rounded-2xl animate-pulse border border-slate-800" />)}
        </div>
      )}

      {!loading && (
        <>
          {/* Activas + Inactivas */}
          {(activas.length > 0 || inactivas.length > 0) && (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
              {[...activas, ...inactivas].map(c => (
                <AccountCard
                  key={c.id}
                  cuenta={c}
                  onUpdate={handleUpdate}
                  onReactivate={handleReactivate}
                  onDeactivate={handleDeactivate}
                  onPermanentDelete={handlePermanentDelete}
                />
              ))}
            </div>
          )}

          {/* Eliminadas (al final, colapsadas) */}
          {eliminadas.length > 0 && (
            <EliminadasSection cuentas={eliminadas} />
          )}

          {cuentas.length === 0 && (
            <div className="py-16 text-center text-slate-500">No hay cuentas. Crea la primera.</div>
          )}
        </>
      )}
    </div>
  )
}

// ── AccountCard ───────────────────────────────────────────────────────────────

function AccountCard({
  cuenta, onUpdate, onReactivate, onDeactivate, onPermanentDelete,
}: {
  cuenta: Cuenta
  onUpdate: (id: number, titular: string) => Promise<void>
  onReactivate: (id: number) => void
  onDeactivate: (id: number) => void
  onPermanentDelete: (id: number, titular: string) => void
}) {
  const [editing, setEditing]       = useState(false)
  const [newTitular, setNewTitular] = useState(cuenta.titular)
  const [saving, setSaving]         = useState(false)

  const isActiva  = cuenta.estado === 'ACTIVA'
  const isInactiva = cuenta.estado === 'INACTIVA'

  const handleSave = async () => {
    if (!newTitular.trim() || newTitular === cuenta.titular) { setEditing(false); return }
    setSaving(true)
    await onUpdate(cuenta.id, newTitular)
    setSaving(false)
    setEditing(false)
  }

  const borderColor = isActiva
    ? 'border-slate-700 hover:border-purple-700'
    : 'border-slate-800 border-dashed'

  return (
    <div className={`relative p-5 rounded-2xl border bg-slate-900 transition-all ${borderColor}`}>
      {/* Status */}
      <div className="flex items-center justify-between mb-4">
        <span className={`text-xs font-medium px-2.5 py-1 rounded-full border ${
          isActiva
            ? 'bg-emerald-950 text-emerald-400 border-emerald-900'
            : 'bg-slate-800 text-slate-500 border-slate-700'
        }`}>
          {isActiva ? '● ACTIVA' : '○ INACTIVA'}
        </span>
        <span className="text-xs text-slate-600 font-mono">#{cuenta.id}</span>
      </div>

      <p className="font-mono text-sm text-slate-400 tracking-widest mb-1">{fmtAcct(cuenta.numero_cuenta)}</p>

      {/* Titular — inline edit */}
      {editing ? (
        <div className="flex gap-2 mb-3">
          <input value={newTitular} onChange={e => setNewTitular(e.target.value)} autoFocus
            className="flex-1 bg-slate-800 border border-purple-600 text-white rounded-lg px-2 py-1 text-sm focus:outline-none" />
          <button onClick={handleSave} disabled={saving}
            className="px-2 py-1 bg-purple-600 hover:bg-purple-500 text-white rounded-lg text-xs disabled:opacity-50">
            {saving ? '...' : '✓'}
          </button>
          <button onClick={() => { setEditing(false); setNewTitular(cuenta.titular) }}
            className="px-2 py-1 bg-slate-700 text-slate-300 rounded-lg text-xs">✕</button>
        </div>
      ) : (
        <p className={`font-semibold text-base mb-3 ${isActiva ? 'text-white' : 'text-slate-400'}`}>
          {cuenta.titular}
        </p>
      )}

      {/* Balance */}
      <div className="py-3 border-t border-slate-800">
        <p className="text-xs text-slate-500 mb-0.5">Saldo</p>
        <p className={`text-2xl font-bold ${isActiva ? 'text-white' : 'text-slate-500'}`}>
          {fmt(cuenta.saldo)}
        </p>
      </div>

      {/* Actions */}
      {!editing && (
        <div className="mt-3 space-y-2">
          {isActiva && (
            <div className="flex gap-2">
              <button onClick={() => setEditing(true)}
                className="flex-1 py-2 text-xs text-slate-400 hover:text-purple-300 hover:bg-purple-950/30 rounded-lg border border-slate-800 hover:border-purple-800 transition-colors">
                ✏️ Editar
              </button>
              <button onClick={() => onDeactivate(cuenta.id)}
                className="flex-1 py-2 text-xs text-slate-400 hover:text-amber-400 hover:bg-amber-950/30 rounded-lg border border-slate-800 hover:border-amber-900 transition-colors">
                ⏸ Desactivar
              </button>
            </div>
          )}
          {isInactiva && (
            <button onClick={() => onReactivate(cuenta.id)}
              className="w-full py-2 text-xs text-slate-400 hover:text-emerald-400 hover:bg-emerald-950/30 rounded-lg border border-slate-800 hover:border-emerald-900 transition-colors">
              ▶️ Reactivar
            </button>
          )}
          {/* Permanent delete always available for non-deleted accounts */}
          <button onClick={() => onPermanentDelete(cuenta.id, cuenta.titular)}
            className="w-full py-2 text-xs text-slate-600 hover:text-red-400 hover:bg-red-950/20 rounded-lg border border-slate-800 hover:border-red-900 transition-colors">
            💀 Eliminar permanentemente
          </button>
        </div>
      )}
    </div>
  )
}

// ── Sección de cuentas eliminadas (colapsable) ────────────────────────────────

function EliminadasSection({ cuentas }: { cuentas: Cuenta[] }) {
  const [open, setOpen] = useState(false)
  return (
    <div className="mt-4">
      <button
        onClick={() => setOpen(v => !v)}
        className="flex items-center gap-2 text-sm text-slate-500 hover:text-slate-300 transition-colors mb-3"
      >
        <span className={`transition-transform ${open ? 'rotate-90' : ''}`}>▶</span>
        {cuentas.length} cuenta{cuentas.length !== 1 ? 's' : ''} eliminada{cuentas.length !== 1 ? 's' : ''} — solo lectura
      </button>
      {open && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 slide-in">
          {cuentas.map(c => (
            <div key={c.id}
              className="p-5 rounded-2xl border border-slate-800 bg-slate-900/30 opacity-50">
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-medium px-2.5 py-1 rounded-full bg-slate-800 text-red-500 border border-red-900/50">
                  ✕ ELIMINADA
                </span>
                <span className="text-xs text-slate-700 font-mono">#{c.id}</span>
              </div>
              <p className="font-mono text-xs text-slate-600 tracking-widest mb-1">{fmtAcct(c.numero_cuenta)}</p>
              <p className="font-semibold text-slate-500 text-sm mb-2">{c.titular}</p>
              <p className="text-xs text-slate-600">Historial conservado · sin acciones disponibles</p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
