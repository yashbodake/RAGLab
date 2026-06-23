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
    <div class="switch-outer">
      <input type="checkbox" :checked="modelValue" class="hidden-input" />
      <div class="switch-slider" :class="{ active: modelValue }"></div>
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
  padding: var(--spacing-sm) 0;
  user-select: none;
}

.label-text {
  font-size: 0.9rem;
  color: var(--text-primary);
  font-weight: 500;
  transition: color var(--transition-fast);
}

.toggle-switch:hover .label-text {
  color: var(--accent-primary);
}

.switch-outer {
  position: relative;
  width: 44px;
  height: 22px;
  background-color: var(--bg-secondary);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-full);
  transition: all var(--transition-normal);
}

.hidden-input {
  display: none;
}

.switch-slider {
  position: absolute;
  top: 2px;
  left: 2px;
  width: 16px;
  height: 16px;
  background-color: var(--text-dim);
  border-radius: 50%;
  transition: all var(--transition-normal);
}

.switch-slider.active {
  transform: translateX(22px);
  background-color: var(--accent-primary);
  box-shadow: 0 0 10px var(--accent-primary);
}

.toggle-switch:hover .switch-outer {
  border-color: rgba(255, 255, 255, 0.2);
}
</style>
