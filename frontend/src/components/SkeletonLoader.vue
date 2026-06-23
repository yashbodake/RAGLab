<template>
  <div class="skeleton-wrapper">
    <div class="avatar skeleton shimmer"></div>
    <div class="bubble-container">
      <div class="skeleton-bubble glass-panel shimmer"></div>
      <div class="skeleton-source glass-panel shimmer"></div>
    </div>
  </div>
</template>

<style scoped>
.skeleton-wrapper {
  display: flex;
  gap: var(--spacing-sm);
  max-width: 85%;
  margin-bottom: var(--spacing-sm);
  align-self: flex-start;
}

.avatar.skeleton {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  flex-shrink: 0;
}

.bubble-container {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
  flex-grow: 1;
  width: 300px;
}

.skeleton-bubble {
  height: 50px;
  width: 100%;
  border-radius: var(--radius-md);
  background-color: var(--bg-panel);
}

.skeleton-source {
  height: 24px;
  width: 60%;
  border-radius: var(--radius-sm);
  background-color: var(--bg-panel);
}
</style>
