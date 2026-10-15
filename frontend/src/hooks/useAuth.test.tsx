import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, act } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider, useAuth } from '../hooks/useAuth';
import { authApi } from '../api/client';

vi.mock('../api/client');

const mockAuthApi = authApi as any;

describe('useAuth', () => {
  beforeEach(() => {
    vi.resetAllMocks();
    sessionStorage.clear();
    mockAuthApi.getConfig.mockResolvedValue({
      data: {
        keycloak_url: 'http://localhost:8080',
        realm: 'nexus',
        client_id: 'nexus-workbench',
        redirect_uri: 'http://localhost:3000/callback',
        authenticated: false,
        user: null,
      },
    });
    mockAuthApi.getMe.mockRejectedValue(new Error('Not authenticated'));
  });

  it('provides login function', () => {
    function TestComponent() {
      const { login } = useAuth();
      return <button onClick={login}>Login</button>;
    }

    render(
      <BrowserRouter>
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      </BrowserRouter>
    );

    expect(screen.getByText('Login')).toBeInTheDocument();
  });

  it('provides logout function', () => {
    function TestComponent() {
      const { logout } = useAuth();
      return <button onClick={logout}>Logout</button>;
    }

    render(
      <BrowserRouter>
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      </BrowserRouter>
    );

    expect(screen.getByText('Logout')).toBeInTheDocument();
  });

  it('shows loading state initially then ready', async () => {
    let resolveConfig: (value: any) => void;
    const configPromise = new Promise((resolve) => {
      resolveConfig = resolve;
    });
    mockAuthApi.getConfig.mockReturnValue(configPromise);
    mockAuthApi.getMe.mockRejectedValue(new Error('Not authenticated'));

    function TestComponent() {
      const { loading } = useAuth();
      return <div data-testid="loading">{loading ? 'loading' : 'ready'}</div>;
    }

    render(
      <BrowserRouter>
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      </BrowserRouter>
    );

    expect(screen.getByTestId('loading')).toHaveTextContent('loading');

    act(() => {
      resolveConfig!({
        data: {
          keycloak_url: 'http://localhost:8080',
          realm: 'nexus',
          client_id: 'nexus-workbench',
          redirect_uri: 'http://localhost:3000/callback',
          authenticated: false,
          user: null,
        },
      });
    });

    await waitFor(() => {
      expect(screen.getByTestId('loading')).toHaveTextContent('ready');
    });
  });
});