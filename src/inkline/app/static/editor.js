/**
 * Inkline Editor — CodeMirror 6 markdown editor with live PDF preview.
 *
 * Uses the vendored codemirror.bundle.mjs which exports:
 *   EditorView, basicSetup, minimalSetup
 *
 * The lang-markdown.bundle.mjs exports:
 *   markdown (language support)
 *
 * Endpoints used:
 *   POST /render — non-agentic render
 *   WS   /watch?file=<path> — file-change push
 *   GET  /authoring/directives — auto-completion
 *   POST /redesign_slide — D3 fix-this-slide
 *   GET  /output/<basename>.notes.txt — speaker notes
 */

// ── Module imports ────────────────────────────────────────────────────────────

import {
  EditorView,
  basicSetup,
} from '/static/vendor/codemirror/codemirror.bundle.mjs';

// markdown() language support — loaded lazily to avoid duplicate @codemirror/state
// instances between the two bundles. If it fails, the editor works without syntax highlighting.
let _markdownExtension = null;
async function _loadMarkdown() {
  try {
    const mod = await import('/static/vendor/codemirror/lang-markdown.bundle.mjs');
    _markdownExtension = mod.markdown();
  } catch (_) {
    // Graceful degradation — editor works without markdown highlighting
    console.warn('[Inkline] lang-markdown not loaded — editor will work without MD highlighting');
  }
}

// ── State ─────────────────────────────────────────────────────────────────────

let _editorView = null;
let _autoRenderTimer = null;
let _autoRenderEnabled = true;
const _autoRenderDebounce = 1500;
let _lastPdfBasename = null;
let _auditResults = [];

// ── Settings persistence ───────────────────────────────────────────────────────

const SETTINGS_KEY = 'inkline_editor_settings';

function _loadSettings() {
  try {
    const s = JSON.parse(localStorage.getItem(SETTINGS_KEY) || '{}');
    _autoRenderEnabled = s.autoRender !== false;
  } catch (_) {}
}

function _saveSettings() {
  try {
    localStorage.setItem(SETTINGS_KEY, JSON.stringify({ autoRender: _autoRenderEnabled }));
  } catch (_) {}
}

// ── CodeMirror theme ──────────────────────────────────────────────────────────

const _inklineTheme = EditorView.theme({
  '&': {
    color: '#e8eaf0',
    backgroundColor: '#0f1117',
    height: '100%',
  },
  '.cm-content': {
    caretColor: '#6c63ff',
    fontFamily: '"JetBrains Mono", "Fira Code", "Cascadia Code", ui-monospace, monospace',
    fontSize: '13px',
    lineHeight: '1.65',
    padding: '12px 0',
  },
  '.cm-cursor, .cm-dropCursor': { borderLeftColor: '#6c63ff' },
  '.cm-line': { paddingLeft: '12px', paddingRight: '12px' },
  '.cm-activeLine': { backgroundColor: 'rgba(108,99,255,0.06)' },
  '.cm-activeLineGutter': { backgroundColor: 'rgba(108,99,255,0.08)' },
  '.cm-gutters': {
    backgroundColor: '#0f1117',
    borderRight: '1px solid #2a2d3a',
    color: '#8890a4',
    fontSize: '11px',
  },
  '.cm-selectionBackground': { backgroundColor: 'rgba(108,99,255,0.25)' },
  '&.cm-focused .cm-selectionBackground': { backgroundColor: 'rgba(108,99,255,0.3)' },
}, { dark: true });

// ── Status bar helpers ────────────────────────────────────────────────────────

function _setStatus(state, text) {
  const dot   = document.getElementById('editor-status-dot');
  const label = document.getElementById('editor-status-text');
  if (dot)   { dot.className = state; }
  if (label) label.textContent = text;
}

function _setAuditBadge(auditResult) {
  const badge = document.getElementById('editor-audit-badge');
  if (!badge || !auditResult) return;
  const { fail = 0, pass = 0 } = auditResult;
  if (fail > 0) {
    badge.textContent = `${fail} fail`;
    badge.className = 'has-fail';
  } else if (pass > 0) {
    badge.textContent = `${pass} pass`;
    badge.className = 'all-pass';
  } else {
    badge.textContent = '';
    badge.className = '';
  }
}

// ── PDF preview ───────────────────────────────────────────────────────────────

function _showEditorPdf(basename) {
  const frame = document.getElementById('editor-pdf-frame');
  if (!frame) return;
  const url = `/output/${basename}?t=${Date.now()}`;
  _lastPdfBasename = basename;
  frame.src = url;
  _loadNotes(basename.replace(/\.pdf$/, ''));
}

// ── Speaker notes ─────────────────────────────────────────────────────────────

async function _loadNotes(stem) {
  const notesBody = document.getElementById('notes-body');
  if (!notesBody) return;
  try {
    const r = await fetch(`/output/${stem}.notes.txt?t=${Date.now()}`);
    if (r.ok) {
      notesBody.textContent = await r.text();
    } else {
      notesBody.textContent = '(no speaker notes)';
    }
  } catch (_) {
    notesBody.textContent = '(could not load notes)';
  }
}

// ── POST /render ──────────────────────────────────────────────────────────────

async function _triggerRender(content, skipAudit = true) {
  _setStatus('rendering', 'Rendering…');

  try {
    const r = await fetch('/render', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ markdown: content, skip_audit: skipAudit }),
    });

    if (!r.ok) {
      const err = await r.json().catch(() => ({ error: r.statusText }));
      _setStatus('error', `Error: ${err.error || r.statusText}`);
      return;
    }

    const data = await r.json();
    const pdfPath = data.outputs && data.outputs.pdf;
    if (pdfPath) {
      const basename = pdfPath.split('/').pop();
      _showEditorPdf(basename);
      _auditResults = data.audit ? (data.audit.details || []) : [];
      _setAuditBadge(data.audit);
      const warnCount = data.warnings ? data.warnings.length : 0;
      _setStatus('done', warnCount > 0 ? `Done — ${warnCount} warnings` : 'Done');
    } else if (data.error) {
      _setStatus('error', `Error: ${data.error}`);
    }
  } catch (err) {
    _setStatus('error', `Render failed: ${err.message}`);
  }
}

// ── Auto-render debounce ──────────────────────────────────────────────────────

function _scheduleAutoRender(content) {
  if (!_autoRenderEnabled) return;
  if (_autoRenderTimer) clearTimeout(_autoRenderTimer);
  _setStatus('idle', 'Waiting to render…');
  _autoRenderTimer = setTimeout(() => {
    _autoRenderTimer = null;
    _triggerRender(content, true);
  }, _autoRenderDebounce);
}

// ── Manual save ───────────────────────────────────────────────────────────────

function _handleManualSave(view) {
  if (_autoRenderTimer) clearTimeout(_autoRenderTimer);
  _triggerRender(view.state.doc.toString(), false);
  return true;
}

// ── Fix-this-slide ────────────────────────────────────────────────────────────

async function _fixThisSlide(slideIndex, auditFindings) {
  _setStatus('rendering', 'Redesigning slide…');
  const content = _editorView ? _editorView.state.doc.toString() : '';

  try {
    const r = await fetch('/redesign_slide', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        slide_index: slideIndex,
        audit_findings: auditFindings,
        current_spec: {},
        source_section: { narrative: content },
      }),
    });

    if (!r.ok) { _setStatus('error', 'Redesign failed'); return; }

    const data = await r.json();
    if (data.suggested_markdown) _showDiffOverlay(data.suggested_markdown, data.rationale);
    _setStatus('idle', 'Redesign ready — review suggestion');
  } catch (err) {
    _setStatus('error', `Redesign error: ${err.message}`);
  }
}

function _escapeHtml(str) {
  return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

function _showDiffOverlay(suggestedMarkdown, rationale) {
  const host = document.getElementById('cm-host');
  if (!host) return;
  const existing = host.querySelector('.redesign-diff-overlay');
  if (existing) existing.remove();

  const overlay = document.createElement('div');
  overlay.className = 'redesign-diff-overlay';
  overlay.innerHTML = `
    <div class="redesign-diff-header">Redesign suggestion${rationale ? ' — ' + _escapeHtml(rationale) : ''}</div>
    <div class="redesign-diff-body">${_escapeHtml(suggestedMarkdown)}</div>
    <div class="redesign-diff-actions">
      <button class="btn-accept">Accept</button>
      <button class="btn-reject">Reject</button>
    </div>
  `;

  overlay.querySelector('.btn-accept').addEventListener('click', () => {
    if (_editorView) {
      const { from } = _editorView.state.selection.main;
      _editorView.dispatch({ changes: { from, insert: suggestedMarkdown } });
    }
    overlay.remove();
    _setStatus('idle', 'Accepted redesign suggestion');
  });

  overlay.querySelector('.btn-reject').addEventListener('click', () => {
    overlay.remove();
    _setStatus('idle', 'Rejected redesign suggestion');
  });

  host.appendChild(overlay);
}

// ── Editor initialisation ─────────────────────────────────────────────────────

const _initialContent = [
  '---',
  'brand: minimal',
  'template: consulting',
  'title: My Deck',
  '---',
  '',
  '## Introduction',
  '<!-- _layout: content -->',
  'Write your content here. Each `##` heading starts a new slide.',
  '',
  '## Key points',
  '<!-- _layout: three_card -->',
  '- First important point',
  '- Second important point',
  '- Third important point',
  '',
].join('\n');

async function _initEditor() {
  const host = document.getElementById('cm-host');
  if (!host || _editorView) return;

  // Try to load markdown language support (graceful degradation on failure)
  await _loadMarkdown();

  const updateListener = EditorView.updateListener.of((update) => {
    if (update.docChanged) {
      _scheduleAutoRender(update.view.state.doc.toString());
    }
  });

  const saveKeymap = EditorView.domEventHandlers({
    keydown(event, view) {
      if ((event.ctrlKey || event.metaKey) && event.key === 's') {
        event.preventDefault();
        _handleManualSave(view);
        return true;
      }
      return false;
    },
  });

  const baseExtensions = [
    basicSetup,
    EditorView.lineWrapping,
    _inklineTheme,
    updateListener,
    saveKeymap,
  ];

  // Try with markdown extension first; fall back to base-only on conflict error
  const tryCreate = (extensions) => {
    try {
      return new EditorView({ doc: _initialContent, extensions, parent: host });
    } catch (e) {
      return null;
    }
  };

  if (_markdownExtension) {
    const withMd = [_markdownExtension, ...baseExtensions];
    _editorView = tryCreate(withMd);
  }

  if (!_editorView) {
    // Fallback: base editor without markdown highlighting
    _editorView = new EditorView({
      doc: _initialContent,
      extensions: baseExtensions,
      parent: host,
    });
    console.info('[Inkline] Using editor without markdown highlighting (bundle conflict avoided)');
  }
}

// ── Notes pane toggle ─────────────────────────────────────────────────────────

function _initNotesPane() {
  const header = document.getElementById('notes-header');
  const pane   = document.getElementById('notes-pane');
  if (!header || !pane) return;

  header.addEventListener('click', () => {
    pane.classList.toggle('open');
    header.textContent = pane.classList.contains('open')
      ? 'Speaker notes ▲'
      : 'Speaker notes ▼';
  });
}

// ── Settings popover ──────────────────────────────────────────────────────────

function _initSettingsPopover() {
  const btn = document.getElementById('editor-settings-btn');
  const pop = document.getElementById('editor-settings-popover');
  const cb  = document.getElementById('editor-auto-render-cb');
  if (!btn || !pop) return;

  btn.addEventListener('click', (e) => {
    e.stopPropagation();
    pop.classList.toggle('open');
  });

  document.addEventListener('click', () => pop.classList.remove('open'));
  pop.addEventListener('click', (e) => e.stopPropagation());

  if (cb) {
    cb.checked = _autoRenderEnabled;
    cb.addEventListener('change', () => {
      _autoRenderEnabled = cb.checked;
      _saveSettings();
    });
  }
}

// ── Tab switching ─────────────────────────────────────────────────────────────

function _initTabs() {
  const chatBtn    = document.getElementById('tab-btn-chat');
  const editorBtn  = document.getElementById('tab-btn-editor');
  const chatPane   = document.getElementById('tab-chat');
  const editorPane = document.getElementById('tab-editor');

  if (!chatBtn || !editorBtn || !chatPane || !editorPane) {
    console.warn('[Inkline] Tab elements not found — editor tab will not work');
    return;
  }

  function showChat() {
    chatBtn.classList.add('active');
    editorBtn.classList.remove('active');
    chatPane.style.display = 'grid';
    editorPane.style.display = 'none';
  }

  function showEditor() {
    editorBtn.classList.add('active');
    chatBtn.classList.remove('active');
    editorPane.style.display = 'flex';
    chatPane.style.display = 'none';
    // Lazy-init the editor on first switch (async to allow markdown ext load)
    _initEditor().then(() => {
      if (_editorView && !_lastPdfBasename) {
        _triggerRender(_editorView.state.doc.toString(), true);
      }
    });
  }

  chatBtn.addEventListener('click', showChat);
  editorBtn.addEventListener('click', showEditor);
}

// ── Boot ──────────────────────────────────────────────────────────────────────

_loadSettings();

document.addEventListener('DOMContentLoaded', () => {
  _initTabs();
  _initNotesPane();
  _initSettingsPopover();
  console.log('[Inkline] Editor module loaded');
});
