// frontend/app/page.js
'use client'

import { useState } from 'react'
import PlayerDashboard from './components/PlayerDashboard'

export default function Home() {
  const [steamId, setSteamId] = useState('')
  const [submitted, setSubmitted] = useState('')

  function handleSearch(e) {
    e.preventDefault()
    if (steamId.trim()) setSubmitted(steamId.trim())
  }

  return (
    <main style={{ minHeight: '100vh', background: '#0f1117', color: '#e8e6e0', fontFamily: 'sans-serif' }}>
      {/* Header */}
      <header style={{
        borderBottom: '1px solid #2a2a2a',
        padding: '0 2rem',
        height: '56px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        background: '#0f1117'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span style={{ fontSize: '20px', fontWeight: 700, color: '#e8593c', letterSpacing: '-0.5px' }}>
            TF2Hub
          </span>
          <span style={{ fontSize: '11px', color: '#666', background: '#1a1a1a', padding: '2px 8px', borderRadius: '4px', border: '1px solid #2a2a2a' }}>
            BR
          </span>
        </div>
        <nav style={{ display: 'flex', gap: '1.5rem', fontSize: '13px', color: '#888' }}>
          <a href="#" style={{ color: '#e8e6e0', textDecoration: 'none' }}>Dashboard</a>
          <a href="#" style={{ color: '#888', textDecoration: 'none' }}>Leaderboard</a>
          <a href="#" style={{ color: '#888', textDecoration: 'none' }}>Watchdog</a>
        </nav>
      </header>

      <div style={{ maxWidth: '900px', margin: '0 auto', padding: '3rem 2rem' }}>
        {/* Hero */}
        {!submitted && (
          <div style={{ textAlign: 'center', marginBottom: '3rem' }}>
            <h1 style={{ fontSize: '2.5rem', fontWeight: 700, margin: '0 0 0.5rem', lineHeight: 1.2 }}>
              O sistema operacional do<br />
              <span style={{ color: '#e8593c' }}>TF2 competitivo brasileiro</span>
            </h1>
            <p style={{ color: '#888', fontSize: '1rem', margin: '1rem 0 2rem' }}>
              Cole seu Steam ID e veja sua evolução, Performance Score e análise de suspeita
            </p>
          </div>
        )}

        {/* Busca */}
        <form onSubmit={handleSearch} style={{ display: 'flex', gap: '8px', maxWidth: '520px', margin: '0 auto 2.5rem' }}>
          <input
            type="text"
            value={steamId}
            onChange={e => setSteamId(e.target.value)}
            placeholder="Steam ID ex: 76561198xxxxxxxxx"
            style={{
              flex: 1,
              background: '#1a1a1a',
              border: '1px solid #2a2a2a',
              borderRadius: '8px',
              padding: '10px 14px',
              color: '#e8e6e0',
              fontSize: '14px',
              outline: 'none',
            }}
          />
          <button type="submit" style={{
            background: '#e8593c',
            color: '#fff',
            border: 'none',
            borderRadius: '8px',
            padding: '10px 20px',
            fontSize: '14px',
            fontWeight: 600,
            cursor: 'pointer',
          }}>
            Buscar
          </button>
        </form>

        {/* Dashboard do jogador */}
        {submitted && <PlayerDashboard steamId={submitted} />}
      </div>
    </main>
  )
}