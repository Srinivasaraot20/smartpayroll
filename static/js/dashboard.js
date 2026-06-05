document.addEventListener('DOMContentLoaded', function() {
    // Initialize attendance chart if exists on page
    const attendanceChartEl = document.getElementById('attendanceChart');
    if (attendanceChartEl) {
        initAttendanceChart(attendanceChartEl);
    }

    // Initialize leave chart if exists on page
    const leaveChartEl = document.getElementById('leaveChart');
    if (leaveChartEl) {
        initLeaveChart(leaveChartEl);
    }

    // Initialize salary distribution chart if exists on page
    const salaryChartEl = document.getElementById('salaryDistributionChart');
    if (salaryChartEl) {
        initSalaryChart(salaryChartEl);
    }
});

function initAttendanceChart(canvas) {
    // Sample data - in a real app, this would come from the server
    const ctx = canvas.getContext('2d');
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
            datasets: [{
                label: 'Attendance %',
                data: [95, 92, 88, 96, 94, 90, 98, 97, 95, 93, 96, 92],
                borderColor: '#0d6efd',
                backgroundColor: 'rgba(13, 110, 253, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    mode: 'index',
                    intersect: false
                }
            },
            scales: {
                y: {
                    min: 0,
                    max: 100,
                    ticks: {
                        callback: function(value) {
                            return value + '%';
                        }
                    }
                }
            }
        }
    });
}

function initLeaveChart(canvas) {
    // Sample data - in a real app, this would come from the server
    const ctx = canvas.getContext('2d');
    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Annual', 'Sick', 'Casual', 'Unpaid'],
            datasets: [{
                data: [5, 3, 2, 1],
                backgroundColor: [
                    '#0d6efd',
                    '#dc3545',
                    '#ffc107',
                    '#6c757d'
                ]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}

function initSalaryChart(canvas) {
    // Sample data - in a real app, this would come from the server
    const ctx = canvas.getContext('2d');
    new Chart(ctx, {
        type: 'pie',
        data: {
            labels: ['Basic Salary', 'Allowances', 'PF', 'ESI', 'TDS'],
            datasets: [{
                data: [75, 10, 5, 2, 8],
                backgroundColor: [
                    '#0d6efd',
                    '#198754',
                    '#dc3545',
                    '#ffc107',
                    '#6c757d'
                ]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}
