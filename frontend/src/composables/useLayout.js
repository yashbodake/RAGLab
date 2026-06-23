import { ref } from 'vue';

const rightPanelTab = ref(0); // 0: Logs, 1: Chunks, 2: Compare
const rightPanelOpen = ref(true);
const activeInspectChunkId = ref(null);

export function useLayout() {
  function inspectChunk(chunkId) {
    rightPanelOpen.value = true;
    rightPanelTab.value = 1; // Chunk Inspector
    activeInspectChunkId.value = chunkId;

    setTimeout(() => {
      const element = document.getElementById(`chunk-card-${chunkId}`);
      if (element) {
        element.scrollIntoView({ behavior: 'smooth', block: 'center' });
        element.classList.add('highlight-flash');
        setTimeout(() => {
          element.classList.remove('highlight-flash');
        }, 1500);
      }
    }, 100);
  }

  return {
    rightPanelTab,
    rightPanelOpen,
    activeInspectChunkId,
    inspectChunk
  };
}
