import { ref } from 'vue';
import { useFeatures } from './useFeatures';
import { useMetrics } from './useMetrics';
import { useLogs } from './useLogs';
import { useChunks } from './useChunks';

const messages = ref([]);
const isStreaming = ref(false);
const compareWithBaseline = ref(false);

export function useChat() {
  const { getFeaturePayload } = useFeatures();
  const { updateMetrics, updateBaseline, resetMetrics } = useMetrics();
  const { appendLogs, clearLogs } = useLogs();
  const { setChunks, clearChunks } = useChunks();

  function clearConversation() {
    messages.value = [];
    isStreaming.value = false;
    clearLogs();
    clearChunks();
    resetMetrics();
  }

  async function sendQuery(queryText) {
    if (!queryText.trim() || isStreaming.value) return;

    // Reset metrics, logs, and chunks for the new query
    clearLogs();
    clearChunks();
    resetMetrics();

    // 1. Append User Message
    const userMsgId = Date.now().toString() + '-user';
    messages.value.push({
      id: userMsgId,
      role: 'user',
      content: queryText,
      timestamp: new Date().toISOString()
    });

    // 2. Append Placeholder Bot Message
    const assistantMsgId = Date.now().toString() + '-assistant';
    const assistantMsg = ref({
      id: assistantMsgId,
      role: 'assistant',
      content: '',
      sources: null,
      timestamp: new Date().toISOString(),
      isStreaming: true
    });
    messages.value.push(assistantMsg.value);

    isStreaming.value = true;

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
          compare_with_baseline: compareWithBaseline.value
        })
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
              // Find the assistant message in array and update it
              const idx = messages.value.findIndex(m => m.id === assistantMsgId);
              if (idx !== -1) {
                messages.value[idx].sources = data.chunks;
              }
              setChunks(data.chunks, false);
            } else if (eventType === 'baseline_sources') {
              setChunks(data.chunks, true);
            } else if (eventType === 'token') {
              const idx = messages.value.findIndex(m => m.id === assistantMsgId);
              if (idx !== -1) {
                messages.value[idx].content += data.text;
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
              const idx = messages.value.findIndex(m => m.id === assistantMsgId);
              if (idx !== -1) {
                messages.value[idx].isStreaming = false;
              }
            }
          } catch (e) {
            console.error('Error parsing SSE event payload:', e, dataStr);
          }
        }
      }
    } catch (err) {
      console.error('SSE Stream error:', err);
      const idx = messages.value.findIndex(m => m.id === assistantMsgId);
      if (idx !== -1) {
        messages.value[idx].content = `System Error: ${err.message || 'Failed to complete RAG query pipeline.'}`;
        messages.value[idx].isStreaming = false;
      }
    } finally {
      isStreaming.value = false;
      const idx = messages.value.findIndex(m => m.id === assistantMsgId);
      if (idx !== -1) {
        messages.value[idx].isStreaming = false;
      }
    }
  }

  return {
    messages,
    isStreaming,
    compareWithBaseline,
    sendQuery,
    clearConversation
  };
}
