import { useAuth } from '../hooks/useAuth';

export function LoginPage() {
  const { login, config, loading } = useAuth();

  const handleLogin = async () => {
    try {
      await login();
    } catch (error) {
      console.error('Login failed:', error);
      alert('Failed to initiate login. Please try again.');
    }
  };

  if (loading) {
    return (
      <div className="empty-state">
        <div className="loading-spinner" style={{ width: '3rem', height: '3rem', borderWidth: '3px' }} />
        <p>Loading...</p>
      </div>
    );
  }

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: '70vh',
      textAlign: 'center',
      maxWidth: '480px',
      margin: '0 auto',
      padding: '2rem',
    }}>
      <div style={{ marginBottom: '2rem' }}>
        <svg width="80" height="80" viewBox="0 0 32 32" fill="none">
          <rect width="32" height="32" rx="6" fill="#1e1e2e"/>
          <path d="M8 12h16M8 16h12M8 20h8" stroke="#89b4fa" strokeWidth="2" strokeLinecap="round"/>
          <circle cx="24" cy="20" r="4" stroke="#fab387" strokeWidth="2"/>
        </svg>
      </div>

      <h1 style={{ fontSize: '2.5rem', fontWeight: '700', marginBottom: '0.5rem', color: 'var(--fg-primary)' }}>
        Nexus Workbench
      </h1>
      <p style={{ fontSize: '1.125rem', color: 'var(--fg-secondary)', marginBottom: '2.5rem', maxWidth: '400px' }}>
        AI-assisted reverse engineering workbench for decompiler analysis.
        Sign in with Keycloak to access your analyses.
      </p>

      <button
        onClick={handleLogin}
        className="btn btn-primary"
        style={{ width: '100%', padding: '0.875rem 1.5rem', fontSize: '1rem' }}
        disabled={loading}
      >
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"/>
          <polyline points="10 17 15 12 10 7"/>
          <line x1="15" y1="12" x2="3" y2="12"/>
        </svg>
        Sign in with Keycloak
      </button>

      {config && (
        <div style={{ marginTop: '2rem', padding: '1rem', background: 'var(--bg-secondary)', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-md)', textAlign: 'left', maxWidth: '480px', width: '100%' }}>
          <p style={{ fontSize: '0.75rem', color: 'var(--fg-muted)', marginBottom: '0.5rem' }}>Keycloak Configuration:</p>
          <dl style={{ display: 'grid', gridTemplateColumns: 'auto 1fr', gap: '0.5rem 1rem', fontSize: '0.8125rem' }}>
            <dt style={{ color: 'var(--fg-muted)' }}>URL:</dt>
            <dd style={{ color: 'var(--fg-primary)', fontFamily: 'monospace' }}>{config.keycloak_url}</dd>
            <dt style={{ color: 'var(--fg-muted)' }}>Realm:</dt>
            <dd style={{ color: 'var(--fg-primary)' }}>{config.realm}</dd>
            <dt style={{ color: 'var(--fg-muted)' }}>Client:</dt>
            <dd style={{ color: 'var(--fg-primary)' }}>{config.client_id}</dd>
          </dl>
        </div>
      )}
    </div>
  );
}