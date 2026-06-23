import { ref } from 'vue';

// Module-level singleton refs — shared across every caller of useLayout().
const rightPanelTab = ref(0);            // 0 = Log Stream, 1 = Chunk Inspector, 2 = Comparison
const rightPanelOpen = ref(false);       // right drawer (inspect) — default closed in single-column layout
const sidebarOpen = ref(false);          // left drawer (features) — default closed
const activeInspectChunkId = ref(null);

export function useLayout() {
  function toggleRightPanel() {
    rightPanelOpen.value = !rightPanelOpen.value;
  }

  function toggleSidebar() {
    sidebarOpen.value = !sidebarOpen.value;
  }

  function setRightPanelTab(tab) {
    rightPanelTab.value = tab;
    rightPanelOpen.value = true;
  }

  // Opens the right drawer, switches to Chunk Inspector (tab 1), and highlights
  // the target chunk card. Preserves the chunk-card-${id} / highlight-flash DOM contract.
  function inspectChunk(chunkId) {
    rightPanelOpen.value = true;
    rightPanelTab.value = 1;
    activeInspectChunkId.value = chunkId;

    setTimeout(() => {
      const el = document.getElementById(`chunk-card-${chunkId}`);
      if (el) {
        el.scrollIntoView({ behavior: 'smooth', block: 'center' });
        el.classList.add('highlight-flash');
        setTimeout(() => el.classList.remove('highlight-flash'), 1500);
      }
    }, 100);
  }

  return {
    // state
    rightPanelTab,
    rightPanelOpen,
    sidebarOpen,
    activeInspectChunkId,
    // actions
    toggleRightPanel,
    toggleSidebar,
    setRightPanelTab,
    inspectChunk,
  };
}
