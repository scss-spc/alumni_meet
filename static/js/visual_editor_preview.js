/**
 * Visual Editor Preview Client Script — Pure Inline In-Place Editor
 * Allows direct on-page editing of text elements and inline floating section controls without popups or new windows.
 * Dynamically resolves ADMIN_PATH_PREFIX to prevent 404 errors.
 */

document.addEventListener("DOMContentLoaded", function () {
    const editableSections = document.querySelectorAll("[data-editable-section]");
    if (editableSections.length === 0) return;

    // Detect current page from path
    let currentPage = "index";
    const path = window.location.pathname.toLowerCase();
    if (path.includes("meet")) currentPage = "meet";
    else if (path.includes("about")) currentPage = "about";
    else if (path.includes("contribute")) currentPage = "contribute";

    // Helper to dynamically resolve admin route prefix
    function getAdminPrefix() {
        try {
            if (window.parent && window.parent.ADMIN_PREFIX) {
                return window.parent.ADMIN_PREFIX.replace(/\/+$/, "");
            }
        } catch (e) {}

        if (window.ADMIN_PREFIX) {
            return window.ADMIN_PREFIX.replace(/\/+$/, "");
        }

        const urlParams = new URLSearchParams(window.location.search);
        if (urlParams.has("admin_prefix")) {
            return urlParams.get("admin_prefix").replace(/\/+$/, "");
        }

        return "/admin";
    }

    // Inject Toast Notification Container into Preview Body
    const toastContainer = document.createElement("div");
    toastContainer.className = "inline-editor-toast-container";
    document.body.appendChild(toastContainer);

    function showInlineToast(message, type = "success") {
        const toast = document.createElement("div");
        toast.className = `inline-editor-toast toast-${type}`;
        toast.innerHTML = type === "success" ? `✓ ${message}` : `⚠ ${message}`;
        toastContainer.appendChild(toast);
        setTimeout(() => toast.classList.add("show"), 10);
        setTimeout(() => {
            toast.classList.remove("show");
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    editableSections.forEach((section, idx) => {
        const sectionKey = section.getAttribute("data-editable-section") || `section_${idx}`;
        const sectionTitle = section.getAttribute("data-section-title") || "Section";

        // Find editable text elements inside section
        const textElements = section.querySelectorAll("h1, h2, h3, h4, p, .eyebrow, .hero-card-badge, .badge, [data-field-key]");

        textElements.forEach(el => {
            if (el.tagName === "BUTTON" || el.classList.contains("btn") || el.closest(".btn-group")) {
                return;
            }

            el.contentEditable = "true";
            el.spellcheck = false;
            el.setAttribute("data-inline-editable", "true");

            el.addEventListener("focus", function () {
                section.classList.add("section-preview-active");
                el.classList.add("text-editing-active");
            });

            el.addEventListener("blur", function () {
                el.classList.remove("text-editing-active");
            });

            el.addEventListener("keydown", function (e) {
                if (e.key === "Enter" && ["H1", "H2", "H3", "H4", "SPAN"].includes(el.tagName)) {
                    e.preventDefault();
                    el.blur();
                }
            });
        });

        // Build Inline Floating Control Toolbar
        const toolbar = document.createElement("div");
        toolbar.className = "inline-section-toolbar";
        toolbar.innerHTML = `
            <div class="toolbar-info">
                <span class="toolbar-icon">✏️</span>
                <span class="toolbar-title">${sectionTitle}</span>
            </div>
            <div class="toolbar-actions">
                <button type="button" class="btn-inline-save" title="Save changes for this section directly">
                    💾 Save Section
                </button>
            </div>
        `;

        section.prepend(toolbar);
        toolbar.addEventListener("click", e => e.stopPropagation());

        const saveBtn = toolbar.querySelector(".btn-inline-save");
        saveBtn.addEventListener("click", function (e) {
            e.preventDefault();
            e.stopPropagation();

            saveBtn.disabled = true;
            saveBtn.textContent = "⏳ Saving...";

            const updates = {};
            const fieldsInSec = section.querySelectorAll("[data-field-key]");

            if (fieldsInSec.length > 0) {
                fieldsInSec.forEach(f => {
                    const key = f.getAttribute("data-field-key");
                    const val = f.isContentEditable ? f.innerText.trim() : (f.value || f.innerText.trim());
                    if (key) updates[key] = val;
                });
            } else {
                textElements.forEach((el, index) => {
                    const key = el.getAttribute("data-field-key") || `${sectionKey}_field_${index}`;
                    updates[key] = el.innerText.trim();
                });
            }

            const adminPrefix = getAdminPrefix();
            const endpoint = `${adminPrefix}/sections/ajax-update`;

            fetch(endpoint, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-Requested-With": "XMLHttpRequest"
                },
                body: JSON.stringify({
                    page: currentPage,
                    updates: updates
                })
            })
            .then(res => {
                if (!res.ok) {
                    throw new Error(`Server returned HTTP ${res.status}`);
                }
                return res.json();
            })
            .then(data => {
                saveBtn.disabled = false;
                saveBtn.textContent = "💾 Save Section";
                if (data.success) {
                    showInlineToast(data.message || "Section saved successfully!", "success");
                    section.classList.remove("section-preview-active");
                } else {
                    showInlineToast(data.error || "Failed to save section.", "danger");
                }
            })
            .catch(err => {
                saveBtn.disabled = false;
                saveBtn.textContent = "💾 Save Section";
                showInlineToast(`Save error: ${err.message}`, "danger");
            });
        });
    });
});
