// Tripline Client Utilities — Vanilla JS, Zero External Libraries
// Handles: dismissible banner, copy-to-clipboard, client-side table search & filters, relative timestamps, mobile nav toggle.

document.addEventListener("DOMContentLoaded", () => {
    // 1. Dismissible Info Banner with localStorage wrapped in try/catch
    const banner = document.getElementById("info-banner");
    const bannerClose = document.getElementById("banner-close");
    if (banner && bannerClose) {
        try {
            if (localStorage.getItem("tripline_banner_dismissed") === "true") {
                banner.style.display = "none";
            } else {
                banner.style.display = "flex";
            }
        } catch (e) {
            banner.style.display = "flex";
        }

        bannerClose.addEventListener("click", () => {
            banner.style.display = "none";
            try {
                localStorage.setItem("tripline_banner_dismissed", "true");
            } catch (e) {
                // Ignore storage failure
            }
        });
    }

    // 2. Mobile Nav Toggle
    const mobileToggle = document.getElementById("nav-mobile-toggle");
    const navLinks = document.getElementById("nav-links");
    if (mobileToggle && navLinks) {
        mobileToggle.addEventListener("click", () => {
            navLinks.classList.toggle("is-open");
        });
    }

    // 3. Copy-to-Clipboard with visual feedback
    document.querySelectorAll("[data-copy]").forEach((btn) => {
        btn.addEventListener("click", async (e) => {
            e.preventDefault();
            const text = btn.getAttribute("data-copy");
            if (!text) return;

            try {
                await navigator.clipboard.writeText(text);
                const originalHtml = btn.innerHTML;
                btn.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#34d399" stroke-width="2"><polyline points="20 6 9 17 4 12"></polyline></svg>`;
                btn.setAttribute("title", "Copied!");
                setTimeout(() => {
                    btn.innerHTML = originalHtml;
                    btn.setAttribute("title", "Copy");
                }, 1500);
            } catch (err) {
                console.error("Clipboard copy failed:", err);
            }
        });
    });

    // 4. Client-side Search and Filter for Tables
    const searchInputs = document.querySelectorAll("[data-table-search]");
    searchInputs.forEach((input) => {
        const tableCard = input.closest(".table-card");
        if (!tableCard) return;

        const table = tableCard.querySelector(".data-table");
        if (!table) return;

        const rows = table.querySelectorAll("tbody tr");
        const filterChips = tableCard.querySelectorAll("[data-filter]");

        let currentSearch = "";
        let currentFilter = "all";
        let currentColumn = "";

        const applyFilters = () => {
            rows.forEach((row) => {
                const text = row.textContent.toLowerCase();
                const matchesSearch = !currentSearch || text.includes(currentSearch);

                let matchesChip = true;
                if (currentFilter !== "all") {
                    if (currentColumn) {
                        const targetCell = row.querySelector(`[data-cell="${currentColumn}"]`);
                        matchesChip = targetCell && targetCell.textContent.toUpperCase().includes(currentFilter.toUpperCase());
                    } else {
                        matchesChip = text.includes(currentFilter.toLowerCase());
                    }
                }

                if (matchesSearch && matchesChip) {
                    row.style.display = "";
                } else {
                    row.style.display = "none";
                }
            });
        };

        input.addEventListener("input", (e) => {
            currentSearch = e.target.value.toLowerCase().trim();
            applyFilters();
        });

        filterChips.forEach((chip) => {
            chip.addEventListener("click", () => {
                filterChips.forEach((c) => c.classList.remove("active"));
                chip.classList.add("active");
                currentFilter = chip.getAttribute("data-filter") || "all";
                currentColumn = chip.getAttribute("data-col") || "";
                applyFilters();
            });
        });
    });

    // 5. Relative Timestamps with Absolute in title=
    const timeElements = document.querySelectorAll("[data-timestamp]");
    timeElements.forEach((el) => {
        const raw = el.getAttribute("data-timestamp");
        if (!raw || raw === "—" || raw === "None") return;

        try {
            const date = new Date(raw);
            if (isNaN(date.getTime())) return;

            el.setAttribute("title", date.toUTCString());

            const now = new Date();
            const diffSeconds = Math.floor((now - date) / 1000);

            if (diffSeconds < 60) {
                el.textContent = "just now";
            } else if (diffSeconds < 3600) {
                const mins = Math.floor(diffSeconds / 60);
                el.textContent = `${mins}m ago`;
            } else if (diffSeconds < 86400) {
                const hours = Math.floor(diffSeconds / 3600);
                el.textContent = `${hours}h ago`;
            } else {
                const days = Math.floor(diffSeconds / 86400);
                el.textContent = `${days}d ago`;
            }
        } catch (e) {
            // Keep original string if parsing fails
        }
    });
});
