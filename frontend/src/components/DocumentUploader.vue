<script setup>
import { ref } from 'vue';

const fileInputRef = ref(null);
const file = ref(null);
const isUploading = ref(false);
const errorMsg = ref('');
const successMsg = ref('');
const isDragging = ref(false);

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
  // Max size 5MB
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

  try {
    const response = await fetch('/upload', {
      method: 'POST',
      body: formData
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || 'Failed to upload document');
    }

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
  }
}
</script>

<template>
  <div class="document-uploader">
    <div
      class="dropzone glass-panel"
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
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="upload-icon">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
          <polyline points="17 8 12 3 7 8"></polyline>
          <line x1="12" y1="3" x2="12" y2="15"></line>
        </svg>
        <span v-if="!file" class="dropzone-text">Drag & drop or Click to browse</span>
        <span v-else class="filename-text">{{ file.name }}</span>
        <span class="file-limits">TXT, JSON, PDF (max 5MB)</span>
      </div>
    </div>
    
    <button
      v-if="file"
      class="upload-btn"
      :disabled="isUploading"
      @click.stop="uploadFile"
    >
      <span v-if="!isUploading">Index Document</span>
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
</template>

<style scoped>
.document-uploader {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
  width: 100%;
}

.dropzone {
  border: 1px dashed var(--border-subtle);
  border-radius: var(--radius-md);
  padding: var(--spacing-md) var(--spacing-sm);
  text-align: center;
  cursor: pointer;
  background-color: rgba(255, 255, 255, 0.01);
  transition: all var(--transition-normal);
}

.dropzone:hover, .dropzone.dragging {
  border-color: var(--accent-primary);
  background-color: rgba(0, 240, 255, 0.02);
  box-shadow: 0 0 8px rgba(0, 240, 255, 0.1);
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
  gap: var(--spacing-xs);
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
  font-size: 0.82rem;
  color: var(--text-primary);
  font-weight: 600;
  word-break: break-all;
}

.file-limits {
  font-size: 0.68rem;
  color: var(--text-dim);
}

.upload-btn {
  background-color: var(--bg-panel);
  border: 1px solid var(--border-subtle);
  color: var(--accent-primary);
  padding: 10px;
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
  box-shadow: 0 0 10px rgba(0, 240, 255, 0.15);
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
  animation: slideIn 0.2s ease-out;
}

@keyframes slideIn {
  from { opacity: 0; transform: translateY(-5px); }
  to { opacity: 1; transform: translateY(0); }
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

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
