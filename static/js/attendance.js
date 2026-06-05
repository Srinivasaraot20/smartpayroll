document.addEventListener('DOMContentLoaded', function() {
    // Calendar view for attendance
    initAttendanceCalendar();
    
    // Filter functionality
    const filterForm = document.getElementById('attendanceFilterForm');
    if (filterForm) {
        filterForm.addEventListener('submit', function(e) {
            // Form will submit normally, no need to prevent default
        });
    }
    
    // Date picker initialization
    const datePickers = document.querySelectorAll('.datepicker');
    if (datePickers.length > 0) {
        datePickers.forEach(function(picker) {
            picker.addEventListener('focus', function() {
                this.type = 'date';
            });
            picker.addEventListener('blur', function() {
                if (!this.value) {
                    this.type = 'text';
                }
            });
        });
    }
});

function initAttendanceCalendar() {
    const calendarEl = document.getElementById('attendanceCalendar');
    if (!calendarEl) return;
    
    // Get the current date
    const today = new Date();
    const currentMonth = today.getMonth();
    const currentYear = today.getFullYear();
    
    // Create calendar grid
    let calendarHTML = `
        <div class="calendar-header d-flex justify-content-between align-items-center mb-3">
            <button class="btn btn-sm btn-outline-secondary" id="prevMonth">&laquo; Prev</button>
            <h5 id="calendarMonthYear" class="m-0">${getMonthName(currentMonth)} ${currentYear}</h5>
            <button class="btn btn-sm btn-outline-secondary" id="nextMonth">Next &raquo;</button>
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
            <div id="calendarDaysGrid" class="calendar-days-grid">
                ${generateCalendarDays(currentMonth, currentYear)}
            </div>
        </div>
    `;
    
    calendarEl.innerHTML = calendarHTML;
    
    // Add event listeners for navigation buttons
    document.getElementById('prevMonth').addEventListener('click', function() {
        navigateMonth(-1);
    });
    
    document.getElementById('nextMonth').addEventListener('click', function() {
        navigateMonth(1);
    });
}

function generateCalendarDays(month, year) {
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
        
        // Determine attendance status for the day (this would come from server data in a real app)
        let attendanceClass = '';
        let attendanceStatus = '';
        
        // Just for demonstration - simulate some attendance data
        if (date <= today && !isWeekend) {
            const random = Math.random();
            if (random > 0.9) {
                attendanceClass = 'absent';
                attendanceStatus = 'Absent';
            } else if (random > 0.8) {
                attendanceClass = 'half-day';
                attendanceStatus = 'Half Day';
            } else if (random > 0.7) {
                attendanceClass = 'wfh';
                attendanceStatus = 'WFH';
            } else {
                attendanceClass = 'present';
                attendanceStatus = 'Present';
            }
        }
        
        // Add classes for styling
        let className = 'calendar-day';
        if (isToday) className += ' today';
        if (isWeekend) className += ' weekend';
        if (attendanceClass) className += ` ${attendanceClass}`;
        
        html += `
            <div class="${className}">
                <div class="day-number">${day}</div>
                ${attendanceStatus ? `<div class="attendance-status">${attendanceStatus}</div>` : ''}
            </div>
        `;
    }
    
    return html;
}

function navigateMonth(direction) {
    // Get the current displayed month/year
    const calendarTitle = document.getElementById('calendarMonthYear').textContent;
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
    document.getElementById('calendarMonthYear').textContent = `${getMonthName(newMonth)} ${newYear}`;
    document.getElementById('calendarDaysGrid').innerHTML = generateCalendarDays(newMonth, newYear);
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
