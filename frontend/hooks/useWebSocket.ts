'use client'

import { useEffect, useState, useCallback } from 'react'
import { wsClient, WSEvent } from '@/lib/ws'

export function useWebSocket() {
  const [connected, setConnected] = useState(false)

  useEffect(() => {
    wsClient.connect()

    const offConn = wsClient.on('__connected', () => setConnected(true))
    const offDisc = wsClient.on('__disconnected', () => setConnected(false))

    return () => {
      offConn()
      offDisc()
    }
  }, [])

  const subscribe = useCallback((type: string, handler: (data: unknown) => void) => {
    return wsClient.on(type, (e: WSEvent) => handler(e.data))
  }, [])

  return { connected, subscribe, send: wsClient.send.bind(wsClient) }
}

export function useWSEvent<T>(type: string, initial: T): T {
  const [value, setValue] = useState<T>(initial)

  useEffect(() => {
    wsClient.connect()
    const off = wsClient.on(type, (e: WSEvent) => setValue(e.data as T))
    return off
  }, [type])

  return value
}
