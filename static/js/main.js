// Main JavaScript for Crypto Prediction App

$(document).ready(function() {
    // Initialize app
    initializeApp();
    
    // Check system status
    checkSystemStatus();
    
    // Set up periodic status check
    setInterval(checkSystemStatus, 30000); // Check every 30 seconds
});

function initializeApp() {
    // Add loading animations
    $('.card').addClass('fade-in');
    
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Smooth scrolling for anchor links
    $('a[href^="#"]').on('click', function(event) {
        var target = $(this.getAttribute('href'));
        if( target.length ) {
            event.preventDefault();
            $('html, body').stop().animate({
                scrollTop: target.offset().top - 100
            }, 1000);
        }
    });
    
    // Add ripple effect to buttons
    $('.btn').on('click', function(e) {
        var ripple = $('<span class="ripple"></span>');
        var x = e.pageX - $(this).offset().left;
        var y = e.pageY - $(this).offset().top;
        
        ripple.css({
            'top': y + 'px',
            'left': x + 'px'
        });
        
        $(this).append(ripple);
        
        setTimeout(function() {
            ripple.remove();
        }, 600);
    });
    
    console.log('🚀 Crypto Prediction App initialized successfully');
}

function checkSystemStatus() {
    $.ajax({
        url: '/api/status',
        method: 'GET',
        timeout: 10000,
        success: function(response) {
            if (response.success && response.status === 'online') {
                updateStatusIndicator('online', 'Hệ thống hoạt động');
            } else {
                updateStatusIndicator('offline', 'Hệ thống offline');
            }
        },
        error: function() {
            updateStatusIndicator('offline', 'Không thể kết nối');
        }
    });
}

function updateStatusIndicator(status, text) {
    const indicator = $('#status-indicator');
    indicator.removeClass('bg-success bg-danger bg-secondary')
             .addClass(status === 'online' ? 'bg-success' : 'bg-danger')
             .text(text);
}

// Utility functions
function formatNumber(num, decimals = 6) {
    if (typeof num === 'string') {
        num = parseFloat(num);
    }
    if (isNaN(num)) return 'N/A';
    return num.toFixed(decimals);
}

function formatPercentage(num, decimals = 2) {
    if (typeof num === 'string') {
        num = parseFloat(num.replace('%', ''));
    }
    if (isNaN(num)) return 'N/A';
    return (num >= 0 ? '+' : '') + num.toFixed(decimals) + '%';
}

function showToast(message, type = 'info') {
    const toastHtml = `
        <div class="toast align-items-center text-white bg-${type} border-0" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        </div>
    `;
    
    // Create toast container if it doesn't exist
    if ($('#toast-container').length === 0) {
        $('body').append('<div id="toast-container" class="toast-container position-fixed bottom-0 end-0 p-3"></div>');
    }
    
    const $toast = $(toastHtml);
    $('#toast-container').append($toast);
    
    const toast = new bootstrap.Toast($toast[0]);
    toast.show();
    
    // Remove toast element after hiding
    $toast.on('hidden.bs.toast', function() {
        $(this).remove();
    });
}

function showLoadingOverlay(message = 'Đang tải...') {
    const overlay = `
        <div id="loading-overlay" class="position-fixed w-100 h-100 top-0 start-0 d-flex align-items-center justify-content-center" style="background: rgba(0,0,0,0.5); z-index: 9999;">
            <div class="text-center text-white">
                <div class="spinner-border mb-3" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <div>${message}</div>
            </div>
        </div>
    `;
    
    $('body').append(overlay);
}

function hideLoadingOverlay() {
    $('#loading-overlay').remove();
}

// Copy to clipboard function
function copyToClipboard(text, successMessage = 'Đã copy!') {
    if (navigator.clipboard) {
        navigator.clipboard.writeText(text).then(function() {
            showToast(successMessage, 'success');
        });
    } else {
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = text;
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        try {
            document.execCommand('copy');
            showToast(successMessage, 'success');
        } catch (err) {
            showToast('Không thể copy', 'danger');
        }
        document.body.removeChild(textArea);
    }
}

// Add event listeners for copy functionality
$(document).on('click', '.copy-btn', function() {
    const text = $(this).data('copy');
    if (text) {
        copyToClipboard(text);
    }
});

// Format currency display
function formatCurrency(value, symbol = '') {
    if (typeof value === 'string') {
        value = parseFloat(value);
    }
    if (isNaN(value)) return 'N/A';
    
    return value.toLocaleString('en-US', {
        minimumFractionDigits: 6,
        maximumFractionDigits: 6
    }) + (symbol ? ' ' + symbol : '');
}

// Add CSS for ripple effect
const rippleCSS = `
    <style>
    .btn {
        position: relative;
        overflow: hidden;
    }
    
    .ripple {
        position: absolute;
        border-radius: 50%;
        background: rgba(255, 255, 255, 0.6);
        transform: scale(0);
        animation: ripple-animation 0.6s linear;
        pointer-events: none;
    }
    
    @keyframes ripple-animation {
        to {
            transform: scale(4);
            opacity: 0;
        }
    }
    </style>
`;

$('head').append(rippleCSS);

// Error handling for AJAX requests
$(document).ajaxError(function(event, xhr, settings, thrownError) {
    console.error('AJAX Error:', {
        url: settings.url,
        status: xhr.status,
        error: thrownError
    });
    
    if (xhr.status === 0) {
        showToast('Không thể kết nối đến server', 'danger');
    } else if (xhr.status === 500) {
        showToast('Lỗi server nội bộ', 'danger');
    } else if (xhr.status === 404) {
        showToast('Không tìm thấy API endpoint', 'warning');
    } else {
        showToast('Có lỗi xảy ra: ' + thrownError, 'danger');
    }
});

// Global AJAX setup
$.ajaxSetup({
    beforeSend: function() {
        // Add loading state to buttons
        $('.btn:focus').prop('disabled', true);
    },
    complete: function() {
        // Remove loading state
        setTimeout(() => {
            $('.btn').prop('disabled', false);
        }, 1000);
    }
});

console.log('📱 Main JavaScript loaded successfully');
