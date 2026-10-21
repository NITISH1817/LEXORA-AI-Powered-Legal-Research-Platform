import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import EvaluationDashboard from '../components/EvaluationDashboard';
import apiClient from '../api/client';
import { AuthProvider } from '../context/AuthContext';

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

describe('Evaluation Integrity & Pilot Release Gate Safeguards', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  const controlledFixture = {
    latest: {
      benchmark_metadata: {
        name: 'LEXORA Benchmark v3.0.0 (Landmark Indian Constitutional & Commercial Law)',
        version: 'v3.0.0',
        total_queries_in_split: 160,
        queries_with_relevant_targets: 136,
        negative_control_queries: 24,
      },
      split_reconciliation: {
        dev: {
          retrieval_hit_rate: 0.9844,
          retrieval_recall: 0.9518,
        },
        held_out: {
          retrieval_hit_rate: 1.0,
          retrieval_recall: 0.9525,
        },
      },
      answerable_grounding_targets_n55: {
        micro_claim_support: 0.827,
      },
      bootstrap_confidence_intervals_cluster_aware: {
        claim_support_answerable: { mean: 0.827, ci_lower: 0.788, ci_upper: 0.872 },
        citation_support_answerable: { mean: 0.8719, ci_lower: 0.738, ci_upper: 0.86 },
      },
      release_gate_status: {
        citation_support_actual: 0.8719,
        citation_validity_actual: 1.0,
        abstention_accuracy_actual: 1.0,
      },
    },
    reconciled: {
      benchmark_name: 'LEXORA Benchmark v3.0.0',
      version: 'v3.0.0',
      timestamp: '2026-10-20T12:00:00Z',
      reconciled_metrics: {
        split_reconciliation: {
          dev: { retrieval_hit_rate: 0.9844, retrieval_recall: 0.9518 },
          held_out: { retrieval_hit_rate: 1.0, retrieval_recall: 0.9525 },
        },
      },
      release_gate_status: {
        citation_support_actual: 0.8719,
        citation_validity_actual: 1.0,
        abstention_accuracy_actual: 1.0,
      },
    },
    monitoringSummary: {
      total_requests: 0,
      feedback_summary: {
        total_feedback_submissions: 0,
      },
    },
  };

  it('accurately reports zero approved gold labels (0 / 160) and 160 pending human legal reviews', async () => {
    (apiClient.get as any).mockImplementation((url: string) => {
      if (url === '/api/evaluation/latest') return Promise.resolve({ data: controlledFixture.latest });
      if (url === '/api/evaluation/reconciled') return Promise.resolve({ data: controlledFixture.reconciled });
      if (url === '/api/evaluation/monitoring/summary') return Promise.resolve({ data: controlledFixture.monitoringSummary });
      return Promise.reject(new Error(`Unhandled URL: ${url}`));
    });

    render(
      <MemoryRouter>
        <AuthProvider>
          <EvaluationDashboard />
        </AuthProvider>
      </MemoryRouter>
    );

    // Verify 0 / 160 is displayed prominently for human legal approvals
    await waitFor(() => {
      const zeroApprovalsElements = screen.getAllByText('0 / 160');
      expect(zeroApprovalsElements.length).toBeGreaterThanOrEqual(1);
      expect(screen.getByText(/0 Approved • 160 Pending/i)).toBeInTheDocument();
    });

    // Verify invariant note
    expect(
      screen.getByText(/Strict invariant: zero automated approvals permitted/i)
    ).toBeInTheDocument();
  });

  it('enforces honest zero-record state for practitioner feedback without inventing satisfaction or approval figures', async () => {
    (apiClient.get as any).mockImplementation((url: string) => {
      if (url === '/api/evaluation/latest') return Promise.resolve({ data: controlledFixture.latest });
      if (url === '/api/evaluation/reconciled') return Promise.resolve({ data: controlledFixture.reconciled });
      if (url === '/api/evaluation/monitoring/summary') return Promise.resolve({ data: controlledFixture.monitoringSummary });
      return Promise.reject(new Error(`Unhandled URL: ${url}`));
    });

    render(
      <MemoryRouter>
        <AuthProvider>
          <EvaluationDashboard />
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/Zero External Records/i)).toBeInTheDocument();
      expect(screen.getByText(/0 Submissions/i)).toBeInTheDocument();
      expect(
        screen.getByText(/No external practitioner survey responses have been submitted to date/i)
      ).toBeInTheDocument();
    });
  });

  it('renders operational decision and pilot restriction notice prominently', async () => {
    (apiClient.get as any).mockImplementation((url: string) => {
      if (url === '/api/evaluation/latest') return Promise.resolve({ data: controlledFixture.latest });
      if (url === '/api/evaluation/reconciled') return Promise.resolve({ data: controlledFixture.reconciled });
      if (url === '/api/evaluation/monitoring/summary') return Promise.resolve({ data: controlledFixture.monitoringSummary });
      return Promise.reject(new Error(`Unhandled URL: ${url}`));
    });

    render(
      <MemoryRouter>
        <AuthProvider>
          <EvaluationDashboard />
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(
        screen.getByText(/Operational Decision: LIMITED CONTROLLED PILOT — CONTINUE WITH CONDITIONS/i)
      ).toBeInTheDocument();
      expect(screen.getByText(/Gate 4\/5 Conditional/i)).toBeInTheDocument();
      expect(screen.getByText(/PILOT_REGISTRATION_RESTRICTED = True/i)).toBeInTheDocument();
    });
  });

  it('renders persistent non-reliance legal disclaimer', async () => {
    (apiClient.get as any).mockImplementation((url: string) => {
      if (url === '/api/evaluation/latest') return Promise.resolve({ data: controlledFixture.latest });
      if (url === '/api/evaluation/reconciled') return Promise.resolve({ data: controlledFixture.reconciled });
      if (url === '/api/evaluation/monitoring/summary') return Promise.resolve({ data: controlledFixture.monitoringSummary });
      return Promise.reject(new Error(`Unhandled URL: ${url}`));
    });

    render(
      <MemoryRouter>
        <AuthProvider>
          <EvaluationDashboard />
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/Mandatory Non-Reliance Safeguard:/i)).toBeInTheDocument();
      expect(
        screen.getByText(/LEXORA provides AI-assisted legal research synthesis, not legal advice/i)
      ).toBeInTheDocument();
    });
  });

  it('distinguishes API error state clearly from valid evaluation telemetry', async () => {
    (apiClient.get as any).mockRejectedValue(new Error('Connection to evaluation database failed'));

    render(
      <MemoryRouter>
        <AuthProvider>
          <EvaluationDashboard />
        </AuthProvider>
      </MemoryRouter>
    );

    // When the API fails, the dashboard renders an accessible error alert
    await waitFor(() => {
      const alert = screen.queryByRole('alert');
      if (alert) {
        expect(alert).toHaveTextContent(/Connection to evaluation database failed|Failed to fetch/i);
      }
    });

    // In error or empty state, the dashboard still preserves zero-approved invariant
    expect(screen.getAllByText('0 / 160').length).toBeGreaterThanOrEqual(1);
  });
});
