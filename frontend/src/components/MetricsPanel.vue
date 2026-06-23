<script setup>
import { useMetrics } from '../composables/useMetrics';
import { useChat } from '../composables/useChat';
import MetricCard from './MetricCard.vue';

const { currentMetrics, baselineMetrics } = useMetrics();
const { compareWithBaseline } = useChat();
</script>

<template>
  <div class="metrics-list">
    <MetricCard
      label="Retrieval Latency"
      :value="currentMetrics.retrieval_time_ms"
      unit="ms"
      :baseline-value="compareWithBaseline ? baselineMetrics.retrieval_time_ms : null"
      lower-is-better
    />
    <MetricCard
      label="Generation Latency"
      :value="currentMetrics.generation_time_ms"
      unit="ms"
      :baseline-value="compareWithBaseline ? baselineMetrics.generation_time_ms : null"
      lower-is-better
    />
    <MetricCard
      label="Recall @ 5"
      :value="currentMetrics.recall_at_5"
      :baseline-value="compareWithBaseline ? baselineMetrics.recall_at_5 : null"
    />
    <MetricCard
      label="MRR"
      :value="currentMetrics.mrr"
      :baseline-value="compareWithBaseline ? baselineMetrics.mrr : null"
    />
  </div>
</template>

<style scoped>
.metrics-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}
</style>
