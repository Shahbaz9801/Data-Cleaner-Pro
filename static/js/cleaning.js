document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const marketplaceCards = document.querySelectorAll('.marketplace-card');
    const selectedMarketplaceInput = document.getElementById('selectedMarketplace');
    const cleanBtn = document.getElementById('cleanBtn');
    const fileInput = document.getElementById('fileInput');
    const fileDropArea = document.getElementById('fileDropArea');
    const browseBtn = document.getElementById('browseBtn');
    const downloadBtn = document.getElementById('downloadBtn');
    const clearFileBtn = document.getElementById('clearFileBtn');
    const sampleDataBtn = document.getElementById('sampleDataBtn');
    const sampleDataModal = new bootstrap.Modal(document.getElementById('sampleDataModal'));
    
    // Current session ID for download
    let currentSessionId = null;
    
    // Initialize
    if (marketplaceCards.length > 0) {
        marketplaceCards[0].classList.add('active');
        selectedMarketplaceInput.value = marketplaceCards[0].dataset.marketplace;
    }
    
    // Marketplace selection
    marketplaceCards.forEach(card => {
        card.addEventListener('click', function() {
            marketplaceCards.forEach(c => c.classList.remove('active'));
            this.classList.add('active');
            selectedMarketplaceInput.value = this.dataset.marketplace;
            updateCleanButtonState();
        });
    });
    
    // Sample Data Button
    sampleDataBtn.addEventListener('click', function() {
        showSampleDataModal();
    });
    
    function showSampleDataModal() {
        const content = document.getElementById('sampleDataContent');
        
        content.innerHTML = `
            <div class="text-center py-3">
                <p class="mb-3">Select marketplace to download sample data:</p>
                <div class="d-flex flex-column gap-2">
                    <button class="btn btn-primary download-sample-btn" data-marketplace="Noon">
                        <i class="fas fa-sun me-2"></i>Download Noon Sample Data
                    </button>
                    <button class="btn btn-primary download-sample-btn" data-marketplace="Amazon">
                        <i class="fab fa-amazon me-2"></i>Download Amazon Sample Data
                    </button>
                    <button class="btn btn-secondary download-sample-btn" data-marketplace="Revibe" disabled>
                        <i class="fas fa-recycle me-2"></i>Revibe (Coming Soon)
                    </button>
                </div>
                <div class="mt-4">
                    <h6>Sample Data Format:</h6>
                    <div class="text-start small text-muted">
                        <p class="mb-1"><strong>Noon:</strong> order_timestamp, item_nr, sku, status, id_partner, country_code, partner_sku, fulfillment_model, offer_price</p>
                        <p class="mb-0"><strong>Amazon:</strong> purchase-date, amazon-order-id, sku, item-status, ship-country, sales-channel, product-name, asin, fulfillment-channel, item-price, quantity</p>
                    </div>
                </div>
            </div>
        `;
        
        // Add download handlers
        document.querySelectorAll('.download-sample-btn:not(:disabled)').forEach(btn => {
            btn.addEventListener('click', function() {
                const marketplace = this.dataset.marketplace;
                downloadSampleData(marketplace);
            });
        });
        
        sampleDataModal.show();
    }
    
    // Download Sample Data
    async function downloadSampleData(marketplace) {
        try {
            // Show loading
            const originalText = sampleDataBtn.innerHTML;
            sampleDataBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Downloading...';
            sampleDataBtn.disabled = true;
            
            // Download the file
            const response = await fetch(`/api/sample-data/${marketplace}`);
            
            if (!response.ok) {
                const error = await response.text();
                throw new Error(`Server error: ${response.status}`);
            }
            
            // Create download link
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `Sample_${marketplace}_Data.csv`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
            
            // Close modal
            sampleDataModal.hide();
            
            // Show success message
            showAlert(`Sample ${marketplace} data downloaded successfully!`, 'success');
            
            // Reset button
            setTimeout(() => {
                sampleDataBtn.innerHTML = originalText;
                sampleDataBtn.disabled = false;
            }, 1000);
            
        } catch (error) {
            console.error('Error downloading sample:', error);
            showError(`Failed to download sample: ${error.message}`);
            
            // Reset button
            sampleDataBtn.innerHTML = '<i class="fas fa-download me-1"></i>Download Sample Data';
            sampleDataBtn.disabled = false;
        }
    }
    
    // File upload handling
    browseBtn.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', handleFileSelect);
    
    // Drag and drop
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        fileDropArea.addEventListener(eventName, preventDefaults, false);
    });
    
    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    ['dragenter', 'dragover'].forEach(eventName => {
        fileDropArea.addEventListener(eventName, () => fileDropArea.classList.add('dragover'), false);
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
        fileDropArea.addEventListener(eventName, () => fileDropArea.classList.remove('dragover'), false);
    });
    
    fileDropArea.addEventListener('drop', handleDrop, false);
    
    function handleDrop(e) {
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            fileInput.files = files;
            handleFileSelect();
        }
    }
    
    function handleFileSelect() {
        if (fileInput.files.length > 0) {
            const file = fileInput.files[0];
            showFileInfo(file);
            updateCleanButtonState();
        }
    }
    
    // Clear file button
    clearFileBtn.addEventListener('click', function() {
        fileInput.value = '';
        document.getElementById('fileInfo').style.display = 'none';
        updateCleanButtonState();
    });
    
    function updateCleanButtonState() {
        const hasMarketplace = selectedMarketplaceInput.value !== '';
        const hasFile = fileInput.files.length > 0;
        cleanBtn.disabled = !(hasMarketplace && hasFile);
    }
    
    function showFileInfo(file) {
        const fileInfoDiv = document.getElementById('fileInfo');
        const fileDetailsDiv = document.getElementById('fileDetails');
        
        const fileSize = (file.size / 1024 / 1024).toFixed(2);
        const fileType = file.name.split('.').pop().toUpperCase();
        const fileIcon = getFileIcon(fileType);
        
        fileDetailsDiv.innerHTML = `
            <div class="fw-bold">${file.name}</div>
            <div class="small">
                <span class="me-3"><i class="fas fa-weight me-1"></i>${fileSize} MB</span>
                <span><i class="fas ${fileIcon} me-1"></i>${fileType}</span>
            </div>
        `;
        
        fileInfoDiv.style.display = 'block';
    }
    
    function getFileIcon(fileType) {
        if (fileType === 'CSV') return 'fa-file-csv';
        if (fileType === 'XLSX' || fileType === 'XLS') return 'fa-file-excel';
        return 'fa-file';
    }
    
    // Clean data button
    cleanBtn.addEventListener('click', async function() {
        const marketplace = selectedMarketplaceInput.value;
        const file = fileInput.files[0];
        
        if (!marketplace || !file) {
            showError('Please select a marketplace and upload a file');
            return;
        }
        
        if (!validateFile(file)) {
            return;
        }
        
        const loader = document.getElementById('loader');
        loader.style.display = 'block';
        cleanBtn.disabled = true;
        hideError();
        
        try {
            const formData = new FormData();
            formData.append('marketplace', marketplace);
            formData.append('file', file);
            
            const response = await fetch('/api/clean', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            
            loader.style.display = 'none';
            cleanBtn.disabled = false;
            
            if (result.success) {
                currentSessionId = result.session_id;
                showPreview(result);
                downloadBtn.disabled = false;
                localStorage.setItem('cleanedData', JSON.stringify(result));
                showAlert('Data cleaned successfully!', 'success');
            } else {
                showError(result.error || 'Failed to clean data');
            }
            
        } catch (error) {
            loader.style.display = 'none';
            cleanBtn.disabled = false;
            
            if (error.name === 'TypeError' && error.message.includes('fetch')) {
                showError('Network error: Unable to connect to server.');
            } else {
                showError('Error: ' + error.message);
            }
            console.error('API Error:', error);
        }
    });
    
    function validateFile(file) {
        const maxSize = 16 * 1024 * 1024;
        if (file.size > maxSize) {
            showError(`File size (${(file.size / 1024 / 1024).toFixed(2)}MB) exceeds 16MB limit`);
            return false;
        }
        
        const allowedExtensions = ['.csv', '.xlsx', '.xls'];
        const fileExtension = '.' + file.name.toLowerCase().split('.').pop();
        
        if (!allowedExtensions.includes(fileExtension)) {
            showError(`File type ${fileExtension} not allowed. Please upload CSV or Excel files.`);
            return false;
        }
        
        return true;
    }
    
    // Download button
    downloadBtn.addEventListener('click', async function() {
        if (!currentSessionId) {
            showError('No cleaned data available for download');
            return;
        }
        
        try {
            const originalText = this.innerHTML;
            this.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Preparing...';
            this.disabled = true;
            
            // Download using session ID
            const response = await fetch(`/api/download/${currentSessionId}`);
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Download failed');
            }
            
            // Create download link
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            
            // Get filename from headers or use default
            const contentDisposition = response.headers.get('Content-Disposition');
            let filename = `Cleaned_${selectedMarketplaceInput.value}_Data.csv`;
            
            if (contentDisposition) {
                const filenameMatch = contentDisposition.match(/filename="?(.+)"?/);
                if (filenameMatch && filenameMatch[1]) {
                    filename = filenameMatch[1];
                }
            }
            
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
            
            setTimeout(() => {
                this.innerHTML = originalText;
                this.disabled = false;
                showAlert('Download started!', 'success');
            }, 1000);
            
        } catch (error) {
            console.error('Download error:', error);
            showError('Failed to download file: ' + error.message);
            this.innerHTML = '<i class="fas fa-download me-2"></i>Download All Data';
            this.disabled = false;
        }
    });
    
    // Show preview function
    function showPreview(data) {
        const previewPlaceholder = document.getElementById('previewPlaceholder');
        const previewContent = document.getElementById('previewContent');
        const tableHeader = document.getElementById('tableHeader');
        const tableBody = document.getElementById('tableBody');
        const rowCountBadge = document.getElementById('rowCount');
        
        previewPlaceholder.style.display = 'none';
        previewContent.style.display = 'block';
        
        const totalRows = data.rows_count || data.all_data.length;
        rowCountBadge.textContent = `${formatNumber(totalRows)} rows`;
        
        tableHeader.innerHTML = '';
        tableBody.innerHTML = '';
        
        // Create header
        const headerRow = document.createElement('tr');
        data.columns.forEach((column, index) => {
            const th = document.createElement('th');
            th.textContent = column;
            th.title = column;
            th.style.minWidth = '120px';
            headerRow.appendChild(th);
        });
        tableHeader.appendChild(headerRow);
        
        // Create body with ALL data
        if (data.all_data && data.all_data.length > 0) {
            data.all_data.forEach((row, rowIndex) => {
                const tr = document.createElement('tr');
                
                data.columns.forEach(column => {
                    const td = document.createElement('td');
                    let value = row[column];
                    
                    if (value === null || value === undefined || value === '') {
                        value = '';
                        td.classList.add('text-muted');
                        td.innerHTML = '<em>—</em>';
                    } else {
                        if (typeof value === 'number') {
                            value = value.toLocaleString('en-IN', {
                                minimumFractionDigits: 2,
                                maximumFractionDigits: 2
                            });
                        }
                        
                        if (column.toLowerCase().includes('date')) {
                            const date = new Date(value);
                            if (!isNaN(date.getTime())) {
                                value = date.toLocaleDateString('en-IN', {
                                    day: '2-digit',
                                    month: 'short',
                                    year: 'numeric'
                                });
                            }
                        }
                        
                        td.textContent = value;
                    }
                    
                    td.title = `${column}: ${value}`;
                    tr.appendChild(td);
                });
                
                tableBody.appendChild(tr);
            });
        }
        
        // Scroll to preview
        setTimeout(() => {
            document.querySelector('.preview-section').scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }, 300);
    }
    
    // Utility functions
    function formatNumber(num) {
        return new Intl.NumberFormat('en-IN').format(num);
    }
    
    // Error handling
    function showError(message) {
        const errorAlert = document.getElementById('errorAlert');
        const errorMessage = document.getElementById('errorMessage');
        errorMessage.textContent = message;
        errorAlert.classList.remove('d-none');
        
        setTimeout(hideError, 5000);
    }
    
    function hideError() {
        const errorAlert = document.getElementById('errorAlert');
        errorAlert.classList.add('d-none');
    }
    
    function showAlert(message, type = 'success') {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        alertDiv.style.cssText = `
            top: 20px;
            right: 20px;
            z-index: 9999;
            min-width: 300px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        `;
        
        const icon = type === 'success' ? 'fa-check-circle' : 'fa-exclamation-circle';
        
        alertDiv.innerHTML = `
            <i class="fas ${icon} me-2"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(alertDiv);
        
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 5000);
    }
    
    // Keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        if ((e.ctrlKey || e.metaKey) && e.key === 'o') {
            e.preventDefault();
            fileInput.click();
        }
        
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter' && !cleanBtn.disabled) {
            e.preventDefault();
            cleanBtn.click();
        }
        
        if ((e.ctrlKey || e.metaKey) && e.key === 'd' && !downloadBtn.disabled) {
            e.preventDefault();
            downloadBtn.click();
        }
    });
});