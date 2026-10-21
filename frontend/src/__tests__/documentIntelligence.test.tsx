import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import DocumentIntelligence from '../components/DocumentIntelligence';
import apiClient from '../api/client';
import { AuthProvider } from '../context/AuthContext';
import { ToastProvider } from '../context/ToastContext';

// Mock apiClient
vi.mock('../api/client', async () => {
  const actual = await vi.importActual<typeof import('../api/client')>('../api/client');
  return {
    ...actual,
    default: {
      ...actual.default,
      post: vi.fn(),
      get: vi.fn(),
      delete: vi.fn(),
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

describe('Document Intelligence & Pipeline Status Workflows', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  const mockDocuments = [
    {
      id: 101,
      title: 'Puttaswamy Right to Privacy Judgment 2017',
      original_filename: 'puttaswamy_2017_9j.pdf',
      document_type: 'pdf',
      status: 'READY',
      page_count: 547,
      file_size_bytes: 4200000,
      version_number: 1,
      uploaded_at: '2026-10-15T10:00:00Z',
      case_id: 1,
      case_name: 'Justice K.S. Puttaswamy (Retd.) v. Union of India',
    },
    {
      id: 102,
      title: 'Navtej Singh Johar Section 377 Ruling',
      original_filename: 'navtej_johar_2018.pdf',
      document_type: 'pdf',
      status: 'PARSING',
      progress: 45,
      current_stage: 'Extracting constitutional ratios',
      uploaded_at: '2026-10-20T14:30:00Z',
      case_id: 2,
      case_name: 'Navtej Singh Johar v. Union of India',
    },
    {
      id: 103,
      title: 'Arbitration Clause Commercial Brief',
      original_filename: 'arbitration_brief.docx',
      document_type: 'docx',
      status: 'FAILED',
      uploaded_at: '2026-10-21T08:00:00Z',
      case_id: 3,
      case_name: 'Commercial Dispute #44',
    },
  ];

  const renderComponent = () => {
    return render(
      <MemoryRouter>
        <AuthProvider>
          <ToastProvider>
            <DocumentIntelligence />
          </ToastProvider>
        </AuthProvider>
      </MemoryRouter>
    );
  };

  it('renders document catalog header, metrics row, and uploaded documents list', async () => {
    (apiClient.get as any).mockResolvedValueOnce({ data: mockDocuments });

    renderComponent();

    expect(
      screen.getByRole('heading', { name: /Document Intelligence & Ingestion/i })
    ).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /upload document/i })).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText('Puttaswamy Right to Privacy Judgment 2017')).toBeInTheDocument();
      expect(screen.getByText('Navtej Singh Johar Section 377 Ruling')).toBeInTheDocument();
      expect(screen.getByText('Arbitration Clause Commercial Brief')).toBeInTheDocument();
    });

    // Check pipeline status badges
    expect(screen.getByText('Ready')).toBeInTheDocument();
    expect(screen.getByText('Parsing')).toBeInTheDocument();
    expect(screen.getAllByText('Failed').length).toBeGreaterThanOrEqual(1);

    // Check stats cards
    expect(screen.getByText('3')).toBeInTheDocument(); // Total
  });

  it('renders honest empty catalog state when no documents exist', async () => {
    (apiClient.get as any).mockResolvedValueOnce({ data: [] });

    renderComponent();

    await waitFor(() => {
      expect(screen.getByText('No documents in catalog')).toBeInTheDocument();
      expect(
        screen.getByText(/Upload your first primary transcript, ruling, or pleading to begin extraction/i)
      ).toBeInTheDocument();
    });
  });

  it('filters documents dynamically based on search query', async () => {
    (apiClient.get as any).mockResolvedValueOnce({ data: mockDocuments });

    renderComponent();

    await waitFor(() => {
      expect(screen.getByText('Puttaswamy Right to Privacy Judgment 2017')).toBeInTheDocument();
    });

    const searchInput = screen.getByPlaceholderText(/Search documents by title/i);
    fireEvent.change(searchInput, { target: { value: 'Arbitration' } });

    expect(screen.getByText('Arbitration Clause Commercial Brief')).toBeInTheDocument();
    expect(screen.queryByText('Puttaswamy Right to Privacy Judgment 2017')).not.toBeInTheDocument();
    expect(screen.queryByText('Navtej Singh Johar Section 377 Ruling')).not.toBeInTheDocument();
  });

  it('filters documents by pipeline status', async () => {
    (apiClient.get as any).mockResolvedValueOnce({ data: mockDocuments });

    renderComponent();

    await waitFor(() => {
      expect(screen.getByText('Puttaswamy Right to Privacy Judgment 2017')).toBeInTheDocument();
    });

    const statusFilter = screen.getByLabelText(/Filter by processing status/i);
    fireEvent.change(statusFilter, { target: { value: 'FAILED' } });

    expect(screen.getByText('Arbitration Clause Commercial Brief')).toBeInTheDocument();
    expect(screen.queryByText('Puttaswamy Right to Privacy Judgment 2017')).not.toBeInTheDocument();
    expect(screen.queryByText('Navtej Singh Johar Section 377 Ruling')).not.toBeInTheDocument();
  });

  it('shows no matching results message when search filter yields zero items and allows resetting filters', async () => {
    (apiClient.get as any).mockResolvedValueOnce({ data: mockDocuments });

    renderComponent();

    await waitFor(() => {
      expect(screen.getByText('Puttaswamy Right to Privacy Judgment 2017')).toBeInTheDocument();
    });

    const searchInput = screen.getByPlaceholderText(/Search documents by title/i);
    fireEvent.change(searchInput, { target: { value: 'NonexistentUnmatchedDocXYZ' } });

    expect(screen.getByText('No matching documents found')).toBeInTheDocument();
    const clearBtn = screen.getByRole('button', { name: /clear filters/i });
    expect(clearBtn).toBeInTheDocument();

    fireEvent.click(clearBtn);
    expect(screen.getByText('Puttaswamy Right to Privacy Judgment 2017')).toBeInTheDocument();
  });

  it('displays API error alert when document retrieval fails', async () => {
    const errorResponse = {
      isAxiosError: true,
      response: {
        status: 500,
        data: { detail: 'Document database storage unreachable.' },
      },
    };
    (apiClient.get as any).mockRejectedValueOnce(errorResponse);

    renderComponent();

    const alert = await screen.findByRole('alert');
    expect(alert).toHaveTextContent(/Document database storage unreachable/i);
  });
});
