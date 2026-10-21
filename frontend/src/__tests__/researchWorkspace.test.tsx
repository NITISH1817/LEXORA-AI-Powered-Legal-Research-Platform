import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import ResearchWorkspace from '../components/ResearchWorkspace';
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

describe('Research Workspace & Synthesis Interactions', () => {
  const activeSessionFixture = {
    id: 1,
    title: 'Constitutional Rights Session',
    research_question: 'Fundamental rights under Part III',
    cases: [],
    notes: [],
  };

  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
    (apiClient.get as any).mockImplementation((url: string) => {
      if (url === '/api/research') return Promise.resolve({ data: [activeSessionFixture] });
      if (url === '/api/research/1') return Promise.resolve({ data: activeSessionFixture });
      return Promise.resolve({ data: {} });
    });
  });

  const renderWorkspace = () => {
    return render(
      <MemoryRouter>
        <AuthProvider>
          <ToastProvider>
            <ResearchWorkspace />
          </ToastProvider>
        </AuthProvider>
      </MemoryRouter>
    );
  };

  it('renders workspace query input, mode controls, and persistent non-reliance disclaimer', async () => {
    renderWorkspace();

    expect(
      screen.getByLabelText(/Legal Research Proposition or Inquiry/i)
    ).toBeInTheDocument();
    expect(
      screen.getByRole('button', { name: /execute/i })
    ).toBeInTheDocument();

    // Verify persistent legal disclaimer and scope notice
    expect(
      screen.getByText(/Controlled Pilot Safeguards & Mandatory Verification Standard/i)
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Non-Reliance Notice:/i)
    ).toBeInTheDocument();
    expect(
      screen.getByText(/LEXORA provides AI-assisted legal research synthesis, not legal advice/i)
    ).toBeInTheDocument();
  });

  it('submits a legal synthesis query and renders structured synthesis answer and citations', async () => {
    const mockSynthesisResponse = {
      query: 'Is privacy a fundamental right under Article 21?',
      answer: '### Privacy under Article 21\n\nIn [AIR 2017 SC 4401], a nine-judge Constitution Bench held that the right to privacy is an intrinsic part of the right to life and personal liberty.',
      citations: ['AIR 2017 SC 4401'],
      grounded: true,
      sources: [
        {
          case_name: 'Justice K.S. Puttaswamy (Retd.) v. Union of India',
          source_id: 'puttaswamy_chunk_42',
          matched_text: 'Privacy is a constitutionally protected right emerging primarily from Article 21.',
          court: 'Supreme Court of India',
        },
      ],
    };

    (apiClient.post as any).mockImplementation((url: string) => {
      if (url === '/api/research/ask') return Promise.resolve({ data: mockSynthesisResponse });
      return Promise.resolve({ data: {} });
    });

    renderWorkspace();

    const textarea = screen.getByLabelText(/Legal Research Proposition or Inquiry/i);
    fireEvent.change(textarea, { target: { value: 'Is privacy a fundamental right under Article 21?' } });

    const submitBtn = screen.getByRole('button', { name: /execute/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByText('Privacy under Article 21')).toBeInTheDocument();
      expect(
        screen.getByText(/nine-judge Constitution Bench held that the right to privacy is an intrinsic part/i)
      ).toBeInTheDocument();
    });

    // Check verified citations rendered as interactive button
    expect(screen.getByRole('button', { name: 'AIR 2017 SC 4401' })).toBeInTheDocument();
  });

  it('opens evidence inspector drawer when citation pill is clicked', async () => {
    const mockSynthesisResponse = {
      query: 'What did the court hold in Puttaswamy?',
      answer: 'The Supreme Court affirmed privacy in [AIR 2017 SC 4401].',
      citations: ['AIR 2017 SC 4401'],
      grounded: true,
      sources: [
        {
          case_name: 'Justice K.S. Puttaswamy v. Union of India',
          source_id: 'AIR 2017 SC 4401',
          matched_text: 'Privacy is the constitutional core of human dignity and liberty.',
          court: 'Supreme Court of India',
          page_number: 42,
          year: 2017,
        },
      ],
    };

    (apiClient.post as any).mockImplementation((url: string) => {
      if (url === '/api/research/ask') return Promise.resolve({ data: mockSynthesisResponse });
      if (url === '/api/research') return Promise.resolve({ data: activeSessionFixture });
      return Promise.resolve({ data: {} });
    });

    renderWorkspace();

    await waitFor(() => {
      expect(screen.getByText('Constitutional Rights Session')).toBeInTheDocument();
    });

    const textarea = screen.getByLabelText(/Legal Research Proposition or Inquiry/i);
    fireEvent.change(textarea, { target: { value: 'What did the court hold in Puttaswamy?' } });
    fireEvent.click(screen.getByRole('button', { name: /execute/i }));

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'AIR 2017 SC 4401' })).toBeInTheDocument();
    });

    const inspectBtn = screen.getByRole('button', { name: 'Inspect' });
    fireEvent.click(inspectBtn);

    await waitFor(() => {
      expect(screen.getByText('Source Evidence Inspector')).toBeInTheDocument();
      expect(screen.getAllByText(/Privacy is the constitutional core of human dignity and liberty/i).length).toBeGreaterThanOrEqual(1);
    });
  });

  it('renders accessible error alert when backend research request fails', async () => {
    (apiClient.post as any).mockImplementation((url: string) => {
      if (url === '/api/research/ask') {
        return Promise.reject({
          isAxiosError: true,
          response: {
            status: 503,
            data: { detail: 'Legal RAG retrieval service is momentarily unavailable.' },
          },
        });
      }
      return Promise.resolve({ data: {} });
    });

    renderWorkspace();

    const textarea = screen.getByLabelText(/Legal Research Proposition or Inquiry/i);
    fireEvent.change(textarea, { target: { value: 'Test query' } });
    fireEvent.click(screen.getByRole('button', { name: /execute/i }));

    const alert = await screen.findByRole('alert');
    expect(alert).toHaveTextContent(/Legal RAG retrieval service is momentarily unavailable/i);
  });

  it('triggers search on Ctrl+Enter keyboard shortcut in query textarea', async () => {
    (apiClient.post as any).mockImplementation((url: string) => {
      if (url === '/api/research/ask') {
        return Promise.resolve({
          data: {
            query: 'Shortcut trigger',
            answer: 'Keyboard shortcut submission result.',
            citations: [],
            grounded: true,
          },
        });
      }
      return Promise.resolve({ data: {} });
    });

    renderWorkspace();

    const textarea = screen.getByLabelText(/Legal Research Proposition or Inquiry/i);
    fireEvent.change(textarea, { target: { value: 'Shortcut trigger' } });
    fireEvent.keyDown(textarea, { key: 'Enter', ctrlKey: true });

    await waitFor(() => {
      expect(apiClient.post).toHaveBeenCalledWith(
        '/api/research/ask',
        expect.objectContaining({ query: 'Shortcut trigger' })
      );
    });
  });
});
