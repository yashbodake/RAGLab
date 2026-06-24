<script setup>
import { ref, computed } from 'vue';
import SourcesAccordion from './SourcesAccordion.vue';

const props = defineProps({
  role: String, // 'user' | 'assistant'
  content: String,
  sources: Array,
  isStreaming: Boolean
});

// Copy-to-clipboard for code blocks. Tracks which block is showing the
// "copied" confirmation so multiple blocks don't all flash at once.
const copiedBlockIndex = ref(-1);
async function copyCode(text, index) {
  try {
    await navigator.clipboard.writeText(text);
    copiedBlockIndex.value = index;
    setTimeout(() => { if (copiedBlockIndex.value === index) copiedBlockIndex.value = -1; }, 1500);
  } catch (e) {
    // Fallback for non-secure contexts (HF HTTP): use a hidden textarea
    const ta = document.createElement('textarea');
    ta.value = text;
    ta.style.position = 'fixed';
    ta.style.opacity = '0';
    document.body.appendChild(ta);
    ta.select();
    try { document.execCommand('copy'); } catch (_) {}
    document.body.removeChild(ta);
    copiedBlockIndex.value = index;
    setTimeout(() => { if (copiedBlockIndex.value === index) copiedBlockIndex.value = -1; }, 1500);
  }
}

function parseInline(text) {
  const segments = [];
  let remaining = text;

  while (remaining) {
    const codeMatch = remaining.match(/`([^`\n]+)`/);
    const boldAsteriskMatch = remaining.match(/\*\*([^*\n]+)\*\*/);
    const boldUnderscoreMatch = remaining.match(/__([^\n_]+)__/);
    const italicAsteriskMatch = remaining.match(/\*([^*\n]+)\*/);
    const italicUnderscoreMatch = remaining.match(/_([^\n_]+)_/);

    let firstMatch = null;
    let matchType = '';
    let startIndex = -1;
    let matchLength = 0;
    let matchText = '';

    const checkMatch = (match, type) => {
      if (match && (startIndex === -1 || match.index < startIndex)) {
        firstMatch = match;
        matchType = type;
        startIndex = match.index;
        matchLength = match[0].length;
        matchText = match[1];
      }
    };

    checkMatch(codeMatch, 'code');
    checkMatch(boldAsteriskMatch, 'bold');
    checkMatch(boldUnderscoreMatch, 'bold');
    checkMatch(italicAsteriskMatch, 'italic');
    checkMatch(italicUnderscoreMatch, 'italic');

    if (firstMatch !== null) {
      if (startIndex > 0) {
        segments.push({ type: 'text', text: remaining.substring(0, startIndex) });
      }
      segments.push({ type: matchType, text: matchText });
      remaining = remaining.substring(startIndex + matchLength);
    } else {
      segments.push({ type: 'text', text: remaining });
      break;
    }
  }
  return segments;
}

const parsedBlocks = computed(() => {
  if (!props.content) return [];
  const lines = props.content.split('\n');
  const result = [];

  let i = 0;
  while (i < lines.length) {
    const line = lines[i];

    // ── Fenced code block (```) ──────────────────────────────────────
    const fenceMatch = line.match(/^```(\w*)/);
    if (fenceMatch) {
      const lang = fenceMatch[1] || '';
      const codeLines = [];
      i++;
      while (i < lines.length && !lines[i].startsWith('```')) {
        codeLines.push(lines[i]);
        i++;
      }
      i++; // skip closing fence
      result.push({ type: 'codeblock', lang, text: codeLines.join('\n') });
      continue;
    }

    // ── Table (GFM): header row | separator row | body rows ──────────
    // A table is detected when the current line has a pipe and the NEXT line
    // is a separator (---|:--:|---:).
    if (line.includes('|') && i + 1 < lines.length && /^\s*\|?[\s:|-]+\|?\s*$/.test(lines[i + 1]) && lines[i + 1].includes('-')) {
      const parseRow = (rowLine) =>
        rowLine.replace(/^\s*\|/, '').replace(/\|\s*$/, '').split('|').map(c => c.trim());
      const headers = parseRow(line);
      i += 2; // skip header + separator
      const rows = [];
      while (i < lines.length && lines[i].includes('|') && lines[i].trim() !== '') {
        rows.push(parseRow(lines[i]));
        i++;
      }
      result.push({ type: 'table', headers, rows });
      continue;
    }

    // ── Horizontal rule (---, ***, ___) ──────────────────────────────
    if (/^\s*([-*_])\1{2,}\s*$/.test(line)) {
      result.push({ type: 'hr' });
      i++;
      continue;
    }

    // ── Blockquote (> ...) ───────────────────────────────────────────
    if (/^\s*>\s?/.test(line)) {
      const quoteLines = [];
      while (i < lines.length && /^\s*>\s?/.test(lines[i])) {
        quoteLines.push(lines[i].replace(/^\s*>\s?/, ''));
        i++;
      }
      result.push({ type: 'blockquote', segments: parseInline(quoteLines.join(' ')) });
      continue;
    }

    // ── Header ───────────────────────────────────────────────────────
    const headerMatch = line.match(/^(\s*)(#{1,6})\s+(.*)/);
    if (headerMatch) {
      result.push({ type: 'header', segments: parseInline(headerMatch[3]) });
      i++;
      continue;
    }

    // ── Unordered list (- or *) ──────────────────────────────────────
    if (line.trim().startsWith('- ') || line.trim().startsWith('* ')) {
      result.push({ type: 'list', isOrdered: false, segments: parseInline(line.trim().substring(2)) });
      i++;
      continue;
    }

    // ── Ordered list (1. 2.) ─────────────────────────────────────────
    const orderedMatch = line.match(/^\s*(\d+)\.\s+(.*)/);
    if (orderedMatch) {
      result.push({ type: 'list', isOrdered: true, listNumber: orderedMatch[1], segments: parseInline(orderedMatch[2]) });
      i++;
      continue;
    }

    // ── Empty line (paragraph break, no block) ───────────────────────
    if (line.trim() === '') {
      i++;
      continue;
    }

    // ── Paragraph (default) ──────────────────────────────────────────
    result.push({ type: 'paragraph', segments: parseInline(line) });
    i++;
  }
  return result;
});

// Index of the first paragraph block — used to apply the drop-cap.
const firstParagraphIndex = computed(() =>
  parsedBlocks.value.findIndex(b => b.type === 'paragraph')
);
</script>

<template>
  <article class="message" :class="[role]">

    <!-- ── USER: manuscript input card ─────────────────────────────── -->
    <template v-if="role === 'user'">
      <div class="user-card">
        <span class="user-label label-caps">USER_INPUT // {{ new Date().toLocaleTimeString('en-GB') }}</span>
        <p class="user-text">{{ content }}</p>
      </div>
    </template>

    <!-- ── ASSISTANT: RAGLab synthesis ─────────────────────────────── -->
    <template v-else>
      <div class="synthesis-head">
        <span class="material-symbols-outlined synthesis-icon" :class="{ 'fade-pulse': isStreaming }">auto_awesome</span>
        <span class="synthesis-label label-caps">{{ isStreaming && !content ? 'RAGLAB_SYNTHESIS_THINKING' : 'RAGLAB_SYNTHESIS' }}</span>
      </div>

      <div class="synthesis-body">
        <div v-for="(block, bIdx) in parsedBlocks" :key="bIdx" :class="['block', block.type]">

          <h4 v-if="block.type === 'header'" class="block-header">
            <template v-for="(seg, sIdx) in block.segments" :key="sIdx">
              <code v-if="seg.type === 'code'" class="inline-code">{{ seg.text }}</code>
              <strong v-else-if="seg.type === 'bold'" class="bold-text">{{ seg.text }}</strong>
              <em v-else-if="seg.type === 'italic'" class="italic-text">{{ seg.text }}</em>
              <span v-else>{{ seg.text }}</span>
            </template>
          </h4>

          <p
            v-else-if="block.type === 'paragraph'"
            class="block-paragraph"
            :class="{ 'drop-cap': bIdx === firstParagraphIndex && parsedBlocks.length > 1 }"
          >
            <template v-for="(seg, sIdx) in block.segments" :key="sIdx">
              <code v-if="seg.type === 'code'" class="inline-code">{{ seg.text }}</code>
              <strong v-else-if="seg.type === 'bold'" class="bold-text">{{ seg.text }}</strong>
              <em v-else-if="seg.type === 'italic'" class="italic-text">{{ seg.text }}</em>
              <span v-else>{{ seg.text }}</span>
            </template>
          </p>

          <div v-else-if="block.type === 'list'" class="block-list-item" :class="{ ordered: block.isOrdered }">
            <span v-if="block.isOrdered" class="list-number">{{ block.listNumber }}_</span>
            <span v-else class="list-bullet">▸</span>
            <span class="list-content">
              <template v-for="(seg, sIdx) in block.segments" :key="sIdx">
                <code v-if="seg.type === 'code'" class="inline-code">{{ seg.text }}</code>
                <strong v-else-if="seg.type === 'bold'" class="bold-text">{{ seg.text }}</strong>
                <em v-else-if="seg.type === 'italic'" class="italic-text">{{ seg.text }}</em>
                <span v-else>{{ seg.text }}</span>
              </template>
            </span>
          </div>

          <!-- ── Fenced code block ─────────────────────────────────────── -->
          <div v-else-if="block.type === 'codeblock'" class="codeblock-wrap">
            <button
              class="code-copy-btn"
              :class="{ copied: copiedBlockIndex === bIdx }"
              @click="copyCode(block.text, bIdx)"
              :aria-label="copiedBlockIndex === bIdx ? 'Copied' : 'Copy code'"
            >
              <span class="material-symbols-outlined">{{ copiedBlockIndex === bIdx ? 'check' : 'content_copy' }}</span>
              <span class="copy-text">{{ copiedBlockIndex === bIdx ? 'COPIED' : 'COPY' }}</span>
            </button>
            <pre class="block-codeblock">
              <span v-if="block.lang" class="code-lang label-caps">{{ block.lang }}</span>
              <code>{{ block.text }}</code>
            </pre>
          </div>

          <!-- ── Table ─────────────────────────────────────────────────── -->
          <div v-else-if="block.type === 'table'" class="block-table-wrap">
            <table class="block-table">
              <thead>
                <tr>
                  <th v-for="(h, hIdx) in block.headers" :key="hIdx">{{ h }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(row, rIdx) in block.rows" :key="rIdx">
                  <td v-for="(cell, cIdx) in row" :key="cIdx">{{ cell }}</td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- ── Blockquote ────────────────────────────────────────────── -->
          <blockquote v-else-if="block.type === 'blockquote'" class="block-blockquote">
            <template v-for="(seg, sIdx) in block.segments" :key="sIdx">
              <code v-if="seg.type === 'code'" class="inline-code">{{ seg.text }}</code>
              <strong v-else-if="seg.type === 'bold'" class="bold-text">{{ seg.text }}</strong>
              <em v-else-if="seg.type === 'italic'" class="italic-text">{{ seg.text }}</em>
              <span v-else>{{ seg.text }}</span>
            </template>
          </blockquote>

          <!-- ── Horizontal rule ───────────────────────────────────────── -->
          <hr v-else-if="block.type === 'hr'" class="block-hr" />
        </div>

        <!-- Inline typing cursor: sits at the end of the streaming text so it
             tracks the "typing head" like ChatGPT/Claude, instead of floating
             below the content where it's rarely visible. -->
        <span v-if="isStreaming && content" class="typing-cursor-inline"></span>
      </div>

      <!-- Expandable cited documents -->
      <SourcesAccordion v-if="role === 'assistant' && sources && sources.length > 0" :sources="sources" />
    </template>

  </article>
</template>

<style scoped>
.message {
  width: 100%;
  animation: fadeSlide 0.25s ease-out;
}

/* ── USER card ─────────────────────────────────────────────────────── */
.user-card {
  position: relative;
  background: rgba(245, 239, 220, 0.45);
  border: 1px solid rgba(7, 54, 66, 0.12);
  padding: var(--spacing-lg);
  margin-bottom: var(--spacing-2xl);
}
.user-label {
  position: absolute;
  top: -9px;
  left: var(--spacing-md);
  background: var(--bg-primary);
  padding: 0 6px;
  font-size: 9px;
  color: rgba(7, 54, 66, 0.55);
}
.user-text {
  font-family: var(--font-body);
  font-size: 1.05rem;
  line-height: 1.6;
  font-style: italic;
  color: rgba(7, 54, 66, 0.9);
}

/* ── ASSISTANT synthesis ───────────────────────────────────────────── */
.synthesis-head {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-lg);
}
.synthesis-icon {
  font-size: 22px;
  color: var(--accent-secondary);
  font-variation-settings: 'FILL' 1, 'wght' 400, 'GRAD' 0, 'opsz' 24;
}
.synthesis-label {
  color: var(--accent-primary);
  font-size: 12px;
}

.synthesis-body {
  font-family: var(--font-body);
  font-size: 1rem;
  line-height: 1.7;
  color: rgba(7, 54, 66, 0.9);
}
.synthesis-body .block + .block { margin-top: var(--spacing-md); }

.block-header {
  font-family: var(--font-headline);
  font-weight: 700;
  font-size: 1.5rem;
  line-height: 1.25;
  color: var(--accent-primary);
  margin: var(--spacing-lg) 0 var(--spacing-sm);
}

.block-paragraph { color: rgba(7, 54, 66, 0.9); }

/* Inline typing cursor — sits at the end of the streaming text (inline-block),
   tracking the typing head like ChatGPT/Claude. */
.typing-cursor-inline {
  display: inline-block;
  width: 8px;
  height: 1.1em;
  background: var(--accent-secondary);
  margin-left: 3px;
  vertical-align: text-bottom;
  animation: cursorBlink 0.9s infinite;
}

.block-list-item {
  display: flex;
  align-items: flex-start;
  gap: var(--spacing-sm);
  padding: 4px 0;
}
.block-list-item.ordered {
  font-family: var(--font-mono);
  font-size: 0.9rem;
}
.list-number {
  color: var(--accent-secondary);
  font-weight: 700;
  flex-shrink: 0;
  min-width: 28px;
}
.list-bullet {
  color: var(--accent-secondary);
  flex-shrink: 0;
}
.list-content { flex: 1; }

/* ── Code block ─────────────────────────────────────────────────── */
.codeblock-wrap {
  position: relative;
  margin: var(--spacing-sm) 0;
}
.code-copy-btn {
  position: absolute;
  top: var(--spacing-xs);
  right: var(--spacing-xs);
  display: flex;
  align-items: center;
  gap: 4px;
  background: rgba(253, 246, 227, 0.12);
  border: 1px solid rgba(253, 246, 227, 0.2);
  color: rgba(253, 246, 227, 0.7);
  padding: 4px 8px;
  cursor: pointer;
  font-family: var(--font-mono);
  font-size: 0.6rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  transition: all var(--transition-fast);
  z-index: 1;
  opacity: 0;
}
.codeblock-wrap:hover .code-copy-btn { opacity: 1; }
.code-copy-btn:hover {
  background: rgba(253, 246, 227, 0.2);
  color: var(--bg-primary);
}
.code-copy-btn.copied {
  background: var(--accent-success);
  border-color: var(--accent-success);
  color: #fff;
  opacity: 1;
}
.code-copy-btn .material-symbols-outlined { font-size: 14px; }

.block-codeblock {
  position: relative;
  background: var(--accent-primary);
  color: #f5efdc;
  padding: var(--spacing-md) var(--spacing-md) var(--spacing-sm);
  overflow-x: auto;
  font-family: var(--font-mono);
  font-size: 0.82rem;
  line-height: 1.6;
}
.block-codeblock code {
  background: none;
  border: none;
  padding: 0;
  color: inherit;
  font-size: inherit;
  white-space: pre;
}
.code-lang {
  display: block;
  color: var(--accent-secondary);
  margin-bottom: var(--spacing-xs);
  font-size: 9px;
}

/* ── Table ───────────────────────────────────────────────────────── */
.block-table-wrap {
  overflow-x: auto;
  margin: var(--spacing-sm) 0;
}
.block-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.85rem;
  font-family: var(--font-body);
}
.block-table th,
.block-table td {
  border: 1px solid rgba(7, 54, 66, 0.2);
  padding: var(--spacing-xs) var(--spacing-sm);
  text-align: left;
  vertical-align: top;
}
.block-table th {
  background: var(--bg-surface-low);
  font-family: var(--font-mono);
  font-size: 0.72rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-muted);
}
.block-table tr:nth-child(even) td {
  background: rgba(7, 54, 66, 0.03);
}

/* ── Blockquote ──────────────────────────────────────────────────── */
.block-blockquote {
  border-left: 3px solid var(--accent-secondary);
  padding: var(--spacing-xs) var(--spacing-md);
  margin: var(--spacing-sm) 0;
  color: var(--text-muted);
  font-style: italic;
  background: rgba(203, 75, 22, 0.04);
}

/* ── Horizontal rule ─────────────────────────────────────────────── */
.block-hr {
  border: none;
  border-top: 1px solid rgba(7, 54, 66, 0.2);
  margin: var(--spacing-md) 0;
}

/* Inline formatting */
.inline-code {
  font-family: var(--font-mono);
  font-size: 0.88em;
  background: rgba(7, 54, 66, 0.08);
  border: 1px solid rgba(7, 54, 66, 0.12);
  padding: 1px 5px;
  color: var(--accent-primary);
}
.bold-text { font-weight: 700; color: var(--accent-primary); }
.italic-text { font-style: italic; }

@keyframes fadeSlide {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

/* ── Mobile: slightly smaller body text, tighter headers ─────────── */
@media (max-width: 600px) {
  .synthesis-body {
    font-size: 0.95rem;
    line-height: 1.65;
  }
  .block-header {
    font-size: 1.25rem;
  }
  .user-text {
    font-size: 0.95rem;
  }
}
</style>
