<script setup>
import { ref, watch } from 'vue';
import { useLayout } from './composables/useLayout';
import { useConversations } from './composables/useConversations';
import AppHeader from './components/AppHeader.vue';
import SlideDrawer from './components/SlideDrawer.vue';
import LeftSidebar from './components/LeftSidebar.vue';
import ChatArea from './components/ChatArea.vue';
import RightPanel from './components/RightPanel.vue';
import HistoryDrawer from './components/HistoryDrawer.vue';
import DocumentManager from './components/DocumentManager.vue';

const { sidebarOpen, rightPanelOpen, historyOpen, toggleSidebar, toggleRightPanel, toggleHistory } = useLayout();
const { activeConversation, createConversation } = useConversations();

const currentPage = ref('chat');

// When switching to the chat view, ensure there's an active conversation so
// the user can start typing immediately (history persists across page switches).
watch(currentPage, (page) => {
  if (page === 'chat' && !activeConversation.value) {
    createConversation();
  }
});
</script>

<template>
  <div class="app-container">
    <AppHeader
      :sidebar-open="sidebarOpen"
      :right-panel-open="rightPanelOpen"
      :history-open="historyOpen"
      :current-page="currentPage"
      @update:current-page="currentPage = $event"
      @toggle-sidebar="toggleSidebar"
      @toggle-right-panel="toggleRightPanel"
      @toggle-history="toggleHistory"
      @new-conversation="createConversation"
    />

    <!-- View swap: old view scales-down + fades out, new view scales-up + fades in -->
    <Transition name="view-transition" mode="out-in">
      <!-- Chat view: single immersive column + CONFIG modal + INSPECT side panel + HISTORY -->
      <div class="manuscript-layout" v-if="currentPage === 'chat'" key="chat">
        <ChatArea />

        <!-- HISTORY: left slide-over panel (conversation list, localStorage) -->
        <SlideDrawer
          side="left"
          :open="historyOpen"
          title="Conversations"
          sub="SAVED LOCALLY"
          @close="toggleHistory"
        >
          <HistoryDrawer />
        </SlideDrawer>

        <!-- CONFIG: centered modal overlay -->
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
