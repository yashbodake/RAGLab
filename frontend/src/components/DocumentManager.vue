<script setup>
import { ref, onMounted, computed, onUnmounted } from 'vue';

const fileInputRef = ref(null);
const file = ref(null);
const isUploading = ref(false);
const errorMsg = ref('');
const successMsg = ref('');
const isDragging = ref(false);

const documents = ref([]);
const isLoadingDocs = ref(false);
const deleteLoadingId = ref('');
const toggleLoadingId = ref('');

// Poll for processing documents
let pollInterval = null;

async function fetchDocuments() {
  isLoadingDocs.value = true;
  try {
    const response = await fetch('/documents');
    if (response.ok) {
      documents.value = await response.json();
      
      // Start polling if any document is in 'processing' state
      const hasProcessing = documents.value.some(d => d.status === 'processing');
      if (hasProcessing && !pollInterval) {
        startPolling();
      } else if (!hasProcessing && pollInterval) {
        stopPolling();
      }
    }
  } catch (err) {
    console.error('Failed to load documents list:', err);
  } finally {
    isLoadingDocs.value = false;
  }
}

async function fetchDocumentsSilent() {
  try {
    const response = await fetch('/documents');
    if (response.ok) {
      documents.value = await response.json();
      const hasProcessing = documents.value.some(d => d.status === 'processing');
      if (!hasProcessing && pollInterval) {
        stopPolling();
      }
    }
  } catch (err) {
    console.error('Failed to silently poll documents list:', err);
  }
}

function startPolling() {
  pollInterval = setInterval(fetchDocumentsSilent, 3000);
}

function stopPolling() {
  if (pollInterval) {
    clearInterval(pollInterval);
    pollInterval = null;
  }
}

onMounted(() => {
  fetchDocuments();
});

onUnmounted(() => {
  stopPolling();
});

const stats = computed(() => {
  const total = documents.value.length;
  const active = documents.value.filter(d => d.active && d.status === 'success').length;
  const failed = documents.value.filter(d => d.status === 'failed').length;
  const processing = documents.value.filter(d => d.status === 'processing').length;
  return { total, active, failed, processing };
});

function triggerFileSelect() {
  if (fileInputRef.value) {
    fileInputRef.value.click();
  }
}

function handleFileChange(e) {
  const selected = e.target.files?.[0];
  if (selected) {
    setFile(selected);
  }
}

function setFile(selectedFile) {
  errorMsg.value = '';
  successMsg.value = '';
  const ext = selectedFile.name.split('.').pop().toLowerCase();
  if (!['txt', 'json', 'pdf'].includes(ext)) {
    errorMsg.value = 'Unsupported format. Choose .txt, .json, or .pdf';
    file.value = null;
    return;
  }
  if (selectedFile.size > 5 * 1024 * 1024) {
    errorMsg.value = 'File size exceeds the 5MB limit';
    file.value = null;
    return;
  }
  file.value = selectedFile;
}

function handleDragOver(e) {
  e.preventDefault();
  isDragging.value = true;
}

function handleDragLeave() {
  isDragging.value = false;
}

function handleDrop(e) {
  e.preventDefault();
  isDragging.value = false;
  const dropped = e.dataTransfer?.files?.[0];
  if (dropped) {
    setFile(dropped);
  }
}

async function uploadFile() {
  if (!file.value || isUploading.value) return;

  isUploading.value = true;
  errorMsg.value = '';
  successMsg.value = '';

  const formData = new FormData();
  formData.append('file', file.value);

  // Trigger loading immediately
  fetchDocuments();

  try {
    const response = await fetch('/upload', {
      method: 'POST',
      body: formData
    });

    if (!response.ok) {
      let errorMsgText = 'Failed to upload document';
      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        try {
          const errorData = await response.json();
          errorMsgText = errorData.detail || errorMsgText;
        } catch (_) {
          errorMsgText = response.statusText || errorMsgText;
        }
      } else {
        try {
          const textData = await response.text();
          if (textData) errorMsgText = textData.substring(0, 100);
        } catch (_) {
          errorMsgText = response.statusText || errorMsgText;
        }
      }
      throw new Error(errorMsgText);
    }

    const data = await response.json();
    successMsg.value = `Successfully indexed! Added ${data.chunks_added} chunks.`;
    file.value = null;
    if (fileInputRef.value) {
      fileInputRef.value.value = '';
    }
  } catch (err) {
    console.error('Upload error:', err);
    errorMsg.value = err.message || 'Server error occurred during ingestion.';
  } finally {
    isUploading.value = false;
    fetchDocuments();
  }
}

async function toggleActive(doc) {
  if (toggleLoadingId.value) return;
  toggleLoadingId.value = doc.id;
  try {
    const response = await fetch(`/documents/${doc.id}/toggle`, {
      method: 'POST'
    });
    if (response.ok) {
      const data = await response.json();
      doc.active = data.active;
    } else {
      let errorMsgText = 'Failed to toggle document status';
      try {
        const errorData = await response.json();
        errorMsgText = errorData.detail || errorMsgText;
      } catch (_) {}
      alert(errorMsgText);
    }
  } catch (err) {
    console.error('Toggle active error:', err);
    alert('Network error occurred while toggling status.');
  } finally {
    toggleLoadingId.value = '';
  }
}

async function deleteDoc(doc) {
  if (deleteLoadingId.value) return;
  if (!confirm(`Are you sure you want to permanently delete "${doc.filename}"? This will purge all associated chunks.`)) {
    return;
  }
  deleteLoadingId.value = doc.id;
  try {
    const response = await fetch(`/documents/${doc.id}`, {
      method: 'DELETE'
    });
    if (response.ok) {
      documents.value = documents.value.filter(d => d.id !== doc.id);
    } else {
      let errorMsgText = 'Failed to delete document';
      try {
        const errorData = await response.json();
        errorMsgText = errorData.detail || errorMsgText;
      } catch (_) {}
      alert(errorMsgText);
    }
  } catch (err) {
    console.error('Delete document error:', err);
    alert('Network error occurred while deleting document.');
  } finally {
    deleteLoadingId.value = '';
  }
}

function formatDate(isoStr) {
  if (!isoStr) return '';
  const date = new Date(isoStr);
  return date.toLocaleString(undefined, {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
}

function getFileIcon(filename) {
  const ext = filename.split('.').pop().toLowerCase();
  if (ext === 'pdf') return 'PDF';
  if (ext === 'json') return 'JSON';
  return 'TXT';
}
</script>

<template>
  <div class="document-manager-page">
    <div class="page-header">
      <h2>Document Management</h2>
      <p class="subtitle">Upload custom manuals, toggle database visibility, and track indexing processing states.</p>
    </div>

    <!-- Metrics Bar -->
    <div class="metrics-grid">
      <div class="metric-card glass-panel">
        <div class="metric-label">Total Custom Files</div>
        <div class="metric-value">{{ stats.total }}</div>
      </div>
      <div class="metric-card glass-panel text-success">
        <div class="metric-label">Active in RAG</div>
        <div class="metric-value">{{ stats.active }}</div>
      </div>
      <div class="metric-card glass-panel" :class="{ 'pulse-blue': stats.processing > 0 }">
        <div class="metric-label">Indexing File Queue</div>
        <div class="metric-value">{{ stats.processing }}</div>
      </div>
      <div class="metric-card glass-panel text-error">
        <div class="metric-label">Failed Uploads</div>
        <div class="metric-value">{{ stats.failed }}</div>
      </div>
    </div>

    <div class="content-split">
      <!-- Upload Section -->
      <div class="upload-side glass-panel">
        <h3>Index New Document</h3>
        <p class="description">Upload maintenance logs, specifications, or troubleshooting guides to dynamically inject custom contexts into RAG queries.</p>

        <div
          class="dropzone"
          :class="{ dragging: isDragging, 'has-file': !!file }"
          @dragover="handleDragOver"
          @dragleave="handleDragLeave"
          @drop="handleDrop"
          @click="triggerFileSelect"
        >
          <input
            ref="fileInputRef"
            type="file"
            accept=".txt,.json,.pdf"
            class="hidden-file-input"
            @change="handleFileChange"
          />
          
          <div class="dropzone-content">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="32" height="32" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="upload-icon">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
              <polyline points="17 8 12 3 7 8"></polyline>
              <line x1="12" y1="3" x2="12" y2="15"></line>
            </svg>
            <span v-if="!file" class="dropzone-text">Drag & drop a file here, or click to browse</span>
            <span v-else class="filename-text">{{ file.name }}</span>
            <span class="file-limits">Supports TXT, JSON, and PDF (Max 5MB)</span>
          </div>
        </div>

        <button
          v-if="file"
          class="upload-btn"
          :disabled="isUploading"
          @click.stop="uploadFile"
        >
          <span v-if="!isUploading">Ingest & Chunk Document</span>
          <span v-else class="loader-container">
            <span class="upload-loader"></span> Ingesting...
          </span>
        </button>

        <div v-if="successMsg" class="feedback-msg success">
          {{ successMsg }}
        </div>
        <div v-if="errorMsg" class="feedback-msg error">
          {{ errorMsg }}
        </div>
      </div>

      <!-- Listing Section -->
      <div class="listing-side glass-panel">
        <div class="section-title">
          <h3>Ingested Documents Library</h3>
          <button class="refresh-btn" @click="fetchDocuments" :disabled="isLoadingDocs">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" :class="{ spinning: isLoadingDocs }">
              <polyline points="23 4 23 10 17 10"></polyline>
              <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"></path>
            </svg>
          </button>
        </div>

        <div class="table-container">
          <table class="docs-table">
            <thead>
              <tr>
                <th>Format</th>
                <th>File / Title</th>
                <th>Uploaded At</th>
                <th>Status</th>
                <th>Chunks</th>
                <th>Active</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="documents.length === 0">
                <td colspan="7" class="empty-state">
                  <div class="empty-content">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="48" height="48" fill="none" stroke="var(--text-dim)" stroke-width="1" stroke-linecap="round" stroke-linejoin="round">
                      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                      <polyline points="14 2 14 8 20 8"></polyline>
                      <line x1="9" y1="15" x2="15" y2="15"></line>
                    </svg>
                    <p>No custom documents uploaded yet.</p>
                  </div>
                </td>
              </tr>
              <tr v-for="doc in documents" :key="doc.id" class="doc-row">
                <td>
                  <span class="format-badge" :class="doc.filename.split('.').pop().toLowerCase()">
                    {{ getFileIcon(doc.filename) }}
                  </span>
                </td>
                <td class="title-cell">
                  <div class="doc-title">{{ doc.title }}</div>
                  <div class="doc-filename">{{ doc.filename }}</div>
                </td>
                <td class="date-cell">{{ formatDate(doc.upload_time) }}</td>
                <td>
                  <div v-if="doc.status === 'success'" class="status-badge success">
                    <span class="indicator-dot"></span> Available
                  </div>
                  <div v-else-if="doc.status === 'processing'" class="status-badge processing">
                    <span class="spinner-dot"></span> Ingesting
                  </div>
                  <div v-else class="status-badge error" :title="doc.error_message">
                    Failed ⚠️
                  </div>
                </td>
                <td class="chunk-count">{{ doc.status === 'success' ? doc.chunk_count : '—' }}</td>
                <td>
                  <label class="switch" v-if="doc.status === 'success'">
                    <input 
                      type="checkbox" 
                      :checked="doc.active" 
                      @change="toggleActive(doc)" 
                      :disabled="toggleLoadingId === doc.id"
                    />
                    <span class="slider round"></span>
                  </label>
                  <span v-else>—</span>
                </td>
                <td>
                  <button 
                    class="delete-btn" 
                    @click="deleteDoc(doc)" 
                    :disabled="deleteLoadingId === doc.id"
                    title="Delete document permanently"
                  >
                    <svg v-if="deleteLoadingId !== doc.id" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                      <polyline points="3 6 5 6 21 6"></polyline>
                      <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                    </svg>
                    <span v-else class="btn-loader"></span>
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.document-manager-page {
  flex: 1;
  padding: var(--spacing-lg);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
  overflow-y: auto;
  height: 100%;
  color: var(--text-primary);
  background-color: var(--bg-primary);
}

.page-header h2 {
  font-size: 1.5rem;
  font-weight: 700;
  letter-spacing: 0.5px;
  color: var(--text-primary);
}

.page-header .subtitle {
  font-size: 0.85rem;
  color: var(--text-muted);
  margin-top: 4px;
}

/* Metrics Bar */
.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: var(--spacing-md);
}

.metric-card {
  padding: var(--spacing-md);
  display: flex;
  flex-direction: column;
  gap: 4px;
  background-color: rgba(17, 24, 39, 0.4);
}

.metric-label {
  font-size: 0.72rem;
  text-transform: uppercase;
  letter-spacing: 1px;
  color: var(--text-muted);
}

.metric-value {
  font-size: 1.8rem;
  font-weight: 800;
}

.text-success .metric-value {
  color: var(--accent-success);
  text-shadow: 0 0 10px rgba(0, 255, 136, 0.3);
}

.text-error .metric-value {
  color: var(--accent-error);
  text-shadow: 0 0 10px rgba(255, 51, 102, 0.3);
}

.pulse-blue {
  border-color: var(--accent-primary) !important;
  box-shadow: 0 0 12px rgba(0, 240, 255, 0.2);
  animation: pulseBorder 2s infinite ease-in-out;
}

@keyframes pulseBorder {
  0%, 100% { border-color: var(--border-subtle); }
  50% { border-color: var(--accent-primary); }
}

/* Layout Content */
.content-split {
  display: flex;
  gap: var(--spacing-lg);
  flex: 1;
  min-height: 0;
}

@media (max-width: 1100px) {
  .content-split {
    flex-direction: column;
    min-height: auto;
  }
}

.upload-side {
  flex: 1;
  max-width: 380px;
  padding: var(--spacing-lg);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
  height: fit-content;
  background-color: rgba(17, 24, 39, 0.3);
}

.upload-side h3 {
  font-size: 1rem;
  font-weight: 700;
}

.upload-side .description {
  font-size: 0.8rem;
  color: var(--text-muted);
  line-height: 1.4;
}

.listing-side {
  flex: 2;
  padding: var(--spacing-lg);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
  min-height: 400px;
  background-color: rgba(17, 24, 39, 0.3);
  overflow: hidden;
}

.section-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.section-title h3 {
  font-size: 1rem;
  font-weight: 700;
}

.refresh-btn {
  background: none;
  border: 1px solid var(--border-subtle);
  color: var(--text-muted);
  padding: 6px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  display: flex;
  align-items: center;
  transition: all var(--transition-fast);
}

.refresh-btn:hover {
  color: var(--accent-primary);
  border-color: var(--accent-primary);
  background-color: rgba(0, 240, 255, 0.05);
}

.refresh-btn:disabled {
  cursor: not-allowed;
  opacity: 0.5;
}

.spinning {
  animation: spin 1s infinite linear;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Dropzone Styling */
.dropzone {
  border: 1px dashed var(--border-subtle);
  border-radius: var(--radius-md);
  padding: var(--spacing-xl) var(--spacing-md);
  text-align: center;
  cursor: pointer;
  background-color: rgba(255, 255, 255, 0.01);
  transition: all var(--transition-normal);
}

.dropzone:hover, .dropzone.dragging {
  border-color: var(--accent-primary);
  background-color: rgba(0, 240, 255, 0.02);
  box-shadow: 0 0 10px rgba(0, 240, 255, 0.1);
}

.dropzone.has-file {
  border-style: solid;
  border-color: rgba(0, 255, 136, 0.3);
  background-color: rgba(0, 255, 136, 0.01);
}

.hidden-file-input {
  display: none;
}

.dropzone-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-sm);
}

.upload-icon {
  color: var(--text-dim);
  transition: color var(--transition-fast);
}

.dropzone:hover .upload-icon, .dropzone.dragging .upload-icon {
  color: var(--accent-primary);
}

.dropzone.has-file .upload-icon {
  color: var(--accent-success);
}

.dropzone-text {
  font-size: 0.8rem;
  color: var(--text-muted);
}

.filename-text {
  font-size: 0.85rem;
  color: var(--text-primary);
  font-weight: 600;
  word-break: break-all;
}

.file-limits {
  font-size: 0.68rem;
  color: var(--text-dim);
}

.upload-btn {
  background-color: var(--bg-primary);
  border: 1px solid var(--border-subtle);
  color: var(--accent-primary);
  padding: 12px;
  border-radius: var(--radius-sm);
  font-family: var(--font-body);
  font-size: 0.85rem;
  font-weight: 700;
  cursor: pointer;
  transition: all var(--transition-fast);
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.upload-btn:hover:not(:disabled) {
  border-color: var(--accent-primary);
  background-color: rgba(0, 240, 255, 0.05);
  box-shadow: 0 0 12px rgba(0, 240, 255, 0.15);
}

.upload-btn:disabled {
  color: var(--text-dim);
  cursor: not-allowed;
  border-color: var(--border-subtle);
}

.feedback-msg {
  font-size: 0.78rem;
  padding: var(--spacing-sm);
  border-radius: var(--radius-sm);
  border: 1px solid transparent;
  margin-top: 4px;
}

.feedback-msg.success {
  background-color: rgba(0, 255, 136, 0.05);
  border-color: rgba(0, 255, 136, 0.15);
  color: var(--accent-success);
}

.feedback-msg.error {
  background-color: rgba(255, 51, 102, 0.05);
  border-color: rgba(255, 51, 102, 0.15);
  color: var(--accent-error);
}

.loader-container {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.upload-loader {
  display: inline-block;
  width: 14px;
  height: 14px;
  border: 2px solid rgba(0, 240, 255, 0.2);
  border-radius: 50%;
  border-top-color: var(--accent-primary);
  animation: spin 0.8s infinite linear;
}

/* Document Table Styling */
.table-container {
  flex: 1;
  overflow-y: auto;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm);
}

.docs-table {
  width: 100%;
  border-collapse: collapse;
  text-align: left;
  font-size: 0.82rem;
}

.docs-table th {
  background-color: rgba(17, 24, 39, 0.6);
  padding: 12px var(--spacing-md);
  font-weight: 700;
  text-transform: uppercase;
  font-size: 0.7rem;
  letter-spacing: 1px;
  color: var(--text-muted);
  border-bottom: 1px solid var(--border-subtle);
  position: sticky;
  top: 0;
  z-index: 1;
}

.docs-table td {
  padding: 12px var(--spacing-md);
  border-bottom: 1px solid var(--border-subtle);
  vertical-align: middle;
}

.doc-row {
  transition: background-color var(--transition-fast);
}

.doc-row:hover {
  background-color: rgba(255, 255, 255, 0.02);
}

.format-badge {
  padding: 3px 6px;
  border-radius: 4px;
  font-weight: 800;
  font-size: 0.65rem;
  letter-spacing: 0.5px;
}

.format-badge.pdf {
  background-color: rgba(255, 51, 102, 0.15);
  color: var(--accent-error);
  border: 1px solid rgba(255, 51, 102, 0.3);
}

.format-badge.txt {
  background-color: rgba(0, 240, 255, 0.1);
  color: var(--accent-primary);
  border: 1px solid rgba(0, 240, 255, 0.3);
}

.format-badge.json {
  background-color: rgba(255, 184, 0, 0.1);
  color: var(--accent-warning);
  border: 1px solid rgba(255, 184, 0, 0.3);
}

.title-cell {
  max-width: 250px;
}

.doc-title {
  font-weight: 600;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.doc-filename {
  font-size: 0.72rem;
  color: var(--text-muted);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-top: 2px;
}

.date-cell {
  color: var(--text-muted);
  white-space: nowrap;
}

.chunk-count {
  font-family: var(--font-mono);
}

/* Status Badges */
.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 0.75rem;
  font-weight: 600;
}

.status-badge.success {
  color: var(--accent-success);
}

.status-badge.processing {
  color: var(--accent-primary);
}

.status-badge.error {
  color: var(--accent-error);
  cursor: help;
  text-decoration: underline dotted;
}

.indicator-dot {
  width: 6px;
  height: 6px;
  background-color: var(--accent-success);
  border-radius: 50%;
  box-shadow: 0 0 6px var(--accent-success);
  animation: pulseDot 1.5s infinite ease-in-out;
}

.spinner-dot {
  width: 8px;
  height: 8px;
  border: 1.5px solid rgba(0, 240, 255, 0.2);
  border-radius: 50%;
  border-top-color: var(--accent-primary);
  animation: spin 0.8s infinite linear;
}

@keyframes pulseDot {
  0%, 100% { opacity: 0.4; }
  50% { opacity: 1; }
}

/* Toggle Switch */
.switch {
  position: relative;
  display: inline-block;
  width: 34px;
  height: 20px;
}

.switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: var(--bg-secondary);
  border: 1px solid var(--border-subtle);
  transition: .3s;
}

.slider:before {
  position: absolute;
  content: "";
  height: 12px;
  width: 12px;
  left: 3px;
  bottom: 3px;
  background-color: var(--text-muted);
  transition: .3s;
}

input:checked + .slider {
  background-color: rgba(0, 255, 136, 0.1);
  border-color: var(--accent-success);
}

input:checked + .slider:before {
  transform: translateX(14px);
  background-color: var(--accent-success);
  box-shadow: 0 0 6px var(--accent-success);
}

/* Actions */
.delete-btn {
  background: none;
  border: 1px solid transparent;
  color: var(--text-dim);
  cursor: pointer;
  padding: 6px;
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all var(--transition-fast);
}

.delete-btn:hover:not(:disabled) {
  color: var(--accent-error);
  border-color: var(--accent-error);
  background-color: rgba(255, 51, 102, 0.05);
}

.delete-btn:disabled {
  cursor: not-allowed;
  opacity: 0.5;
}

.btn-loader {
  display: inline-block;
  width: 12px;
  height: 12px;
  border: 1.5px solid rgba(255, 51, 102, 0.2);
  border-radius: 50%;
  border-top-color: var(--accent-error);
  animation: spin 0.8s infinite linear;
}

.empty-state {
  padding: 48px 0;
  text-align: center;
}

.empty-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-sm);
  color: var(--text-dim);
}

.empty-content p {
  font-size: 0.85rem;
}
</style>
