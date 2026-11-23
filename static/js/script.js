// Dynamic BMI Calculator and Form Enhancements
document.addEventListener("DOMContentLoaded", function () {
    const heightInput = document.getElementById("height");
    const weightInput = document.getElementById("weight");
    const bmiDisplay = document.getElementById("bmi-display");
    const bmiBadge = document.getElementById("bmi-badge");

    function updateBMI() {
        if (!heightInput || !weightInput || !bmiDisplay) return;

        const h = parseFloat(heightInput.value);
        const w = parseFloat(weightInput.value);

        if (h > 50 && w > 20) {
            const h_m = h / 100.0;
            const bmi = (w / (h_m * h_m)).toFixed(1);
            bmiDisplay.textContent = bmi;

            let category = "Normal";
            let badgeClass = "bg-success";

            if (bmi < 18.5) {
                category = "Underweight";
                badgeClass = "bg-secondary";
            } else if (bmi <= 24.9) {
                category = "Normal";
                badgeClass = "bg-success";
            } else if (bmi <= 29.9) {
                category = "Overweight";
                badgeClass = "bg-warning text-dark";
            } else {
                category = "Obese";
                badgeClass = "bg-danger";
            }

            if (bmiBadge) {
                bmiBadge.textContent = category;
                bmiBadge.className = "badge ms-2 " + badgeClass;
                bmiBadge.style.display = "inline-block";
            }
        } else {
            bmiDisplay.textContent = "--";
            if (bmiBadge) bmiBadge.style.display = "none";
        }
    }

    if (heightInput && weightInput) {
        heightInput.addEventListener("input", updateBMI);
        weightInput.addEventListener("input", updateBMI);
        updateBMI();
    }

    // Questionnaire Progress tracking
    const form = document.getElementById("questionnaire-form");
    if (form) {
        const inputs = form.querySelectorAll("input, select");
        const progressBar = document.getElementById("questionnaire-progress");
        const progressCount = document.getElementById("answered-count");

        function updateProgress() {
            // Distinct group names in the form
            const countedFields = [
                "age", "gender", "height", "weight", "family_history",
                "frequent_thirst", "frequent_urination", "fatigue",
                "unexplained_weight_loss", "slow_healing", "blurry_vision",
                "exercise_daily", "high_bp"
            ];

            let answered = 0;
            countedFields.forEach(field => {
                const elements = form.elements[field];
                if (!elements) return;

                if (elements.type === "radio" || elements.length > 1) {
                    const checked = form.querySelector(`input[name="${field}"]:checked`);
                    if (checked) answered++;
                } else if (elements.value && elements.value.trim() !== "") {
                    answered++;
                }
            });

            const percent = Math.round((answered / countedFields.length) * 100);
            if (progressBar) progressBar.style.width = percent + "%";
            if (progressCount) progressCount.textContent = `${answered} of ${countedFields.length} completed`;
        }

        form.addEventListener("change", updateProgress);
        form.addEventListener("input", updateProgress);
        updateProgress();
    }

    // Fill Sample Data Button Handler
    const fillSampleBtn = document.getElementById("fill-sample-btn");
    if (fillSampleBtn && form) {
        fillSampleBtn.addEventListener("click", function () {
            // Populate realistic demonstration sample values
            if (form.elements["name"]) form.elements["name"].value = "Priya Raman";
            if (form.elements["age"]) form.elements["age"].value = 46;
            if (form.elements["gender"]) form.elements["gender"].value = "Female";
            if (form.elements["height"]) form.elements["height"].value = 162;
            if (form.elements["weight"]) form.elements["weight"].value = 73.5;

            // Health History & Symptoms Radios
            const sampleRadioValues = {
                "family_history": "yes",
                "exercise_daily": "no",
                "high_bp": "yes",
                "frequent_thirst": "yes",
                "frequent_urination": "yes",
                "fatigue": "yes",
                "unexplained_weight_loss": "no",
                "slow_healing": "no",
                "blurry_vision": "no"
            };

            for (const [name, val] of Object.entries(sampleRadioValues)) {
                const radio = form.querySelector(`input[name="${name}"][value="${val}"]`);
                if (radio) radio.checked = true;
            }

            // Trigger updates for BMI calculation and progress bar
            updateBMI();
            if (typeof updateProgress === "function") updateProgress();
        });
    }

    // Initialize all Bootstrap 5 Tooltips across the document
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    const tooltips = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));

    // Theme Management (Light / Dark mode)
    const themeToggleBtn = document.getElementById("theme-toggle");
    const themeToggleIcon = document.getElementById("theme-toggle-icon");

    function getPreferredTheme() {
        try {
            const saved = localStorage.getItem("diaguard_theme");
            if (saved === "dark" || saved === "light") return saved;
        } catch (e) {}
        if (window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches) {
            return "dark";
        }
        return "light";
    }

    function updateThemeUI(theme) {
        if (!themeToggleBtn || !themeToggleIcon) return;
        if (theme === "dark") {
            themeToggleIcon.className = "bi bi-sun-fill text-warning";
            themeToggleBtn.setAttribute("aria-label", "Switch to light mode");
            themeToggleBtn.setAttribute("title", "Switch to light mode");
            themeToggleBtn.setAttribute("data-bs-original-title", "Switch to light mode");
        } else {
            themeToggleIcon.className = "bi bi-moon-stars-fill text-secondary";
            themeToggleBtn.setAttribute("aria-label", "Switch to dark mode");
            themeToggleBtn.setAttribute("title", "Switch to dark mode");
            themeToggleBtn.setAttribute("data-bs-original-title", "Switch to dark mode");
        }
    }

    function updateChartsForTheme(theme) {
        if (typeof Chart === "undefined") return;

        const isDark = (theme === "dark");
        const gridColor = isDark ? "#334155" : "#e2e8f0";
        const textColor = isDark ? "#94a3b8" : "#64748b";

        // Update default Chart.js styling
        Chart.defaults.color = textColor;
        Chart.defaults.borderColor = gridColor;

        // Iterate all active Chart instances and update scales & legend
        if (Chart.instances) {
            Object.values(Chart.instances).forEach(chart => {
                if (chart.options.scales) {
                    Object.values(chart.options.scales).forEach(scale => {
                        if (scale.grid) scale.grid.color = gridColor;
                        if (scale.ticks) scale.ticks.color = textColor;
                        if (scale.title) scale.title.color = textColor;
                    });
                }
                if (chart.options.plugins && chart.options.plugins.legend) {
                    if (chart.options.plugins.legend.labels) {
                        chart.options.plugins.legend.labels.color = textColor;
                    }
                }
                // Custom handling for risk gauge background slice
                if (chart.canvas && chart.canvas.id === "riskGaugeChart") {
                    if (chart.data.datasets && chart.data.datasets[0]) {
                        chart.data.datasets[0].backgroundColor[1] = isDark ? "#334155" : "#e9ecef";
                    }
                }
                chart.update();
            });
        }
    }

    function setTheme(theme) {
        document.documentElement.setAttribute("data-bs-theme", theme);
        try {
            localStorage.setItem("diaguard_theme", theme);
        } catch (e) {}
        updateThemeUI(theme);
        updateChartsForTheme(theme);
    }

    // Initialize toggle UI state
    const currentTheme = document.documentElement.getAttribute("data-bs-theme") || getPreferredTheme();
    updateThemeUI(currentTheme);

    // Initial chart refresh after scripts load
    setTimeout(() => {
        updateChartsForTheme(currentTheme);
    }, 150);

    if (themeToggleBtn) {
        themeToggleBtn.addEventListener("click", function () {
            const activeTheme = document.documentElement.getAttribute("data-bs-theme") || "light";
            const nextTheme = activeTheme === "dark" ? "light" : "dark";
            setTheme(nextTheme);
        });
    }

    // Listen for OS system theme change if no explicit choice saved
    if (window.matchMedia) {
        window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", e => {
            try {
                if (!localStorage.getItem("diaguard_theme")) {
                    setTheme(e.matches ? "dark" : "light");
                }
            } catch (err) {}
        });
    }
});

