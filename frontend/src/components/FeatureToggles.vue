<script setup>
import { useFeatures } from '../composables/useFeatures';
import ToggleSwitch from './ToggleSwitch.vue';

const { features } = useFeatures();
</script>

<template>
  <div class="features-list">
    <ToggleSwitch label="Hybrid Search (Dense + Sparse)" v-model="features.hybrid" />
    <ToggleSwitch label="Remote Embedding Service" v-model="features.remote_embed" />
    <ToggleSwitch label="Adaptive Query Routing" v-model="features.query_understanding" />
    <ToggleSwitch label="Metadata Filtering" v-model="features.metadata_aware" />
    <ToggleSwitch label="Multi-index Selection" v-model="features.multi_index" />
    <ToggleSwitch label="HNSW Vector Tuning" v-model="features.hnsw" />
    <ToggleSwitch label="Stream Sources Eagerly" v-model="features.stream_sources" />
  </div>
</template>

<style scoped>
.features-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}
</style>
