// Main JavaScript for Blood Test Analyzer

document.addEventListener('DOMContentLoaded', function() {
    // Initialize Bootstrap tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize Bootstrap popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // File upload preview
    const fileInput = document.getElementById('file');
    if (fileInput) {
        fileInput.addEventListener('change', function(e) {
            const fileName = e.target.files[0]?.name;
            const fileSize = e.target.files[0]?.size;
            
            if (fileName) {
                // Display file info
                const fileInfoElement = document.getElementById('file-info');
                if (fileInfoElement) {
                    const fileSizeFormatted = formatFileSize(fileSize);
                    fileInfoElement.innerHTML = `<strong>Selected file:</strong> ${fileName} (${fileSizeFormatted})`;
                    fileInfoElement.classList.remove('d-none');
                }
            }
        });
    }

    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });
});

// Format file size in human-readable format
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Function to confirm deletion
function confirmDelete(testId) {
    if (confirm('Are you sure you want to delete this blood test? This action cannot be undone.')) {
        window.location.href = `/delete/${testId}`;
    }
}

// Function to toggle reference ranges visibility
function toggleReferenceRanges() {
    const rangeElements = document.querySelectorAll('.reference-range');
    rangeElements.forEach(element => {
        element.classList.toggle('d-none');
    });
    
    const toggleButton = document.getElementById('toggle-ranges');
    if (toggleButton) {
        if (toggleButton.innerText === 'Show Reference Ranges') {
            toggleButton.innerText = 'Hide Reference Ranges';
        } else {
            toggleButton.innerText = 'Show Reference Ranges';
        }
    }
}

// Function to export data as CSV
function exportAsCSV(testId) {
    window.location.href = `/export/${testId}/csv`;
}

// Function to export data as PDF
function exportAsPDF(testId) {
    window.location.href = `/export/${testId}/pdf`;
}

// Function to compare two blood tests
function compareBiomarkers(testId1, testId2) {
    window.location.href = `/compare?test1=${testId1}&test2=${testId2}`;
}
