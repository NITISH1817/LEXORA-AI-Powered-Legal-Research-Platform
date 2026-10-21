import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import Login from '../components/auth/Login';
import { AuthProvider } from '../context/AuthContext';
import { ProtectedRoute } from '../App';
import apiClient from '../api/client';
import { useAuth } from '../hooks/useAuth';

// Mock apiClient
vi.mock('../api/client', async () => {
  const actual = await vi.importActual<typeof import('../api/client')>('../api/client');
  return {
    ...actual,
    default: {
      ...actual.default,
      post: vi.fn(),
      get: vi.fn(),
      defaults: {
        headers: {
          common: {},
        },
      },
      interceptors: {
        request: { use: vi.fn() },
        response: { use: vi.fn() },
      },
    },
  };
});

describe('Authentication & Route Protection Workflows', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  const renderWithAuth = (ui: React.ReactNode, initialEntries = ['/']) => {
    return render(
      <MemoryRouter initialEntries={initialEntries}>
        <AuthProvider>{ui}</AuthProvider>
      </MemoryRouter>
    );
  };

  it('renders login form with accessible labels, input fields, and submit button', () => {
    renderWithAuth(<Login />, ['/login']);

    expect(screen.getByRole('heading', { name: /lexora/i })).toBeInTheDocument();
    expect(screen.getByLabelText(/institutional email/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText('••••••••')).toBeInTheDocument();
    expect(
      screen.getByRole('button', { name: /sign in to legal workspace/i })
    ).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /register pilot account/i })).toBeInTheDocument();
  });

  it('validates empty inputs and presents an accessible error alert without calling API', async () => {
    renderWithAuth(<Login />, ['/login']);

    const submitBtn = screen.getByRole('button', { name: /sign in to legal workspace/i });
    fireEvent.click(submitBtn);

    const alert = await screen.findByRole('alert');
    expect(alert).toHaveTextContent(/please provide both your institutional email and password/i);
    expect(apiClient.post).not.toHaveBeenCalled();
  });

  it('toggles password visibility with accessible aria-label update', () => {
    renderWithAuth(<Login />, ['/login']);

    const passwordInput = screen.getByPlaceholderText('••••••••');
    expect(passwordInput).toHaveAttribute('type', 'password');

    const toggleBtn = screen.getByRole('button', { name: /show password/i });
    fireEvent.click(toggleBtn);

    expect(passwordInput).toHaveAttribute('type', 'text');
    expect(screen.getByRole('button', { name: /hide password/i })).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /hide password/i }));
    expect(passwordInput).toHaveAttribute('type', 'password');
  });

  it('handles failed authentication response and displays backend error message in role="alert"', async () => {
    const errorResponse = {
      isAxiosError: true,
      response: {
        status: 401,
        data: { detail: 'Invalid credentials or unverified institutional advocate account.' },
      },
    };
    (apiClient.post as any).mockRejectedValueOnce(errorResponse);

    renderWithAuth(<Login />, ['/login']);

    fireEvent.change(screen.getByLabelText(/institutional email/i), {
      target: { value: 'advocate@bar.in' },
    });
    fireEvent.change(screen.getByPlaceholderText('••••••••'), {
      target: { value: 'WrongPassword99!' },
    });

    const submitBtn = screen.getByRole('button', { name: /sign in to legal workspace/i });
    fireEvent.click(submitBtn);

    const alert = await screen.findByRole('alert');
    expect(alert).toHaveTextContent(/Invalid credentials or unverified institutional advocate account/i);
  });

  it('stores access token in localStorage upon successful authentication', async () => {
    (apiClient.post as any).mockResolvedValueOnce({
      data: { access_token: 'mock-jwt-token-xyz', token_type: 'bearer' },
    });
    (apiClient.get as any).mockImplementation((url: string) => {
      if (url === '/api/auth/me') {
        return Promise.resolve({
          data: {
            id: 1,
            email: 'researcher@lexora.ai',
            role: 'RESEARCHER',
            full_name: 'Lead Legal Researcher',
          },
        });
      }
      return Promise.reject(new Error(`Unhandled GET ${url}`));
    });

    render(
      <MemoryRouter initialEntries={['/login']}>
        <AuthProvider>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/" element={<div data-testid="workspace">Legal Workspace Active</div>} />
          </Routes>
        </AuthProvider>
      </MemoryRouter>
    );

    fireEvent.change(screen.getByLabelText(/institutional email/i), {
      target: { value: 'researcher@lexora.ai' },
    });
    fireEvent.change(screen.getByPlaceholderText('••••••••'), {
      target: { value: 'Password123!' },
    });

    fireEvent.click(screen.getByRole('button', { name: /sign in to legal workspace/i }));

    await waitFor(() => {
      expect(localStorage.getItem('token')).toBe('mock-jwt-token-xyz');
      expect(screen.getByTestId('workspace')).toBeInTheDocument();
    });
  });

  it('redirects unauthenticated users attempting to access protected routes', () => {
    render(
      <MemoryRouter initialEntries={['/protected']}>
        <AuthProvider>
          <Routes>
            <Route
              path="/protected"
              element={
                <ProtectedRoute>
                  <div>Confidential Case Docket</div>
                </ProtectedRoute>
              }
            />
            <Route path="/login" element={<div data-testid="login-view">Login Required</div>} />
          </Routes>
        </AuthProvider>
      </MemoryRouter>
    );

    expect(screen.getByTestId('login-view')).toBeInTheDocument();
    expect(screen.queryByText(/Confidential Case Docket/i)).not.toBeInTheDocument();
  });

  it('blocks non-admin users from adminOnly routes with 403 Forbidden notice', async () => {
    localStorage.setItem('token', 'researcher-token');
    (apiClient.get as any).mockImplementation((url: string) => {
      if (url === '/api/auth/me') {
        return Promise.resolve({
          data: {
            id: 2,
            email: 'researcher@lexora.ai',
            role: 'RESEARCHER',
            full_name: 'Junior Researcher',
          },
        });
      }
      return Promise.reject(new Error(`Unhandled GET ${url}`));
    });

    render(
      <MemoryRouter initialEntries={['/admin-route']}>
        <AuthProvider>
          <Routes>
            <Route
              path="/admin-route"
              element={
                <ProtectedRoute adminOnly>
                  <div>Restricted Release Gates</div>
                </ProtectedRoute>
              }
            />
          </Routes>
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/403 Forbidden: Administrator Role Required/i)).toBeInTheDocument();
      expect(screen.queryByText(/Restricted Release Gates/i)).not.toBeInTheDocument();
    });
  });

  it('allows verified admin users to access adminOnly protected routes', async () => {
    localStorage.setItem('token', 'admin-token');
    (apiClient.get as any).mockImplementation((url: string) => {
      if (url === '/api/auth/me') {
        return Promise.resolve({
          data: {
            id: 1,
            email: 'admin@lexora.ai',
            role: 'ADMIN',
            full_name: 'System Admin',
          },
        });
      }
      return Promise.reject(new Error(`Unhandled GET ${url}`));
    });

    render(
      <MemoryRouter initialEntries={['/admin-route']}>
        <AuthProvider>
          <Routes>
            <Route
              path="/admin-route"
              element={
                <ProtectedRoute adminOnly>
                  <div data-testid="admin-console">Restricted Release Gates</div>
                </ProtectedRoute>
              }
            />
          </Routes>
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByTestId('admin-console')).toBeInTheDocument();
    });
  });

  it('clears session tokens and authorization headers on logout', async () => {
    localStorage.setItem('token', 'valid-active-token');
    (apiClient.get as any).mockImplementation((url: string) => {
      if (url === '/api/auth/me') {
        return Promise.resolve({
          data: { id: 1, email: 'user@lexora.ai', role: 'RESEARCHER' },
        });
      }
      return Promise.reject(new Error(`Unhandled GET ${url}`));
    });

    function TestLogoutComponent() {
      const { logout, isAuthenticated } = useAuth();
      return (
        <div>
          <span data-testid="auth-state">{isAuthenticated ? 'LOGGED_IN' : 'LOGGED_OUT'}</span>
          <button onClick={logout}>Sign Out</button>
        </div>
      );
    }

    render(
      <MemoryRouter>
        <AuthProvider>
          <TestLogoutComponent />
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByTestId('auth-state')).toHaveTextContent('LOGGED_IN');
    });

    fireEvent.click(screen.getByRole('button', { name: /sign out/i }));

    expect(localStorage.getItem('token')).toBeNull();
    expect(localStorage.getItem('access_token')).toBeNull();
    expect(screen.getByTestId('auth-state')).toHaveTextContent('LOGGED_OUT');
  });

  it('listens for lexora:unauthorized custom event and resets user session', async () => {
    localStorage.setItem('token', 'expired-token');
    (apiClient.get as any).mockImplementation((url: string) => {
      if (url === '/api/auth/me') {
        return Promise.resolve({
          data: { id: 1, email: 'user@lexora.ai', role: 'RESEARCHER' },
        });
      }
      return Promise.reject(new Error(`Unhandled GET ${url}`));
    });

    function TestListenerComponent() {
      const { isAuthenticated } = useAuth();
      return <div data-testid="session-status">{isAuthenticated ? 'ACTIVE' : 'INACTIVE'}</div>;
    }

    render(
      <MemoryRouter>
        <AuthProvider>
          <TestListenerComponent />
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByTestId('session-status')).toHaveTextContent('ACTIVE');
    });

    // Simulate 401 unauthorized event fired by Axios interceptor
    window.dispatchEvent(new CustomEvent('lexora:unauthorized'));

    await waitFor(() => {
      expect(screen.getByTestId('session-status')).toHaveTextContent('INACTIVE');
      expect(localStorage.getItem('token')).toBeNull();
    });
  });
});
