import { Link, NavLink } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';

export function Layout({ children }: { children: React.ReactNode }) {
  const { user, logout } = useAuth();

  const navItems = [
    { path: '/', label: 'Dashboard', icon: '📊' },
    { path: '/analyses', label: 'Analyses', icon: '🔍' },
    { path: '/settings', label: 'Settings', icon: '⚙️' },
  ];

  return (
    <div style={{ display: 'flex', minHeight: '100vh' }}>
      <aside style={{
        width: '260px',
        background: 'var(--bg-secondary)',
        borderRight: '1px solid var(--border-color)',
        display: 'flex',
        flexDirection: 'column',
        padding: '1.5rem 1rem',
        gap: '1rem',
        position: 'sticky',
        top: 0,
        height: '100vh',
        overflowY: 'auto',
      }}>
        <Link to="/" style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.75rem',
          fontSize: '1.25rem',
          fontWeight: '700',
          color: 'var(--accent-blue)',
          padding: '0.5rem 0',
          marginBottom: '0.5rem',
        }}>
          <svg width="28" height="28" viewBox="0 0 32 32" fill="none">
            <rect width="32" height="32" rx="6" fill="#1e1e2e"/>
            <path d="M8 12h16M8 16h12M8 20h8" stroke="#89b4fa" strokeWidth="2" strokeLinecap="round"/>
            <circle cx="24" cy="20" r="4" stroke="#fab387" strokeWidth="2"/>
          </svg>
          Nexus Workbench
        </Link>

        <nav style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem', flex: 1 }}>
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              style={({ isActive }) => ({
                display: 'flex',
                alignItems: 'center',
                gap: '0.75rem',
                padding: '0.625rem 0.875rem',
                borderRadius: 'var(--radius-sm)',
                color: isActive ? 'var(--accent-blue)' : 'var(--fg-secondary)',
                background: isActive ? 'rgba(137, 180, 250, 0.1)' : 'transparent',
                fontWeight: isActive ? '600' : '500',
                fontSize: '0.875rem',
                transition: 'all var(--transition-fast)',
              })}
            >
              <span style={{ fontSize: '1rem' }}>{item.icon}</span>
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div style={{
          paddingTop: '1rem',
          borderTop: '1px solid var(--border-color)',
          display: 'flex',
          flexDirection: 'column',
          gap: '0.75rem',
        }}>
          <div style={{
            padding: '0.75rem',
            background: 'var(--bg-tertiary)',
            borderRadius: 'var(--radius-sm)',
            border: '1px solid var(--border-color)',
          }}>
            <div style={{ fontSize: '0.75rem', color: 'var(--fg-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.25rem' }}>
              Signed in as
            </div>
            <div style={{ fontWeight: '500', color: 'var(--fg-primary)' }}>
              {user?.username || 'Unknown'}
            </div>
            <div style={{ fontSize: '0.75rem', color: 'var(--fg-muted)' }}>
              {user?.role || 'viewer'}
            </div>
          </div>

          <button
            onClick={logout}
            className="btn btn-secondary"
            style={{ width: '100%', justifyContent: 'center' }}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
              <polyline points="16 17 21 12 16 7"/>
              <line x1="21" y1="12" x2="9" y2="12"/>
            </svg>
            Logout
          </button>
        </div>
      </aside>

      <main style={{
        flex: 1,
        padding: '2rem',
        overflowY: 'auto',
        background: 'var(--bg-primary)',
      }}>
        {children}
      </main>
    </div>
  );
}