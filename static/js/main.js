// Educational Management System - Client Side Script

document.addEventListener('DOMContentLoaded', function () {
    // Enable Bootstrap tooltips if any
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Auto-dismiss alerts after 5 seconds
    setTimeout(function () {
        var alerts = document.querySelectorAll('.alert-dismissible');
        alerts.forEach(function (alert) {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);
});

// Demo credential filler function for login page
function fillLogin(username, password) {
    var uField = document.getElementById('username');
    var pField = document.getElementById('password');
    if (uField && pField) {
        uField.value = username;
        pField.value = password;
        uField.focus();
    }
}

