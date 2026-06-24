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

    <!-- View swap: old view scales-down + fades out, new view scales-up + fades in -->
    <Transition name="view-transition" mode="out-in">
      <!-- Chat view: single immersive column + CONFIG modal + INSPECT side panel -->
      <div class="manuscript-layout" v-if="currentPage === 'chat'" key="chat">
        <ChatArea />

        <!-- CONFIG: centered modal overlay (matches inspiration MODES menu) -->
        <SlideDrawer
          side="center"
          :open="sidebarOpen"
          title="Terminal Config"
          sub="RETRIEVAL // FEATURES // METRICS"
          @close="toggleSidebar"
        >
          <LeftSidebar :embedded="true" />
        </SlideDrawer>

        <!-- INSPECT: right slide-over panel (reference panel) -->
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
      <DocumentManager v-else key="documents" />
    </Transition>
  </div>
</template>

<style scoped>
.manuscript-layout {
  position: relative;
  height: calc(100vh - var(--header-height));
  height: calc(100dvh - var(--header-height));
  overflow: hidden;
  background-color: var(--bg-primary);
}
</style>
