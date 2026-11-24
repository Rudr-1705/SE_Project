/**
 * Presentational-only inline SVG icons (no state, no side effects).
 * Used to replace emoji glyphs with crisp, theme-coloured vector icons.
 */
import React from 'react';

type IconProps = { className?: string };

const base = {
  viewBox: '0 0 20 20',
  fill: 'none',
  stroke: 'currentColor',
  strokeWidth: 1.5,
  strokeLinecap: 'round' as const,
  strokeLinejoin: 'round' as const,
  'aria-hidden': true,
  focusable: false,
};

/** Institution / jurisdiction */
export const IconBank = ({ className = 'w-4 h-4' }: IconProps) => (
  <svg {...base} className={className}>
    <path d="M3 8l7-4.5L17 8" />
    <path d="M4.5 8.5h11" />
    <path d="M5.5 10v5M8.5 10v5M11.5 10v5M14.5 10v5" />
    <path d="M3.5 16.5h13" />
  </svg>
);

/** Folder / empty workspace */
export const IconFolder = ({ className = 'w-6 h-6' }: IconProps) => (
  <svg {...base} className={className}>
    <path d="M2.5 6.5a1.5 1.5 0 011.5-1.5h3.2l1.6 1.8H16a1.5 1.5 0 011.5 1.5v6.2A1.5 1.5 0 0116 16H4a1.5 1.5 0 01-1.5-1.5v-8z" />
  </svg>
);

/** Analysis / magnifier over bars */
export const IconAnalysis = ({ className = 'w-6 h-6' }: IconProps) => (
  <svg {...base} className={className}>
    <circle cx="8.5" cy="8.5" r="5" />
    <path d="M12.2 12.2L17 17" />
    <path d="M6.5 10.5V9M8.5 10.5V7M10.5 10.5V8.2" />
  </svg>
);

/** Balance / governance trade-offs */
export const IconScale = ({ className = 'w-6 h-6' }: IconProps) => (
  <svg {...base} className={className}>
    <path d="M10 3v13.5M6.5 16.5h7" />
    <path d="M4 6.5h12" />
    <path d="M4 6.5l-2 5a2.6 2.6 0 004 0l-2-5zM16 6.5l-2 5a2.6 2.6 0 004 0l-2-5z" />
  </svg>
);

/** Warning triangle */
export const IconAlert = ({ className = 'w-5 h-5' }: IconProps) => (
  <svg {...base} className={className}>
    <path d="M10 3.2l7.2 12.6a.9.9 0 01-.8 1.4H3.6a.9.9 0 01-.8-1.4L10 3.2z" />
    <path d="M10 8v3.5M10 14h.01" />
  </svg>
);

/** PDF / document */
export const IconFilePdf = ({ className = 'w-4 h-4' }: IconProps) => (
  <svg {...base} className={className}>
    <path d="M5 2.8h6.2L15 6.6v9.6a1 1 0 01-1 1H5a1 1 0 01-1-1V3.8a1 1 0 011-1z" />
    <path d="M11 2.8v3.8h4" />
    <path d="M6.7 13.6h3.6M6.7 10.8h6" />
  </svg>
);

/** DOCX / editable document */
export const IconFileDoc = ({ className = 'w-4 h-4' }: IconProps) => (
  <svg {...base} className={className}>
    <path d="M5 2.8h6.2L15 6.6v9.6a1 1 0 01-1 1H5a1 1 0 01-1-1V3.8a1 1 0 011-1z" />
    <path d="M11 2.8v3.8h4" />
    <path d="M6.7 14.2l1.2-4.4 1.1 3 1.1-3 1.2 4.4" />
  </svg>
);

/** Check (success) */
export const IconCheck = ({ className = 'w-5 h-5' }: IconProps) => (
  <svg {...base} strokeWidth={1.8} className={className}>
    <path d="M4.5 10.5l3.5 3.5 7.5-8" />
  </svg>
);
