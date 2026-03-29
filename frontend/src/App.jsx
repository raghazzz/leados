import { useState, useEffect } from 'react'
import { getLeads, createLead, generateEmail, uploadCSV } from './api/client'
import './App.css'

function ScoreBadge({ score }) {
  const color = score >= 80 ? '#00ff88' : score >= 60 ? '#ffbb00' : '#ff4466'
  return (
    <span style={{
      background: `${color}22`,
      color: color,
      border: `1px solid ${color}44`,
      borderRadius: 6,
      padding: '2px 10px',
      fontWeight: 700,
      fontSize: 13,
    }}>
      {score}
    </span>
  )
}

function StatusBadge({ status }) {
  const colors = {
    qualified: '#00ff88',
    disqualified: '#ff4466',
    email_sent: '#00bbff',
    follow_up_1: '#ffbb00',
    follow_up_2: '#ff8833',
    converted: '#aa44ff',
    ingested: '#667799',
    scoring: '#667799',
  }
  const color = colors[status] || '#667799'
  return (
    <span style={{
      background: `${color}22`,
      color: color,
      border: `1px solid ${color}44`,
      borderRadius: 6,
      padding: '2px 10px',
      fontSize: 11,
      fontWeight: 600,
      textTransform: 'uppercase',
      letterSpacing: '0.05em',
    }}>
      {status}
    </span>
  )
}

export default function App() {
  const [leads, setLeads] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [selectedLead, setSelectedLead] = useState(null)
  const [emails, setEmails] = useState([])
  const [generatingEmail, setGeneratingEmail] = useState(false)
  const [activeTab, setActiveTab] = useState('leads')
  const [uploading, setUploading] = useState(false)
  const [uploadResult, setUploadResult] = useState(null)
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [newLead, setNewLead] = useState({
    name: '', email: '', company: '',
    title: '', industry: '', company_size: ''
  })

  // Load leads when app starts
  useEffect(() => {
    loadLeads()
  }, [])

  const loadLeads = async () => {
    try {
      setLoading(true)
      const data = await getLeads()
      setLeads(data.leads)
      setError(null)
    } catch (err) {
      setError('Could not connect to backend. Is your server running?')
    } finally {
      setLoading(false)
    }
  }

  const handleSelectLead = async (lead) => {
    setSelectedLead(lead)
    setActiveTab('detail')
    try {
      const { getLeadEmails } = await import('./api/client')
      const data = await getLeadEmails(lead.id)
      setEmails(data)
    } catch {
      setEmails([])
    }
  }

  const handleGenerateEmail = async (emailType = 'outreach') => {
    if (!selectedLead) return
    setGeneratingEmail(true)
    try {
      const email = await generateEmail(selectedLead.id, emailType)
      setEmails(prev => [email, ...prev])
    } catch (err) {
      alert('Email generation failed')
    } finally {
      setGeneratingEmail(false)
    }
  }

  const handleCSVUpload = async (e) => {
    const file = e.target.files[0]
    if (!file) return
    setUploading(true)
    setUploadResult(null)
    try {
      const result = await uploadCSV(file)
      setUploadResult(result)
      loadLeads()
    } catch (err) {
      alert('Upload failed')
    } finally {
      setUploading(false)
    }
  }

  const handleCreateLead = async (e) => {
    e.preventDefault()
    try {
      await createLead(newLead)
      setShowCreateForm(false)
      setNewLead({ name: '', email: '', company: '', title: '', industry: '', company_size: '' })
      loadLeads()
    } catch (err) {
      alert('Failed to create lead')
    }
  }

  const styles = {
    app: {
      minHeight: '100vh',
      background: '#080c14',
      color: '#e8edf5',
      fontFamily: 'system-ui, sans-serif',
      display: 'flex',
    },
    sidebar: {
      width: 220,
      background: 'rgba(255,255,255,0.02)',
      borderRight: '1px solid rgba(255,255,255,0.06)',
      padding: '24px 12px',
      display: 'flex',
      flexDirection: 'column',
      gap: 4,
      flexShrink: 0,
    },
    logo: {
      fontWeight: 800,
      fontSize: 20,
      color: '#00ff88',
      padding: '0 12px 24px',
      letterSpacing: '-0.02em',
    },
    navBtn: (active) => ({
      background: active ? 'rgba(0,255,136,0.1)' : 'transparent',
      border: active ? '1px solid rgba(0,255,136,0.2)' : '1px solid transparent',
      color: active ? '#00ff88' : '#4a6080',
      borderRadius: 8,
      padding: '10px 14px',
      cursor: 'pointer',
      textAlign: 'left',
      fontSize: 13,
      fontWeight: 500,
    }),
    main: {
      flex: 1,
      padding: 32,
      overflow: 'auto',
    },
    card: {
      background: 'rgba(255,255,255,0.03)',
      border: '1px solid rgba(255,255,255,0.07)',
      borderRadius: 14,
      padding: 24,
      marginBottom: 20,
    },
    table: {
      width: '100%',
      borderCollapse: 'collapse',
    },
    th: {
      textAlign: 'left',
      padding: '10px 16px',
      fontSize: 10,
      color: '#2d3d55',
      letterSpacing: '0.1em',
      textTransform: 'uppercase',
      borderBottom: '1px solid rgba(255,255,255,0.05)',
    },
    td: {
      padding: '14px 16px',
      borderBottom: '1px solid rgba(255,255,255,0.03)',
      fontSize: 13,
    },
    btn: (color = '#00ff88') => ({
      background: `${color}18`,
      color: color,
      border: `1px solid ${color}33`,
      borderRadius: 8,
      padding: '8px 16px',
      cursor: 'pointer',
      fontSize: 13,
      fontWeight: 600,
    }),
    input: {
      background: 'rgba(255,255,255,0.05)',
      border: '1px solid rgba(255,255,255,0.1)',
      borderRadius: 8,
      padding: '10px 14px',
      color: '#e8edf5',
      fontSize: 13,
      width: '100%',
      marginBottom: 12,
    },
  }

  return (
    <div style={styles.app}>
      {/* Sidebar */}
      <div style={styles.sidebar}>
        <div style={styles.logo}>⚡ LeadOS</div>
        {[
          { id: 'leads', label: '◈ Pipeline' },
          { id: 'upload', label: '⬆ Import CSV' },
          { id: 'create', label: '+ New Lead' },
        ].map(item => (
          <button
            key={item.id}
            style={styles.navBtn(activeTab === item.id)}
            onClick={() => {
              setActiveTab(item.id)
              if (item.id === 'create') setShowCreateForm(true)
            }}
          >
            {item.label}
          </button>
        ))}
      </div>

      {/* Main content */}
      <div style={styles.main}>

        {/* LEADS TAB */}
        {activeTab === 'leads' && (
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
              <div>
                <h1 style={{ fontSize: 24, fontWeight: 800, margin: 0 }}>Lead Pipeline</h1>
                <p style={{ color: '#4a6080', margin: '4px 0 0', fontSize: 13 }}>
                  {leads.length} leads · sorted by score
                </p>
              </div>
              <button style={styles.btn()} onClick={loadLeads}>↻ Refresh</button>
            </div>

            {error && (
              <div style={{ ...styles.card, borderColor: '#ff446633', color: '#ff4466' }}>
                ⚠ {error}
              </div>
            )}

            {loading ? (
              <div style={{ ...styles.card, textAlign: 'center', color: '#4a6080' }}>
                Loading leads...
              </div>
            ) : (
              <div style={styles.card}>
                <table style={styles.table}>
                  <thead>
                    <tr>
                      {['Name', 'Company', 'Title', 'Industry', 'Score', 'Status', 'Action'].map(h => (
                        <th key={h} style={styles.th}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {leads.map(lead => (
                      <tr key={lead.id} style={{ cursor: 'pointer' }}
                        onMouseEnter={e => e.currentTarget.style.background = 'rgba(0,255,136,0.03)'}
                        onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                      >
                        <td style={styles.td}>
                          <div style={{ fontWeight: 600 }}>{lead.name}</div>
                          <div style={{ fontSize: 11, color: '#4a6080' }}>{lead.email}</div>
                        </td>
                        <td style={styles.td}>{lead.company || '—'}</td>
                        <td style={styles.td}>{lead.title || '—'}</td>
                        <td style={styles.td}>{lead.industry || '—'}</td>
                        <td style={styles.td}><ScoreBadge score={lead.score} /></td>
                        <td style={styles.td}><StatusBadge status={lead.status} /></td>
                        <td style={styles.td}>
                          <button style={styles.btn()} onClick={() => handleSelectLead(lead)}>
                            View →
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* LEAD DETAIL TAB */}
        {activeTab === 'detail' && selectedLead && (
          <div>
            <button style={{ ...styles.btn('#667799'), marginBottom: 20 }}
              onClick={() => setActiveTab('leads')}>
              ← Back to Pipeline
            </button>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
              {/* Lead info */}
              <div style={styles.card}>
                <h2 style={{ margin: '0 0 16px', fontSize: 18 }}>{selectedLead.name}</h2>
                {[
                  ['Email', selectedLead.email],
                  ['Company', selectedLead.company],
                  ['Title', selectedLead.title],
                  ['Industry', selectedLead.industry],
                  ['Company Size', selectedLead.company_size],
                  ['Status', selectedLead.status],
                  ['Qualified', selectedLead.is_qualified ? '✅ Yes' : '❌ No'],
                  ['Responded', selectedLead.responded ? '✅ Yes' : '❌ No'],
                  ['Converted', selectedLead.converted ? '✅ Yes' : '❌ No'],
                ].map(([label, value]) => (
                  <div key={label} style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid rgba(255,255,255,0.04)', fontSize: 13 }}>
                    <span style={{ color: '#4a6080' }}>{label}</span>
                    <span>{value || '—'}</span>
                  </div>
                ))}
              </div>

              {/* Score breakdown */}
              <div style={styles.card}>
                <h2 style={{ margin: '0 0 16px', fontSize: 18 }}>
                  Score: <span style={{ color: '#00ff88' }}>{selectedLead.score}</span>
                </h2>
                {selectedLead.score_breakdown && Object.entries(selectedLead.score_breakdown)
                  .filter(([key]) => key !== 'overall')
                  .map(([key, value]) => (
                    <div key={key} style={{ marginBottom: 12 }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, marginBottom: 4 }}>
                        <span style={{ color: '#4a6080', textTransform: 'capitalize' }}>
                          {key.replace(/_/g, ' ')}
                        </span>
                        <span style={{ color: '#00ff88' }}>{(value * 100).toFixed(0)}%</span>
                      </div>
                      <div style={{ height: 4, background: 'rgba(255,255,255,0.06)', borderRadius: 2 }}>
                        <div style={{ height: '100%', width: `${value * 100}%`, background: '#00ff88', borderRadius: 2 }} />
                      </div>
                    </div>
                  ))
                }
              </div>
            </div>

            {/* Email generation */}
            <div style={styles.card}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                <h2 style={{ margin: 0, fontSize: 18 }}>AI Emails</h2>
                <div style={{ display: 'flex', gap: 8 }}>
                  {['outreach', 'follow_up_1', 'follow_up_2'].map(type => (
                    <button key={type} style={styles.btn()} onClick={() => handleGenerateEmail(type)}
                      disabled={generatingEmail}>
                      {generatingEmail ? '⚡ Generating...' : `+ ${type.replace(/_/g, ' ')}`}
                    </button>
                  ))}
                </div>
              </div>

              {emails.length === 0 ? (
                <p style={{ color: '#4a6080', fontSize: 13 }}>No emails generated yet. Click a button above to generate one.</p>
              ) : (
                emails.map(email => (
                  <div key={email.id} style={{ background: 'rgba(0,0,0,0.3)', borderRadius: 10, padding: 16, marginBottom: 12, border: '1px solid rgba(255,255,255,0.06)' }}>
                    <div style={{ fontSize: 11, color: '#4a6080', marginBottom: 4, textTransform: 'uppercase', letterSpacing: '0.08em' }}>{email.email_type}</div>
                    <div style={{ fontWeight: 600, marginBottom: 8 }}>{email.subject}</div>
                    <div style={{ fontSize: 13, color: '#8899bb', lineHeight: 1.7, whiteSpace: 'pre-line' }}>{email.body}</div>
                  </div>
                ))
              )}
            </div>
          </div>
        )}

        {/* UPLOAD TAB */}
        {activeTab === 'upload' && (
          <div>
            <h1 style={{ fontSize: 24, fontWeight: 800, marginBottom: 24 }}>Import CSV</h1>
            <div style={{ ...styles.card, textAlign: 'center', padding: 48 }}>
              {!uploading && !uploadResult && (
                <>
                  <div style={{ fontSize: 48, marginBottom: 16 }}>⬆</div>
                  <h2 style={{ marginBottom: 8 }}>Upload your leads CSV</h2>
                  <p style={{ color: '#4a6080', marginBottom: 24 }}>
                    All leads will be automatically scored by the ML model
                  </p>
                  <input type="file" accept=".csv" onChange={handleCSVUpload}
                    style={{ display: 'none' }} id="csvInput" />
                  <label htmlFor="csvInput" style={{ ...styles.btn(), padding: '12px 28px', cursor: 'pointer' }}>
                    Select CSV File
                  </label>
                  <div style={{ marginTop: 24, color: '#2d3d55', fontSize: 12 }}>
                    Expected columns: name, email, company, title, industry, company_size
                  </div>
                </>
              )}
              {uploading && (
                <div>
                  <div style={{ fontSize: 32, marginBottom: 16 }}>⚡</div>
                  <h2 style={{ color: '#00ff88' }}>Processing leads...</h2>
                  <p style={{ color: '#4a6080' }}>Scoring all leads with ML model</p>
                </div>
              )}
              {uploadResult && (
                <div>
                  <div style={{ fontSize: 48, marginBottom: 16 }}>✅</div>
                  <h2 style={{ color: '#00ff88', marginBottom: 16 }}>
                    {uploadResult.ingested} leads imported!
                  </h2>
                  {[
                    ['Qualified', uploadResult.qualified],
                    ['Disqualified', uploadResult.disqualified],
                    ['Errors', uploadResult.errors?.length || 0],
                  ].map(([label, value]) => (
                    <div key={label} style={{ fontSize: 14, color: '#8899bb', marginBottom: 4 }}>
                      {label}: <strong style={{ color: '#e8edf5' }}>{value}</strong>
                    </div>
                  ))}
                  <button style={{ ...styles.btn(), marginTop: 20 }}
                    onClick={() => { setUploadResult(null); setActiveTab('leads') }}>
                    View Pipeline →
                  </button>
                </div>
              )}
            </div>
          </div>
        )}

        {/* CREATE LEAD TAB */}
        {activeTab === 'create' && (
          <div>
            <h1 style={{ fontSize: 24, fontWeight: 800, marginBottom: 24 }}>Add New Lead</h1>
            <div style={{ ...styles.card, maxWidth: 500 }}>
              <form onSubmit={handleCreateLead}>
                {[
                  { key: 'name', label: 'Full Name *', placeholder: 'Sophia Chen' },
                  { key: 'email', label: 'Email *', placeholder: 'sophia@company.com' },
                  { key: 'company', label: 'Company', placeholder: 'NovaTech Labs' },
                  { key: 'title', label: 'Job Title', placeholder: 'VP Sales' },
                  { key: 'industry', label: 'Industry', placeholder: 'SaaS' },
                  { key: 'company_size', label: 'Company Size', placeholder: '50-200' },
                ].map(field => (
                  <div key={field.key}>
                    <label style={{ fontSize: 12, color: '#4a6080', display: 'block', marginBottom: 4 }}>
                      {field.label}
                    </label>
                    <input
                      style={styles.input}
                      placeholder={field.placeholder}
                      value={newLead[field.key]}
                      onChange={e => setNewLead(prev => ({ ...prev, [field.key]: e.target.value }))}
                      required={field.key === 'name' || field.key === 'email'}
                    />
                  </div>
                ))}
                <button type="submit" style={{ ...styles.btn(), width: '100%', padding: '12px' }}>
                  ✦ Create + Score Lead
                </button>
              </form>
            </div>
          </div>
        )}

      </div>
    </div>
  )
}
