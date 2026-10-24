import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { analysesApi } from '../api/client';
import type { Analysis, AnalysisStatus, AnalysisType, AnalysisUpdate, AnalysisRunResponse } from '../types';

const statusLabels: Record<AnalysisStatus, string> = {
  pending: 'Pending',
  running: 'Running',
  completed: 'Completed',
  failed: 'Failed',
};

const typeLabels: Record<AnalysisType, string> = {
  vtable_resolution: 'VTable Resolution',
  switch_recovery: 'Switch Recovery',
  jmp_call_recovery: 'JMP+Call Recovery',
  string_recovery: 'String Recovery',
  batch_decompilation: 'Batch Decompilation',
};

export function AnalysisDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [runResult, setRunResult] = useState<AnalysisRunResponse | null>(null);

  useEffect(() => {
    if (!id) return;
    const fetchAnalysis = async () => {
      try {
        const response = await analysesApi.get(parseInt(id));
        setAnalysis(response.data);
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to load analysis');
      } finally {
        setLoading(false);
      }
    };
    fetchAnalysis();
  }, [id]);

  const handleUpdate = async (updates: Partial<AnalysisUpdate>) => {
    if (!id || !analysis) return;
    setSaving(true);
    setError(null);
    try {
      const response = await analysesApi.update(parseInt(id), updates);
      setAnalysis(response.data);
    } catch (err: unknown) {
      const detail = err instanceof Error ? err.message : 'Failed to update analysis';
      setError(detail);
    } finally {
      setSaving(false);
    }
  };

  const handleRun = async () => {
    if (!id || !analysis) return;
    setRunning(true);
    setError(null);
    try {
      const response = await analysesApi.run(parseInt(id));
      setRunResult(response.data);
      const updated = await analysesApi.get(parseInt(id));
      setAnalysis(updated.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to run analysis');
    } finally {
      setRunning(false);
    }
  };

  const handleDelete = async () => {
    if (!id || !confirm('Are you sure you want to delete this analysis?')) return;
    try {
      await analysesApi.delete(parseInt(id));
      navigate('/analyses');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete analysis');
    }
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', padding: '3rem' }}>
        <div className="loading-spinner" style={{ width: '2rem', height: '2rem' }} />
      </div>
    );
  }

  if (error && !analysis) {
    return (
      <div className="empty-state">
        <div className="empty-state-icon">⚠️</div>
        <p>{error}</p>
        <button onClick={() => navigate('/analyses')} className="btn btn-primary" style={{ marginTop: '1rem' }}>
          Back to Analyses
        </button>
      </div>
    );
  }

  if (!analysis) return null;

  return (
    <div>
      <header className="page-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', flexWrap: 'wrap' }}>
          <div>
            <h1 className="page-title">{analysis.name}</h1>
            <p className="page-subtitle">
              {typeLabels[analysis.analysis_type]} ·{' '}
              <span className={`badge badge-${analysis.status}`}>{statusLabels[analysis.status]}</span>
            </p>
          </div>
        </div>
        <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
          <button
            onClick={handleRun}
            disabled={saving || running || analysis.status === 'running' || analysis.status === 'completed'}
            className="btn btn-primary"
          >
            {running ? 'Running...' : 'Run Analysis'}
          </button>
          <button
            onClick={() => handleUpdate({ status: analysis.status === 'pending' ? 'running' : 'pending' })}
            disabled={saving}
            className="btn btn-secondary"
          >
            {analysis.status === 'pending' ? 'Start' : 'Reset to Pending'}
          </button>
          <button
            onClick={() => handleUpdate({ status: 'completed', result_data: analysis.result_data || '{"status": "completed"}' })}
            disabled={saving || analysis.status === 'completed'}
            className="btn btn-primary"
          >
            Mark Complete
          </button>
          <button onClick={handleDelete} className="btn btn-danger">Delete</button>
        </div>
      </header>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '1.5rem' }}>
        <section className="card">
          <div style={{ padding: '1.5rem', borderBottom: '1px solid var(--border-color)' }}>
            <h2 style={{ fontSize: '1rem', fontWeight: '600' }}>Details</h2>
          </div>
          <div style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div>
              <label style={{ fontSize: '0.75rem', color: 'var(--fg-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>ID</label>
              <p style={{ fontFamily: 'monospace', fontSize: '0.875rem' }}>#{analysis.id}</p>
            </div>
            <div>
              <label style={{ fontSize: '0.75rem', color: 'var(--fg-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Type</label>
              <p>{typeLabels[analysis.analysis_type]}</p>
            </div>
            <div>
              <label style={{ fontSize: '0.75rem', color: 'var(--fg-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Status</label>
              <p><span className={`badge badge-${analysis.status}`}>{statusLabels[analysis.status]}</span></p>
            </div>
            <div>
              <label style={{ fontSize: '0.75rem', color: 'var(--fg-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Created</label>
              <p>{new Date(analysis.created_at).toLocaleString()}</p>
            </div>
            <div>
              <label style={{ fontSize: '0.75rem', color: 'var(--fg-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Updated</label>
              <p>{new Date(analysis.updated_at).toLocaleString()}</p>
            </div>
            {analysis.started_at && (
              <div>
                <label style={{ fontSize: '0.75rem', color: 'var(--fg-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Started</label>
                <p>{new Date(analysis.started_at).toLocaleString()}</p>
              </div>
            )}
            {analysis.completed_at && (
              <div>
                <label style={{ fontSize: '0.75rem', color: 'var(--fg-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Completed</label>
                <p>{new Date(analysis.completed_at).toLocaleString()}</p>
              </div>
            )}
            {runResult && (
              <div style={{ borderTop: '1px solid var(--border-color)', paddingTop: '1rem', marginTop: '0.5rem' }}>
                <label style={{ fontSize: '0.75rem', color: 'var(--fg-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Last Run Results</label>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '0.5rem', fontSize: '0.875rem' }}>
                  <div><strong>Functions:</strong> {runResult.functions_count}</div>
                  <div><strong>VTables:</strong> {runResult.vtables_count}</div>
                  <div><strong>Switches:</strong> {runResult.switches_count}</div>
                  <div><strong>JMP Calls:</strong> {runResult.jmp_calls_count}</div>
                  <div><strong>Strings:</strong> {runResult.strings_count}</div>
                  <div><strong>Cross-refs:</strong> {runResult.cross_references_count}</div>
                </div>
              </div>
            )}
          </div>
        </section>

        <section className="card" style={{ gridColumn: '1 / -1' }}>
          <div style={{ padding: '1.5rem', borderBottom: '1px solid var(--border-color)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
            <h2 style={{ fontSize: '1rem', fontWeight: '600' }}>Description</h2>
          </div>
          <div style={{ padding: '1.5rem' }}>
            {analysis.description ? (
              <p style={{ whiteSpace: 'pre-wrap', color: 'var(--fg-secondary)' }}>{analysis.description}</p>
            ) : (
              <p style={{ color: 'var(--fg-muted)' }}>No description provided.</p>
            )}
          </div>
        </section>

        <section className="card" style={{ gridColumn: '1 / -1' }}>
          <div style={{ padding: '1.5rem', borderBottom: '1px solid var(--border-color)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
            <h2 style={{ fontSize: '1rem', fontWeight: '600' }}>Input Data</h2>
          </div>
          <div style={{ padding: '1.5rem' }}>
            <pre style={{
              background: 'var(--bg-tertiary)',
              border: '1px solid var(--border-color)',
              borderRadius: 'var(--radius-sm)',
              padding: '1rem',
              overflow: 'auto',
              maxHeight: '300px',
              fontSize: '0.75rem',
              lineHeight: 1.6,
              color: 'var(--fg-secondary)',
            }}>
              {analysis.input_data || 'No input data'}
            </pre>
          </div>
        </section>

        {analysis.result_data && (
          <section className="card" style={{ gridColumn: '1 / -1' }}>
            <div style={{ padding: '1.5rem', borderBottom: '1px solid var(--border-color)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
              <h2 style={{ fontSize: '1rem', fontWeight: '600' }}>Results</h2>
            </div>
            <div style={{ padding: '1.5rem' }}>
              <pre style={{
                background: 'var(--bg-tertiary)',
                border: '1px solid var(--border-color)',
                borderRadius: 'var(--radius-sm)',
                padding: '1rem',
                overflow: 'auto',
                maxHeight: '400px',
                fontSize: '0.75rem',
                lineHeight: 1.6,
                color: 'var(--fg-primary)',
              }}>
                {analysis.result_data}
              </pre>
            </div>
          </section>
        )}

        {analysis.error_message && (
          <section className="card" style={{ gridColumn: '1 / -1', borderColor: 'var(--accent-red)' }}>
            <div style={{ padding: '1.5rem', borderBottom: '1px solid var(--border-color)' }}>
              <h2 style={{ fontSize: '1rem', fontWeight: '600', color: 'var(--accent-red)' }}>Error</h2>
            </div>
            <div style={{ padding: '1.5rem' }}>
              <pre style={{
                background: 'rgba(243, 139, 168, 0.1)',
                border: '1px solid var(--accent-red)',
                borderRadius: 'var(--radius-sm)',
                padding: '1rem',
                overflow: 'auto',
                maxHeight: '200px',
                fontSize: '0.75rem',
                lineHeight: 1.6,
                color: 'var(--accent-red)',
              }}>
                {analysis.error_message}
              </pre>
            </div>
          </section>
        )}
      </div>
    </div>
  );
}
