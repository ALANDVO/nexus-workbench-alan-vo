export function LoadingScreen() {
  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: '100vh',
      gap: '1rem',
      color: 'var(--fg-secondary)',
    }}>
      <div className="loading-spinner" style={{ width: '3rem', height: '3rem', borderWidth: '3px' }} />
      <span>Loading...</span>
    </div>
  );
}