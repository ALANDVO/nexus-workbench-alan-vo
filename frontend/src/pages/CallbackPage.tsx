import { useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { setAccessToken } from '../api/client';

export function CallbackPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  useEffect(() => {
    const token = searchParams.get('token');
    const error = searchParams.get('error');
    const errorDescription = searchParams.get('error_description');

    const handleCallback = () => {
      if (error) {
        console.error('OAuth error:', error, errorDescription);
        alert(`Authentication failed: ${errorDescription || error}`);
        navigate('/login');
        return;
      }

      if (token) {
        setAccessToken(token);
        sessionStorage.removeItem('oauth_state');
        sessionStorage.removeItem('oauth_nonce');
        sessionStorage.removeItem('oauth_code_verifier');
        navigate('/');
      } else {
        console.error('No token in callback');
        alert('Authentication failed: No token received');
        navigate('/login');
      }
    };

    handleCallback();
  }, [searchParams, navigate]);

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: '70vh',
      textAlign: 'center',
    }}>
      <div className="loading-spinner" style={{ width: '3rem', height: '3rem', borderWidth: '3px' }} />
      <p style={{ marginTop: '1rem', color: 'var(--fg-secondary)' }}>Completing authentication...</p>
    </div>
  );
}