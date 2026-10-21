import React from 'react';

interface SafeMarkdownProps {
  content: string;
  className?: string;
  onCitationClick?: (citationText: string) => void;
}

/**
 * Type-safe, XSS-free Markdown renderer tailored for legal briefs and answers.
 * Parses headings, bullet/number lists, blockquotes, bold/italic, inline code,
 * and highlights bracketed legal citations (e.g., "[1978 1 SCC 248]") as pills.
 */
export const SafeMarkdown: React.FC<SafeMarkdownProps> = ({
  content,
  className = '',
  onCitationClick,
}) => {
  if (!content) return null;

  const lines = content.split('\n');
  const elements: React.ReactNode[] = [];
  let currentList: { type: 'ul' | 'ol'; items: string[] } | null = null;
  let currentBlockquote: string[] = [];

  const flushList = () => {
    if (!currentList) return;
    const ListTag = currentList.type;
    const listIndex = elements.length;
    elements.push(
      <ListTag
        key={`list-${listIndex}`}
        className={`my-3 pl-6 space-y-1 text-slate-300 leading-relaxed ${
          ListTag === 'ul' ? 'list-disc marker:text-primary' : 'list-decimal marker:text-primary font-mono'
        }`}
      >
        {currentList.items.map((item, idx) => (
          <li key={idx} className="text-sm">
            {renderInline(item, onCitationClick)}
          </li>
        ))}
      </ListTag>
    );
    currentList = null;
  };

  const flushBlockquote = () => {
    if (currentBlockquote.length === 0) return;
    const bqIndex = elements.length;
    elements.push(
      <blockquote
        key={`bq-${bqIndex}`}
        className="my-4 pl-4 border-l-2 border-primary/60 bg-slate-900/40 p-3 rounded-r-lg font-serif italic text-slate-300 text-sm leading-relaxed"
      >
        {currentBlockquote.map((line, idx) => (
          <p key={idx} className={idx > 0 ? 'mt-2' : ''}>
            {renderInline(line, onCitationClick)}
          </p>
        ))}
      </blockquote>
    );
    currentBlockquote = [];
  };

  for (let i = 0; i < lines.length; i++) {
    const rawLine = lines[i];
    const trimmed = rawLine.trim();

    // Empty lines act as separators
    if (!trimmed) {
      flushList();
      flushBlockquote();
      continue;
    }

    // Horizontal rule
    if (/^(---|___|\*\*\*)$/.test(trimmed)) {
      flushList();
      flushBlockquote();
      elements.push(<hr key={`hr-${i}`} className="my-6 border-slate-800" />);
      continue;
    }

    // Blockquote
    if (trimmed.startsWith('>')) {
      flushList();
      currentBlockquote.push(trimmed.replace(/^>\s?/, ''));
      continue;
    } else {
      flushBlockquote();
    }

    // Headings
    if (trimmed.startsWith('#### ')) {
      flushList();
      elements.push(
        <h4 key={`h4-${i}`} className="text-sm font-bold text-slate-200 uppercase tracking-wider mt-5 mb-2">
          {renderInline(trimmed.substring(5), onCitationClick)}
        </h4>
      );
      continue;
    }
    if (trimmed.startsWith('### ')) {
      flushList();
      elements.push(
        <h3 key={`h3-${i}`} className="text-base font-bold text-white mt-6 mb-2 flex items-center gap-2">
          <span className="w-1.5 h-1.5 rounded-full bg-primary inline-block"></span>
          {renderInline(trimmed.substring(4), onCitationClick)}
        </h3>
      );
      continue;
    }
    if (trimmed.startsWith('## ')) {
      flushList();
      elements.push(
        <h2 key={`h2-${i}`} className="text-lg font-serif font-bold text-white mt-7 mb-3 border-b border-slate-800/80 pb-1.5">
          {renderInline(trimmed.substring(3), onCitationClick)}
        </h2>
      );
      continue;
    }
    if (trimmed.startsWith('# ')) {
      flushList();
      elements.push(
        <h1 key={`h1-${i}`} className="text-xl font-serif font-bold text-white mt-8 mb-4 border-b border-primary/30 pb-2">
          {renderInline(trimmed.substring(2), onCitationClick)}
        </h1>
      );
      continue;
    }

    // Bullet list
    const bulletMatch = trimmed.match(/^[-*•]\s+(.*)$/);
    if (bulletMatch) {
      if (!currentList || currentList.type !== 'ul') {
        flushList();
        currentList = { type: 'ul', items: [] };
      }
      currentList.items.push(bulletMatch[1]);
      continue;
    }

    // Numbered list
    const numMatch = trimmed.match(/^\d+[.)]\s+(.*)$/);
    if (numMatch) {
      if (!currentList || currentList.type !== 'ol') {
        flushList();
        currentList = { type: 'ol', items: [] };
      }
      currentList.items.push(numMatch[1]);
      continue;
    }

    // Regular paragraph
    flushList();
    elements.push(
      <p key={`p-${i}`} className="my-2.5 text-sm text-slate-300 leading-relaxed font-sans">
        {renderInline(trimmed, onCitationClick)}
      </p>
    );
  }

  flushList();
  flushBlockquote();

  return <div className={`safe-markdown space-y-1 ${className}`}>{elements}</div>;
};

/**
 * Helper to parse bold, italic, inline code, and bracketed citation pills
 */
function renderInline(text: string, onCitationClick?: (c: string) => void): React.ReactNode[] {
  // Regex tokens:
  // 1: `code`
  // 2: **bold**
  // 3: *italic*
  // 4: [citation]
  const pattern = /(`[^`]+`|\*\*[^*]+\*\*|\*[^*]+\*|\[[^\]]+\])/g;
  const parts = text.split(pattern);

  return parts.map((part, index) => {
    if (!part) return null;

    if (part.startsWith('`') && part.endsWith('`')) {
      return (
        <code
          key={index}
          className="px-1.5 py-0.5 mx-0.5 rounded bg-slate-900 border border-slate-700/60 font-mono text-xs text-blue-300"
        >
          {part.slice(1, -1)}
        </code>
      );
    }

    if (part.startsWith('**') && part.endsWith('**')) {
      return (
        <strong key={index} className="font-semibold text-slate-100">
          {part.slice(2, -2)}
        </strong>
      );
    }

    if (part.startsWith('*') && part.endsWith('*')) {
      return (
        <em key={index} className="italic text-slate-200">
          {part.slice(1, -1)}
        </em>
      );
    }

    if (part.startsWith('[') && part.endsWith(']')) {
      const citeText = part.slice(1, -1);
      // If it looks like a footnote citation, landmark case, or paragraph quote
      return (
        <button
          key={index}
          type="button"
          onClick={() => onCitationClick && onCitationClick(citeText)}
          className="inline-flex items-center px-1.5 py-0.5 mx-1 rounded text-[11px] font-mono font-medium bg-blue-950/60 text-blue-300 border border-blue-800/60 hover:bg-blue-900/50 hover:text-white transition-colors cursor-pointer"
          title={`Inspect citation: ${citeText}`}
        >
          {citeText}
        </button>
      );
    }

    return <span key={index}>{part}</span>;
  });
}

export default SafeMarkdown;
