/*
   Alumni Network System - Main Javascript File
   Handles global actions like theme toggles, mobile sidebar, and notifications polling.
*/

document.addEventListener("DOMContentLoaded", () => {
    // 1. Theme Toggle Logic
    const themeToggleBtn = document.getElementById("theme-toggle-btn");
    const themeIcon = themeToggleBtn ? themeToggleBtn.querySelector("i") : null;
    
    // Check local storage for preference, fallback to light
    const currentTheme = localStorage.getItem("theme") || "light";
    document.documentElement.setAttribute("data-theme", currentTheme);
    updateThemeIcon(currentTheme);

    if (themeToggleBtn) {
        themeToggleBtn.addEventListener("click", () => {
            const theme = document.documentElement.getAttribute("data-theme");
            const newTheme = theme === "dark" ? "light" : "dark";
            document.documentElement.setAttribute("data-theme", newTheme);
            localStorage.setItem("theme", newTheme);
            updateThemeIcon(newTheme);
        });
    }

    function updateThemeIcon(theme) {
        if (!themeIcon) return;
        if (theme === "dark") {
            themeIcon.className = "fas fa-sun";
        } else {
            themeIcon.className = "fas fa-moon";
        }
    }

    // 2. Mobile Sidebar Toggle
    const menuToggle = document.getElementById("menu-toggle");
    const sidebar = document.querySelector(".sidebar");

    if (menuToggle && sidebar) {
        menuToggle.addEventListener("click", () => {
            sidebar.classList.toggle("open");
        });
        
        // Close sidebar if user clicks outside of it on mobile
        document.addEventListener("click", (e) => {
            if (!sidebar.contains(e.target) && !menuToggle.contains(e.target) && sidebar.classList.contains("open")) {
                sidebar.classList.remove("open");
            }
        });
    }

    // 3. Auto-Dismiss Flash Alerts
    const alerts = document.querySelectorAll(".alert");
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = "0";
            alert.style.transform = "translateX(100%)";
            alert.style.transition = "all 0.5s ease";
            setTimeout(() => alert.remove(), 500);
        }, 5000);
    });

    // 4. Notifications Polling Setup
    // Only poll if the user is logged in (i.e. if sidebar is present indicating dashboard state)
    if (sidebar) {
        pollNotifications();
        setInterval(pollNotifications, 15000); // Check every 15 seconds
    }
});

// Notifications Polling Function
function pollNotifications() {
    fetch("/api/notifications")
        .then(response => {
            if (response.status === 201 || response.status === 200) {
                return response.json();
            }
            throw new Error("Unable to fetch notifications");
        })
        .then(data => {
            if (data.success) {
                const notifBadge = document.getElementById("notif-badge");
                if (notifBadge) {
                    if (data.count > 0) {
                        notifBadge.textContent = data.count;
                        notifBadge.style.display = "inline-flex";
                    } else {
                        notifBadge.style.display = "none";
                    }
                }
                
                // Dynamically update notification list in the dashboard if we are on dashboard page
                const notifListElement = document.getElementById("notif-list-dynamic");
                if (notifListElement && data.notifications.length > 0) {
                    notifListElement.innerHTML = "";
                    data.notifications.slice(0, 5).forEach(n => {
                        const li = document.createElement("li");
                        li.className = "activity-item";
                        li.innerHTML = `
                            <div><i class="fas fa-bell accent-text" style="margin-right: 0.5rem;"></i>${n.message}</div>
                            <div class="activity-time">${n.created_at}</div>
                        `;
                        notifListElement.appendChild(li);
                    });
                }
            }
        })
        .catch(err => console.log("Notification Polling Error:", err));
}
