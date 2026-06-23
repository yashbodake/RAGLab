<script setup>
defineProps({
  label: String,
  modelValue: Boolean
});

defineEmits(['update:modelValue']);
</script>

<template>
  <div class="toggle-switch" role="switch" :aria-checked="modelValue.toString()" @click="$emit('update:modelValue', !modelValue)">
    <span class="label-text">{{ label }}</span>
    <div class="switch-outer" :class="{ active: modelValue }">
      <input type="checkbox" :checked="modelValue" class="hidden-input" />
      <div class="switch-slider"></div>
    </div>
  </div>
</template>

<style scoped>
.toggle-switch {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  cursor: pointer;
  padding: var(--spacing-xs) 0;
  user-select: none;
}

.label-text {
  font-family: var(--font-body);
  font-size: 0.88rem;
  color: var(--text-muted);
  font-weight: 500;
  transition: color var(--transition-fast);
}

.toggle-switch:hover .label-text {
  color: var(--accent-primary);
}

.switch-outer {
  position: relative;
  width: 42px;
  height: 20px;
  background-color: var(--bg-panel);
  border: 1px solid rgba(7, 54, 66, 0.25);
  transition: all var(--transition-normal);
  flex-shrink: 0;
}

.hidden-input {
  display: none;
}

.switch-slider {
  position: absolute;
  top: 1px;
  left: 1px;
  width: 16px;
  height: 16px;
  background-color: var(--text-muted);
  transition: all var(--transition-normal);
}

/* ON state */
.switch-outer.active {
  background-color: var(--accent-primary);
  border-color: var(--accent-primary);
}
.switch-outer.active .switch-slider {
  transform: translateX(22px);
  background-color: var(--bg-primary);
}

.toggle-switch:hover .switch-outer {
  border-color: var(--accent-primary);
}
</style>
