import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import SafeMarkdown from '../components/common/SafeMarkdown';

describe('SafeMarkdown & Untrusted Legal Content Sanitization', () => {
  it('renders harmless plain text nodes for malicious script tag injection', () => {
    const maliciousPayload = '<script>window.__xss_injected = true;</script>';
    const { container } = render(<SafeMarkdown content={maliciousPayload} />);

    // Ensure no actual <script> element exists in the DOM tree
    const scriptElements = container.querySelectorAll('script');
    expect(scriptElements.length).toBe(0);

    // Verify window property was never set
    expect((window as any).__xss_injected).toBeUndefined();

    // Verify text is rendered inertly as escaped text
    expect(container).toHaveTextContent('<script>window.__xss_injected = true;</script>');
  });

  it('renders inert text for img and svg onerror/onload injection vectors', () => {
    const maliciousPayload = '<img src="invalid" onerror="window.__img_xss = true" /> <svg onload="window.__svg_xss = true" />';
    const { container } = render(<SafeMarkdown content={maliciousPayload} />);

    // Ensure no img or svg elements were injected into the DOM
    expect(container.querySelectorAll('img').length).toBe(0);
    expect(container.querySelectorAll('svg').length).toBe(0);
    expect((window as any).__img_xss).toBeUndefined();
    expect((window as any).__svg_xss).toBeUndefined();
  });

  it('renders legal headings hierarchically using semantic HTML', () => {
    const content = [
      '# Landmark Constitutional Ratio',
      '## Right to Privacy Doctrine',
      '### Proportionality Test Tier',
      '#### Legitimate State Aim',
    ].join('\n');

    render(<SafeMarkdown content={content} />);

    expect(screen.getByRole('heading', { level: 1, name: /Landmark Constitutional Ratio/i })).toBeInTheDocument();
    expect(screen.getByRole('heading', { level: 2, name: /Right to Privacy Doctrine/i })).toBeInTheDocument();
    expect(screen.getByRole('heading', { level: 3, name: /Proportionality Test Tier/i })).toBeInTheDocument();
    expect(screen.getByRole('heading', { level: 4, name: /Legitimate State Aim/i })).toBeInTheDocument();
  });

  it('renders bullet lists and numbered lists for legal elements', () => {
    const content = [
      '- First requirement: legality',
      '- Second requirement: necessity',
      '- Third requirement: proportionality',
      '',
      '1. File petition',
      '2. Issue notice',
    ].join('\n');

    render(<SafeMarkdown content={content} />);

    expect(screen.getByText(/First requirement: legality/i)).toBeInTheDocument();
    expect(screen.getByText(/Second requirement: necessity/i)).toBeInTheDocument();
    expect(screen.getByText(/File petition/i)).toBeInTheDocument();
    expect(screen.getByText(/Issue notice/i)).toBeInTheDocument();
  });

  it('renders legal quotes using semantic blockquote element', () => {
    const content = '> Privacy is the constitutional core of human dignity.';
    const { container } = render(<SafeMarkdown content={content} />);

    const bq = container.querySelector('blockquote');
    expect(bq).toBeInTheDocument();
    expect(bq).toHaveTextContent(/Privacy is the constitutional core of human dignity/i);
  });

  it('renders code blocks and inline code blocks', () => {
    const content = [
      'The statute defines Section `377` as follows:',
      '```',
      'SELECT case_id, ratio_decidendi FROM supreme_court_judgments WHERE year = 2018;',
      '```',
    ].join('\n');

    const { container } = render(<SafeMarkdown content={content} />);

    const codeSnippet = container.querySelector('code');
    expect(codeSnippet).toBeInTheDocument();
    expect(codeSnippet).toHaveTextContent('377');

    const preBlock = container.querySelector('pre');
    expect(preBlock).toBeInTheDocument();
    expect(preBlock).toHaveTextContent(/SELECT case_id, ratio_decidendi/i);
  });

  it('renders structured markdown tables with headers and rows', () => {
    const tableMarkdown = [
      '| Case Name | Year | Bench Strength |',
      '| --- | --- | --- |',
      '| K.S. Puttaswamy v. Union of India | 2017 | 9 Judges |',
      '| Navtej Singh Johar v. Union of India | 2018 | 5 Judges |',
    ].join('\n');

    const { container } = render(<SafeMarkdown content={tableMarkdown} />);

    const table = container.querySelector('table');
    expect(table).toBeInTheDocument();
    expect(screen.getByText('Case Name')).toBeInTheDocument();
    expect(screen.getByText('Bench Strength')).toBeInTheDocument();
    expect(screen.getByText(/K.S. Puttaswamy v. Union of India/i)).toBeInTheDocument();
    expect(screen.getByText(/9 Judges/i)).toBeInTheDocument();
    expect(screen.getByText(/Navtej Singh Johar v. Union of India/i)).toBeInTheDocument();
  });

  it('parses bracketed legal citations into interactive pills and triggers onCitationClick', () => {
    const onCitationClick = vi.fn();
    const content = 'As established in [AIR 2017 SC 4401] and reiterated in [AIR 2018 SC 4321], constitutional morality prevails.';

    render(<SafeMarkdown content={content} onCitationClick={onCitationClick} />);

    const citationPill = screen.getByRole('button', { name: /AIR 2017 SC 4401/i });
    expect(citationPill).toBeInTheDocument();
    expect(citationPill).toHaveAttribute('title', expect.stringContaining('AIR 2017 SC 4401'));

    fireEvent.click(citationPill);
    expect(onCitationClick).toHaveBeenCalledTimes(1);
    expect(onCitationClick).toHaveBeenCalledWith('AIR 2017 SC 4401');
  });

  it('renders null gracefully when given empty or null content', () => {
    const { container } = render(<SafeMarkdown content="" />);
    expect(container).toBeEmptyDOMElement();
  });
});
