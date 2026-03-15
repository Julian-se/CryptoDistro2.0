'use client'

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { askIntelligence, researchQuestion } from '@/lib/api'
import { Card } from '@/components/shared/Card'
import { Spinner } from '@/components/shared/Spinner'

interface Message {
  role: 'user' | 'assistant'
  content: string
  duration_ms?: number
  source?: string
}

const QUICK_PROMPTS = [
  'Which market has the best opportunity right now?',
  'Should I refill Noones BTC now?',
  'What is my estimated profit today?',
  'Compare Nigeria vs Argentina',
]

export function IntelligenceChat() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [mode, setMode] = useState<'fast' | 'research'>('fast')

  async function send(question: string) {
    if (!question.trim() || loading) return
    const q = question.trim()
    setInput('')
    setMessages(m => [...m, { role: 'user', content: q }])
    setLoading(true)
    try {
      const fn = mode === 'research' ? researchQuestion : askIntelligence
      const res = await fn(q)
      setMessages(m => [...m, {
        role: 'assistant',
        content: res.answer,
        duration_ms: res.duration_ms,
        source: mode === 'research' ? 'Claude (Anthropic)' : 'Cerebras',
      }])
    } catch (e) {
      setMessages(m => [...m, {
        role: 'assistant',
        content: `Error: ${e instanceof Error ? e.message : String(e)}`,
      }])
    } finally {
      setLoading(false)
    }
  }

  return (
    <Card title="Intelligence" titleRight={
      <div className="flex items-center gap-1 text-xs font-mono">
        {(['fast', 'research'] as const).map(m => (
          <button
            key={m}
            onClick={() => setMode(m)}
            className={`px-2 py-0.5 rounded transition-colors ${
              mode === m
                ? 'bg-accent-green/10 text-accent-green border border-accent-green/20'
                : 'text-text-muted hover:text-text-secondary'
            }`}
          >
            {m === 'fast' ? '⚡ Fast' : '🔬 Research'}
          </button>
        ))}
      </div>
    }>
      {/* Messages */}
      <div className="h-48 overflow-y-auto space-y-3 mb-3">
        {messages.length === 0 && (
          <div className="h-full flex flex-col items-center justify-center gap-2">
            <p className="text-xs text-text-muted">Ask about markets, trades, or strategy</p>
            <div className="flex flex-wrap gap-1 justify-center">
              {QUICK_PROMPTS.map(q => (
                <button
                  key={q}
                  onClick={() => send(q)}
                  className="text-xs px-2 py-1 rounded bg-bg-border text-text-secondary hover:text-text-primary transition-colors"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        <AnimatePresence>
          {messages.map((msg, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className={`text-xs rounded p-2 font-mono ${
                msg.role === 'user'
                  ? 'bg-accent-green/5 border border-accent-green/10 text-accent-green ml-4'
                  : 'bg-bg-border text-text-primary mr-4'
              }`}
            >
              {msg.role === 'assistant' && (
                <p className="text-text-muted text-[10px] mb-1">
                  {msg.source ?? 'AI'} · {msg.duration_ms}ms
                </p>
              )}
              <p className="whitespace-pre-wrap">{msg.content}</p>
            </motion.div>
          ))}
        </AnimatePresence>

        {loading && (
          <div className="flex items-center gap-2 p-2">
            <Spinner size={14} />
            <span className="text-xs text-text-muted font-mono">Thinking...</span>
          </div>
        )}
      </div>

      {/* Input */}
      <div className="flex gap-2">
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && send(input)}
          placeholder="Ask a question..."
          className="flex-1 bg-bg-surface border border-bg-border rounded px-3 py-1.5 text-xs font-mono text-text-primary placeholder-text-muted focus:outline-none focus:border-accent-green/40"
        />
        <button
          onClick={() => send(input)}
          disabled={loading || !input.trim()}
          className="px-3 py-1.5 rounded bg-accent-green/10 text-accent-green border border-accent-green/20 text-xs font-mono hover:bg-accent-green/20 disabled:opacity-40 transition-colors"
        >
          Send
        </button>
      </div>
    </Card>
  )
}
