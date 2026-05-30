// ── Types ─────────────────────────────────────────────────────────────────────

export interface Cuenta {
  id: number
  numero_cuenta: string
  titular: string
  saldo: number
  estado: 'ACTIVA' | 'INACTIVA'
  creado_en: string
}

export interface Transaccion {
  id: number
  cuenta_origen_id: number
  cuenta_destino_id: number
  monto: number
  concepto: string
  payload_cifrado: string | null
  qkd_session_id: string | null
  estado: 'PENDIENTE' | 'COMPLETADA' | 'FALLIDA'
  timestamp: string
}

export interface TransaccionDecifrada extends Transaccion {
  payload_descifrado: {
    monto: string
    concepto: string
    cuenta_origen: string
    cuenta_destino: string
    qkd_qber: number
  } | null
}

export interface SesionQKD {
  id: string
  client_id: string
  clave_hex: string | null
  protocolo: string
  n_bits: number
  qber: number
  sifted_ratio: number
  entropia: number
  n_qubits_usados: number
  intercept_prob: number
  seguro: boolean
  espia_detectado: boolean
  generado_en: string
  mensaje?: string
}

export interface EavesdropCompare {
  sin_espia: SesionQKD
  con_espia: SesionQKD
  conclusion: string
}

// ── HTTP helper ───────────────────────────────────────────────────────────────

async function req<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json', ...init?.headers },
    ...init,
  })
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail ?? `HTTP ${res.status}`)
  }
  if (res.status === 204) return undefined as T
  return res.json()
}

// ── Cuentas ───────────────────────────────────────────────────────────────────

export const getCuentas = () =>
  req<Cuenta[]>('/api/txn/cuentas/')

export const createCuenta = (titular: string, saldo_inicial: number) =>
  req<Cuenta>('/api/txn/cuentas/', {
    method: 'POST',
    body: JSON.stringify({ titular, saldo_inicial }),
  })

export const deactivateCuenta = (id: number) =>
  req<void>(`/api/txn/cuentas/${id}`, { method: 'DELETE' })

// ── Transacciones ─────────────────────────────────────────────────────────────

export const getTransacciones = () =>
  req<Transaccion[]>('/api/txn/transacciones/')

export const createTransaccion = (
  cuenta_origen_id: number,
  cuenta_destino_id: number,
  monto: number,
  concepto: string,
) =>
  req<Transaccion>('/api/txn/transacciones/', {
    method: 'POST',
    body: JSON.stringify({ cuenta_origen_id, cuenta_destino_id, monto, concepto }),
  })

export const descifrarTransaccion = (id: number) =>
  req<TransaccionDecifrada>(`/api/txn/transacciones/${id}/descifrar`)

// ── QKD ───────────────────────────────────────────────────────────────────────

export const getSesionesQKD = () =>
  req<SesionQKD[]>('/api/qkd/sessions')

export const generarClaveQKD = (n_bits = 128) =>
  req<SesionQKD>('/api/qkd/session-key', {
    method: 'POST',
    body: JSON.stringify({ client_id: 'frontend_demo', n_bits, simular_espia: false }),
  })

export const demoEavesdrop = (n_bits = 64) =>
  req<EavesdropCompare>(`/api/qkd/demo/eavesdrop-compare?n_bits=${n_bits}`, {
    method: 'POST',
  })
