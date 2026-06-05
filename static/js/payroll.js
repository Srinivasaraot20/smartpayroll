document.addEventListener('DOMContentLoaded', function() {
    // Handle payslip download
    const downloadButtons = document.querySelectorAll('.download-payslip');
    if (downloadButtons.length > 0) {
        downloadButtons.forEach(button => {
            button.addEventListener('click', function(e) {
                e.preventDefault();
                const payslipId = this.getAttribute('data-id');
                downloadPayslip(payslipId);
            });
        });
    }
    
    // Handle payroll processing
    const processPayrollForm = document.getElementById('processPayrollForm');
    if (processPayrollForm) {
        processPayrollForm.addEventListener('submit', function(e) {
            if (!confirm('Are you sure you want to process payroll for the selected month? This will generate payslips for all active employees.')) {
                e.preventDefault();
            }
        });
    }
    
    // Initialize salary breakdown chart
    const salaryBreakdownChart = document.getElementById('salaryBreakdownChart');
    if (salaryBreakdownChart) {
        initSalaryBreakdownChart(salaryBreakdownChart);
    }
});

function downloadPayslip(payslipId) {
    // Open a link to download the payslip directly as PDF
    window.location.href = `/api/download/payslip/${payslipId}`;
}

function generatePayslipPDF(payslipData) {
    // This is a mock function as we can't generate real PDFs in this example
    // In a real application, this would use a library like jsPDF or call a server endpoint
    
    // Create a "fake" download by displaying the data
    const payslipWindow = window.open('', '_blank');
    
    if (!payslipWindow) {
        alert('Please allow popups for this website to download payslips');
        return;
    }
    
    // Format payslip data in a printable format
    payslipWindow.document.write(`
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Payslip - ${payslipData.month}/${payslipData.year}</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                }
                h1, h2 {
                    text-align: center;
                    color: #333;
                }
                .payslip-header {
                    text-align: center;
                    margin-bottom: 30px;
                }
                .company-name {
                    font-size: 24px;
                    font-weight: bold;
                    margin-bottom: 5px;
                }
                .payslip-title {
                    font-size: 18px;
                    margin-bottom: 20px;
                }
                .employee-details, .salary-details {
                    border: 1px solid #ddd;
                    padding: 15px;
                    margin-bottom: 20px;
                }
                .row {
                    display: flex;
                    margin-bottom: 10px;
                }
                .col {
                    flex: 1;
                }
                .label {
                    font-weight: bold;
                    color: #555;
                }
                .divider {
                    height: 1px;
                    background-color: #ddd;
                    margin: 15px 0;
                }
                .total {
                    font-weight: bold;
                    font-size: 18px;
                }
                .footer {
                    text-align: center;
                    margin-top: 40px;
                    font-size: 12px;
                    color: #777;
                }
                @media print {
                    .no-print {
                        display: none;
                    }
                }
            </style>
        </head>
        <body>
            <div class="payslip-header">
                <div class="company-name">PayrollPro Inc.</div>
                <div class="payslip-title">Salary Slip - ${getMonthName(payslipData.month)} ${payslipData.year}</div>
            </div>
            
            <div class="employee-details">
                <div class="row">
                    <div class="col">
                        <div class="label">Employee Name</div>
                        <div>${payslipData.employee_name}</div>
                    </div>
                    <div class="col">
                        <div class="label">Department</div>
                        <div>${payslipData.department}</div>
                    </div>
                </div>
                <div class="row">
                    <div class="col">
                        <div class="label">Designation</div>
                        <div>${payslipData.designation}</div>
                    </div>
                    <div class="col">
                        <div class="label">Payslip ID</div>
                        <div>#${payslipData.id}</div>
                    </div>
                </div>
            </div>
            
            <div class="salary-details">
                <div class="row">
                    <div class="col">
                        <div class="label">Earnings</div>
                    </div>
                    <div class="col">
                        <div class="label">Amount</div>
                    </div>
                </div>
                <div class="row">
                    <div class="col">Basic Salary</div>
                    <div class="col">$${payslipData.basic_salary.toFixed(2)}</div>
                </div>
                <div class="row">
                    <div class="col">Allowances</div>
                    <div class="col">$${payslipData.allowances.toFixed(2)}</div>
                </div>
                
                <div class="divider"></div>
                
                <div class="row">
                    <div class="col">
                        <div class="label">Deductions</div>
                    </div>
                    <div class="col">
                        <div class="label">Amount</div>
                    </div>
                </div>
                <div class="row">
                    <div class="col">PF Contribution</div>
                    <div class="col">$${payslipData.pf_contribution.toFixed(2)}</div>
                </div>
                <div class="row">
                    <div class="col">ESI Contribution</div>
                    <div class="col">$${payslipData.esi_contribution.toFixed(2)}</div>
                </div>
                <div class="row">
                    <div class="col">TDS (Tax)</div>
                    <div class="col">$${payslipData.tds.toFixed(2)}</div>
                </div>
                
                <div class="divider"></div>
                
                <div class="row total">
                    <div class="col">Net Salary</div>
                    <div class="col">$${payslipData.net_salary.toFixed(2)}</div>
                </div>
            </div>
            
            <div class="footer">
                This is a computer-generated document. No signature is required.
            </div>
            
            <div class="no-print" style="text-align: center; margin-top: 30px;">
                <button onclick="window.print()">Print Payslip</button>
                <button onclick="window.close()">Close</button>
            </div>
        </body>
        </html>
    `);
    
    payslipWindow.document.close();
}

function initSalaryBreakdownChart(canvas) {
    const ctx = canvas.getContext('2d');
    
    // Sample data - in a real app this would come from the server
    new Chart(ctx, {
        type: 'pie',
        data: {
            labels: ['Basic Salary', 'Allowances', 'PF Contribution', 'ESI', 'TDS'],
            datasets: [{
                data: [70, 10, 8, 4, 8],
                backgroundColor: [
                    '#0d6efd', // Basic salary
                    '#20c997', // Allowances
                    '#ffc107', // PF
                    '#fd7e14', // ESI
                    '#dc3545'  // TDS
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.raw || 0;
                            return `${label}: ${value}%`;
                        }
                    }
                }
            }
        }
    });
}

function getMonthName(monthNumber) {
    const months = [
        'January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December'
    ];
    return months[monthNumber - 1];
}
