import { ref } from 'vue';

const enhancedChunks = ref([]);
const baselineChunks = ref([]);

export function useChunks() {
  function setChunks(chunks, isBaseline) {
    if (isBaseline) {
      baselineChunks.value = chunks || [];
    } else {
      enhancedChunks.value = chunks || [];
    }
  }

  function clearChunks() {
    enhancedChunks.value = [];
    baselineChunks.value = [];
  }

  return {
    enhancedChunks,
    baselineChunks,
    setChunks,
    clearChunks
  };
}
