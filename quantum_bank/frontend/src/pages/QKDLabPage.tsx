import { useState } from 'react'
import { generarClaveQKD, demoEavesdrop, type SesionQKD, type EavesdropCompare } from '../api'

function QBERBar({ qber, max = 0.35 }: { qber: number; max?: number }) {
  const pct = Math.min((qber / max) * 100, 100)
  const safe = qber < 0.11
  return (
    <div>
      <div className="flex justify-between text-xs mb-1.5">
        <span className={safe ? 'text-emerald-400' : 'text-red-400'}>
          QBER: {(qber * 100).toFixed(2)}%
        </span>
        <span className="text-slate-500">umbral seguro &lt; 11%</span>
      </div>
      <div className="h-3 bg-slate-800 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-700 ${safe ? 'bg-emerald-500' : 'bg-red-500'}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <div
        className="w-px h-4 bg-yellow-500/60 absolute"
        style={{ marginLeft: `${(0.11 / max) * 100}%`, marginTop: '-12px' }}
      />
    </div>
  )
}

function MetricCard({ label, value, sub, color = 'slate' }: {
  label: string; value: string; sub?: string; color?: string
}) {
  const colors: Record<string, string> = {
    slate:   'text-white',
    emerald: 'text-emerald-400',
    red:     'text-red-400',
    purple:  'text-purple-400',
    blue:    'text-blue-400',
  }
  return (
    <div className="bg-slate-800/60 rounded-xl p-3">
      <p className="text-xs text-slate-500 mb-1">{label}</p>
      <p className={`font-bold text-lg font-mono ${colors[color]}`}>{value}</p>
      {sub && <p className="text-xs text-slate-600 mt-0.5">{sub}</p>}
    </div>
  )
}

function SessionCard({ s, title, borderColor }: {
  s: SesionQKD; title: string; borderColor: string
}) {
  return (
    <div className={`p-5 rounded-2xl border bg-slate-900 ${borderColor}`}>
      <p className={`text-sm font-bold mb-4 ${s.seguro ? 'text-emerald-400' : 'text-red-400'}`}>
        {s.seguro ? '✅' : '🔴'} {title}
      </p>

      <div className="relative mb-4">
        <QBERBar qber={s.qber} />
      </div>

      <div className="grid grid-cols-2 gap-2 mb-4">
        <MetricCard label="QBER" value={`${(s.qber * 100).toFixed(1)}%`} color={s.seguro ? 'emerald' : 'red'} />
        <MetricCard label="Entropía Shannon" value={`${s.entropia.toFixed(3)}`} sub="ideal = 1.0" color="blue" />
        <MetricCard label="Sifted ratio" value={`${(s.sifted_ratio * 100).toFixed(0)}%`} sub="~50% esperado" />
        <MetricCard label="Qubits usados" value={s.n_qubits_usados.toString()} />
      </div>

      <div className="mb-3">
        <p className="text-xs text-slate-500 mb-1">Estado del canal</p>
        <div className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium ${
          s.seguro
            ? 'bg-emerald-950/60 text-emerald-300 border border-emerald-900'
            : 'bg-red-950/60 text-red-300 border border-red-900'
        }`}>
          {s.seguro
            ? '🔐 Canal seguro — clave establecida'
            : '🚨 Espía detectado — clave DESCARTADA'
          }
        </div>
      </div>

      {s.clave_hex ? (
        <div>
          <p className="text-xs text-slate-500 mb-1">Clave (128 bits)</p>
          <p className="font-mono text-xs text-slate-400 bg-slate-800 p-2 rounded-lg break-all">
            {s.clave_hex}
          </p>
        </div>
      ) : (
        <div className="bg-red-950/30 border border-red-900/50 rounded-lg p-3 text-center">
          <p className="text-red-400 text-sm font-mono">clave_hex: null</p>
          <p className="text-xs text-red-500 mt-1">No se genera clave cuando QBER ≥ 11%</p>
        </div>
      )}
    </div>
  )
}

export default function QKDLabPage() {
  const [nBits, setNBits] = useState(128)
  const [genResult, setGenResult] = useState<SesionQKD | null>(null)
  const [genLoading, setGenLoading] = useState(false)

  const [eveResult, setEveResult] = useState<EavesdropCompare | null>(null)
  const [eveLoading, setEveLoading] = useState(false)

  const [error, setError] = useState('')

  const handleGenerate = async () => {
    setGenLoading(true)
    setError('')
    try {
      const r = await generarClaveQKD(nBits)
      setGenResult(r)
    } catch (e: any) {
      setError(e.message)
    } finally {
      setGenLoading(false)
    }
  }

  const handleEavesdrop = async () => {
    setEveLoading(true)
    setError('')
    try {
      const r = await demoEavesdrop(64)
      setEveResult(r)
    } catch (e: any) {
      setError(e.message)
    } finally {
      setEveLoading(false)
    }
  }

  return (
    <div className="slide-in space-y-10">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white mb-1">QKD Lab</h1>
        <p className="text-slate-400 text-sm">
          Protocolo BB84 — IBM Qiskit + AerSimulator (método stabilizer)
        </p>
      </div>

      {error && (
        <div className="p-3 bg-red-950/50 border border-red-800 text-red-300 rounded-xl text-sm">{error}</div>
      )}

      {/* ── Concept cards ──────────────────────────────────────────────── */}
      <div className="grid grid-cols-3 gap-4">
        {[
          {
            icon: '⚛️',
            title: 'Superposición',
            text: 'Cada qubit puede ser 0, 1 o AMBOS simultáneamente hasta ser medido. Alice usa esta propiedad para codificar bits en bases Z (rectilinear) o X (diagonal).',
          },
          {
            icon: '🔗',
            title: 'Principio de No-Clonación',
            text: 'Un qubit desconocido no puede copiarse sin alterar el original. Si Eve intercepta, destruye el estado cuántico — Alice y Bob lo detectan por el QBER elevado.',
          },
          {
            icon: '📊',
            title: 'QBER como detector',
            text: 'Canal limpio → QBER ≈ 0%. Con espía → QBER ≈ 25% (Eve introduce ruido al medir en bases incorrectas). Umbral de seguridad BB84: QBER < 11%.',
          },
        ].map(c => (
          <div key={c.title} className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
            <div className="text-2xl mb-3">{c.icon}</div>
            <h3 className="font-semibold text-white mb-2">{c.title}</h3>
            <p className="text-slate-400 text-sm leading-relaxed">{c.text}</p>
          </div>
        ))}
      </div>

      {/* ── Key generator ──────────────────────────────────────────────── */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
        <h2 className="font-bold text-white text-lg mb-4">Generar Clave Cuántica</h2>
        <div className="flex items-end gap-4 mb-6">
          <div>
            <label className="text-xs text-slate-400 mb-1.5 block">Longitud (bits)</label>
            <select
              value={nBits}
              onChange={e => setNBits(parseInt(e.target.value))}
              className="bg-slate-800 border border-slate-700 text-white rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:border-purple-500"
            >
              {[64, 128, 256, 512].map(n => (
                <option key={n} value={n}>{n} bits ({n / 8} bytes)</option>
              ))}
            </select>
          </div>
          <button
            onClick={handleGenerate}
            disabled={genLoading}
            className="px-5 py-2.5 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 disabled:opacity-50 text-white rounded-xl font-semibold text-sm transition-all shadow-lg shadow-purple-900/40"
          >
            {genLoading ? (
              <span className="flex items-center gap-2">
                <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Ejecutando BB84...
              </span>
            ) : '⚛️ Generar Clave BB84'}
          </button>
        </div>

        {genResult && (
          <div className="slide-in">
            <div className="grid grid-cols-4 gap-3 mb-4">
              <MetricCard label="QBER" value={`${(genResult.qber * 100).toFixed(2)}%`} color={genResult.seguro ? 'emerald' : 'red'} />
              <MetricCard label="Entropía Shannon" value={genResult.entropia.toFixed(4)} sub="ideal = 1.0" color="blue" />
              <MetricCard label="Sifted ratio" value={`${(genResult.sifted_ratio * 100).toFixed(0)}%`} />
              <MetricCard label="Qubits simulados" value={genResult.n_qubits_usados.toString()} color="purple" />
            </div>

            <div className="relative mb-4">
              <QBERBar qber={genResult.qber} />
            </div>

            <div>
              <p className="text-xs text-slate-500 mb-2">Clave generada ({genResult.n_bits} bits)</p>
              <div className="bg-slate-800/80 border border-slate-700 rounded-xl p-4">
                <p className="font-mono text-sm text-purple-300 break-all">{genResult.clave_hex}</p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* ── Eavesdrop demo ─────────────────────────────────────────────── */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
        <div className="flex items-center justify-between mb-2">
          <div>
            <h2 className="font-bold text-white text-lg">Demo: Detección de Espía (Eve)</h2>
            <p className="text-slate-400 text-sm mt-1">
              Ejecuta BB84 dos veces: canal limpio vs Eve interceptando el 100% de los qubits
            </p>
          </div>
          <button
            onClick={handleEavesdrop}
            disabled={eveLoading}
            className="px-5 py-2.5 bg-red-700/80 hover:bg-red-600 disabled:opacity-50 text-white rounded-xl font-semibold text-sm transition-all"
          >
            {eveLoading ? (
              <span className="flex items-center gap-2">
                <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Simulando...
              </span>
            ) : '🕵️ Lanzar ataque de Eve'}
          </button>
        </div>

        {eveLoading && (
          <div className="mt-4 p-4 bg-slate-800/50 rounded-xl text-sm text-slate-400 animate-pulse">
            Ejecutando protocolo BB84 con y sin interceptación... (Qiskit AerSimulator)
          </div>
        )}

        {eveResult && !eveLoading && (
          <div className="slide-in mt-6 space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <SessionCard
                s={eveResult.sin_espia}
                title="Sin espía — canal limpio"
                borderColor="border-emerald-900/60"
              />
              <SessionCard
                s={eveResult.con_espia}
                title="Con espía (Eve intercepta todo)"
                borderColor="border-red-900/60"
              />
            </div>
            <div className="p-4 bg-slate-800/60 border border-slate-700 rounded-xl">
              <p className="text-xs text-slate-500 mb-1 uppercase tracking-wider">Conclusión automática</p>
              <p className="text-slate-200 text-sm">{eveResult.conclusion}</p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
