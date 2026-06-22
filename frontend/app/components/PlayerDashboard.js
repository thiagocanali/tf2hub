// frontend/app/components/PlayerDashboard.js
'use client'

import { useEffect, useState } from 'react'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, ReferenceLine
} from 'recharts'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const FORMAT_LABELS = { '6v6': '6v6', 'highlander': 'Highlander', '4v4': '4v4', 'mix': 'Mix' }
const CLASS_ICONS = {
  soldier: '🚀', medic: '💉', scout: '⚡', sniper: '🎯',
  demoman: '💣', heavyweapons: '🔫', engineer: '🔧', spy: '🔪', pyro: '🔥'
}

function ScoreCard({ label, value, sub, highlight }) {
  return (
    <div style={{
      background: '#1a1a1a',
      border: `1px solid ${highlight ? '#e8593c55' : '#2a2a2a'}`,
      borderRadius: '10px',
      padding: '1rem 1.25rem',
    }}>
      <div style={{ fontSize: '11px', color: '#666', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '6px' }}>
        {label}
      </div>
      <div style={{ fontSize: '22px', fontWeight: 700, color: highlight ? '#e8593c' : '#e8e6e0' }}>
        {value}
      </div>
      {sub && <div style={{ fontSize: '11px', color: '#555', marginTop: '4px' }}>{sub}</div>}
    </div>
  )
}

function PerformanceBadge({ score }) {
  if (score === null || score === undefined) return null
  const positive = score >= 0
  const bg = score > 10 ? '#e8593c22' : score < -10 ? '#3a3a4a' : '#1e1e1e'
  const color = score > 10 ? '#e8593c' : score < -10 ? '#7878aa' : '#888'
  const icon = score > 10 ? '🔥' : score < -10 ? '📉' : '➡️'
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: '4px',
      background: bg, color, borderRadius: '6px',
      padding: '2px 10px', fontSize: '13px', fontWeight: 600,
    }}>
      {icon} {positive ? '+' : ''}{score.toFixed(1)}%
    </span>
  )
}

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  const d = payload[0].payload
  return (
    <div style={{
      background: '#1a1a1a', border: '1px solid #2a2a2a',
      borderRadius: '8px', padding: '10px 14px', fontSize: '12px', color: '#e8e6e0'
    }}>
      <div style={{ marginBottom: '4px', color: '#888' }}>Log #{d.logs_tf_id}</div>
      <div>{CLASS_ICONS[d.class] || '🎮'} {d.class} — {d.format}</div>
      <div style={{ marginTop: '4px' }}>DPM: <strong>{d.dpm?.toFixed(0)}</strong></div>
      <div>KDA: <strong>{d.kda?.toFixed(2)}</strong></div>
      {d.performance_score !== null && (
        <div style={{ marginTop: '4px' }}>
          Score: <PerformanceBadge score={d.performance_score} />
        </div>
      )}
    </div>
  )
}

export default function PlayerDashboard({ steamId }) {
  const [player, setPlayer] = useState(null)
  const [logs, setLogs] = useState([])
  const [watchdog, setWatchdog] = useState(null)
  const [format, setFormat] = useState('6v6')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [importId, setImportId] = useState('')
  const [importing, setImporting] = useState(false)
  const [importResult, setImportResult] = useState(null)

  async function fetchAll(fmt) {
    setLoading(true)
    setError(null)
    try {
      const [pRes, lRes] = await Promise.all([
        fetch(`${API}/players/${steamId}`),
        fetch(`${API}/logs/player/${steamId}?format=${fmt}&limit=30`)
      ])

      if (!pRes.ok) {
        if (pRes.status === 404) {
          // Cria o jogador automaticamente
          await fetch(`${API}/players/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ steam_id: steamId })
          })
          setPlayer({ steam_id: steamId, display_name: 'Novo jogador', ratings: {} })
          setLogs([])
          return
        }
        throw new Error('Erro ao buscar jogador')
      }

      const [pData, lData] = await Promise.all([pRes.json(), lRes.json()])
      setPlayer(pData)
      setLogs(lData)

      // Watchdog em paralelo, sem bloquear
      fetch(`${API}/watchdog/analyze/${steamId}`)
        .then(r => r.ok ? r.json() : null)
        .then(w => setWatchdog(w))
        .catch(() => null)

    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchAll(format) }, [steamId, format])

  async function handleImport(e) {
    e.preventDefault()
    if (!importId.trim()) return
    setImporting(true)
    setImportResult(null)
    try {
      const res = await fetch(
        `${API}/logs/import/${importId.trim()}?steam_id=${steamId}&format=${format}`,
        { method: 'GET' }
      )
      const data = await res.json()
      setImportResult(data)
      if (res.ok) fetchAll(format) // atualiza a lista
    } catch {
      setImportResult({ error: 'Falha ao importar' })
    } finally {
      setImporting(false)
    }
  }

  // Dados para o gráfico de evolução
  const chartData = [...logs].reverse().map((l, i) => ({
    ...l,
    index: i + 1,
    score: l.performance_score,
  }))

  const avgScore = logs.length
    ? logs.filter(l => l.performance_score !== null)
        .reduce((acc, l) => acc + l.performance_score, 0) /
      Math.max(logs.filter(l => l.performance_score !== null).length, 1)
    : 0

  const topClass = logs.length
    ? Object.entries(
        logs.reduce((acc, l) => { acc[l.class] = (acc[l.class] || 0) + 1; return acc }, {})
      ).sort((a, b) => b[1] - a[1])[0]?.[0]
    : null

  const elo = player?.ratings?.[format]?.elo || 1000

  if (loading) return (
    <div style={{ textAlign: 'center', color: '#888', padding: '3rem' }}>
      Carregando perfil...
    </div>
  )

  if (error) return (
    <div style={{ textAlign: 'center', color: '#e8593c', padding: '2rem' }}>
      {error}
    </div>
  )

  return (
    <div>
      {/* Perfil header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1.5rem' }}>
        <div style={{
          width: '48px', height: '48px', borderRadius: '50%',
          background: '#e8593c', display: 'flex', alignItems: 'center',
          justifyContent: 'center', fontSize: '18px', fontWeight: 700, color: '#fff'
        }}>
          {(player?.display_name || steamId)[0].toUpperCase()}
        </div>
        <div>
          <div style={{ fontWeight: 600, fontSize: '16px' }}>
            {player?.display_name || steamId}
          </div>
          <div style={{ fontSize: '12px', color: '#555' }}>
            {steamId} {player?.discord_linked && '· Discord ✓'}
          </div>
        </div>
        {watchdog?.is_suspicious && (
          <div style={{
            marginLeft: 'auto',
            background: '#3a1a1a', color: '#e87070',
            border: '1px solid #e8707040',
            borderRadius: '8px', padding: '6px 14px', fontSize: '12px', fontWeight: 600
          }}>
            ⚠️ Watchdog: {watchdog.flags.length} flag{watchdog.flags.length > 1 ? 's' : ''}
          </div>
        )}
      </div>

      {/* Seletor de formato */}
      <div style={{ display: 'flex', gap: '6px', marginBottom: '1.5rem' }}>
        {Object.entries(FORMAT_LABELS).map(([key, label]) => (
          <button
            key={key}
            onClick={() => setFormat(key)}
            style={{
              background: format === key ? '#e8593c' : '#1a1a1a',
              color: format === key ? '#fff' : '#888',
              border: `1px solid ${format === key ? '#e8593c' : '#2a2a2a'}`,
              borderRadius: '6px', padding: '5px 14px',
              fontSize: '13px', cursor: 'pointer', fontWeight: format === key ? 600 : 400,
            }}
          >
            {label}
          </button>
        ))}
      </div>

      {/* Cards de stats */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '10px', marginBottom: '1.5rem' }}>
        <ScoreCard label="ELO" value={elo} sub={`Formato ${FORMAT_LABELS[format]}`} highlight={elo >= 1400} />
        <ScoreCard label="Partidas" value={player?.ratings?.[format]?.games || logs.length} sub={`${format}`} />
        <ScoreCard
          label="Média de Performance"
          value={`${avgScore >= 0 ? '+' : ''}${avgScore.toFixed(1)}%`}
          sub="vs. sua própria média"
          highlight={avgScore > 10}
        />
        <ScoreCard
          label="Classe principal"
          value={topClass ? `${CLASS_ICONS[topClass] || '🎮'} ${topClass}` : '—'}
          sub={`último ${logs.length} logs`}
        />
      </div>

      {/* Gráfico de evolução do Performance Score */}
      {chartData.length > 1 && (
        <div style={{
          background: '#1a1a1a', border: '1px solid #2a2a2a',
          borderRadius: '10px', padding: '1.25rem', marginBottom: '1.5rem'
        }}>
          <div style={{ fontSize: '13px', fontWeight: 600, marginBottom: '1rem', color: '#e8e6e0' }}>
            Evolução do Performance Score
          </div>
          <ResponsiveContainer width="100%" height={180}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#222" />
              <XAxis dataKey="index" tick={{ fontSize: 11, fill: '#555' }} tickLine={false} axisLine={false} />
              <YAxis tick={{ fontSize: 11, fill: '#555' }} tickLine={false} axisLine={false}
                tickFormatter={v => `${v > 0 ? '+' : ''}${v.toFixed(0)}%`} />
              <Tooltip content={<CustomTooltip />} />
              <ReferenceLine y={0} stroke="#333" strokeDasharray="4 4" />
              <Line
                type="monotone" dataKey="score"
                stroke="#e8593c" strokeWidth={2} dot={{ r: 3, fill: '#e8593c' }}
                activeDot={{ r: 5 }} connectNulls
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Importar log */}
      <div style={{
        background: '#1a1a1a', border: '1px solid #2a2a2a',
        borderRadius: '10px', padding: '1.25rem', marginBottom: '1.5rem'
      }}>
        <div style={{ fontSize: '13px', fontWeight: 600, marginBottom: '0.75rem' }}>
          Importar log do logs.tf
        </div>
        <form onSubmit={handleImport} style={{ display: 'flex', gap: '8px' }}>
          <input
            type="number"
            value={importId}
            onChange={e => setImportId(e.target.value)}
            placeholder="ID do log (ex: 3654321)"
            style={{
              flex: 1, background: '#0f1117', border: '1px solid #2a2a2a',
              borderRadius: '6px', padding: '8px 12px',
              color: '#e8e6e0', fontSize: '13px', outline: 'none',
            }}
          />
          <button type="submit" disabled={importing} style={{
            background: importing ? '#333' : '#1d4ed8',
            color: '#fff', border: 'none', borderRadius: '6px',
            padding: '8px 16px', fontSize: '13px', fontWeight: 600, cursor: 'pointer',
          }}>
            {importing ? 'Importando...' : 'Importar'}
          </button>
        </form>
        {importResult && (
          <div style={{
            marginTop: '10px', padding: '10px 12px', borderRadius: '6px',
            background: importResult.error ? '#2a1a1a' : '#1a2a1a',
            color: importResult.error ? '#e87070' : '#70e870',
            fontSize: '13px'
          }}>
            {importResult.error
              ? `❌ ${importResult.error}`
              : `✅ ${importResult.performance_label || 'Log importado!'}`
            }
          </div>
        )}
      </div>