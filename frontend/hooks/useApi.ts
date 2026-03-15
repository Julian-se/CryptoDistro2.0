'use client'

import { useState, useEffect, useCallback } from 'react'

export function useApi<T>(
  fetcher: () => Promise<T>,
  deps: unknown[] = [],
  options: { refreshInterval?: number } = {}
) {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetch = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const result = await fetcher()
      setData(result)
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setLoading(false)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps)

  useEffect(() => {
    fetch()
    if (options.refreshInterval) {
      const id = setInterval(fetch, options.refreshInterval)
      return () => clearInterval(id)
    }
  }, [fetch, options.refreshInterval])

  return { data, loading, error, refetch: fetch }
}
