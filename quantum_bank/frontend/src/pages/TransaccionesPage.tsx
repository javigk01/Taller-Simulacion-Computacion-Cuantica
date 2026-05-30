import { useEffect, useState, useRef } from 'react'
import {
  getCuentas, getTransacciones, createTransaccion, descifrarTransaccion,
  type Cuenta, type Transaccion, type TransaccionDecifrada,
} from '../api'

const BB84_STEPS = [
  { icon: '⚛️',  text: 'Iniciando protocolo BB84...' },
  { icon: '🎲',  text: 'Alice genera bits y bases aleatorias (384 qubits)' },
  { icon: '🔬',  text: 'AerSimulator ejecuta el circuito cuántico...' },
  { icon: '📡',  text: 'Bob mide en bases aleatorias' },
  { icon: '⚖️',  text: 'Sifting: descartando bases no coincidentes (~50%)' },
  { icon: '🔍',  text: 'Verificando QBER — chequeando canal por espías...' },
  { icon: '🔐',  text: 'Clave cuántica segura. Cifrando con AES-256-GCM...' },
]

function fmt(n: number) {
  return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(n)
}
function fmtDate(s: string) {
  return new Date(s).toLocaleString('es-CO', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' })
}
function truncHex(h: string | null, n = 24) {
  if (!h) return '—'
  return h.slice(0, n) + '...'
}

export default function TransaccionesPage() {
  const [cuentas, setCuentas] = useState<Cuenta[]>([])
  const [txns, setTxns] = useState<Transaccion[]>([])
  const [origen, setOrigen] = useState('')
  const [destino, setDestino] = useState('')
  const [monto, setMonto] = useState('')
  const [concepto, setConcepto] = useState('')
  const [loading, setLoading] = useState(false)
  const [step, setStep] = useState(-1)
  const [lastTxn, setLastTxn] = useState<Transaccion | null>(null)
  const [error, setError] = useState('')
  const [decrypted, setDecrypted] = useState<Record<number, TransaccionDecifrada | null>>({})
  const [decrypting, setDecrypting] = useState<number | null>(null)
  const stepRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const load = async () => {
    const [c, t] = await Promise.all([getCuentas(), getTransacciones()])
    setCuentas(c.filter(x => x.estado === 'ACTIVA'))
    setTxns(t)
  }

  useEffect(() => { load() }, [])

  const handleTransfer = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLastTxn(null)
    setLoading(true)
    setStep(0)

    // Animate steps in parallel with the API call
    let s = 0
    stepRef.current = setInterval(() => {
      s++
      if (s < BB84_STEPS.length - 1) setStep(s)
      else if (stepRef.current) clearInterval(stepRef.current)
    }, 550)

    try {
      const txn = await createTransaccion(
        parseInt(origen), parseInt(destino),
        parseFloat(monto), concepto,
      )
      if (stepRef.current) clearInterval(stepRef.current)
      setStep(BB84_STEPS.length - 1)
      setLastTxn(txn)
      setMonto('')
      setConcepto('')
      await load()
    } catch (err: any) {
      if (stepRef.current) clearInterval(stepRef.current)
      setStep(-1)
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

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
      {/* ── Transfer form (left) ──────────────────────────────────────── */}
      <div className="col-span-2">
        <h1 className="text-2xl font-bold text-white mb-1">Transferencia</h1>
        <p className="text-slate-400 text-sm mb-6">Cifrada con clave cuántica BB84</p>

        {error && (
          <div className="mb-4 p-3 bg-red-950/50 border border-red-800 text-red-300 rounded-xl text-sm">
            {error}
          </div>
        )}

        {/* BB84 Animation */}
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
                    {i < step ? '✓' : i === step ? (
                      <span className="inline-block w-4 h-4 border-2 border-purple-400 border-t-transparent rounded-full animate-spin" />
                    ) : '·'}
                  </span>
                  <span className="mr-1">{s.icon}</span>
                  {s.text}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Success result */}
        {lastTxn && !loading && (
          <div className="mb-6 p-4 bg-emerald-950/40 border border-emerald-800/50 rounded-2xl slide-in">
            <p className="text-emerald-400 font-semibold text-sm mb-3">✓ Transferencia completada</p>
            <div className="space-y-1.5 text-xs">
              <Row label="ID" value={`#${lastTxn.id}`} />
              <Row label="Monto" value={fmt(lastTxn.monto)} />
              <Row label="QKD Session" value={lastTxn.qkd_session_id?.slice(0, 18) + '...' ?? '—'} mono />
              <Row label="Payload cifrado" value={truncHex(lastTxn.payload_cifrado)} mono />
            </div>
          </div>
        )}

        {/* Form */}
        {!loading && (
          <form onSubmit={handleTransfer} className="space-y-4">
            <div>
              <label className="text-xs text-slate-400 mb-1.5 block">Cuenta origen</label>
              <select
                value={origen} onChange={e => setOrigen(e.target.value)} required
                className="w-full bg-slate-800 border border-slate-700 text-white rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:border-purple-500"
              >
                <option value="">Seleccionar...</option>
                {cuentas.map(c => (
                  <option key={c.id} value={c.id}>
                    {c.titular} · {fmt(c.saldo)}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="text-xs text-slate-400 mb-1.5 block">Cuenta destino</label>
              <select
                value={destino} onChange={e => setDestino(e.target.value)} required
                className="w-full bg-slate-800 border border-slate-700 text-white rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:border-purple-500"
              >
                <option value="">Seleccionar...</option>
                {cuentas.filter(c => c.id !== parseInt(origen)).map(c => (
                  <option key={c.id} value={c.id}>{c.titular}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="text-xs text-slate-400 mb-1.5 block">Monto (COP)</label>
              <input
                value={monto} onChange={e => setMonto(e.target.value)}
                type="number" min="1" required placeholder="250000"
                className="w-full bg-slate-800 border border-slate-700 text-white rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:border-purple-500"
              />
            </div>

            <div>
              <label className="text-xs text-slate-400 mb-1.5 block">Concepto</label>
              <input
                value={concepto} onChange={e => setConcepto(e.target.value)}
                required placeholder="Ej: Pago cuota universitaria"
                className="w-full bg-slate-800 border border-slate-700 text-white rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:border-purple-500"
              />
            </div>

            <button
              type="submit"
              className="w-full py-3 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white rounded-xl font-semibold text-sm transition-all shadow-lg shadow-purple-900/40"
            >
              ⚛️ Transferir con BB84
            </button>
          </form>
        )}
      </div>

      {/* ── Transaction history (right) ──────────────────────────────── */}
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
              onDecrypt={handleDecrypt}
              decrypting={decrypting === t.id}
              decryptedData={decrypted[t.id]}
            />
          ))}
        </div>
      </div>
    </div>
  )
}

function TxnRow({
  txn, cuentas, onDecrypt, decrypting, decryptedData,
}: {
  txn: Transaccion
  cuentas: Cuenta[]
  onDecrypt: (id: number) => void
  decrypting: boolean
  decryptedData?: TransaccionDecifrada | null
}) {
  const [open, setOpen] = useState(false)

  const fmt2 = (n: number) =>
    new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(n)

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden hover:border-slate-700 transition-colors">
      <div className="flex items-center justify-between px-4 py-3">
        <div className="flex items-center gap-3">
          <span className="text-slate-600 font-mono text-xs">#{txn.id}</span>
          <div>
            <div className="flex items-center gap-2 text-sm font-medium text-white">
              <span>Cuenta {txn.cuenta_origen_id}</span>
              <span className="text-slate-500">→</span>
              <span>Cuenta {txn.cuenta_destino_id}</span>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">{txn.concepto} · {fmtDate(txn.timestamp)}</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <span className="font-bold text-white">{fmt2(txn.monto)}</span>
          <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
            txn.estado === 'COMPLETADA'
              ? 'bg-emerald-950 text-emerald-400 border border-emerald-900'
              : 'bg-slate-800 text-slate-400 border border-slate-700'
          }`}>{txn.estado}</span>
          <button
            onClick={() => { setOpen(v => !v); if (!decryptedData && !open) onDecrypt(txn.id) }}
            className="text-xs px-3 py-1.5 bg-slate-800 hover:bg-purple-900/50 text-slate-400 hover:text-purple-300 border border-slate-700 hover:border-purple-700 rounded-lg transition-colors"
          >
            {decrypting ? '...' : open ? '🔒 Cerrar' : '🔓 Descifrar'}
          </button>
        </div>
      </div>

      {/* Expanded decrypt view */}
      {open && (
        <div className="border-t border-slate-800 px-4 py-3 bg-slate-950/50 slide-in">
          {decrypting && (
            <p className="text-sm text-slate-500 animate-pulse">Recuperando clave del QKD Service...</p>
          )}
          {decryptedData?.payload_descifrado && (
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-xs text-slate-500 mb-2 uppercase tracking-wider">Payload descifrado (AES-256-GCM)</p>
                <div className="space-y-1.5 text-sm">
                  <Row label="Monto"    value={decryptedData.payload_descifrado.monto} />
                  <Row label="Concepto" value={decryptedData.payload_descifrado.concepto} />
                  <Row label="Origen"   value={decryptedData.payload_descifrado.cuenta_origen} mono />
                  <Row label="Destino"  value={decryptedData.payload_descifrado.cuenta_destino} mono />
                  <Row label="QBER"     value={`${(decryptedData.payload_descifrado.qkd_qber * 100).toFixed(2)}%`} />
                </div>
              </div>
              <div>
                <p className="text-xs text-slate-500 mb-2 uppercase tracking-wider">Payload cifrado (hex)</p>
                <p className="font-mono text-xs text-slate-600 break-all leading-relaxed">
                  {txn.payload_cifrado?.slice(0, 120)}...
                </p>
                <p className="text-xs text-purple-400 mt-2">
                  🔑 QKD: {txn.qkd_session_id?.slice(0, 20)}...
                </p>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function Row({ label, value, mono = false }: { label: string; value: string; mono?: boolean }) {
  return (
    <div className="flex items-baseline gap-2">
      <span className="text-slate-500 text-xs w-20 shrink-0">{label}</span>
      <span className={`text-slate-200 text-xs ${mono ? 'font-mono' : ''}`}>{value}</span>
    </div>
  )
}
