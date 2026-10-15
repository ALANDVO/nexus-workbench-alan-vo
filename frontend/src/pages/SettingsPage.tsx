import { useState } from 'react';
import { useAuth } from '../hooks/useAuth';

export function SettingsPage() {
  const { user, config } = useAuth();
  const [copied, setCopied] = useState(false);

  const copyToClipboard = async (text: string) => {
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div style={{ maxWidth: '800px' }}>
      <header className="page-header">
        <div>
          <h1 className="page-title">Settings</h1>
          <p className="page-subtitle">Configure your workspace and view system information</p>
        </div>
      </header>

      <section className="card" style={{ marginBottom: '1.5rem' }}>
        <div style={{ padding: '1.5rem', borderBottom: '1px solid var(--border-color)' }}>
          <h2 style={{ fontSize: '1rem', fontWeight: '600' }}>Account</h2>
        </div>
        <div style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', flexWrap: 'wrap' }}>
            <div style={{
              width: '64px', height: '64px', borderRadius: '50%',
              background: 'linear-gradient(135deg, var(--accent-blue), var(--accent-peach))',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: '1.5rem', fontWeight: '700', color: 'var(--bg-primary)',
            }}>
              {(user?.username || 'U')[0].toUpperCase()}
            </div>
            <div>
              <p style={{ fontSize: '1.125rem', fontWeight: '600' }}>{user?.username || 'Unknown'}</p>
              <p style={{ fontSize: '0.875rem', color: 'var(--fg-secondary)' }}>{user?.email || 'No email'}</p>
              <span className={`badge`} style={{
                background: user?.role === 'admin' ? 'rgba(249, 226, 175, 0.2)' :
                           user?.role === 'operator' ? 'rgba(137, 180, 250, 0.2)' :
                           'rgba(166, 227, 161, 0.2)',
                color: user?.role === 'admin' ? 'var(--accent-yellow)' :
                       user?.role === 'operator' ? 'var(--accent-blue)' :
                       'var(--accent-green)',
              }}>
                {user?.role || 'viewer'}
              </span>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
            <SettingItem label="Subject ID" value={user?.sub || 'N/A'} copyable onCopy={() => copyToClipboard(user?.sub || '')} copied={copied} />
            <SettingItem label="User ID" value={user?.id?.toString() || 'N/A'} />
            <SettingItem label="Role" value={user?.role || 'N/A'} />
          </div>
        </div>
      </section>

      <section className="card" style={{ marginBottom: '1.5rem' }}>
        <div style={{ padding: '1.5rem', borderBottom: '1px solid var(--border-color)' }}>
          <h2 style={{ fontSize: '1rem', fontWeight: '600' }}>Keycloak Configuration</h2>
        </div>
        <div style={{ padding: '1.5rem' }}>
          {config ? (
            <dl style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '1rem 2rem' }}>
              <SettingItem label="Keycloak URL" value={config.keycloak_url} copyable onCopy={() => copyToClipboard(config.keycloak_url)} copied={copied} />
              <SettingItem label="Realm" value={config.realm} />
              <SettingItem label="Client ID" value={config.client_id} copyable onCopy={() => copyToClipboard(config.client_id)} copied={copied} />
              <SettingItem label="Redirect URI" value={config.redirect_uri} copyable onCopy={() => copyToClipboard(config.redirect_uri)} copied={copied} />
            </dl>
          ) : (
            <p style={{ color: 'var(--fg-muted)' }}>Configuration not loaded</p>
          )}
        </div>
      </section>

      <section className="card" style={{ marginBottom: '1.5rem' }}>
        <div style={{ padding: '1.5rem', borderBottom: '1px solid var(--border-color)' }}>
          <h2 style={{ fontSize: '1rem', fontWeight: '600' }}>API Endpoints</h2>
        </div>
        <div style={{ padding: '1.5rem' }}>
          <dl style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1rem 2rem' }}>
            <SettingItem label="Base URL" value={import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'} copyable onCopy={() => copyToClipboard(import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000')} copied={copied} />
            <SettingItem label="Health Check" value={`${import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'}/health`} copyable onCopy={() => copyToClipboard(`${import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'}/health`)} copied={copied} />
            <SettingItem label="API Docs" value={`${import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'}/docs`} copyable onCopy={() => copyToClipboard(`${import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'}/docs`)} copied={copied} />
            <SettingItem label="Auth Config" value={`${import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'}/auth/config`} copyable onCopy={() => copyToClipboard(`${import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'}/auth/config`)} copied={copied} />
          </dl>
        </div>
      </section>

      <section className="card" style={{ marginBottom: '1.5rem' }}>
        <div style={{ padding: '1.5rem', borderBottom: '1px solid var(--border-color)' }}>
          <h2 style={{ fontSize: '1rem', fontWeight: '600' }}>Application Info</h2>
        </div>
        <div style={{ padding: '1.5rem' }}>
          <dl style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem 2rem' }}>
            <SettingItem label="Version" value="1.0.0" />
            <SettingItem label="Environment" value={import.meta.env.MODE || 'development'} />
            <SettingItem label="Build Time" value={new Date().toISOString().split('T')[0]} />
          </dl>
        </div>
      </section>

      <section className="card">
        <div style={{ padding: '1.5rem', borderBottom: '1px solid var(--border-color)' }}>
          <h2 style={{ fontSize: '1rem', fontWeight: '600' }}>Supported Analysis Types</h2>
        </div>
        <div style={{ padding: '1.5rem' }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1rem' }}>
            <AnalysisTypeCard
              title="VTable Resolution"
              description="Resolve indirect vtable function calls to concrete targets (Ghidra Issue #516)"
              icon="🔧"
            />
            <AnalysisTypeCard
              title="Switch Recovery"
              description="Recover switch statements from jump-table patterns (Ghidra Issue #2628)"
              icon="🔀"
            />
            <AnalysisTypeCard
              title="JMP+Call Recovery"
              description="Fix JMP-with-PUSH return address handling (Ghidra Issue #5747)"
              icon="🔁"
            />
            <AnalysisTypeCard
              title="String Recovery"
              description="Cross-segment string detection in decompiler (Ghidra Issue #4865)"
              icon="📝"
            />
            <AnalysisTypeCard
              title="Batch Decompilation"
              description="Scalable parallel decompilation with shared cache (Ghidra Issue #2791)"
              icon="⚡"
            />
          </div>
        </div>
      </section>
    </div>
  );
}

function SettingItem({ label, value, copyable, onCopy, copied }: { label: string; value: string; copyable?: boolean; onCopy?: () => void; copied?: boolean }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.375rem' }}>
      <label style={{ fontSize: '0.75rem', color: 'var(--fg-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>{label}</label>
      <div style={{
        display: 'flex', alignItems: 'center', gap: '0.5rem',
        background: 'var(--bg-tertiary)', border: '1px solid var(--border-color)',
        borderRadius: 'var(--radius-sm)', padding: '0.5rem 0.75rem',
      }}>
        <code style={{ fontSize: '0.8125rem', color: 'var(--fg-secondary)', flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
          {value}
        </code>
        {copyable && onCopy && (
          <button
            onClick={onCopy}
            className="btn btn-ghost"
            style={{ padding: '0.25rem', opacity: copied ? 1 : 0.5 }}
            title={copied ? 'Copied!' : 'Copy to clipboard'}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
              <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
            </svg>
          </button>
        )}
      </div>
    </div>
  );
}

function AnalysisTypeCard({ title, description, icon }: { title: string; description: string; icon: string }) {
  return (
    <div className="card" style={{ padding: '1.25rem', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
      <span style={{ fontSize: '1.5rem' }}>{icon}</span>
      <h3 style={{ fontSize: '1rem', fontWeight: '600' }}>{title}</h3>
      <p style={{ fontSize: '0.8125rem', color: 'var(--fg-secondary)', lineHeight: 1.5 }}>{description}</p>
    </div>
  );
}
