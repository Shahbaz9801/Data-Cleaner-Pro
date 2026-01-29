// Add Data Page JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const productTableBody = document.getElementById('productTableBody');
    const refreshBtn = document.getElementById('refreshProducts');
    const singleProductForm = document.getElementById('singleProductForm');
    const addSingleBtn = document.getElementById('addSingleBtn');
    const singleLoader = document.getElementById('singleLoader');
    const bulkFileInput = document.getElementById('bulkFileInput');
    const bulkFileDropArea = document.getElementById('bulkFileDropArea');
    const browseBulkBtn = document.getElementById('browseBulkBtn');
    const uploadBulkBtn = document.getElementById('uploadBulkBtn');
    const bulkLoader = document.getElementById('bulkLoader');
    const clearBulkFileBtn = document.getElementById('clearBulkFileBtn');
    const productCount = document.getElementById('productCount');
    const filterInfo = document.getElementById('filterInfo');
    const tableMessage = document.getElementById('tableMessage');
    
    // Filter elements
    const brandFilter = document.getElementById('brandFilter');
    const categoryFilter = document.getElementById('categoryFilter');
    const subCategoryFilter = document.getElementById('subCategoryFilter');
    const skuFilter = document.getElementById('skuFilter');
    const searchFilter = document.getElementById('searchFilter');
    const applyFiltersBtn = document.getElementById('applyFilters');
    const resetFiltersBtn = document.getElementById('resetFilters');
    const clearFiltersBtn = document.getElementById('clearFilters');
    
    // Current filters
    let currentFilters = {
        brand: '',
        category: '',
        sub_category: '',
        sku: '',
        search: ''
    };
    
    // Load products on page load
    loadProducts();
    
    // Refresh products
    refreshBtn.addEventListener('click', loadProducts);
    
    // Apply filters
    applyFiltersBtn.addEventListener('click', function() {
        currentFilters = {
            brand: brandFilter.value,
            category: categoryFilter.value,
            sub_category: subCategoryFilter.value,
            sku: skuFilter.value,
            search: searchFilter.value.trim()
        };
        loadProducts();
    });
    
    // Reset filters
    resetFiltersBtn.addEventListener('click', function() {
        brandFilter.value = '';
        categoryFilter.value = '';
        subCategoryFilter.value = '';
        skuFilter.value = '';
        searchFilter.value = '';
        currentFilters = {
            brand: '',
            category: '',
            sub_category: '',
            sku: '',
            search: ''
        };
        loadProducts();
    });
    
    // Clear filters (search only)
    clearFiltersBtn.addEventListener('click', function() {
        searchFilter.value = '';
        currentFilters.search = '';
        loadProducts();
    });
    
    // Enter key in search
    searchFilter.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            currentFilters.search = this.value.trim();
            loadProducts();
        }
    });
    
    // Single product form submission
    singleProductForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const formData = {
            Brand: document.getElementById('brand').value.trim(),
            Category: document.getElementById('category').value.trim(),
            'Sub-Category': document.getElementById('subCategory').value.trim(),
            'Product Titles': document.getElementById('productTitle').value.trim(),
            SKU: document.getElementById('sku').value.trim(),
            'Partner SKU': document.getElementById('partnerSku').value.trim()
        };
        
        // Validate
        for (const [key, value] of Object.entries(formData)) {
            if (!value) {
                showError(`Please fill in ${key}`, 'singleError');
                return;
            }
        }
        
        singleLoader.style.display = 'block';
        addSingleBtn.disabled = true;
        hideMessages('single');
        
        try {
            const response = await fetch('/api/products/add', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });
            
            const result = await response.json();
            
            if (result.success) {
                showSuccess('Product added successfully!', 'singleSuccess');
                singleProductForm.reset();
                
                // Update filter dropdowns
                updateFilterDropdowns(result.filters);
                
                // Reload products with current filters
                loadProducts();
                
                // Update product count
                productCount.textContent = `(${result.total})`;
                
            } else {
                showError(result.error, 'singleError');
            }
            
        } catch (error) {
            showError('Network error: ' + error.message, 'singleError');
        } finally {
            singleLoader.style.display = 'none';
            addSingleBtn.disabled = false;
        }
    });
    
    // Bulk file handling
    browseBulkBtn.addEventListener('click', () => bulkFileInput.click());
    bulkFileInput.addEventListener('change', handleBulkFileSelect);
    
    // Drag and drop for bulk upload
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        bulkFileDropArea.addEventListener(eventName, preventDefaults, false);
    });
    
    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    ['dragenter', 'dragover'].forEach(eventName => {
        bulkFileDropArea.addEventListener(eventName, () => {
            bulkFileDropArea.classList.add('dragover');
        }, false);
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
        bulkFileDropArea.addEventListener(eventName, () => {
            bulkFileDropArea.classList.remove('dragover');
        }, false);
    });
    
    bulkFileDropArea.addEventListener('drop', handleBulkDrop, false);
    
    function handleBulkDrop(e) {
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            bulkFileInput.files = files;
            handleBulkFileSelect();
        }
    }
    
    function handleBulkFileSelect() {
        if (bulkFileInput.files.length > 0) {
            const file = bulkFileInput.files[0];
            showBulkFileInfo(file);
            uploadBulkBtn.disabled = false;
        }
    }
    
    // Clear bulk file
    clearBulkFileBtn.addEventListener('click', function() {
        bulkFileInput.value = '';
        document.getElementById('bulkFileInfo').style.display = 'none';
        uploadBulkBtn.disabled = true;
    });
    
    // Bulk upload button
    uploadBulkBtn.addEventListener('click', async function() {
        const file = bulkFileInput.files[0];
        
        if (!file) {
            showError('Please select a CSV file first', 'bulkError');
            return;
        }
        
        if (!file.name.toLowerCase().endsWith('.csv')) {
            showError('Only CSV files are allowed for bulk upload', 'bulkError');
            return;
        }
        
        // Validate file size
        const maxSize = 16 * 1024 * 1024;
        if (file.size > maxSize) {
            showError(`File size (${(file.size / 1024 / 1024).toFixed(2)}MB) exceeds 16MB limit`, 'bulkError');
            return;
        }
        
        bulkLoader.style.display = 'block';
        uploadBulkBtn.disabled = true;
        hideMessages('bulk');
        
        try {
            const formData = new FormData();
            formData.append('file', file);
            
            const response = await fetch('/api/products/bulk', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            
            if (result.success) {
                showSuccess(
                    `Added ${result.added} new products. ${result.skipped} duplicates skipped.`,
                    'bulkSuccess'
                );
                bulkFileInput.value = '';
                document.getElementById('bulkFileInfo').style.display = 'none';
                uploadBulkBtn.disabled = true;
                
                // Update filter dropdowns
                updateFilterDropdowns(result.filters);
                
                // Reload products
                loadProducts();
                
                // Update product count
                productCount.textContent = `(${result.total})`;
                
            } else {
                showError(result.error, 'bulkError');
            }
            
        } catch (error) {
            showError('Network error: ' + error.message, 'bulkError');
        } finally {
            bulkLoader.style.display = 'none';
            uploadBulkBtn.disabled = false;
        }
    });
    
    // Download template link
    document.getElementById('downloadTemplate').addEventListener('click', function(e) {
        // This will trigger the download via the href
        showAlert('Template download started...', 'success');
    });
    
    // Functions
    async function loadProducts() {
        const tableLoader = document.getElementById('tableLoader');
        tableLoader.style.display = 'block';
        tableMessage.textContent = 'Loading products...';
        productTableBody.innerHTML = '';
        
        try {
            // Build query string with filters
            const params = new URLSearchParams();
            if (currentFilters.brand) params.append('brand', currentFilters.brand);
            if (currentFilters.category) params.append('category', currentFilters.category);
            if (currentFilters.sub_category) params.append('sub_category', currentFilters.sub_category);
            if (currentFilters.sku) params.append('sku', currentFilters.sku);
            if (currentFilters.search) params.append('search', currentFilters.search);
            
            const url = `/api/products?${params.toString()}`;
            const response = await fetch(url);
            const result = await response.json();
            
            if (result.success) {
                displayProducts(result.products);
                
                // Update filter info
                let filterText = `Showing ${result.filtered_total} products`;
                if (result.filtered_total < result.total) {
                    filterText = `Showing ${result.filtered_total} of ${result.total} products`;
                }
                
                if (currentFilters.brand || currentFilters.category || 
                    currentFilters.sub_category || currentFilters.sku || currentFilters.search) {
                    filterText += ' (filtered)';
                }
                
                filterInfo.textContent = filterText;
                productCount.textContent = `(${result.total})`;
                
                // Update filter dropdowns
                updateFilterDropdowns(result.filters);
                
            } else {
                productTableBody.innerHTML = `
                    <tr>
                        <td colspan="6" class="text-center text-muted py-4">
                            <i class="fas fa-exclamation-triangle me-2"></i>
                            Error loading products: ${result.error}
                        </td>
                    </tr>
                `;
                tableMessage.textContent = 'Error loading products';
            }
        } catch (error) {
            productTableBody.innerHTML = `
                <tr>
                    <td colspan="6" class="text-center text-muted py-4">
                        <i class="fas fa-exclamation-triangle me-2"></i>
                        Network error: ${error.message}
                    </td>
                </tr>
            `;
            tableMessage.textContent = 'Network error';
        } finally {
            tableLoader.style.display = 'none';
        }
    }
    
    function displayProducts(products) {
        if (products.length === 0) {
            productTableBody.innerHTML = `
                <tr>
                    <td colspan="6" class="text-center text-muted py-4">
                        <i class="fas fa-database me-2"></i>
                        No products found. Try changing your filters.
                    </td>
                </tr>
            `;
            tableMessage.textContent = 'No products found';
            return;
        }
        
        let html = '';
        products.forEach(product => {
            html += `
                <tr>
                    <td>${escapeHtml(product.Brand || '')}</td>
                    <td>${escapeHtml(product.Category || '')}</td>
                    <td>${escapeHtml(product['Sub-Category'] || '')}</td>
                    <td title="${escapeHtml(product['Product Titles'] || '')}">
                        ${truncateText(product['Product Titles'] || '', 60)}
                    </td>
                    <td><code>${escapeHtml(product.SKU || '')}</code></td>
                    <td><code>${escapeHtml(product['Partner SKU'] || '')}</code></td>
                </tr>
            `;
        });
        
        productTableBody.innerHTML = html;
        tableMessage.textContent = `Showing ${products.length} products`;
    }
    
    function updateFilterDropdowns(filters) {
        // Update brand dropdown
        updateSelectOptions(brandFilter, filters.brands || []);
        
        // Update category dropdown
        updateSelectOptions(categoryFilter, filters.categories || []);
        
        // Update sub-category dropdown
        updateSelectOptions(subCategoryFilter, filters.sub_categories || []);
        
        // Update SKU dropdown
        updateSelectOptions(skuFilter, filters.skus || []);
    }
    
    function updateSelectOptions(selectElement, options) {
        const currentValue = selectElement.value;
        
        // Keep first option (All)
        selectElement.innerHTML = '<option value="">All</option>';
        
        // Add new options
        options.forEach(option => {
            const opt = document.createElement('option');
            opt.value = option;
            opt.textContent = option;
            selectElement.appendChild(opt);
        });
        
        // Restore selected value if it still exists
        if (currentValue && options.includes(currentValue)) {
            selectElement.value = currentValue;
        }
    }
    
    function showBulkFileInfo(file) {
        const fileInfoDiv = document.getElementById('bulkFileInfo');
        const fileDetailsDiv = document.getElementById('bulkFileDetails');
        
        const fileSize = (file.size / 1024).toFixed(2);
        
        fileDetailsDiv.innerHTML = `
            <div class="fw-bold">${file.name}</div>
            <div>${fileSize} KB • ${file.type || 'CSV'}</div>
        `;
        
        fileInfoDiv.style.display = 'block';
    }
    
    function showSuccess(message, elementId) {
        const element = document.getElementById(elementId);
        element.textContent = message;
        element.classList.remove('d-none');
        
        setTimeout(() => {
            element.classList.add('d-none');
        }, 5000);
    }
    
    function showError(message, elementId) {
        const element = document.getElementById(elementId);
        element.textContent = message;
        element.classList.remove('d-none');
    }
    
    function hideMessages(type) {
        const successEl = document.getElementById(`${type}Success`);
        const errorEl = document.getElementById(`${type}Error`);
        
        if (successEl) successEl.classList.add('d-none');
        if (errorEl) errorEl.classList.add('d-none');
    }
    
    function truncateText(text, maxLength) {
        if (text.length <= maxLength) return escapeHtml(text);
        return escapeHtml(text.substring(0, maxLength)) + '...';
    }
    
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
});