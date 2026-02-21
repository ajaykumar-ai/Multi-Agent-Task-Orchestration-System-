'use client'

import { useState, useEffect, useRef } from 'react'
import ReactMarkdown from 'react-markdown'
import styles from './page.module.css'

const API = 'http://localhost:8001'

const AGENTS = ['Planner', 'Researcher', 'Writer', 'Reviewer']
const STAGE_MAP: Record<string, string> = {
  pending: '',
  planning: 'Planner',
  researching: 'Researcher',
  writing: 'Writer',
  reviewing: 'Reviewer',
  revising: 'Writer',
  done: '',
  error: '',
}

interface Event {
  agent: string
  message: string
  data?: unknown
}

interface Task {
  id: string
  prompt: string
  status: string
  current_agent: string | null
  events: Event[]
  plan: string[] | null
  draft: string | null
  feedback: string | null
  final_report: string | null
  error: string | null
}

export default function Home() {
  const [prompt, setPrompt] = useState('')
  const [taskId, setTaskId] = useState<string | null>(null)
  const [task, setTask] = useState<Task | null>(null)
  const [events, setEvents] = useState<Event[]>([])
  const [loading, setLoading] = useState(false)
  const [activeTab, setActiveTab] = useState<'log' | 'report'>('log')
  const eventSourceRef = useRef<EventSource | null>(null)
  const logEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [events])

  const submit = async () => {
    if (!prompt.trim()) return
    setLoading(true)
    setTask(null)
    setEvents([])
    setActiveTab('log')

    const res = await fetch(`${API}/tasks`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prompt }),
    })
    const data = await res.json()
    setTaskId(data.task_id)

    // SSE stream
    const es = new EventSource(`${API}/tasks/${data.task_id}/stream`)
    eventSourceRef.current = es

    es.onmessage = (e) => {
      const parsed = JSON.parse(e.data)
      if (parsed.type === 'done') {
        setTask(parsed.task)
        setActiveTab('report')
        es.close()
        setLoading(false)
      } else {
        setEvents((prev) => [...prev, parsed])
        // Also poll task state for status bar
        fetch(`${API}/tasks/${data.task_id}`)
          .then((r) => r.json())
          .then((t) => setTask(t))
      }
    }

    es.onerror = () => {
      es.close()
      setLoading(false)
    }
  }

  const currentAgent = task?.current_agent || STAGE_MAP[task?.status || ''] || ''
  const isDone = task?.status === 'done'
  const isError = task?.status === 'error'

  return (
    <main className={styles.main}>
      {/* Header */}
      <header className={styles.header}>
        <div className="container">
          <div className={styles.headerInner}>
            <div className={styles.logo}>
              <span className={styles.logoIcon}>◈</span>
              <span>ORCHESTR<em>AI</em></span>
            </div>
            <div className={styles.headerMeta}>
              <span className={styles.pill}>Groq Llama 3.1</span>
              <span className={styles.pill}>4 Agents</span>
            </div>
          </div>
        </div>
      </header>

      <div className="container">
        {/* Prompt Form */}
        <section className={styles.promptSection}>
          <h1 className={styles.headline}>
            Multi-agent<br /><span>intelligence,</span><br />at your prompt.
          </h1>
          <div className={styles.formBox}>
            <textarea
              className={styles.textarea}
              placeholder="e.g. Research the pros and cons of microservices vs monoliths and produce a summary report"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              rows={3}
              onKeyDown={(e) => { if (e.key === 'Enter' && e.metaKey) submit() }}
            />
            <div className={styles.formFooter}>
              <span className={styles.hint}>⌘ + Enter to submit</span>
              <button className={styles.btn} onClick={submit} disabled={loading || !prompt.trim()}>
                {loading ? <span className={styles.spinner} /> : '▶ Run Pipeline'}
              </button>
            </div>
          </div>
        </section>

        {/* Pipeline Visualizer */}
        {task && (
          <section className={styles.pipeline}>
            {AGENTS.map((agent, i) => {
              const isActive = currentAgent === agent
              const agentIdx = AGENTS.indexOf(currentAgent)
              const done = isDone || (agentIdx > i && agentIdx !== -1)
              return (
                <div key={agent} className={styles.pipelineItem}>
                  <div
                    className={`${styles.agentNode} ${isActive ? styles.active : ''} ${done ? styles.done : ''}`}
                  >
                    <span className={styles.agentIcon}>
                      {done ? '✓' : isActive ? <span className={styles.pulse}>●</span> : '○'}
                    </span>
                    <span className={styles.agentName}>{agent}</span>
                  </div>
                  {i < AGENTS.length - 1 && (
                    <div className={`${styles.connector} ${done ? styles.connectorDone : ''}`} />
                  )}
                </div>
              )
            })}
          </section>
        )}

        {/* Plan sub-tasks */}
        {task?.plan && (
          <div className={styles.planBox}>
            <p className={styles.planLabel}>EXECUTION PLAN</p>
            <div className={styles.planTasks}>
              {task.plan.map((t, i) => (
                <div key={i} className={styles.planTask}>
                  <span className={styles.planNum}>{String(i + 1).padStart(2, '0')}</span>
                  <span>{t}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Tabs */}
        {taskId && (
          <div className={styles.workspace}>
            <div className={styles.tabs}>
              <button
                className={`${styles.tab} ${activeTab === 'log' ? styles.tabActive : ''}`}
                onClick={() => setActiveTab('log')}
              >
                Activity Log
                {loading && <span className={styles.tabBadge}>{events.length}</span>}
              </button>
              <button
                className={`${styles.tab} ${activeTab === 'report' ? styles.tabActive : ''}`}
                onClick={() => setActiveTab('report')}
                disabled={!task?.final_report}
              >
                Final Report
                {isDone && <span className={styles.tabBadgeDone}>✓</span>}
              </button>
            </div>

            {/* Log Panel */}
            {activeTab === 'log' && (
              <div className={styles.logPanel}>
                {events.map((ev, i) => (
                  <div key={i} className={styles.logEntry}>
                    <span className={styles.logAgent}>{ev.agent}</span>
                    <span className={styles.logMsg}>{ev.message}</span>
                    {ev.data && Array.isArray(ev.data) && (
                      <div className={styles.logData}>
                        {(ev.data as string[]).map((d, j) => (
                          <div key={j} className={styles.logDataItem}>→ {d}</div>
                        ))}
                      </div>
                    )}
                    {ev.data && typeof ev.data === 'object' && !Array.isArray(ev.data) && (ev.data as Record<string, string>).feedback && (
                      <div className={styles.feedbackBox}>
                        <p className={styles.feedbackLabel}>REVIEWER FEEDBACK</p>
                        <p className={styles.feedbackText}>{(ev.data as Record<string, string>).feedback}</p>
                      </div>
                    )}
                  </div>
                ))}
                {loading && (
                  <div className={styles.logEntry}>
                    <span className={styles.logAgent}>{currentAgent || 'System'}</span>
                    <span className={styles.logMsg}>
                      <span className={styles.dots}>processing</span>
                    </span>
                  </div>
                )}
                {isError && (
                  <div className={styles.errorBox}>Error: {task?.error}</div>
                )}
                <div ref={logEndRef} />
              </div>
            )}

            {/* Report Panel */}
            {activeTab === 'report' && task?.final_report && (
              <div className={styles.reportPanel}>
                {task.feedback && (
                  <div className={styles.revisionBanner}>
                    <strong>Revised after review</strong> — The report was sent back for revision and improved based on reviewer feedback.
                  </div>
                )}
                <div className="markdown">
                  <ReactMarkdown>{task.final_report}</ReactMarkdown>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </main>
  )
}
