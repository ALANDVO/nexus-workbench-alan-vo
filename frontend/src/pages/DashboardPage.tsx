import { Link } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { analysesApi } from '../api/client';
import type { Analysis, AnalysisStatus } from '../types';

const statusLabels: Record<AnalysisStatus, string> = {
  pending: 'Pending',
  running: 'Running',
  completed: 'Completed',
  failed: 'Failed',
};

const typeLabels: Record<string, string> = {
  vtable_resolution: 'VTable Resolution',
  switch_recovery: 'Switch Recovery',
  jmp_call_recovery: 'JMP+Call Recovery',
  string_recovery: 'String Recovery',
  batch_decompilation: 'Batch Decompilation',
};

export function DashboardPage() {
  const { user } = useAuth();
  const [recentAnalyses, setRecentAnalyses] = useState<Analysis[]>([]);
  const [stats, setStats] = useState({ total: 0, completed: 0, running: 0, failed: 0 });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [listRes] = await Promise.all([
          analysesApi.list({ page: 1, page_size: 5 }),
        ]);
        setRecentAnalyses(listRes.data.items);
        setStats({
          total: listRes.data.total,
          completed: listRes.data.items.filter(a => a.status === 'completed').length,
          running: listRes.data.items.filter(a => a.status === 'running').length,
          failed: listRes.data.items.filter(a => a.status === 'failed').length,
        });
      } catch (error) {
        console.error('Failed to fetch dashboard data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  return (
    <div>
      <header className="page-header">
        <div>
          <h1 className="page-title">Dashboard</h1>
          <p className="page-subtitle">Welcome back, {user?.username || 'User'}</p>
        </div>
        <Link to="/analyses" className="btn btn-primary">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <line x1="12" y1="5" x2="12" y2="19"/>
            <line x1="5" y1="12" x2="19" y2="12"/>
          </svg>
          New Analysis
        </Link>
      </header>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginBottom: '2rem' }}>
        <StatCard label="Total Analyses" value={stats.total} icon="📋" />
        <StatCard label="Completed" value={stats.completed} icon="✅" color="var(--accent-green)" />
        <StatCard label="Running" value={stats.running} icon="⚙️" color="var(--accent-blue)" />
        <StatCard label="Failed" value={stats.failed} icon="❌" color="var(--accent-red)" />
      </div>

      <section className="card">
        <div style={{ padding: '1.5rem', borderBottom: '1px solid var(--border-color)' }}>
          <h2 style={{ fontSize: '1.125rem', fontWeight: '600' }}>Recent Analyses</h2>
        </div>
        {loading ? (
          <div style={{ padding: '3rem', textAlign: 'center' }}>
            <div className="loading-spinner" />
          </div>
        ) : recentAnalyses.length === 0 ? (
          <div className="empty-state" style={{ padding: '3rem' }}>
            <div className="empty-state-icon">🔍</div>
            <p>No analyses yet</p>
            <Link to="/analyses" className="btn btn-primary" style={{ marginTop: '1rem' }}>
              Create your first analysis
            </Link>
          </div>
        ) : (
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Type</th>
                  <th>Status</th>
                  <th>Updated</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {recentAnalyses.map((analysis) => (
                  <tr key={analysis.id}>
                    <td>
                      <Link to={`/analyses/${analysis.id}`} style={{ fontWeight: '500' }}>
                        {analysis.name}
                      </Link>
                    </td>
                    <td>
                      <span style={{ fontSize: '0.8125rem', color: 'var(--fg-secondary)' }}>
                        {typeLabels[analysis.analysis_type] || analysis.analysis_type}
                      </span>
                    </td>
                    <td>
                      <span className={`badge badge-${analysis.status}`}>
                        {statusLabels[analysis.status]}
                      </span>
                    </td>
                    <td style={{ fontSize: '0.8125rem', color: 'var(--fg-secondary)' }}>
                      {new Date(analysis.updated_at).toLocaleDateString()}
                    </td>
                    <td>
                      <Link to={`/analyses/${analysis.id}`} className="btn btn-ghost" style={{ padding: '0.375rem' }}>
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                          <circle cx="12" cy="12" r="3"/>
                        </svg>
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        {!loading && recentAnalyses.length > 0 && (
          <div style={{ padding: '1rem 1.5rem', borderTop: '1px solid var(--border-color)', textAlign: 'right' }}>
            <Link to="/analyses" className="btn btn-ghost">
              View all analyses
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="5" y1="12" x2="19" y2="12"/>
                <polyline points="12 5 19 12 12 19"/>
              </svg>
            </Link>
          </div>
        )}
      </section>
    </div>
  );
}

function StatCard({ label, value, icon, color = 'var(--accent-blue)' }: { label: string; value: number; icon: string; color?: string }) {
  return (
    <div className="card" style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <span style={{ fontSize: '0.875rem', color: 'var(--fg-secondary)' }}>{label}</span>
        <span style={{ fontSize: '1.5rem' }}>{icon}</span>
      </div>
      <div style={{ fontSize: '2.5rem', fontWeight: '700', color, lineHeight: 1 }}>
        {value}
      </div>
    </div>
  );
}

import { useState, useEffect } from 'react';