const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws'

type Listener = (event: WSEvent) => void

export interface WSEvent {
  type: string
  data: unknown
  timestamp: number
}

class WebSocketClient {
  private ws: WebSocket | null = null
  private listeners: Map<string, Set<Listener>> = new Map()
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null
  private reconnectDelay = 2000
  private maxReconnectDelay = 30000
  private connected = false

  connect() {
    if (typeof window === 'undefined') return
    if (this.ws?.readyState === WebSocket.OPEN) return

    try {
      this.ws = new WebSocket(WS_URL)

      this.ws.onopen = () => {
        this.connected = true
        this.reconnectDelay = 2000
        this.emit('__connected', { connected: true })
      }

      this.ws.onclose = () => {
        this.connected = false
        this.emit('__disconnected', { connected: false })
        this._scheduleReconnect()
      }

      this.ws.onerror = () => {
        this.connected = false
      }

      this.ws.onmessage = (e) => {
        try {
          const msg = JSON.parse(e.data) as WSEvent
          this.emit(msg.type, msg.data, msg.timestamp)
          this.emit('*', msg)
        } catch {
          // ignore malformed messages
        }
      }
    } catch {
      this._scheduleReconnect()
    }
  }

  disconnect() {
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer)
    this.ws?.close()
    this.ws = null
  }

  send(data: object) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data))
    }
  }

  ping() {
    this.send({ cmd: 'ping' })
  }

  subscribeLogs() {
    this.send({ cmd: 'subscribe_logs' })
  }

  on(type: string, listener: Listener) {
    if (!this.listeners.has(type)) this.listeners.set(type, new Set())
    this.listeners.get(type)!.add(listener)
    return () => this.off(type, listener)
  }

  off(type: string, listener: Listener) {
    this.listeners.get(type)?.delete(listener)
  }

  isConnected() {
    return this.connected
  }

  private emit(type: string, data?: unknown, timestamp?: number) {
    const event: WSEvent = { type, data, timestamp: timestamp ?? Date.now() / 1000 }
    this.listeners.get(type)?.forEach(l => l(event))
  }

  private _scheduleReconnect() {
    if (this.reconnectTimer) return
    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null
      this.reconnectDelay = Math.min(this.reconnectDelay * 1.5, this.maxReconnectDelay)
      this.connect()
    }, this.reconnectDelay)
  }
}

export const wsClient = new WebSocketClient()
