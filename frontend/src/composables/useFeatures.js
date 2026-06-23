import { reactive } from 'vue';

const features = reactive({
  hybrid: false,
  remote_embed: false,
  query_understanding: false,
  metadata_aware: false,
  multi_index: false,
  hnsw: false,
  stream_sources: false
});

export function useFeatures() {
  function toggleFeature(key) {
    if (key in features) {
      features[key] = !features[key];
    }
  }

  function resetAllFeatures() {
    for (const key in features) {
      features[key] = false;
    }
  }

  function getFeaturePayload() {
    return { ...features };
  }

  return {
    features,
    toggleFeature,
    resetAllFeatures,
    getFeaturePayload
  };
}
