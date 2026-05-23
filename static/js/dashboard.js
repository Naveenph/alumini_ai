/*
   Alumni Network System - Dashboard Analytics Charts
   Fetches analytics from API and renders Chart.js charts.
*/

document.addEventListener("DOMContentLoaded", () => {
    const userChartCanvas = document.getElementById("userDistributionChart");
    const activityChartCanvas = document.getElementById("activityMetricsChart");

    if (userChartCanvas || activityChartCanvas) {
        fetch("/api/admin/analytics")
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    if (userChartCanvas) {
                        renderUserDistributionChart(userChartCanvas, data.distribution);
                    }
                    if (activityChartCanvas) {
                        renderActivityMetricsChart(activityChartCanvas, data.activities);
                    }
                }
            })
            .catch(err => console.error("Error loading analytics data:", err));
    }
});

function renderUserDistributionChart(canvas, distributionData) {
    const isDarkMode = document.documentElement.getAttribute("data-theme") === "dark";
    const textThemeColor = isDarkMode ? "#94a3b8" : "#64748b";

    new Chart(canvas, {
        type: 'doughnut',
        data: {
            labels: ['Alumni', 'Students'],
            datasets: [{
                data: [distributionData.alumni, distributionData.students],
                backgroundColor: [
                    'hsl(245, 80%, 60%)',
                    'hsl(270, 85%, 58%)'
                ],
                borderWidth: isDarkMode ? 2 : 1,
                borderColor: isDarkMode ? '#0f172a' : '#ffffff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        color: textThemeColor,
                        font: {
                            family: 'Outfit',
                            size: 13
                        }
                    }
                }
            },
            cutout: '65%'
        }
    });
}

function renderActivityMetricsChart(canvas, activityData) {
    const isDarkMode = document.documentElement.getAttribute("data-theme") === "dark";
    const textThemeColor = isDarkMode ? "#94a3b8" : "#64748b";
    const gridColor = isDarkMode ? "rgba(255,255,255,0.05)" : "rgba(0,0,0,0.05)";

    new Chart(canvas, {
        type: 'bar',
        data: {
            labels: ['Jobs Posted', 'Events Held', 'Webinars Hosted'],
            datasets: [{
                label: 'System Activity Count',
                data: [activityData.jobs, activityData.events, activityData.webinars],
                backgroundColor: [
                    'rgba(16, 185, 129, 0.85)',
                    'rgba(6, 182, 212, 0.85)',
                    'rgba(245, 158, 11, 0.85)'
                ],
                borderRadius: 8,
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                x: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        color: textThemeColor,
                        font: {
                            family: 'Outfit'
                        }
                    }
                },
                y: {
                    grid: {
                        color: gridColor
                    },
                    ticks: {
                        color: textThemeColor,
                        precision: 0,
                        font: {
                            family: 'Outfit'
                        }
                    }
                }
            }
        }
    });
}
