<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
import { useLayout } from './composables/useLayout';
import AppHeader from './components/AppHeader.vue';
import LeftSidebar from './components/LeftSidebar.vue';
import ChatArea from './components/ChatArea.vue';
import RightPanel from './components/RightPanel.vue';
import DocumentManager from './components/DocumentManager.vue';

const sidebarOpen = ref(true);
const { rightPanelOpen } = useLayout();
const currentPage = ref('chat');

function toggleSidebar() {
  sidebarOpen.value = !sidebarOpen.value;
}

function toggleRightPanel() {
  rightPanelOpen.value = !rightPanelOpen.value;
}

function handleResize() {
  if (window.innerWidth < 1400) {
    sidebarOpen.value = false;
    rightPanelOpen.value = false;
  } else {
    sidebarOpen.value = true;
    rightPanelOpen.value = true;
  }
}

onMounted(() => {
  window.addEventListener('resize', handleResize);
  handleResize();
});

onUnmounted(() => {
  window.removeEventListener('resize', handleResize);
});
</script>

<template>
  <div class="app-container">
    <AppHeader
      :sidebar-open="sidebarOpen"
      :right-panel-open="rightPanelOpen"
      :current-page="currentPage"
      @update:current-page="currentPage = $event"
      @toggle-sidebar="toggleSidebar"
      @toggle-right-panel="toggleRightPanel"
    />
    <div class="main-layout" v-if="currentPage === 'chat'">
      <LeftSidebar :open="sidebarOpen" />
      <ChatArea />
      <RightPanel :open="rightPanelOpen" />
    </div>
    <DocumentManager v-else />
  </div>
</template>

<style scoped>
.main-layout {
  display: flex;
  height: calc(100vh - var(--header-height));
  position: relative;
  overflow: hidden;
  background-color: var(--bg-primary);
}
</style>
