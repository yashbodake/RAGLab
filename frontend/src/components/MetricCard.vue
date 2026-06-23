<script setup>
import { computed } from 'vue';

const props = defineProps({
  label: String,
  value: [Number, String],
  unit: { type: String, default: '' },
  baselineValue: [Number, String],
  lowerIsBetter: { type: Boolean, default: false }
});

const displayValue = computed(() => {
  if (props.value === null || props.value === undefined) return '—';
  if (typeof props.value === 'number') {
    return props.value.toFixed(props.label.includes('Time') ? 1 : 2);
  }
  return props.value;
});

const displayBaseline = computed(() => {
  if (props.baselineValue === null || props.baselineValue === undefined) return null;
  if (typeof props.baselineValue === 'number') {
    return props.baselineValue.toFixed(props.label.includes('Time') ? 1 : 2);
  }
  return props.baselineValue;
});

const delta = computed(() => {
  if (typeof props.value !== 'number' || typeof props.baselineValue !== 'number') return null;
  return props.value - props.baselineValue;
});

const deltaClass = computed(() => {
  if (delta.value === null || delta.value === 0) return '';
  const isPositiveBetter = !props.lowerIsBetter;
  const isBetter = isPositiveBetter ? delta.value > 0 : delta.value < 0;
  return isBetter ? 'delta-better' : 'delta-worse';
});

const displayDelta = computed(() => {
  if (delta.value === null) return '';
  const sign = delta.value > 0 ? '+' : '';
  const valStr = delta.value.toFixed(props.label.includes('Time') ? 1 : 2);
  return `${sign}${valStr}`;
});
</script>

<template>
  <div class="metric-card glass-panel">
    <div class="metric-label">{{ label }}</div>
    <div class="metric-main">
      <div class="metric-value">
        {{ displayValue }}<span class="metric-unit">{{ unit }}</span>
      </div>
      <div v-if="displayBaseline !== null" class="metric-compare">
        <div class="metric-baseline">Base: {{ displayBaseline }}{{ unit }}</div>
        <div class="metric-delta" :class="deltaClass">{{ displayDelta }}{{ unit }}</div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.metric-card {
  padding: var(--spacing-sm) var(--spacing-md);
  border-radius: var(--radius-sm);
  background-color: var(--bg-panel);
  border: 1px solid rgba(7, 54, 66, 0.12);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
  transition: border-color var(--transition-fast);
}

.metric-card:hover {
  background-color: var(--bg-panel-hover);
}

.metric-label {
  font-size: 0.7rem;
  color: var(--text-dim);
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.8px;
}

.metric-main {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
}

.metric-value {
  font-size: 1.2rem;
  font-family: var(--font-mono);
  font-weight: 700;
  color: var(--text-primary);
}

.metric-unit {
  font-size: 0.75rem;
  color: var(--text-muted);
  margin-left: 2px;
}

.metric-compare {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  font-size: 0.7rem;
}

.metric-baseline {
  color: var(--text-dim);
}

.metric-delta {
  font-weight: 600;
}

.delta-better {
  color: var(--accent-success);
}

.delta-worse {
  color: var(--accent-error);
}
</style>
