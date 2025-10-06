// Video Auto-Moderation System - Main JavaScript

// Global variables
let uploadInProgress = false;
let currentAnalysisId = null;

// Initialize application
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    // Add loading animations to existing elements
    document.querySelectorAll('.card').forEach(card => {
        card.classList.add('fade-in');
    });
    
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // Set up global error handling
    window.addEventListener('error', handleGlobalError);
    window.addEventListener('unhandledrejection', handleGlobalError);
}

// Utility Functions
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function formatDuration(seconds) {
    if (!seconds || seconds === 0) return '0s';
    
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    
    if (hours > 0) {
        return `${hours}h ${minutes}m ${secs}s`;
    } else if (minutes > 0) {
        return `${minutes}m ${secs}s`;
    } else {
        return `${secs}s`;
    }
}

function getConfidenceColor(confidence) {
    if (confidence >= 80) return 'success';
    if (confidence >= 60) return 'warning';
    return 'danger';
}

function formatDate(dateString) {
    if (!dateString) return 'Unknown';
    const date = new Date(dateString);
    const now = new Date();
    const diffTime = Math.abs(now - date);
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays === 1) {
        return 'Today at ' + date.toLocaleTimeString();
    } else if (diffDays === 2) {
        return 'Yesterday at ' + date.toLocaleTimeString();
    } else if (diffDays <= 7) {
        return diffDays + ' days ago';
    } else {
        return date.toLocaleDateString();
    }
}

// Alert System
function showAlert(message, type = 'info', duration = 5000) {
    const alertContainer = document.getElementById('alertContainer') || createAlertContainer();
    
    const alertId = 'alert-' + Date.now();
    const alertHtml = `
        <div class="alert alert-${type} alert-dismissible fade show slide-up" role="alert" id="${alertId}">
            <i class="fas fa-${getAlertIcon(type)} me-2"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    alertContainer.insertAdjacentHTML('beforeend', alertHtml);
    
    // Auto-dismiss after duration
    if (duration > 0) {
        setTimeout(() => {
            const alert = document.getElementById(alertId);
            if (alert) {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }
        }, duration);
    }
}

function createAlertContainer() {
    const container = document.createElement('div');
    container.id = 'alertContainer';
    container.className = 'position-fixed top-0 end-0 p-3';
    container.style.zIndex = '9999';
    document.body.appendChild(container);
    return container;
}

function getAlertIcon(type) {
    const icons = {
        'success': 'check-circle',
        'danger': 'exclamation-triangle',
        'warning': 'exclamation-circle',
        'info': 'info-circle'
    };
    return icons[type] || 'info-circle';
}

// File Upload Functionality
function setupFileUpload(uploadAreaId, fileInputId, options = {}) {
    const uploadArea = document.getElementById(uploadAreaId);
    const fileInput = document.getElementById(fileInputId);
    
    if (!uploadArea || !fileInput) return;
    
    const defaultOptions = {
        maxSize: 500 * 1024 * 1024, // 500MB
        allowedTypes: ['video/mp4', 'video/mov', 'video/avi', 'video/wmv', 'video/mkv'],
        multiple: false
    };
    
    const config = { ...defaultOptions, ...options };
    
    // Drag and drop handlers
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });
    
    uploadArea.addEventListener('dragleave', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
    });
    
    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        
        const files = Array.from(e.dataTransfer.files);
        handleFileSelection(files, config);
    });
    
    // Click to upload
    uploadArea.addEventListener('click', () => {
        if (!uploadInProgress) {
            fileInput.click();
        }
    });
    
    // File input change
    fileInput.addEventListener('change', (e) => {
        const files = Array.from(e.target.files);
        handleFileSelection(files, config);
    });
}

function handleFileSelection(files, config) {
    if (uploadInProgress) {
        showAlert('Upload already in progress. Please wait.', 'warning');
        return;
    }
    
    if (files.length === 0) return;
    
    const file = files[0]; // Take first file if multiple
    
    // Validate file
    const validation = validateFile(file, config);
    if (!validation.valid) {
        showAlert(validation.message, 'danger');
        return;
    }
    
    // Start upload
    uploadFile(file);
}

function validateFile(file, config) {
    // Check file type
    if (!config.allowedTypes.includes(file.type)) {
        return {
            valid: false,
            message: `Invalid file type. Allowed types: ${config.allowedTypes.join(', ')}`
        };
    }
    
    // Check file size
    if (file.size > config.maxSize) {
        return {
            valid: false,
            message: `File too large. Maximum size: ${formatFileSize(config.maxSize)}`
        };
    }
    
    return { valid: true };
}

async function uploadFile(file) {
    uploadInProgress = true;
    
    try {
        // Update UI
        updateUploadUI(file, 'uploading');
        
        // Create form data
        const formData = new FormData();
        formData.append('video', file);
        
        // Get settings from form if available
        const settingsForm = document.getElementById('uploadSettingsForm');
        if (settingsForm) {
            const settingsData = new FormData(settingsForm);
            for (let [key, value] of settingsData.entries()) {
                formData.append(key, value);
            }
        }
        
        // Upload with progress
        const response = await uploadWithProgress('/moderation/api/analyze', formData, updateUploadProgress);
        
        if (response.success) {
            currentAnalysisId = response.analysis_id;
            showAlert('Video uploaded successfully! Analysis started.', 'success');
            
            // Start polling for results
            pollAnalysisResults(response.analysis_id);
        } else {
            throw new Error(response.message || 'Upload failed');
        }
        
    } catch (error) {
        console.error('Upload error:', error);
        showAlert('Upload failed: ' + error.message, 'danger');
        updateUploadUI(file, 'error');
    }
}

function uploadWithProgress(url, formData, progressCallback) {
    return new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest();
        
        xhr.upload.addEventListener('progress', (e) => {
            if (e.lengthComputable) {
                const percentComplete = (e.loaded / e.total) * 100;
                progressCallback(percentComplete);
            }
        });
        
        xhr.addEventListener('load', () => {
            if (xhr.status === 200) {
                try {
                    const response = JSON.parse(xhr.responseText);
                    resolve(response);
                } catch (e) {
                    reject(new Error('Invalid response format'));
                }
            } else {
                reject(new Error(`HTTP ${xhr.status}: ${xhr.statusText}`));
            }
        });
        
        xhr.addEventListener('error', () => {
            reject(new Error('Network error occurred'));
        });
        
        xhr.open('POST', url);
        xhr.send(formData);
    });
}

function updateUploadProgress(percent) {
    const progressBar = document.querySelector('.upload-progress');
    if (progressBar) {
        progressBar.style.width = percent + '%';
    }
    
    const progressText = document.querySelector('.upload-progress-text');
    if (progressText) {
        progressText.textContent = `Uploading... ${Math.round(percent)}%`;
    }
}

function updateUploadUI(file, state) {
    const uploadArea = document.querySelector('.upload-area');
    const uploadText = document.querySelector('.upload-text');
    const uploadIcon = document.querySelector('.upload-icon');
    
    if (!uploadArea) return;
    
    switch (state) {
        case 'uploading':
            uploadArea.classList.add('uploading');
            if (uploadText) uploadText.textContent = `Uploading ${file.name}...`;
            if (uploadIcon) uploadIcon.className = 'fas fa-spinner fa-spin fa-3x text-primary';
            break;
            
        case 'analyzing':
            if (uploadText) uploadText.textContent = `Analyzing ${file.name}...`;
            if (uploadIcon) uploadIcon.className = 'fas fa-cog fa-spin fa-3x text-info';
            break;
            
        case 'complete':
            uploadArea.classList.remove('uploading');
            if (uploadText) uploadText.textContent = 'Analysis complete!';
            if (uploadIcon) uploadIcon.className = 'fas fa-check-circle fa-3x text-success';
            setTimeout(resetUploadUI, 3000);
            break;
            
        case 'error':
            uploadArea.classList.remove('uploading');
            if (uploadText) uploadText.textContent = 'Upload failed. Click to try again.';
            if (uploadIcon) uploadIcon.className = 'fas fa-exclamation-triangle fa-3x text-danger';
            setTimeout(resetUploadUI, 5000);
            break;
    }
}

function resetUploadUI() {
    const uploadArea = document.querySelector('.upload-area');
    const uploadText = document.querySelector('.upload-text');
    const uploadIcon = document.querySelector('.upload-icon');
    const progressBar = document.querySelector('.upload-progress');
    
    if (uploadArea) uploadArea.classList.remove('uploading');
    if (uploadText) uploadText.textContent = 'Drag and drop your video file here or click to browse';
    if (uploadIcon) uploadIcon.className = 'fas fa-cloud-upload-alt fa-3x text-muted';
    if (progressBar) progressBar.style.width = '0%';
    
    uploadInProgress = false;
    currentAnalysisId = null;
}

// Analysis Results Polling
async function pollAnalysisResults(analysisId, maxAttempts = 60) {
    let attempts = 0;
    
    const poll = async () => {
        try {
            const response = await fetch(`/moderation/api/results/${analysisId}`);
            const result = await response.json();
            
            if (result.status === 'completed') {
                updateUploadUI(null, 'complete');
                showAnalysisResults(result);
                return;
            }
            
            if (result.status === 'failed') {
                throw new Error(result.error || 'Analysis failed');
            }
            
            // Continue polling
            attempts++;
            if (attempts < maxAttempts) {
                updateUploadUI(null, 'analyzing');
                setTimeout(poll, 2000); // Poll every 2 seconds
            } else {
                throw new Error('Analysis timeout');
            }
            
        } catch (error) {
            console.error('Polling error:', error);
            showAlert('Analysis failed: ' + error.message, 'danger');
            updateUploadUI(null, 'error');
        }
    };
    
    poll();
}

function showAnalysisResults(result) {
    // Show results in modal or redirect to results page
    const modal = document.getElementById('analysisResultModal');
    if (modal) {
        populateResultModal(result);
        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();
    } else {
        // Redirect to results page
        window.location.href = `/results?id=${result.id}`;
    }
}

function populateResultModal(result) {
    const modalBody = document.getElementById('analysisResultModalBody');
    if (!modalBody) return;
    
    const decision = result.decision;
    const confidence = Math.round(result.confidence);
    const violations = result.violations || [];
    
    modalBody.innerHTML = `
        <div class="text-center mb-4">
            <div class="mb-3">
                <i class="fas fa-${decision === 'approved' ? 'check-circle' : 'times-circle'} 
                   fa-4x text-${decision === 'approved' ? 'success' : 'danger'}"></i>
            </div>
            <h4 class="text-${decision === 'approved' ? 'success' : 'danger'}">
                ${decision.charAt(0).toUpperCase() + decision.slice(1)}
            </h4>
            <p class="text-muted">Confidence: ${confidence}%</p>
        </div>
        
        <div class="row mb-3">
            <div class="col-md-6">
                <h6>Processing Time</h6>
                <p>${formatDuration(result.processing_time || 0)}</p>
            </div>
            <div class="col-md-6">
                <h6>File Size</h6>
                <p>${formatFileSize(result.file_size || 0)}</p>
            </div>
        </div>
        
        ${violations.length > 0 ? `
            <div class="mb-3">
                <h6>Issues Detected</h6>
                <div class="d-flex flex-wrap gap-2">
                    ${violations.map(v => `<span class="badge bg-danger">${v}</span>`).join('')}
                </div>
            </div>
        ` : ''}
        
        <div class="mb-3">
            <h6>Reasoning</h6>
            <p class="text-muted">${result.reasoning || 'No detailed reasoning available.'}</p>
        </div>
    `;
}

// Chart Utilities
function createChart(canvasId, type, data, options = {}) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;
    
    const defaultOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                position: 'bottom'
            }
        }
    };
    
    return new Chart(ctx, {
        type: type,
        data: data,
        options: { ...defaultOptions, ...options }
    });
}

// Error Handling
function handleGlobalError(event) {
    console.error('Global error:', event.error || event.reason);
    
    // Don't show alerts for every error, just log them
    // Only show user-friendly messages for critical errors
    if (event.error && event.error.message.includes('fetch')) {
        showAlert('Network error. Please check your connection.', 'warning');
    }
}

// Export functions for global use
window.VideoModerationApp = {
    formatFileSize,
    formatDuration,
    getConfidenceColor,
    formatDate,
    showAlert,
    setupFileUpload,
    createChart,
    uploadFile,
    pollAnalysisResults
};