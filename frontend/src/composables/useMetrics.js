import { reactive } from 'vue';

const initialMetrics = () => ({
  retrieval_time_ms: null,
  generation_time_ms: null,
  recall_at_5: null,
  mrr: null,
  total_chunks_retrieved: null,
  collection_used: null,
  classification: null
});

const currentMetrics = reactive(initialMetrics());
const baselineMetrics = reactive(initialMetrics());

export function useMetrics() {
  function updateMetrics(payload) {
    Object.assign(currentMetrics, payload);
  }

  function updateBaseline(payload) {
    Object.assign(baselineMetrics, payload);
  }

  function getDelta(key) {
    const val = currentMetrics[key];
    const base = baselineMetrics[key];
    if (val === null || base === null) return null;
    return val - base;
  }

  function resetMetrics() {
    Object.assign(currentMetrics, initialMetrics());
    Object.assign(baselineMetrics, initialMetrics());
  }

  return {
    currentMetrics,
    baselineMetrics,
    updateMetrics,
    updateBaseline,
    getDelta,
    resetMetrics
  };
}
