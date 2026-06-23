<template>
  <div class="skeleton-wrapper">
    <div class="synth-head shimmer-line w-40"></div>
    <div class="synth-body">
      <div class="shimmer-line w-full"></div>
      <div class="shimmer-line w-full"></div>
      <div class="shimmer-line w-75"></div>
    </div>
  </div>
</template>

<style scoped>
.skeleton-wrapper {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.synth-head {
  height: 18px;
}

.synth-body {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.shimmer-line {
  height: 14px;
  background-color: var(--bg-surface-low); /* visible sand tone for shimmer */
  position: relative;
  overflow: hidden;
}

.shimmer-line::after {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, transparent, rgba(7, 54, 66, 0.06), transparent);
  animation: shimmerSweep 1.4s infinite;
}

.w-full { width: 100%; }
.w-75 { width: 75%; }
.w-40 { width: 40%; }

@keyframes shimmerSweep {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
}
</style>
