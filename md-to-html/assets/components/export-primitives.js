/**
 * export-primitives.js — MDH export utilities
 *
 * WHEN TO USE: Copy this entire block into the <script> of any editor/sandbox
 * output that needs copy-to-clipboard or file download. Always place this at
 * the top of the <script> block before component code that calls MDH.copy or
 * MDH.download.
 *
 * INVARIANTS:
 *   - No network calls (fetch, XHR, WebSocket, etc.) — ever.
 *   - Works on file:// (no isSecureContext requirement for execCommand fallback).
 *   - textContent / escape only; never innerHTML on user data.
 *
 * Functions:
 *   MDH.copy(text)                         — copy string to clipboard
 *   MDH.download(name, text, type?)        — trigger local file download
 *   MDH.escape(str)                        — HTML-escape a string for DOM insertion
 */

window.MDH = window.MDH || {};

// Clipboard: Async API with execCommand fallback for file://
MDH.copy = function(text) {
  if (navigator.clipboard && window.isSecureContext) {
    navigator.clipboard.writeText(text).catch(function() { MDH._legacyCopy(text); });
  } else {
    MDH._legacyCopy(text);
  }
};

MDH._legacyCopy = function(text) {
  var ta = document.createElement('textarea');
  ta.value = text;
  ta.style.position = 'fixed';
  ta.style.opacity = '0';
  document.body.appendChild(ta);
  ta.select();
  try { document.execCommand('copy'); } finally { ta.remove(); }
};

// Local file download — no network, uses object URL
MDH.download = function(name, text, type) {
  type = type || 'text/markdown';
  var blob = new Blob([text], { type: type });
  var url = URL.createObjectURL(blob);
  var a = document.createElement('a');
  a.href = url;
  a.download = name;
  // Firefox dispatches the download only for an anchor in the document, and
  // aborts it if the object URL is revoked before the fetch starts.
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(function() { URL.revokeObjectURL(url); }, 0);
};

// HTML-escape helper — use for inserting text into innerHTML contexts
// Prefer textContent directly when possible (invariant 10)
MDH.escape = function(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
};
