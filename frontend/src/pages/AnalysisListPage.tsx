import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { analysesApi } from '../api/client';
import type { Analysis, AnalysisStatus, AnalysisType } from '../types';

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

const allTypes: AnalysisType[] = [
  'vtable_resolution',
  'switch_recovery',
  'jmp_call_recovery',
  'string_recovery',
  'batch_decompilation',
];

const allStatuses: AnalysisStatus[] = ['pending', 'running', 'completed', 'failed'];

export function AnalysisListPage() {
  const [analyses, setAnalyses] = useState<Analysis[]>([]);
  const [loading, setLoading] = useState(true);
  const [pagination, setPagination] = useState({ total: 0, page: 1, page_size: 20, total_pages: 0 });
  const [filters, setFilters] = useState({ status: '', analysis_type: '' });

  const fetchAnalyses = async () => {
    setLoading(true);
    try {
      const response = await analysesApi.list({
        page: pagination.page,
        page_size: pagination.page_size,
        status: filters.status || undefined,
        analysis_type: filters.analysis_type || undefined,
      });
      setAnalyses(response.data.items);
      setPagination(prev => ({
        ...prev,
        total: response.data.total,
        total_pages: response.data.total_pages,
      }));
    } catch (error) {
      console.error('Failed to fetch analyses:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalyses();
  }, [pagination.page, filters]);

  const handlePageChange = (newPage: number) => {
    if (newPage >= 1 && newPage <= pagination.total_pages) {
      setPagination(prev => ({ ...prev, page: newPage }));
    }
  };

  const handleFilterChange = (key: 'status' | 'analysis_type', value: string) => {
    setFilters(prev => ({ ...prev, [key]: value }));
    setPagination(prev => ({ ...prev, page: 1 }));
  };

  const content = loading ? (
    <div style={{ padding: '3rem', textAlign: 'center' }}>
      <div className="loading-spinner" />
    </div>
  ) : analyses.length === 0 ? (
    <div className="empty-state" style={{ padding: '3rem' }}>
      <div className="empty-state-icon">📋</div>
      <p>No analyses found</p>
      <Link to="/analyses/new" className="btn btn-primary" style={{ marginTop: '1rem' }}>
        Create your first analysis
      </Link>
    </div>
  ) : (
    <>
      <div className="table-container">
        <table>
          <thead>
            <tr>
              <th style={{ width: '35%' }}>Name</th>
              <th style={{ width: '20%' }}>Type</th>
              <th style={{ width: '15%' }}>Status</th>
              <th style={{ width: '15%' }}>Created</th>
              <th style={{ width: '15%' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {analyses.map((analysis) => (
              <tr key={analysis.id}>
                <td>
                  <Link to={`/analyses/${analysis.id}`} style={{ fontWeight: '500' }}>
                    {analysis.name}
                  </Link>
                  {analysis.description && (
                    <p style={{ fontSize: '0.75rem', color: 'var(--fg-muted)', marginTop: '0.25rem', maxWidth: '300px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {analysis.description}
                    </p>
                  )}
                </td>
                <td>
                  <span style={{ fontSize: '0.8125rem', color: 'var(--fg-secondary)' }}>
                    {typeLabels[analysis.analysis_type]}
                  </span>
                </td>
                <td>
                  <span className={`badge badge-${analysis.status}`}>
                    {statusLabels[analysis.status]}
                  </span>
                </td>
                <td style={{ fontSize: '0.8125rem', color: 'var(--fg-secondary)' }}>
                  {new Date(analysis.created_at).toLocaleDateString()}
                </td>
                <td>
                  <div style={{ display: 'flex', gap: '0.5rem' }}>
                    <Link to={`/analyses/${analysis.id}`} className="btn btn-ghost" style={{ padding: '0.375rem' }} title="View">
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                        <circle cx="12" cy="12" r="3"/>
                      </svg>
                    </Link>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {pagination.total_pages > 1 && (
        <div style={{ padding: '1rem 1.5rem', borderTop: '1px solid var(--border-color)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem' }}>
          <p style={{ fontSize: '0.875rem', color: 'var(--fg-secondary)' }}>
            Showing {((pagination.page - 1) * pagination.page_size) + 1}–{Math.min(pagination.page * pagination.page_size, pagination.total)} of {pagination.total}
          </p>
          <div style={{ display: 'flex', gap: '0.375rem' }}>
            <button
              onClick={() => handlePageChange(pagination.page - 1)}
              disabled={pagination.page === 1}
              className="btn btn-secondary"
              style={{ padding: '0.375rem 0.75rem' }}
            >
              Previous
            </button>
            <button
              onClick={() => handlePageChange(pagination.page + 1)}
              disabled={pagination.page === pagination.total_pages}
              className="btn btn-secondary"
              style={{ padding: '0.375rem 0.75rem' }}
            >
              Next
            </button>
          </div>
        </div>
      )}
    </>
  );

  return (
    <div>
      <header className="page-header">
        <div>
          <h1 className="page-title">Analyses</h1>
          <p className="page-subtitle">Manage and track your reverse engineering analyses</p>
        </div>
        <Link to="/analyses/new" className="btn btn-primary">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <line x1="12" y1="5" x2="12" y2="19"/>
            <line x1="5" y1="12" x2="19" y2="12"/>
          </svg>
          New Analysis
        </Link>
      </header>

      <section className="card" style={{ marginBottom: '1.5rem' }}>
        <div style={{ padding: '1rem 1.5rem', display: 'flex', gap: '1rem', flexWrap: 'wrap', alignItems: 'end' }}>
          <div className="form-group" style={{ minWidth: '180px' }}>
            <label className="form-label">Status</label>
            <select
              value={filters.status}
              onChange={(e) => handleFilterChange('status', e.target.value)}
              style={{ width: '100%' }}
            >
              <option value="">All Statuses</option>
              {allStatuses.map(s => <option key={s} value={s}>{statusLabels[s]}</option>)}
            </select>
          </div>
          <div className="form-group" style={{ minWidth: '200px' }}>
            <label className="form-label">Analysis Type</label>
            <select
              value={filters.analysis_type}
              onChange={(e) => handleFilterChange('analysis_type', e.target.value)}
              style={{ width: '100%' }}
            >
              <option value="">All Types</option>
              {allTypes.map(t => <option key={t} value={t}>{typeLabels[t]}</option>)}
            </select>
          </div>
          {(filters.status || filters.analysis_type) && (
            <button
              onClick={() => { setFilters({ status: '', analysis_type: '' }); setPagination(prev => ({ ...prev, page: 1 })); }}
              className="btn btn-ghost"
            >
              Clear filters
            </button>
          )}
        </div>
      </section>

      <section className="card">
        {content}
      </section>
    </div>
  );
}