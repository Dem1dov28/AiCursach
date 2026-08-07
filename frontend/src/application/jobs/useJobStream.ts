import { useCallback, useEffect, useRef, useState } from 'react'
import {
  applyStreamEvent,
  EMPTY_JOB_STREAM,
  type JobStreamState,
} from './applyStreamEvent'
import type { StreamEvent } from '@/domain/jobs/types'
import { jobGateway } from '@/application/container'

const MAX_RECONNECT_DELAY_MS = 30_000

export function useJobStream(jobId: string | null): JobStreamState & { reconnecting: boolean } {
  const [state, setState] = useState<JobStreamState>(EMPTY_JOB_STREAM)
  const [connected, setConnected] = useState(false)
  const [reconnecting, setReconnecting] = useState(false)
  const doneRef = useRef(false)
  const attemptRef = useRef(0)

  const dispatch = useCallback((event: StreamEvent) => {
    if (event.type === 'done') {
      doneRef.current = true
    }
    setState((prev) => applyStreamEvent(prev, event))
  }, [])

  const reconcileSnapshot = useCallback(async () => {
    if (!jobId) return
    try {
      const job = await jobGateway.fetchJob(jobId)
      dispatch({ type: 'snapshot', job })
    } catch {
      /* server may be temporarily unavailable */
    }
  }, [jobId, dispatch])

  useEffect(() => {
    if (!jobId) return

    doneRef.current = false
    attemptRef.current = 0
    setState(EMPTY_JOB_STREAM)
    setConnected(false)
    setReconnecting(false)

    let source: EventSource | null = null
    let retryTimer: ReturnType<typeof setTimeout> | null = null
    let cancelled = false

    const connect = () => {
      if (cancelled || doneRef.current) return

      source?.close()
      source = new EventSource(jobGateway.streamJobUrl(jobId))

      source.onopen = () => {
        attemptRef.current = 0
        setConnected(true)
        setReconnecting(false)
      }

      source.onerror = () => {
        setConnected(false)
        if (cancelled || doneRef.current) return

        source?.close()
        setReconnecting(true)
        void reconcileSnapshot()

        const delay = Math.min(MAX_RECONNECT_DELAY_MS, 1000 * 2 ** attemptRef.current)
        attemptRef.current += 1
        retryTimer = setTimeout(connect, delay)
      }

      source.onmessage = (msg) => {
        try {
          const parsed = JSON.parse(msg.data) as StreamEvent
          dispatch(parsed)
          if (parsed.type === 'done') {
            source?.close()
            setConnected(false)
            setReconnecting(false)
          }
        } catch {
          /* ignore malformed events */
        }
      }
    }

    connect()

    return () => {
      cancelled = true
      source?.close()
      if (retryTimer) clearTimeout(retryTimer)
    }
  }, [jobId, dispatch, reconcileSnapshot])

  return { ...state, connected, reconnecting, applyEvent: dispatch }
}
