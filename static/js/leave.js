document.addEventListener('DOMContentLoaded', function() {
    // Initialize leave calendar
    initLeaveCalendar();
    
    // Handle date validation in leave application form
    const leaveForm = document.getElementById('leaveApplicationForm');
    if (leaveForm) {
        const startDateInput = document.getElementById('start_date');
        const endDateInput = document.getElementById('end_date');
        
        if (startDateInput && endDateInput) {
            // Set minimum date to today
            const today = new Date().toISOString().split('T')[0];
            startDateInput.min = today;
            endDateInput.min = today;
            
            // Update end date min when start date changes
            startDateInput.addEventListener('change', function() {
                endDateInput.min = this.value;
                // If end date is before start date, update it
                if (endDateInput.value && endDateInput.value < this.value) {
                    endDateInput.value = this.value;
                }
            });
        }
    }
    
    // Handle leave approval/rejection
    const actionButtons = document.querySelectorAll('.leave-action-btn');
    if (actionButtons.length > 0) {
        actionButtons.forEach(button => {
            button.addEventListener('click', function() {
                const leaveId = this.getAttribute('data-id');
                const action = this.getAttribute('data-action');
                
                if (action === 'approve') {
                    approveLeave(leaveId);
                } else if (action === 'reject') {
                    rejectLeave(leaveId);
                }
            });
        });
    }
});

function initLeaveCalendar() {
    const calendarEl = document.getElementById('leaveCalendar');
    if (!calendarEl) return;
    
    // Get the current date
    const today = new Date();
    const currentMonth = today.getMonth();
    const currentYear = today.getFullYear();
    
    // Create calendar grid
    let calendarHTML = `
        <div class="calendar-header d-flex justify-content-between align-items-center mb-3">
            <button class="btn btn-sm btn-outline-secondary" id="prevMonthLeave">&laquo; Prev</button>
            <h5 id="leaveCalendarMonth" class="m-0">${getMonthName(currentMonth)} ${currentYear}</h5>
            <button class="btn btn-sm btn-outline-secondary" id="nextMonthLeave">Next &raquo;</button>
        </div>
        <div class="calendar-grid">
            <div class="calendar-days-header">
                <div>Sun</div>
                <div>Mon</div>
                <div>Tue</div>
                <div>Wed</div>
                <div>Thu</div>
                <div>Fri</div>
                <div>Sat</div>
            </div>
            <div id="leaveCalendarGrid" class="calendar-days-grid">
                ${generateLeaveCalendar(currentMonth, currentYear)}
            </div>
        </div>
    `;
    
    calendarEl.innerHTML = calendarHTML;
    
    // Add event listeners for navigation buttons
    document.getElementById('prevMonthLeave').addEventListener('click', function() {
        navigateLeaveMonth(-1);
    });
    
    document.getElementById('nextMonthLeave').addEventListener('click', function() {
        navigateLeaveMonth(1);
    });
}

function generateLeaveCalendar(month, year) {
    // Create a date object for the first day of the month
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    
    // Get the starting day of the week (0 = Sunday, 6 = Saturday)
    const startingDay = firstDay.getDay();
    
    // Get the total number of days in the month
    const monthLength = lastDay.getDate();
    
    // Get the current date for highlighting today
    const today = new Date();
    
    let html = '';
    
    // Create empty cells for days before the first day of the month
    for (let i = 0; i < startingDay; i++) {
        html += '<div class="calendar-day empty"></div>';
    }
    
    // Create cells for each day of the month
    for (let day = 1; day <= monthLength; day++) {
        const date = new Date(year, month, day);
        const isToday = date.getDate() === today.getDate() && 
                       date.getMonth() === today.getMonth() && 
                       date.getFullYear() === today.getFullYear();
        
        const isWeekend = date.getDay() === 0 || date.getDay() === 6;
        
        // Determine leave status for the day (this would come from server data in a real app)
        let leaveClass = '';
        let leaveStatus = '';
        
        // Just for demonstration - simulate some leave data
        // In a real app, this would be actual leave data from the server
        if (day === 15 || day === 16 || day === 17) {
            leaveClass = 'annual-leave';
            leaveStatus = 'Annual';
        } else if (day === 25) {
            leaveClass = 'sick-leave';
            leaveStatus = 'Sick';
        } else if (day === 10) {
            leaveClass = 'pending-leave';
            leaveStatus = 'Pending';
        }
        
        // Add classes for styling
        let className = 'calendar-day';
        if (isToday) className += ' today';
        if (isWeekend) className += ' weekend';
        if (leaveClass) className += ` ${leaveClass}`;
        
        html += `
            <div class="${className}">
                <div class="day-number">${day}</div>
                ${leaveStatus ? `<div class="leave-status">${leaveStatus}</div>` : ''}
            </div>
        `;
    }
    
    return html;
}

function navigateLeaveMonth(direction) {
    // Get the current displayed month/year
    const calendarTitle = document.getElementById('leaveCalendarMonth').textContent;
    const [monthName, year] = calendarTitle.split(' ');
    
    // Convert month name to number (0-11)
    const month = getMonthNumber(monthName);
    
    // Calculate new month and year
    let newMonth = month + direction;
    let newYear = parseInt(year);
    
    if (newMonth < 0) {
        newMonth = 11;
        newYear--;
    } else if (newMonth > 11) {
        newMonth = 0;
        newYear++;
    }
    
    // Update the calendar
    document.getElementById('leaveCalendarMonth').textContent = `${getMonthName(newMonth)} ${newYear}`;
    document.getElementById('leaveCalendarGrid').innerHTML = generateLeaveCalendar(newMonth, newYear);
}

function approveLeave(leaveId) {
    const commentModal = document.getElementById('leaveResponseModal');
    if (commentModal) {
        // Set the leave ID and action in the modal form
        document.getElementById('leave_id').value = leaveId;
        document.getElementById('status').value = 'approved';
        
        // Show the modal
        const modal = new bootstrap.Modal(commentModal);
        modal.show();
    } else {
        // If no modal exists, submit directly
        if (confirm('Are you sure you want to approve this leave request?')) {
            document.getElementById('leaveForm' + leaveId).submit();
        }
    }
}

function rejectLeave(leaveId) {
    const commentModal = document.getElementById('leaveResponseModal');
    if (commentModal) {
        // Set the leave ID and action in the modal form
        document.getElementById('leave_id').value = leaveId;
        document.getElementById('status').value = 'rejected';
        
        // Show the modal
        const modal = new bootstrap.Modal(commentModal);
        modal.show();
    } else {
        // If no modal exists, submit directly
        if (confirm('Are you sure you want to reject this leave request?')) {
            document.getElementById('leaveForm' + leaveId).submit();
        }
    }
}

function getMonthName(monthNumber) {
    const months = [
        'January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December'
    ];
    return months[monthNumber];
}

function getMonthNumber(monthName) {
    const months = [
        'January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December'
    ];
    return months.indexOf(monthName);
}
