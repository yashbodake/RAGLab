import { ref } from 'vue';

const logEntries = ref([]);
const maxEntries = 200;

export function useLogs() {
  function appendLogs(entries) {
    if (!Array.isArray(entries)) return;
    const newLogs = [...logEntries.value, ...entries];
    if (newLogs.length > maxEntries) {
      logEntries.value = newLogs.slice(newLogs.length - maxEntries);
    } else {
      logEntries.value = newLogs;
    }
  }

  function clearLogs() {
    logEntries.value = [];
  }

  return {
    logEntries,
    appendLogs,
    clearLogs
  };
}
