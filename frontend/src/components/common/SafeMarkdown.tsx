import React from 'react';

interface SafeMarkdownProps {
  content: string;
  className?: string;
  onCitationClick?: (citationText: string) => void;
}

/**
 * Type-safe, XSS-free Markdown renderer tailored for legal briefs, synthesis answers,
 * and case ratio decidendi. Parses headings, code blocks, markdown tables, lists,
 * blockquotes, bold/italic, inline code, and bracketed citation pills.
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
  let inCodeBlock = false;
  let codeBlockLines: string[] = [];
  let currentTable: { headers: string[]; rows: string[][] } | null = null;

  const flushList = () => {
    if (!currentList) return;
    const ListTag = currentList.type;
    const listIndex = elements.length;
    elements.push(
      <ListTag
        key={`list-${listIndex}`}
        className={`my-3 pl-6 space-y-1.5 text-slate-300 leading-relaxed font-sans ${
          ListTag === 'ul' ? 'list-disc marker:text-blue-400' : 'list-decimal marker:text-blue-400 font-mono text-xs'
        }`}
      >
        {currentList.items.map((item, idx) => (
          <li key={idx} className="text-xs sm:text-sm leading-relaxed">
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
        className="my-4 pl-4 border-l-2 border-blue-500/70 bg-slate-900/50 p-3.5 rounded-r-xl font-serif italic text-slate-300 text-xs sm:text-sm leading-relaxed"
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

  const flushCodeBlock = () => {
    if (!inCodeBlock) return;
    const codeIndex = elements.length;
    elements.push(
      <pre
        key={`code-${codeIndex}`}
        className="my-4 p-4 rounded-xl bg-slate-950 border border-slate-800 text-slate-200 font-mono text-xs overflow-x-auto custom-scrollbar leading-relaxed"
      >
        <code>{codeBlockLines.join('\n')}</code>
      </pre>
    );
    inCodeBlock = false;
    codeBlockLines = [];
  };

  const flushTable = () => {
    if (!currentTable) return;
    const tableIndex = elements.length;
    elements.push(
      <div key={`table-${tableIndex}`} className="my-5 overflow-x-auto rounded-xl border border-slate-800 custom-scrollbar">
        <table className="w-full text-left text-xs border-collapse">
          <thead>
            <tr className="bg-slate-950/80 border-b border-slate-800 text-slate-400 uppercase tracking-wider text-[10px] font-bold">
              {currentTable.headers.map((h, i) => (
                <th key={i} className="p-3 font-semibold">
                  {renderInline(h.trim(), onCitationClick)}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 bg-slate-900/30">
            {currentTable.rows.map((row, rIdx) => (
              <tr key={rIdx} className="hover:bg-slate-850/40 transition-colors">
                {row.map((cell, cIdx) => (
                  <td key={cIdx} className="p-3 text-slate-300 font-sans leading-relaxed">
                    {renderInline(cell.trim(), onCitationClick)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
    currentTable = null;
  };

  for (let i = 0; i < lines.length; i++) {
    const rawLine = lines[i];
    const trimmed = rawLine.trim();

    // Code blocks toggle
    if (trimmed.startsWith('```')) {
      if (inCodeBlock) {
        flushCodeBlock();
      } else {
        flushList();
        flushBlockquote();
        flushTable();
        inCodeBlock = true;
      }
      continue;
    }

    if (inCodeBlock) {
      codeBlockLines.push(rawLine);
      continue;
    }

    // Markdown table row detection
    if (trimmed.startsWith('|') && trimmed.endsWith('|')) {
      flushList();
      flushBlockquote();
      const cells = trimmed
        .slice(1, -1)
        .split('|')
        .map((c) => c.trim());

      // Check if it's separator row: | --- | --- |
      const isSeparator = cells.every((c) => /^:?-+:?$/.test(c));

      if (isSeparator) {
        // Just marks separation, continue
        continue;
      }

      if (!currentTable) {
        // First row is header
        currentTable = { headers: cells, rows: [] };
      } else {
        currentTable.rows.push(cells);
      }
      continue;
    } else if (currentTable) {
      flushTable();
    }

    // Empty lines act as block separators
    if (!trimmed) {
      flushList();
      flushBlockquote();
      continue;
    }

    // Horizontal rule
    if (/^(---|___|\*\*\*)$/.test(trimmed)) {
      flushList();
      flushBlockquote();
      elements.push(<hr key={`hr-${i}`} className="my-6 border-slate-800/80" />);
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
        <h4 key={`h4-${i}`} className="text-xs sm:text-sm font-bold text-slate-200 uppercase tracking-wider mt-5 mb-2">
          {renderInline(trimmed.substring(5), onCitationClick)}
        </h4>
      );
      continue;
    }
    if (trimmed.startsWith('### ')) {
      flushList();
      elements.push(
        <h3 key={`h3-${i}`} className="text-sm sm:text-base font-bold text-white mt-6 mb-2 flex items-center gap-2">
          <span className="w-1.5 h-1.5 rounded-full bg-blue-500 inline-block shrink-0" />
          <span>{renderInline(trimmed.substring(4), onCitationClick)}</span>
        </h3>
      );
      continue;
    }
    if (trimmed.startsWith('## ')) {
      flushList();
      elements.push(
        <h2 key={`h2-${i}`} className="text-base sm:text-lg font-serif font-bold text-white mt-7 mb-3 border-b border-slate-800/80 pb-1.5">
          {renderInline(trimmed.substring(3), onCitationClick)}
        </h2>
      );
      continue;
    }
    if (trimmed.startsWith('# ')) {
      flushList();
      elements.push(
        <h1 key={`h1-${i}`} className="text-lg sm:text-xl font-serif font-bold text-white mt-8 mb-4 border-b border-blue-500/30 pb-2">
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
      <p key={`p-${i}`} className="my-2.5 text-xs sm:text-sm text-slate-300 leading-relaxed font-sans break-words">
        {renderInline(trimmed, onCitationClick)}
      </p>
    );
  }

  flushList();
  flushBlockquote();
  flushCodeBlock();
  flushTable();

  return <div className={`safe-markdown space-y-1 break-words ${className}`}>{elements}</div>;
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
          className="px-1.5 py-0.5 mx-0.5 rounded bg-slate-950 border border-slate-700/60 font-mono text-[11px] text-blue-300"
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
        <em key={index} className="italic text-slate-200 font-serif">
          {part.slice(1, -1)}
        </em>
      );
    }

    if (part.startsWith('[') && part.endsWith(']')) {
      const citeText = part.slice(1, -1);
      return (
        <button
          key={index}
          type="button"
          onClick={() => onCitationClick && onCitationClick(citeText)}
          className="inline-flex items-center px-1.5 py-0.5 mx-0.5 rounded text-[11px] font-mono font-medium bg-blue-950/70 text-blue-300 border border-blue-800/60 hover:bg-blue-900/60 hover:text-white hover:border-blue-700 transition-colors cursor-pointer select-none align-baseline"
          title={`Inspect verified legal citation: ${citeText}`}
        >
          {citeText}
        </button>
      );
    }

    return <span key={index}>{part}</span>;
  });
}

export default SafeMarkdown;
