<script setup>
import { ref } from 'vue';
import { useLayout } from './composables/useLayout';
import AppHeader from './components/AppHeader.vue';
import SlideDrawer from './components/SlideDrawer.vue';
import LeftSidebar from './components/LeftSidebar.vue';
import ChatArea from './components/ChatArea.vue';
import RightPanel from './components/RightPanel.vue';
import DocumentManager from './components/DocumentManager.vue';

const { sidebarOpen, rightPanelOpen, toggleSidebar, toggleRightPanel } = useLayout();
const currentPage = ref('chat');
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

    <!-- Chat view: single immersive column + two slide-over drawers -->
    <div class="manuscript-layout" v-if="currentPage === 'chat'">
      <ChatArea />

      <SlideDrawer
        side="left"
        :open="sidebarOpen"
        title="Configuration"
        sub="RETRIEVAL // FEATURES // METRICS"
        @close="toggleSidebar"
      >
        <LeftSidebar :embedded="true" />
      </SlideDrawer>

      <SlideDrawer
        side="right"
        :open="rightPanelOpen"
        title="Inspector"
        sub="LOGS // CHUNKS // COMPARE"
        @close="toggleRightPanel"
      >
        <RightPanel :embedded="true" />
      </SlideDrawer>
    </div>

    <!-- Document Manager view (full-page replacement) -->
    <DocumentManager v-else />
  </div>
</template>

<style scoped>
.manuscript-layout {
  position: relative;
  height: calc(100vh - var(--header-height));
  overflow: hidden;
  background-color: var(--bg-primary);
}
</style>
