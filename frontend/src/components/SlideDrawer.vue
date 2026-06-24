<script setup>
const props = defineProps({
  // 'left' | 'right' = side slide-over panel; 'center' = centered modal overlay
  side: {
    type: String,
    default: 'right',
    validator: v => ['left', 'right', 'center'].includes(v)
  },
  open: { type: Boolean, default: false },
  title: { type: String, default: '' },
  sub: { type: String, default: '' }
});
const emit = defineEmits(['close']);

function onBackdropClick() {
  emit('close');
}
</script>

<template>
  <Transition :name="`drawer-${side}`">
    <div v-if="open" class="drawer-root" :class="`drawer-${side}`">
      <!-- Backdrop scrim -->
      <div class="drawer-backdrop" @click="onBackdropClick"></div>

      <!-- Panel -->
      <div class="drawer-panel" role="dialog" aria-modal="true">
        <header class="drawer-head">
          <div>
            <h2 class="drawer-title label-caps">{{ title }}</h2>
            <p v-if="sub" class="drawer-sub">{{ sub }}</p>
          </div>
          <button class="drawer-close" aria-label="Close" @click="emit('close')">
            <span class="material-symbols-outlined">close</span>
          </button>
        </header>
        <div class="drawer-body">
          <slot />
        </div>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
/* ── Root + backdrop ──────────────────────────────────────────────── */
.drawer-root {
  position: fixed;
  inset: 0;
  z-index: 80;
  display: flex;
}

.drawer-backdrop {
  position: fixed;
  inset: 0;
  /* Default resting state (fully open). Animations below ramp into this. */
  background: rgba(7, 54, 66, 0.34);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
}

/*
 * Smooth blur ramp. We ramp BOTH the tint opacity AND the blur radius together
 * in a single keyframe so the frost genuinely grows little-by-little.
 *
 * IMPORTANT: the parent (.drawer-root) must NOT animate opacity — an ancestor
 * with opacity < 1 disables backdrop-filter entirely, which makes the blur snap.
 * So the backdrop fades itself here, and the root only carries the transition
 * lifecycle (no opacity change).
 */
@keyframes backdropIn {
  0%   { background: rgba(7, 54, 66, 0);    backdrop-filter: blur(0px); -webkit-backdrop-filter: blur(0px); }
  25%  { background: rgba(7, 54, 66, 0.08); backdrop-filter: blur(2px); -webkit-backdrop-filter: blur(2px); }
  50%  { background: rgba(7, 54, 66, 0.17); backdrop-filter: blur(4px); -webkit-backdrop-filter: blur(4px); }
  75%  { background: rgba(7, 54, 66, 0.26); backdrop-filter: blur(6px); -webkit-backdrop-filter: blur(6px); }
  100% { background: rgba(7, 54, 66, 0.34); backdrop-filter: blur(8px); -webkit-backdrop-filter: blur(8px); }
}
@keyframes backdropOut {
  0%   { background: rgba(7, 54, 66, 0.34); backdrop-filter: blur(8px); -webkit-backdrop-filter: blur(8px); }
  25%  { background: rgba(7, 54, 66, 0.26); backdrop-filter: blur(6px); -webkit-backdrop-filter: blur(6px); }
  50%  { background: rgba(7, 54, 66, 0.17); backdrop-filter: blur(4px); -webkit-backdrop-filter: blur(4px); }
  75%  { background: rgba(7, 54, 66, 0.08); backdrop-filter: blur(2px); -webkit-backdrop-filter: blur(2px); }
  100% { background: rgba(7, 54, 66, 0);    backdrop-filter: blur(0px); -webkit-backdrop-filter: blur(0px); }
}
.drawer-right-enter-active .drawer-backdrop,
.drawer-left-enter-active .drawer-backdrop,
.drawer-center-enter-active .drawer-backdrop {
  animation: backdropIn var(--transition-normal) ease both;
}
.drawer-right-leave-active .drawer-backdrop,
.drawer-left-leave-active .drawer-backdrop,
.drawer-center-leave-active .drawer-backdrop {
  animation: backdropOut var(--transition-normal) ease both;
}

/* ── Panel surface ────────────────────────────────────────────────── */
.drawer-panel {
  position: relative;
  display: flex;
  flex-direction: column;
  background: var(--bg-primary);
}

/* Side panels */
.drawer-left .drawer-panel,
.drawer-right .drawer-panel {
  position: absolute;
  top: 0;
  bottom: 0;
  width: var(--drawer-width);
  max-width: 90vw;
  border-left: 1px solid rgba(7, 54, 66, 0.25);
  border-right: 1px solid rgba(7, 54, 66, 0.25);
}
.drawer-right .drawer-panel { right: 0; box-shadow: -6px 0 0 0 rgba(7, 54, 66, 0.12); }
.drawer-left  .drawer-panel { left: 0;  box-shadow: 6px 0 0 0 rgba(7, 54, 66, 0.12); }

/* Centered modal */
.drawer-center {
  /* Push the flex content area below the header with breathing room.
     Root scrolls vertically if the panel is taller than the viewport,
     so nothing gets cut off in small windows. */
  align-items: flex-start;
  overflow-y: auto;
  padding-top: calc(var(--header-height) + var(--spacing-xl));
  padding-bottom: var(--spacing-xl);
  padding-left: var(--spacing-md);
  padding-right: var(--spacing-md);
}
.drawer-center .drawer-panel {
  margin: 0 auto;            /* horizontal centering only */
  width: min(720px, 92vw);
  max-height: none;          /* let it grow; the root handles overflow */
  flex-shrink: 0;
  border: 1px solid rgba(7, 54, 66, 0.28);
  box-shadow:
    0 24px 60px -12px rgba(7, 54, 66, 0.35),
    0 8px 20px -8px rgba(7, 54, 66, 0.25);
}

/* ── Header / body ────────────────────────────────────────────────── */
.drawer-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: var(--spacing-lg) var(--spacing-lg) var(--spacing-md);
  border-bottom: 1px solid rgba(7, 54, 66, 0.12);
}
.drawer-title { color: var(--accent-primary); font-size: 13px; }
.drawer-sub {
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--text-dim);
  margin-top: 4px;
  letter-spacing: 0.05em;
}
.drawer-close {
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  padding: 4px;
  display: flex;
  transition: color var(--transition-fast);
}
.drawer-close:hover { color: var(--accent-secondary); }
.drawer-body {
  flex: 1;
  overflow-y: auto;
  padding: var(--spacing-lg);
}

/* ── Transitions: SIDE panels (slide panel; backdrop self-fades) ──── */
/* Root carries NO opacity change — an opacity<1 ancestor disables the
 * backdrop's backdrop-filter, which would make the blur snap. The backdrop
 * ramps its own tint+blur via the backdropIn/backdropOut keyframes above. */
.drawer-right-enter-active, .drawer-right-leave-active,
.drawer-left-enter-active, .drawer-left-leave-active {
  /* root does not animate opacity */
}
.drawer-right-enter-active .drawer-panel, .drawer-right-leave-active .drawer-panel,
.drawer-left-enter-active .drawer-panel, .drawer-left-leave-active .drawer-panel {
  transition: transform var(--transition-normal) cubic-bezier(0.22, 1, 0.36, 1);
}
/* Panel: slides in from off-screen on enter, slides back off-screen on leave */
.drawer-right-enter-from .drawer-panel,
.drawer-right-leave-to   .drawer-panel { transform: translateX(100%); }
.drawer-left-enter-from  .drawer-panel,
.drawer-left-leave-to    .drawer-panel { transform: translateX(-100%); }
/* Panel rests at 0 transform while open */
.drawer-right-enter-to .drawer-panel,
.drawer-right-leave-from .drawer-panel,
.drawer-left-enter-to .drawer-panel,
.drawer-left-leave-from .drawer-panel { transform: translateX(0); }

/* ── Transitions: CENTERED modal — macOS "Genie" minimize feel ────── */
/* Pure CSS can't do the real non-linear pixel warp of macOS Genie, but
 * asymmetric scaleY-squash + slight scaleX-stretch + the macOS minimize
 * easing curve reproduces the "liquid pour in / suck down" feel closely.
 *
 * Key: opacity must stay visible for the WHOLE transform duration, otherwise
 * the panel fades out before the squash can be seen. Opacity starts at 0.5
 * (not 0) so the panel is visible from the very first frame of the pour. */
.drawer-center-enter-active .drawer-panel, .drawer-center-leave-active .drawer-panel {
  transition:
    transform var(--transition-normal) cubic-bezier(0.32, 0.72, 0, 1),
    opacity var(--transition-normal) ease;
  transform-origin: top center;
  will-change: transform, opacity;
}
/* Start (enter-from) / end (leave-to): squashed flat. Keep opacity at 0.5 so
 * the squash is visible on the way in, and visible on the way out until the
 * very end. */
.drawer-center-enter-from .drawer-panel, .drawer-center-leave-to .drawer-panel {
  transform: scaleY(0.15) scaleX(1.12);
  opacity: 0.6;
}
/* Resting (enter-to / leave-from): full size + opaque. */
.drawer-center-enter-to .drawer-panel, .drawer-center-leave-from .drawer-panel {
  transform: scaleY(1) scaleX(1);
  opacity: 1;
}
</style>
