import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import NotFound from '../components/common/NotFound';
import AppNavbar from '../components/common/AppNavbar';
import Modal from '../components/ui/Modal';
import ConfirmDialog from '../components/ui/ConfirmDialog';
import { AuthProvider } from '../context/AuthContext';
import apiClient, { getErrorMessage } from '../api/client';
import { AxiosError } from 'axios';

// Mock apiClient
vi.mock('../api/client', async () => {
  const actual = await vi.importActual<typeof import('../api/client')>('../api/client');
  return {
    ...actual,
    default: {
      ...actual.default,
      post: vi.fn(),
      get: vi.fn(),
      defaults: { headers: { common: {} } },
      interceptors: { request: { use: vi.fn() }, response: { use: vi.fn() } },
    },
  };
});

describe('Navigation, 404 Routes & Common Dialog Workflows', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  describe('404 NotFound Page', () => {
    it('renders 404 error header, descriptive notice, and navigational action buttons', () => {
      render(
        <MemoryRouter>
          <NotFound />
        </MemoryRouter>
      );

      expect(screen.getByText(/Error 404 • Unindexed Route/i)).toBeInTheDocument();
      expect(
        screen.getByRole('heading', { name: /Authority or Resource Not Found/i })
      ).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Research Workspace/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Document Catalog/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Go Back/i })).toBeInTheDocument();
    });

    it('navigates to workspace when Research Workspace button is clicked', () => {
      render(
        <MemoryRouter initialEntries={['/non-existent-page']}>
          <Routes>
            <Route path="/non-existent-page" element={<NotFound />} />
            <Route path="/" element={<div data-testid="workspace-root">Workspace Active</div>} />
          </Routes>
        </MemoryRouter>
      );

      fireEvent.click(screen.getByRole('button', { name: /Research Workspace/i }));
      expect(screen.getByTestId('workspace-root')).toBeInTheDocument();
    });
  });

  describe('AppNavbar Role-Based Navigation & Sign Out', () => {
    it('renders workspace and documents links for standard researchers, omitting admin console', () => {
      // Mock logged-in researcher
      localStorage.setItem('token', 'researcher-token');
      (apiClient.get as any).mockResolvedValue({
        data: { id: 2, email: 'researcher@lexora.ai', role: 'RESEARCHER', full_name: 'Junior Researcher' },
      });

      render(
        <MemoryRouter initialEntries={['/']}>
          <AuthProvider>
            <AppNavbar />
          </AuthProvider>
        </MemoryRouter>
      );

      expect(screen.getByRole('link', { name: /Research Workspace/i })).toBeInTheDocument();
      expect(screen.getByRole('link', { name: /Document Intelligence/i })).toBeInTheDocument();
      // Regular researcher must NOT see administrative evaluation console
      expect(screen.queryByRole('link', { name: /Evaluation & Gates/i })).not.toBeInTheDocument();
    });

    it('displays pilot status badge in branding', () => {
      render(
        <MemoryRouter>
          <AuthProvider>
            <AppNavbar />
          </AuthProvider>
        </MemoryRouter>
      );

      expect(screen.getByText('Pilot')).toBeInTheDocument();
      expect(screen.getByText('AI Legal Intelligence')).toBeInTheDocument();
    });
  });

  describe('Modal & ConfirmDialog Accessibility Fundamentals', () => {
    it('renders accessible dialog container with role="dialog" and aria-modal="true"', () => {
      render(
        <Modal isOpen={true} onClose={vi.fn()} title="Legal Precedent Excerpt">
          <p>Ratio decidendi details</p>
        </Modal>
      );

      const dialog = screen.getByRole('dialog');
      expect(dialog).toBeInTheDocument();
      expect(dialog).toHaveAttribute('aria-modal', 'true');
      expect(screen.getByText('Legal Precedent Excerpt')).toBeInTheDocument();
      expect(screen.getByText('Ratio decidendi details')).toBeInTheDocument();
    });

    it('triggers onClose when Escape key is pressed', () => {
      const handleClose = vi.fn();
      render(
        <Modal isOpen={true} onClose={handleClose} title="Dismissable Dialog">
          <p>Content</p>
        </Modal>
      );

      fireEvent.keyDown(window, { key: 'Escape' });
      expect(handleClose).toHaveBeenCalledTimes(1);
    });

    it('renders confirm and cancel buttons in ConfirmDialog and triggers handlers', () => {
      const handleConfirm = vi.fn();
      const handleCancel = vi.fn();

      render(
        <ConfirmDialog
          isOpen={true}
          onClose={handleCancel}
          onConfirm={handleConfirm}
          title="Delete Research Session"
          message="Are you certain you wish to purge this session?"
          confirmLabel="Purge Session"
          cancelLabel="Retain"
          isDestructive={true}
        />
      );

      expect(screen.getByText('Delete Research Session')).toBeInTheDocument();
      expect(
        screen.getByText('Are you certain you wish to purge this session?')
      ).toBeInTheDocument();

      const cancelBtn = screen.getByRole('button', { name: 'Retain' });
      const confirmBtn = screen.getByRole('button', { name: 'Purge Session' });

      fireEvent.click(cancelBtn);
      expect(handleCancel).toHaveBeenCalledTimes(1);

      fireEvent.click(confirmBtn);
      expect(handleConfirm).toHaveBeenCalledTimes(1);
    });

    it('disables actions while ConfirmDialog isLoading is true', () => {
      render(
        <ConfirmDialog
          isOpen={true}
          onClose={vi.fn()}
          onConfirm={vi.fn()}
          title="Processing Authority"
          message="Re-indexing vectors in background..."
          isLoading={true}
        />
      );

      expect(screen.getByRole('button', { name: 'Cancel' })).toBeDisabled();
      expect(screen.getByRole('button', { name: 'Confirm' })).toBeDisabled();
    });
  });

  describe('API Error Handling Utility getErrorMessage', () => {
    it('extracts string detail from backend error response', () => {
      const axiosErr = {
        isAxiosError: true,
        response: {
          data: { detail: 'Bar Council registration number unverified.' },
        },
      } as unknown as AxiosError;

      expect(getErrorMessage(axiosErr)).toBe('Bar Council registration number unverified.');
    });

    it('formats array detail from backend FastAPI validation errors', () => {
      const validationErr = {
        isAxiosError: true,
        response: {
          data: {
            detail: [
              { msg: 'Field required: invite_code' },
              { msg: 'Invalid email format' },
            ],
          },
        },
      } as unknown as AxiosError;

      expect(getErrorMessage(validationErr)).toBe('Field required: invite_code, Invalid email format');
    });

    it('falls back to default message when error structure is unknown', () => {
      expect(getErrorMessage(null, 'Custom legal gateway fallback')).toBe(
        'Custom legal gateway fallback'
      );
    });
  });
});
