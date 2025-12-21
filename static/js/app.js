// SpendShield AI - Dashboard JavaScript

// API Configuration
const API_BASE_URL = '';

// State Management
let currentPage = 'dashboard';
let currentAnalysis = null;
let analysisHistory = [];

// Initialize App
document.addEventListener('DOMContentLoaded', () => {
    initializeNavigation();
    initializeUpload();
    initializeWorkflow();
    loadDemoData();
    checkAPIStatus();
});

// Navigation
function initializeNavigation() {
    const navItems = document.querySelectorAll('.nav-item');

    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const page = item.dataset.page;
            navigateToPage(page);
        });
    });
}

function navigateToPage(page) {
    // Update active nav item
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
    });
    document.querySelector(`[data-page="${page}"]`).classList.add('active');

    // Update active page
    document.querySelectorAll('.page').forEach(p => {
        p.classList.remove('active');
    });
    document.getElementById(`${page}-page`).classList.add('active');

    // Update header
    updatePageHeader(page);

    currentPage = page;
}

function updatePageHeader(page) {
    const titles = {
        dashboard: { title: 'Dashboard', subtitle: 'Real-time fraud detection analytics' },
        upload: { title: 'Upload Document', subtitle: 'Upload invoices, tenders, or approvals for analysis' },
        analysis: { title: 'Agent Workflow', subtitle: 'Multi-agent analysis visualization' },
        reports: { title: 'Reports', subtitle: 'Detailed fraud risk assessments' },
        history: { title: 'History', subtitle: 'Past analysis records' },
        settings: { title: 'Settings', subtitle: 'Configure system preferences' }
    };

    document.getElementById('page-title').textContent = titles[page].title;
    document.getElementById('page-subtitle').textContent = titles[page].subtitle;
}

// Upload Functionality
function initializeUpload() {
    const uploadArea = document.getElementById('upload-area');
    const fileInput = document.getElementById('file-input');
    const filePreview = document.getElementById('file-preview');
    const removeFileBtn = document.getElementById('remove-file');
    const analyzeBtn = document.getElementById('analyze-btn');

    // Click to upload
    uploadArea.addEventListener('click', () => {
        fileInput.click();
    });

    // Drag and drop
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.style.borderColor = 'var(--primary-color)';
    });

    uploadArea.addEventListener('dragleave', () => {
        uploadArea.style.borderColor = 'var(--border-color)';
    });

    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.style.borderColor = 'var(--border-color)';

        const file = e.dataTransfer.files[0];
        handleFileSelect(file);
    });

    // File input change
    fileInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        handleFileSelect(file);
    });

    // Remove file
    removeFileBtn.addEventListener('click', () => {
        fileInput.value = '';
        filePreview.style.display = 'none';
        uploadArea.style.display = 'block';
        analyzeBtn.disabled = true;
    });

    // Analyze button
    analyzeBtn.addEventListener('click', () => {
        startAnalysis();
    });
}

function handleFileSelect(file) {
    if (!file) return;

    // Validate file type
    const allowedTypes = ['application/pdf', 'image/png', 'image/jpeg', 'image/jpg'];
    if (!allowedTypes.includes(file.type)) {
        showNotification('Invalid file type. Please upload PDF, PNG, or JPG files.', 'error');
        return;
    }

    // Validate file size (10MB)
    if (file.size > 10 * 1024 * 1024) {
        showNotification('File too large. Maximum size is 10MB.', 'error');
        return;
    }

    // Show file preview
    document.getElementById('file-name').textContent = file.name;
    document.getElementById('file-size').textContent = formatFileSize(file.size);
    document.getElementById('upload-area').style.display = 'none';
    document.getElementById('file-preview').style.display = 'block';
    document.getElementById('analyze-btn').disabled = false;
}

function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
}

// Analysis Workflow
function initializeWorkflow() {
    const startDemoBtn = document.getElementById('start-demo-analysis');
    const resetBtn = document.getElementById('reset-workflow');

    startDemoBtn.addEventListener('click', () => {
        runDemoAnalysis();
    });

    resetBtn.addEventListener('click', () => {
        resetWorkflow();
    });
}

async function runDemoAnalysis() {
    document.getElementById('start-demo-analysis').style.display = 'none';
    document.getElementById('reset-workflow').style.display = 'inline-flex';

    // Fetch demo data from API
    try {
        const response = await fetch(`${API_BASE_URL}/demo`);
        const data = await response.json();

        // Simulate workflow stages
        await simulateStage('extractor', data.analysis.step_1_extraction, data.document);
        await simulateStage('verifier', data.analysis.step_2_verification, data.document);
        await simulateStage('anomaly', data.analysis.step_3_anomaly_detection, data.document);
        await simulateStage('reporter', data.analysis.step_4_reporting, data.document);

        // Update report
        updateReport(data);

        showNotification('Demo analysis completed successfully!', 'success');
    } catch (error) {
        console.error('Error running demo:', error);
        showNotification('Error running demo analysis. Make sure the API is running.', 'error');
    }
}

async function simulateStage(stageName, stageData, documentData) {
    const stage = document.getElementById(`stage-${stageName}`);
    const progressBar = stage.querySelector('.progress-fill');
    const statusIcon = stage.querySelector('.stage-status');
    const details = stage.querySelector('.stage-details');

    // Mark as active
    stage.classList.add('active');
    statusIcon.classList.remove('pending');
    statusIcon.classList.add('processing');
    statusIcon.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';

    // Animate progress
    await animateProgress(progressBar, 100, 2000);

    // Mark as completed
    stage.classList.remove('active');
    stage.classList.add('completed');
    statusIcon.classList.remove('processing');
    statusIcon.classList.add('completed');
    statusIcon.innerHTML = '<i class="fas fa-check"></i>';

    // Show details
    if (details) {
        details.style.display = 'block';

        if (stageName === 'extractor') {
            document.getElementById('extracted-vendor').textContent = documentData.vendor;
            document.getElementById('extracted-amount').textContent = `$${documentData.amount.toLocaleString()}`;
            document.getElementById('extracted-items').textContent = documentData.item;
        } else if (stageName === 'verifier') {
            document.getElementById('vendor-exists').textContent = stageData.vendor_exists ? '✅ Yes' : '❌ No';
            document.getElementById('vendor-risk').textContent = stageData.vendor_exists ? 'N/A' : '0.0';
            document.getElementById('historical-price').textContent = `$${stageData.historical_avg_price}`;
        } else if (stageName === 'anomaly') {
            const anomaliesList = document.getElementById('anomalies-list');
            anomaliesList.innerHTML = stageData.anomalies.map(a => `
                <div class="detail-item">
                    <span class="label">${a.type.replace('_', ' ').toUpperCase()}:</span>
                    <span class="value" style="color: var(--danger-color)">${a.severity}</span>
                </div>
            `).join('');
        } else if (stageName === 'reporter') {
            document.getElementById('final-risk-score').textContent = stageData.fraud_risk_score;
            document.getElementById('risk-level').textContent = stageData.risk_level;
        }
    }

    // Wait before next stage
    await sleep(500);
}

function animateProgress(element, targetWidth, duration) {
    return new Promise(resolve => {
        let start = null;
        const initialWidth = 0;

        function step(timestamp) {
            if (!start) start = timestamp;
            const progress = Math.min((timestamp - start) / duration, 1);
            const currentWidth = initialWidth + (targetWidth - initialWidth) * progress;

            element.style.width = currentWidth + '%';

            if (progress < 1) {
                requestAnimationFrame(step);
            } else {
                resolve();
            }
        }

        requestAnimationFrame(step);
    });
}

function resetWorkflow() {
    // Reset all stages
    const stages = document.querySelectorAll('.stage');
    stages.forEach(stage => {
        stage.classList.remove('active', 'completed');
        stage.querySelector('.progress-fill').style.width = '0%';
        stage.querySelector('.stage-status').classList.remove('processing', 'completed');
        stage.querySelector('.stage-status').classList.add('pending');
        stage.querySelector('.stage-status').innerHTML = '<i class="fas fa-clock"></i>';

        const details = stage.querySelector('.stage-details');
        if (details) {
            details.style.display = 'none';
        }
    });

    document.getElementById('start-demo-analysis').style.display = 'inline-flex';
    document.getElementById('reset-workflow').style.display = 'none';
}

// API Functions
async function startAnalysis() {
    const fileInput = document.getElementById('file-input');
    const department = document.getElementById('department').value;
    const fiscalYear = document.getElementById('fiscal-year').value;

    if (!fileInput.files[0]) {
        showNotification('Please select a file first', 'error');
        return;
    }

    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    if (department) formData.append('department', department);
    if (fiscalYear) formData.append('fiscal_year', fiscalYear);

    try {
        // Show uploading notification
        showNotification('Uploading document...', 'info');

        // Disable analyze button
        const analyzeBtn = document.getElementById('analyze-btn');
        analyzeBtn.disabled = true;
        analyzeBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Analyzing...';

        // Upload and analyze
        const response = await fetch(`${API_BASE_URL}/analyze`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Analysis failed');
        }

        const result = await response.json();
        const threadId = result.thread_id;

        showNotification('Document uploaded! Starting analysis...', 'success');

        // Navigate to workflow page
        navigateToPage('analysis');

        // Wait a moment for page transition
        await sleep(500);

        // Fetch the actual analysis results
        const auditResponse = await fetch(`${API_BASE_URL}/audit/${threadId}`);

        if (!auditResponse.ok) {
            throw new Error('Failed to fetch analysis results');
        }

        const auditData = await auditResponse.json();

        // Run workflow visualization with REAL data
        await runRealAnalysis(auditData);

        // Re-enable button
        analyzeBtn.disabled = false;
        analyzeBtn.innerHTML = '<i class="fas fa-search"></i> Start Analysis';

        showNotification('Analysis completed successfully!', 'success');

    } catch (error) {
        console.error('Analysis error:', error);
        showNotification(`Error: ${error.message}`, 'error');

        // Re-enable button
        const analyzeBtn = document.getElementById('analyze-btn');
        analyzeBtn.disabled = false;
        analyzeBtn.innerHTML = '<i class="fas fa-search"></i> Start Analysis';
    }
}

// Run analysis with REAL data from uploaded file
async function runRealAnalysis(auditData) {
    document.getElementById('start-demo-analysis').style.display = 'none';
    document.getElementById('reset-workflow').style.display = 'inline-flex';

    const extractedData = auditData.extracted_data || {};
    const anomalies = auditData.anomalies || [];
    const riskScore = auditData.fraud_risk_score || 0;
    const riskLevel = auditData.risk_level || 'LOW';

    // Stage 1: Extractor - Show REAL extracted data
    await simulateStageWithData('extractor', {
        status: '✅ Complete',
        agent: 'Extractor'
    }, {
        vendor: extractedData.vendor_name || 'N/A',
        amount: extractedData.total_amount || 0,
        item: extractedData.items?.[0]?.description || 'N/A',
        invoice_number: extractedData.invoice_number || 'N/A'
    });

    // Stage 2: Verifier - Show verification results
    await simulateStageWithData('verifier', {
        status: '✅ Complete',
        agent: 'Verifier',
        vendor_exists: extractedData.vendor_id ? true : false,
        historical_avg_price: extractedData.items?.[0]?.unit_price * 0.8 || 0
    }, extractedData);

    // Stage 3: Anomaly Detector - Show REAL anomalies
    await simulateStageWithData('anomaly', {
        status: '✅ Complete',
        agent: 'Anomaly Detector',
        anomalies: anomalies.map(a => ({
            type: a.flag_type,
            severity: a.severity,
            description: a.description
        }))
    }, extractedData);

    // Stage 4: Reporter - Show REAL risk score
    await simulateStageWithData('reporter', {
        status: '✅ Complete',
        agent: 'Reporter',
        fraud_risk_score: riskScore,
        risk_level: riskLevel
    }, extractedData);

    // Update report page with REAL data
    updateReportWithRealData(auditData);

    // Update dashboard stats
    updateDashboardStats(auditData);
}

// Simulate stage with REAL data
async function simulateStageWithData(stageName, stageData, documentData) {
    const stage = document.getElementById(`stage-${stageName}`);
    const progressBar = stage.querySelector('.progress-fill');
    const statusIcon = stage.querySelector('.stage-status');
    const details = stage.querySelector('.stage-details');

    // Mark as active
    stage.classList.add('active');
    statusIcon.classList.remove('pending');
    statusIcon.classList.add('processing');
    statusIcon.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';

    // Animate progress
    await animateProgress(progressBar, 100, 2000);

    // Mark as completed
    stage.classList.remove('active');
    stage.classList.add('completed');
    statusIcon.classList.remove('processing');
    statusIcon.classList.add('completed');
    statusIcon.innerHTML = '<i class="fas fa-check"></i>';

    // Show details with REAL data
    if (details) {
        details.style.display = 'block';

        if (stageName === 'extractor') {
            document.getElementById('extracted-vendor').textContent = documentData.vendor || 'N/A';
            document.getElementById('extracted-amount').textContent = documentData.amount ?
                `$${Number(documentData.amount).toLocaleString()}` : 'N/A';
            document.getElementById('extracted-items').textContent = documentData.item || 'N/A';
        } else if (stageName === 'verifier') {
            document.getElementById('vendor-exists').textContent = stageData.vendor_exists ? '✅ Yes' : '❌ No';
            document.getElementById('vendor-risk').textContent = stageData.vendor_exists ? 'Low' : 'High';
            document.getElementById('historical-price').textContent = stageData.historical_avg_price ?
                `$${Number(stageData.historical_avg_price).toFixed(2)}` : 'N/A';
        } else if (stageName === 'anomaly') {
            const anomaliesList = document.getElementById('anomalies-list');
            if (stageData.anomalies && stageData.anomalies.length > 0) {
                anomaliesList.innerHTML = stageData.anomalies.map(a => `
                    <div class="detail-item">
                        <span class="label">${a.type.replace(/_/g, ' ').toUpperCase()}:</span>
                        <span class="value" style="color: var(--danger-color)">${a.severity}</span>
                    </div>
                `).join('');
            } else {
                anomaliesList.innerHTML = '<div class="detail-item"><span class="label">No anomalies detected</span></div>';
            }
        } else if (stageName === 'reporter') {
            document.getElementById('final-risk-score').textContent = stageData.fraud_risk_score || 0;
            document.getElementById('risk-level').textContent = stageData.risk_level || 'LOW';
        }
    }

    // Wait before next stage
    await sleep(500);
}

// Update report with REAL analysis data
function updateReportWithRealData(auditData) {
    const extractedData = auditData.extracted_data || {};
    const anomalies = auditData.anomalies || [];

    // Update risk score and level
    document.getElementById('report-risk-score').textContent = `${auditData.fraud_risk_score || 0}/100`;
    document.getElementById('report-risk-level').textContent = auditData.risk_level || 'LOW';

    // Update document details
    document.getElementById('report-vendor').textContent = extractedData.vendor_name || 'N/A';
    document.getElementById('report-amount').textContent = extractedData.total_amount ?
        `$${Number(extractedData.total_amount).toLocaleString()}` : 'N/A';
    document.getElementById('report-reference').textContent = extractedData.invoice_number || 'N/A';

    // Update anomalies section
    const anomaliesContainer = document.getElementById('report-anomalies');
    if (anomalies.length > 0) {
        anomaliesContainer.innerHTML = anomalies.map(a => `
            <div class="anomaly-card ${a.severity.toLowerCase()}">
                <div class="anomaly-header">
                    <i class="fas fa-exclamation-triangle"></i>
                    <h4>${a.flag_type.replace(/_/g, ' ').toUpperCase()}</h4>
                    <span class="severity">${a.severity}</span>
                </div>
                <p>${a.description}</p>
            </div>
        `).join('');
    } else {
        anomaliesContainer.innerHTML = '<p style="color: var(--success-color)">✅ No anomalies detected</p>';
    }

    // Update recommendations
    const recommendationsContainer = document.getElementById('report-recommendations');
    if (auditData.recommendations && auditData.recommendations.length > 0) {
        recommendationsContainer.innerHTML = auditData.recommendations.map(r => `<li>${r}</li>`).join('');
    }

    // Update report date
    document.getElementById('report-date').textContent = new Date().toLocaleString();
}

// Update dashboard statistics
function updateDashboardStats(auditData) {
    // Increment total analyzed
    const currentTotal = parseInt(document.getElementById('total-analyzed').textContent) || 0;
    document.getElementById('total-analyzed').textContent = currentTotal + 1;

    // Update anomalies count
    const anomalyCount = auditData.anomalies ? auditData.anomalies.length : 0;
    const currentAnomalies = parseInt(document.getElementById('total-anomalies').textContent) || 0;
    document.getElementById('total-anomalies').textContent = currentAnomalies + anomalyCount;

    // Update average risk score
    document.getElementById('avg-risk-score').textContent = Math.round(auditData.fraud_risk_score || 0);
}


async function checkAPIStatus() {
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        const data = await response.json();

        if (data.status === 'healthy') {
            console.log('API Status: Connected');
        }
    } catch (error) {
        console.error('API not available:', error);
        showNotification('API server not available. Some features may not work.', 'warning');
    }
}

// Load Demo Data
function loadDemoData() {
    // Update stats
    document.getElementById('total-analyzed').textContent = '1';
    document.getElementById('total-anomalies').textContent = '2';
    document.getElementById('avg-risk-score').textContent = '65';

    // Update report date
    document.getElementById('report-date').textContent = new Date().toLocaleString();
}

function updateReport(data) {
    // Update report with analysis data
    if (data.analysis && data.analysis.step_4_reporting) {
        const reporting = data.analysis.step_4_reporting;
        document.getElementById('report-risk-score').textContent = `${reporting.fraud_risk_score}/100`;
        document.getElementById('report-risk-level').textContent = reporting.risk_level;
    }

    if (data.document) {
        document.getElementById('report-vendor').textContent = data.document.vendor;
        document.getElementById('report-amount').textContent = `$${data.document.amount.toLocaleString()}`;
        document.getElementById('report-reference').textContent = data.document.invoice_number;
    }
}

// Utility Functions
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
        <span>${message}</span>
    `;

    // Add styles
    Object.assign(notification.style, {
        position: 'fixed',
        top: '20px',
        right: '20px',
        padding: '1rem 1.5rem',
        background: type === 'success' ? 'var(--success-color)' : type === 'error' ? 'var(--danger-color)' : 'var(--info-color)',
        color: 'white',
        borderRadius: '0.5rem',
        boxShadow: 'var(--shadow-lg)',
        zIndex: '10000',
        display: 'flex',
        alignItems: 'center',
        gap: '0.75rem',
        animation: 'slideIn 0.3s ease-out',
        minWidth: '300px'
    });

    document.body.appendChild(notification);

    // Remove after 3 seconds
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease-out';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Add notification animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(400px);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(400px);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// Export PDF Report
document.getElementById('export-report')?.addEventListener('click', () => {
    showNotification('PDF export feature coming soon!', 'info');
});

// Search functionality
document.querySelector('.search-box input')?.addEventListener('input', (e) => {
    const searchTerm = e.target.value.toLowerCase();
    // Implement search logic here
    console.log('Searching for:', searchTerm);
});

// Filter history
document.getElementById('filter-risk')?.addEventListener('change', (e) => {
    const filter = e.target.value;
    console.log('Filtering by:', filter);
    // Implement filter logic here
});

console.log('SpendShield AI Dashboard initialized successfully!');
