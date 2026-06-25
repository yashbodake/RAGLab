import { ref } from 'vue';
import { useFeatures } from './useFeatures';
import { useMetrics } from './useMetrics';
import { useLogs } from './useLogs';
import { useChunks } from './useChunks';
import { useConversations } from './useConversations';

const isStreaming = ref(false);
const compareWithBaseline = ref(false);

// AbortController for the in-flight /query fetch — lets the user stop
// generation mid-stream. Reset on each new query; null when not streaming.
let abortController = null;

// Direct reactive ref of the active conversation's message array. We keep this
// in sync with the conversation store manually (syncMessages) so the chat view
// re-renders reliably when messages are added or content streams in — a plain
// ref avoids any computed/indirection reactivity edge cases during streaming.
const messages = ref([]);

export function useChat() {
  const { getFeaturePayload } = useFeatures();
  const { updateMetrics, updateBaseline, resetMetrics } = useMetrics();
  const { appendLogs, clearLogs } = useLogs();
  const { setChunks, clearChunks } = useChunks();
  const {
    conversations,
    activeConversation,
    activeId,
    ensureActive,
    loadConversation,
    persist,
  } = useConversations();

  // Replace messages ref with the active conversation's message array (same
  // array reference the conversation object holds, so mutations are visible
  // through both paths).
  function syncMessages() {
    messages.value = activeConversation.value ? activeConversation.value.messages : [];
  }

  function clearConversation() {
    isStreaming.value = false;
    clearLogs();
    clearChunks();
    resetMetrics();
  }

  // When the active conversation changes (user picks one in history), refresh
  // the messages ref to point at it.
  function setActiveConversation(id) {
    loadConversation(id);
    syncMessages();
  }

  async function sendQuery(queryText) {
    if (!queryText.trim() || isStreaming.value) return;

    // Reset metrics, logs, and chunks for the new query
    clearLogs();
    clearChunks();
    resetMetrics();

    // Ensure we have an active conversation to append to.
    const conv = ensureActive();
    // Point the messages ref at this conversation's array.
    messages.value = conv.messages;

    // 1. Append User Message (persisted)
    const userMsg = {
      id: Date.now().toString() + '-user',
      role: 'user',
      content: queryText,
      timestamp: new Date().toISOString(),
      isStreaming: false,
    };
    conv.messages.push(userMsg);
    if (conv.title === 'New Conversation') {
      conv.title = queryText.slice(0, 40) + (queryText.length > 40 ? '…' : '');
    }

    // Build multi-turn history from prior turns (everything before this query).
    // Skip streaming/placeholder messages and cap to last 6 turns for token budget.
    const history = conv.messages
      .filter(m => m.id !== userMsg.id && m.content && !m.isStreaming)
      .slice(-6)
      .map(m => ({ role: m.role, content: m.content }));

    // 2. Append Placeholder Assistant Message (streaming)
    const assistantMsgId = Date.now().toString() + '-assistant';
    const assistantMsg = {
      id: assistantMsgId,
      role: 'assistant',
      content: '',
      sources: null,
      timestamp: new Date().toISOString(),
      isStreaming: true,
    };
    conv.messages.push(assistantMsg);
    persist();

    isStreaming.value = true;

    // Fresh AbortController for this query — stopGeneration() aborts it.
    abortController = new AbortController();

    // Typewriter reveal queue — decouples token arrival speed from reveal
    // speed so the answer types out at a natural cadence (ChatGPT/Claude feel)
    // instead of dumping each SSE chunk instantly.
    let queuedChars = '';
    let revealDone = false;

    // Helper to find the live assistant message object in the active conv.
    const findAssistant = () => conv.messages.find(m => m.id === assistantMsgId);

    // Drain a few characters per tick at a steady cadence. Characters per tick
    // scales up slightly when the queue grows long, so a fast backend burst
    // doesn't make the reveal lag unreasonably behind.
    const REVEAL_INTERVAL_MS = 24;   // ~42fps — deliberate typing pace
    const BASE_CHARS_PER_TICK = 1;
    const revealTimer = setInterval(() => {
      const msg = findAssistant();
      if (!msg) return;
      if (queuedChars.length === 0) {
        // Queue empty — if the stream already finished, complete the reveal:
        // stop the timer and flip isStreaming off (cursor stops blinking).
        if (revealDone) {
          clearInterval(revealTimer);
          msg.isStreaming = false;
          isStreaming.value = false;
          persist();
          // Once the answer is fully revealed, fetch follow-up suggestions.
          fetchSuggestions(queryText, msg.content);
        }
        return;
      }
      // Reveal more chars when falling behind so we never lag far behind the
      // backend while still looking like deliberate typing.
      const burst = queuedChars.length > 60 ? Math.ceil(queuedChars.length / 30) : BASE_CHARS_PER_TICK;
      const chunk = queuedChars.slice(0, burst);
      queuedChars = queuedChars.slice(burst);
      msg.content += chunk;
    }, REVEAL_INTERVAL_MS);

    try {
      const response = await fetch('/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'text/event-stream'
        },
        body: JSON.stringify({
          query: queryText,
          features: getFeaturePayload(),
          compare_with_baseline: compareWithBaseline.value,
          history,   // multi-turn context
        }),
        signal: abortController.signal,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: `HTTP error ${response.status}` }));
        throw new Error(errorData.detail || 'Failed to submit query');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const parts = buffer.split('\n\n');
        buffer = parts.pop(); // Save the incomplete part to parse in the next iteration

        for (const part of parts) {
          if (!part.trim()) continue;

          let eventType = '';
          let dataStr = '';

          const lines = part.split('\n');
          for (const line of lines) {
            if (line.startsWith('event:')) {
              eventType = line.substring(6).trim();
            } else if (line.startsWith('data:')) {
              dataStr = line.substring(5).trim();
            }
          }

          if (!eventType || !dataStr) continue;

          try {
            const data = JSON.parse(dataStr);

            if (eventType === 'classification') {
              // Store or log query classification metadata
            } else if (eventType === 'sources') {
              const msg = findAssistant();
              if (msg) msg.sources = data.chunks;
              setChunks(data.chunks, false);
            } else if (eventType === 'baseline_sources') {
              setChunks(data.chunks, true);
            } else if (eventType === 'token') {
              const msg = findAssistant();
              if (msg) {
                // Queue tokens for smooth typewriter reveal instead of dumping
                // each SSE chunk instantly (which reads as "appears all at once").
                queuedChars += data.text;
              }
            } else if (eventType === 'metrics') {
              updateMetrics(data);
            } else if (eventType === 'baseline_metrics') {
              updateBaseline(data);
            } else if (eventType === 'logs') {
              appendLogs(data.entries);
            } else if (eventType === 'error') {
              throw new Error(data.message || 'Stream processing error');
            } else if (eventType === 'done') {
              // Stream finished — let the reveal queue drain the rest, then
              // the finally block flips isStreaming off once revealed.
              revealDone = true;
            }
          } catch (e) {
            console.error('Error parsing SSE event payload:', e, dataStr);
          }
        }
      }
    } catch (err) {
      // User-initiated stop: don't show an error, just finalize what we have.
      const isAbort = err.name === 'AbortError';
      clearInterval(revealTimer);
      const msg = findAssistant();
      if (msg) {
        // Flush whatever was revealed so far so the partial answer stays.
        msg.content += queuedChars;
        queuedChars = '';
        if (!isAbort) {
          // Only show the system error for genuine failures.
          msg.content += `\n\nSystem Error: ${err.message || 'Failed to complete RAG query pipeline.'}`;
        }
        msg.isStreaming = false;
        isStreaming.value = false;
        persist();
      }
      if (!isAbort) console.error('SSE Stream error:', err);
    } finally {
      abortController = null;
      revealDone = true;
    }
  }

  // Stop an in-flight generation: abort the fetch, flush queued text, finalize.
  function stopGeneration() {
    if (abortController) abortController.abort();
  }

  // Export the active conversation as a PDF (generated client-side via jsPDF).
  async function exportPDF() {
    const conv = activeConversation.value;
    if (!conv || conv.messages.length === 0) return;

    const { jsPDF } = await import('jspdf');
    const doc = new jsPDF({ unit: 'pt', format: 'a4' });
    const pageW = doc.internal.pageSize.getWidth();
    const pageH = doc.internal.pageSize.getHeight();
    const margin = 48;
    const maxW = pageW - margin * 2;
    let y = margin;

    // Title
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(18);
    doc.setTextColor(7, 54, 66);
    const titleLines = doc.splitTextToSize(conv.title, maxW);
    doc.text(titleLines, margin, y);
    y += titleLines.length * 24 + 10;

    // Subtitle line
    doc.setFont('helvetica', 'normal');
    doc.setFontSize(9);
    doc.setTextColor(136, 136, 136);
    doc.text(`RAGLab export · ${new Date().toLocaleString()}`, margin, y);
    y += 24;

    for (const m of conv.messages) {
      const label = m.role === 'user' ? 'QUESTION' : 'ANSWER';
      const isUser = m.role === 'user';

      // Ensure room for at least the label + a couple of lines; else new page.
      if (y > pageH - margin - 60) { doc.addPage(); y = margin; }

      // Role label
      doc.setFont('helvetica', 'bold');
      doc.setFontSize(11);
      doc.setTextColor(isUser ? 203 : 7, isUser ? 75 : 54, isUser ? 22 : 66);
      doc.text(label, margin, y);
      y += 16;

      // Body — wrapped, with page breaks.
      doc.setFont('helvetica', 'normal');
      doc.setFontSize(11);
      doc.setTextColor(30, 30, 30);
      const body = (m.content || '_(no content)_').replace(/\n{3,}/g, '\n\n');
      const lines = doc.splitTextToSize(body, maxW);
      const lineH = 15;
      for (const ln of lines) {
        if (y > pageH - margin) { doc.addPage(); y = margin; }
        doc.text(ln, margin, y);
        y += lineH;
      }
      y += 18; // gap between turns
    }

    doc.save('raglab-conversation.pdf');
  }

  // Suggestions for the most recent answer (shown as follow-up chips).
  const suggestions = ref([]);

  async function fetchSuggestions(query, answer) {
    if (!query || !answer) { suggestions.value = []; return; }
    try {
      const res = await fetch('/suggest', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, answer }),
      });
      if (!res.ok) { suggestions.value = []; return; }
      const data = await res.json();
      suggestions.value = data.suggestions || [];
    } catch (e) {
      suggestions.value = [];
    }
  }

  // Regenerate: remove the last assistant answer and re-run the pipeline on the
  // last user question, preserving multi-turn history up to that point.
  async function regenerate() {
    if (isStreaming.value) return;
    const conv = activeConversation.value;
    if (!conv || conv.messages.length < 2) return;

    // Find the last user message and the assistant message after it.
    let lastUserIdx = -1;
    for (let i = conv.messages.length - 1; i >= 0; i--) {
      if (conv.messages[i].role === 'user') { lastUserIdx = i; break; }
    }
    if (lastUserIdx === -1) return;

    const lastQuery = conv.messages[lastUserIdx].content;
    // Drop everything from the assistant answer onward.
    conv.messages.splice(lastUserIdx + 1);
    persist();
    suggestions.value = [];

    // Re-send the same query (history is rebuilt inside sendQuery from conv).
    await sendQuery(lastQuery);
  }

  return {
    messages,
    isStreaming,
    compareWithBaseline,
    suggestions,
    sendQuery,
    stopGeneration,
    regenerate,
    fetchSuggestions,
    exportPDF,
    clearConversation,
    setActiveConversation,
    syncMessages,
  };
}
