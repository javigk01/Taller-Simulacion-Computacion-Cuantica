import { useEffect, useState, useRef } from 'react'
import {
  getCuentas, getTransacciones,
  createTransaccion, updateTransaccion, deleteTransaccion, descifrarTransaccion,
  type Cuenta, type Transaccion, type TransaccionDecifrada,
} from '../api'

// ── Helpers ───────────────────────────────────────────────────────────────────

const BB84_STEPS = [
  { icon: '⚛️',  text: 'Iniciando protocolo BB84...' },
  { icon: '🎲',  text: 'Alice genera bits y bases aleatorias (384 qubits)' },
  { icon: '🔬',  text: 'AerSimulator ejecuta el circuito cuántico...' },
  { icon: '📡',  text: 'Bob mide en bases aleatorias' },
  { icon: '⚖️',  text: 'Sifting: descartando bases no coincidentes (~50%)' },
  { icon: '🔍',  text: 'Verificando QBER — chequeando canal por espías...' },
  { icon: '🔐',  text: 'Clave cuántica segura. Cifrando con AES-256-GCM...' },
]

const fmt = (n: number) =>
  new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(n)

const fmtDate = (s: string) =>
  new Date(s).toLocaleString('es-CO', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' })

// ── Main component ────────────────────────────────────────────────────────────

export default function TransaccionesPage() {
  const [allCuentas, setAllCuentas] = useState<Cuenta[]>([])
  const [txns, setTxns]            = useState<Transaccion[]>([])
  // Active accounts only — for dropdowns
  const cuentas = allCuentas.filter(c => c.estado === 'ACTIVA')

  // Create form
  const [origen,   setOrigen]   = useState('')
  const [destino,  setDestino]  = useState('')
  const [monto,    setMonto]    = useState('')
  const [concepto, setConcepto] = useState('')
  const [loading,  setLoading]  = useState(false)
  const [step,     setStep]     = useState(-1)
  const [lastTxn,  setLastTxn]  = useState<Transaccion | null>(null)
  const [error,    setError]    = useState('')
  const stepRef = useRef<ReturnType<typeof setInterval> | null>(null)

  // Per-row state
  const [decrypted,   setDecrypted]   = useState<Record<number, TransaccionDecifrada | null>>({})
  const [decrypting,  setDecrypting]  = useState<number | null>(null)
  const [editingId,   setEditingId]   = useState<number | null>(null)
  const [deletingId,  setDeletingId]  = useState<number | null>(null)

  const load = async () => {
    const [c, t] = await Promise.all([getCuentas(), getTransacciones()])
    setAllCuentas(c)   // all states — needed to detect ELIMINADA accounts in history
    setTxns(t)
  }

  useEffect(() => { load() }, [])

  // ── BB84 animation helper ───────────────────────────────────────────────────
  const startAnimation = () => {
    setStep(0)
    let s = 0
    stepRef.current = setInterval(() => {
      s++
      if (s < BB84_STEPS.length - 1) setStep(s)
      else if (stepRef.current) clearInterval(stepRef.current)
    }, 550)
  }
  const stopAnimation = (success: boolean) => {
    if (stepRef.current) clearInterval(stepRef.current)
    setStep(success ? BB84_STEPS.length - 1 : -1)
  }

  // ── Create ──────────────────────────────────────────────────────────────────
  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLastTxn(null)
    setLoading(true)
    startAnimation()
    try {
      const txn = await createTransaccion(parseInt(origen), parseInt(destino), parseFloat(monto), concepto)
      stopAnimation(true)
      setLastTxn(txn)
      setMonto('')
      setConcepto('')
      await load()
    } catch (err: any) {
      stopAnimation(false)
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  // ── Delete ──────────────────────────────────────────────────────────────────
  const handleDelete = async (txn: Transaccion) => {
    const completada = txn.estado === 'COMPLETADA'
    const msg = completada
      ? `¿Eliminar la transacción #${txn.id}?\n\nSe revertirá ${fmt(txn.monto)} a la cuenta origen.`
      : `¿Eliminar la transacción #${txn.id}?`
    if (!confirm(msg)) return
    setDeletingId(txn.id)
    setError('')
    try {
      await deleteTransaccion(txn.id)
      await load()
    } catch (err: any) {
      setError(err.message)
    } finally {
      setDeletingId(null)
    }
  }

  // ── Decrypt ─────────────────────────────────────────────────────────────────
  const handleDecrypt = async (id: number) => {
    setDecrypting(id)
    try {
      const res = await descifrarTransaccion(id)
      setDecrypted(prev => ({ ...prev, [id]: res }))
    } catch (err: any) {
      setError(err.message)
    } finally {
      setDecrypting(null)
    }
  }

  return (
    <div className="slide-in grid grid-cols-5 gap-6">

      {/* ── Left: create form ───────────────────────────────────────────── */}
      <div className="col-span-2">
        <h1 className="text-2xl font-bold text-white mb-1">Transferencia</h1>
        <p className="text-slate-400 text-sm mb-6">Cifrada con clave cuántica BB84</p>

        {error && (
          <div className="mb-4 p-3 bg-red-950/50 border border-red-800 text-red-300 rounded-xl text-sm">
            {error}
          </div>
        )}

        {/* BB84 animation */}
        {loading && step >= 0 && (
          <div className="mb-6 p-4 bg-purple-950/40 border border-purple-800/50 rounded-2xl slide-in">
            <p className="text-xs font-medium text-purple-300 mb-3 uppercase tracking-wider">
              Protocolo BB84 — Qiskit AerSimulator
            </p>
            <div className="space-y-2">
              {BB84_STEPS.map((s, i) => (
                <div key={i} className={`flex items-center gap-2.5 text-sm transition-all duration-300 ${
                  i < step ? 'text-emerald-400' : i === step ? 'text-white' : 'text-slate-600'
                }`}>
                  <span className="w-5 text-center">
                    {i < step ? '✓' : i === step
                      ? <span className="inline-block w-4 h-4 border-2 border-purple-400 border-t-transparent rounded-full animate-spin" />
                      : '·'}
                  </span>
                  <span className="mr-1">{s.icon}</span>{s.text}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Success badge */}
        {lastTxn && !loading && (
          <div className="mb-6 p-4 bg-emerald-950/40 border border-emerald-800/50 rounded-2xl slide-in">
            <p className="text-emerald-400 font-semibold text-sm mb-3">✓ Transferencia completada</p>
            <div className="space-y-1.5 text-xs">
              <InfoRow label="ID"      value={`#${lastTxn.id}`} />
              <InfoRow label="Monto"   value={fmt(lastTxn.monto)} />
              <InfoRow label="Session" value={(lastTxn.qkd_session_id ?? '').slice(0, 18) + '...'} mono />
              <InfoRow label="Payload" value={(lastTxn.payload_cifrado ?? '').slice(0, 24) + '...'} mono />
            </div>
          </div>
        )}

        {/* Create form */}
        {!loading && (
          <form onSubmit={handleCreate} className="space-y-4">
            <SelectCuenta label="Cuenta origen"  value={origen}  onChange={setOrigen}  cuentas={cuentas} />
            <SelectCuenta label="Cuenta destino" value={destino} onChange={setDestino}
              cuentas={cuentas.filter(c => c.id !== parseInt(origen))} />
            <div>
              <label className="text-xs text-slate-400 mb-1.5 block">Monto (COP)</label>
              <input value={monto} onChange={e => setMonto(e.target.value)}
                type="number" min="1" required placeholder="250000"
                className="w-full bg-slate-800 border border-slate-700 text-white rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:border-purple-500" />
            </div>
            <div>
              <label className="text-xs text-slate-400 mb-1.5 block">Concepto</label>
              <input value={concepto} onChange={e => setConcepto(e.target.value)}
                required placeholder="Ej: Pago cuota universitaria"
                className="w-full bg-slate-800 border border-slate-700 text-white rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:border-purple-500" />
            </div>
            <button type="submit"
              className="w-full py-3 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white rounded-xl font-semibold text-sm transition-all shadow-lg shadow-purple-900/40">
              ⚛️ Transferir con BB84
            </button>
          </form>
        )}
      </div>

      {/* ── Right: transaction list ─────────────────────────────────────── */}
      <div className="col-span-3">
        <h2 className="text-xl font-bold text-white mb-1">Historial</h2>
        <p className="text-slate-400 text-sm mb-6">{txns.length} transacciones</p>

        <div className="space-y-3">
          {txns.length === 0 && (
            <div className="py-16 text-center text-slate-600">Aún no hay transacciones.</div>
          )}
          {txns.map(t => (
            <TxnRow
              key={t.id}
              txn={t}
              cuentas={cuentas}
              allCuentas={allCuentas}
              isEditing={editingId === t.id}
              onEditOpen={() => setEditingId(t.id)}
              onEditClose={() => setEditingId(null)}
              onEditSave={async (id, data) => {
                await updateTransaccion(id, data)
                setEditingId(null)
                await load()
              }}
              isDeleting={deletingId === t.id}
              onDelete={handleDelete}
              isDecrypting={decrypting === t.id}
              onDecrypt={handleDecrypt}
              decryptedData={decrypted[t.id]}
            />
          ))}
        </div>
      </div>
    </div>
  )
}

// ── Sub-components ────────────────────────────────────────────────────────────

function SelectCuenta({
  label, value, onChange, cuentas,
}: { label: string; value: string; onChange: (v: string) => void; cuentas: Cuenta[] }) {
  return (
    <div>
      <label className="text-xs text-slate-400 mb-1.5 block">{label}</label>
      <select value={value} onChange={e => onChange(e.target.value)} required
        className="w-full bg-slate-800 border border-slate-700 text-white rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:border-purple-500">
        <option value="">Seleccionar...</option>
        {cuentas.map(c => (
          <option key={c.id} value={c.id}>{c.titular} · {new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(c.saldo)}</option>
        ))}
      </select>
    </div>
  )
}

function TxnRow({
  txn, cuentas, allCuentas,
  isEditing, onEditOpen, onEditClose, onEditSave,
  isDeleting, onDelete,
  isDecrypting, onDecrypt, decryptedData,
}: {
  txn: Transaccion
  cuentas: Cuenta[]
  allCuentas: Cuenta[]
  isEditing: boolean
  onEditOpen: () => void
  onEditClose: () => void
  onEditSave: (id: number, data: any) => Promise<void>
  isDeleting: boolean
  onDelete: (txn: Transaccion) => void
  isDecrypting: boolean
  onDecrypt: (id: number) => void
  decryptedData?: TransaccionDecifrada | null
}) {
  const [showDecrypt, setShowDecrypt] = useState(false)

  // A transaction is read-only if either account was permanently deleted
  const cuentaOrigen  = allCuentas.find(c => c.id === txn.cuenta_origen_id)
  const cuentaDestino = allCuentas.find(c => c.id === txn.cuenta_destino_id)
  const readOnly = cuentaOrigen?.estado === 'ELIMINADA' || cuentaDestino?.estado === 'ELIMINADA'

  const origenNombre  = cuentaOrigen?.titular  ?? `Cuenta ${txn.cuenta_origen_id}`
  const destinoNombre = cuentaDestino?.titular ?? `Cuenta ${txn.cuenta_destino_id}`

  // Edit form state (pre-filled with current values)
  const [eOrigen,   setEOrigen]   = useState(String(txn.cuenta_origen_id))
  const [eDestino,  setEDestino]  = useState(String(txn.cuenta_destino_id))
  const [eMonto,    setEMonto]    = useState(String(txn.monto))
  const [eConcepto, setEConcepto] = useState(txn.concepto)
  const [saving,    setSaving]    = useState(false)
  const [editErr,   setEditErr]   = useState('')

  const handleSave = async () => {
    setSaving(true)
    setEditErr('')
    try {
      await onEditSave(txn.id, {
        cuenta_origen_id:  parseInt(eOrigen)  !== txn.cuenta_origen_id  ? parseInt(eOrigen)  : undefined,
        cuenta_destino_id: parseInt(eDestino) !== txn.cuenta_destino_id ? parseInt(eDestino) : undefined,
        monto:    parseFloat(eMonto)  !== txn.monto   ? parseFloat(eMonto)  : undefined,
        concepto: eConcepto           !== txn.concepto ? eConcepto           : undefined,
      })
    } catch (err: any) {
      setEditErr(err.message)
    } finally {
      setSaving(false)
    }
  }

  const completada = txn.estado === 'COMPLETADA'

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden hover:border-slate-700 transition-colors">
      {/* Row header */}
      <div className="flex items-center justify-between px-4 py-3">
        <div className="flex items-center gap-3">
          <span className="text-slate-600 font-mono text-xs">#{txn.id}</span>
          <div>
            <div className="flex items-center gap-2 text-sm font-medium text-white flex-wrap">
              <span className={cuentaOrigen?.estado === 'ELIMINADA' ? 'text-red-400 line-through' : ''}>
                {origenNombre}
              </span>
              <span className="text-slate-500">→</span>
              <span className={cuentaDestino?.estado === 'ELIMINADA' ? 'text-red-400 line-through' : ''}>
                {destinoNombre}
              </span>
              {readOnly && (
                <span className="text-xs px-2 py-0.5 rounded-full bg-red-950 text-red-400 border border-red-900 font-normal">
                  🔒 solo lectura
                </span>
              )}
            </div>
            <p className="text-xs text-slate-500 mt-0.5">{txn.concepto} · {fmtDate(txn.timestamp)}</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="font-bold text-white">{fmt(txn.monto)}</span>
          <span className={`text-xs px-2 py-0.5 rounded-full font-medium border ${
            completada
              ? 'bg-emerald-950 text-emerald-400 border-emerald-900'
              : 'bg-slate-800 text-slate-400 border-slate-700'
          }`}>{txn.estado}</span>

          {/* Descifrar */}
          <button
            onClick={() => { setShowDecrypt(v => !v); if (!decryptedData && !showDecrypt) onDecrypt(txn.id) }}
            className="text-xs px-2.5 py-1.5 bg-slate-800 hover:bg-purple-900/50 text-slate-400 hover:text-purple-300 border border-slate-700 hover:border-purple-700 rounded-lg transition-colors"
          >
            {isDecrypting ? '...' : showDecrypt ? '🔒' : '🔓'}
          </button>

          {/* Editar — disabled when read-only */}
          <button
            onClick={readOnly ? undefined : (isEditing ? onEditClose : onEditOpen)}
            disabled={readOnly}
            title={readOnly ? 'Transacción de solo lectura: una cuenta fue eliminada' : 'Editar transacción'}
            className={`text-xs px-2.5 py-1.5 border rounded-lg transition-colors ${
              readOnly
                ? 'bg-slate-900 text-slate-700 border-slate-800 cursor-not-allowed'
                : isEditing
                  ? 'bg-purple-900/50 text-purple-300 border-purple-700'
                  : 'bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white border-slate-700'
            }`}
          >
            ✏️
          </button>

          {/* Eliminar */}
          <button
            onClick={() => onDelete(txn)}
            disabled={isDeleting}
            title={completada ? 'Eliminar y revertir saldo' : 'Eliminar'}
            className="text-xs px-2.5 py-1.5 bg-slate-800 hover:bg-red-950/50 text-slate-400 hover:text-red-400 border border-slate-700 hover:border-red-900 rounded-lg transition-colors disabled:opacity-40"
          >
            {isDeleting ? '...' : completada ? '↩️' : '🗑️'}
          </button>
        </div>
      </div>

      {/* Edit form */}
      {isEditing && (
        <div className="border-t border-slate-800 px-4 py-4 bg-slate-950/60 slide-in">
          {completada && (
            <div className="mb-3 p-2.5 bg-amber-950/40 border border-amber-800/50 rounded-lg text-xs text-amber-300">
              ⚠️ Modificar esta transacción ajustará los saldos de las cuentas involucradas automáticamente.
            </div>
          )}
          {editErr && (
            <div className="mb-3 p-2.5 bg-red-950/50 border border-red-800 text-red-300 rounded-lg text-xs">{editErr}</div>
          )}
          <div className="grid grid-cols-2 gap-3 mb-3">
            <div>
              <label className="text-xs text-slate-400 mb-1 block">Cuenta origen</label>
              <select value={eOrigen} onChange={e => setEOrigen(e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 text-white rounded-lg px-2 py-2 text-xs focus:outline-none focus:border-purple-500">
                {[...cuentas, ...(cuentas.find(c => c.id === txn.cuenta_origen_id) ? [] : [{ id: txn.cuenta_origen_id, titular: `Cuenta ${txn.cuenta_origen_id}`, saldo: 0, estado: 'ACTIVA', numero_cuenta: '', creado_en: '' } as Cuenta])].map(c => (
                  <option key={c.id} value={c.id}>{c.titular || `Cuenta ${c.id}`}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-xs text-slate-400 mb-1 block">Cuenta destino</label>
              <select value={eDestino} onChange={e => setEDestino(e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 text-white rounded-lg px-2 py-2 text-xs focus:outline-none focus:border-purple-500">
                {[...cuentas, ...(cuentas.find(c => c.id === txn.cuenta_destino_id) ? [] : [{ id: txn.cuenta_destino_id, titular: `Cuenta ${txn.cuenta_destino_id}`, saldo: 0, estado: 'ACTIVA', numero_cuenta: '', creado_en: '' } as Cuenta])].map(c => (
                  <option key={c.id} value={c.id}>{c.titular || `Cuenta ${c.id}`}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-xs text-slate-400 mb-1 block">Monto (COP)</label>
              <input value={eMonto} onChange={e => setEMonto(e.target.value)} type="number" min="1"
                className="w-full bg-slate-800 border border-slate-700 text-white rounded-lg px-2 py-2 text-xs focus:outline-none focus:border-purple-500" />
            </div>
            <div>
              <label className="text-xs text-slate-400 mb-1 block">Concepto</label>
              <input value={eConcepto} onChange={e => setEConcepto(e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 text-white rounded-lg px-2 py-2 text-xs focus:outline-none focus:border-purple-500" />
            </div>
          </div>
          <div className="flex gap-2">
            <button onClick={handleSave} disabled={saving}
              className="px-3 py-1.5 bg-purple-600 hover:bg-purple-500 disabled:opacity-50 text-white rounded-lg text-xs font-medium transition-colors">
              {saving ? 'Guardando...' : '💾 Guardar cambios'}
            </button>
            <button onClick={onEditClose}
              className="px-3 py-1.5 bg-slate-700 hover:bg-slate-600 text-slate-300 rounded-lg text-xs transition-colors">
              Cancelar
            </button>
          </div>
        </div>
      )}

      {/* Decrypt panel */}
      {showDecrypt && !isEditing && (
        <div className="border-t border-slate-800 px-4 py-3 bg-slate-950/50 slide-in">
          {isDecrypting && <p className="text-sm text-slate-500 animate-pulse">Recuperando clave del QKD Service...</p>}
          {decryptedData?.payload_descifrado && (
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-xs text-slate-500 mb-2 uppercase tracking-wider">Payload descifrado</p>
                <div className="space-y-1.5 text-xs">
                  <InfoRow label="Monto"    value={decryptedData.payload_descifrado.monto} />
                  <InfoRow label="Concepto" value={decryptedData.payload_descifrado.concepto} />
                  <InfoRow label="Origen"   value={decryptedData.payload_descifrado.cuenta_origen} mono />
                  <InfoRow label="Destino"  value={decryptedData.payload_descifrado.cuenta_destino} mono />
                </div>
              </div>
              <div>
                <p className="text-xs text-slate-500 mb-2 uppercase tracking-wider">Payload cifrado</p>
                <p className="font-mono text-xs text-slate-600 break-all">{(txn.payload_cifrado ?? '').slice(0, 100)}...</p>
                <p className="text-xs text-purple-400 mt-2">🔑 {(txn.qkd_session_id ?? '').slice(0, 20)}...</p>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function InfoRow({ label, value, mono = false }: { label: string; value: string; mono?: boolean }) {
  return (
    <div className="flex items-baseline gap-2">
      <span className="text-slate-500 text-xs w-20 shrink-0">{label}</span>
      <span className={`text-slate-200 text-xs ${mono ? 'font-mono' : ''}`}>{value}</span>
    </div>
  )
}
