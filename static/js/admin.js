/**
 * SC&SS JNU Alumni Meet Platform — Admin Dashboard Scripts
 */

document.addEventListener("DOMContentLoaded", () => {
    // Modal helpers
    window.openModal = function(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.add("active");
        }
    };

    window.closeModal = function(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.remove("active");
        }
    };

    // Close modal on outside click
    document.querySelectorAll(".modal-overlay").forEach(overlay => {
        overlay.addEventListener("click", (e) => {
            if (e.target === overlay) {
                overlay.classList.remove("active");
            }
        });
    });

    // Verification modal triggers
    window.openVerifyModal = function(contribId, amount, name) {
        const modal = document.getElementById("verifyModal");
        if (modal) {
            const form = modal.querySelector("form");
            const prefix = window.ADMIN_PREFIX || "/admin";
            form.action = `${prefix}/contributions/${contribId}/verify`;
            document.getElementById("verifyContribId").textContent = contribId;
            document.getElementById("verifyAlumniName").textContent = name;
            document.getElementById("verifyAmount").textContent = amount;
            openModal("verifyModal");
        }
    };

    window.openRejectModal = function(contribId, amount, name) {
        const modal = document.getElementById("rejectModal");
        if (modal) {
            const form = modal.querySelector("form");
            const prefix = window.ADMIN_PREFIX || "/admin";
            form.action = `${prefix}/contributions/${contribId}/reject`;
            document.getElementById("rejectContribId").textContent = contribId;
            document.getElementById("rejectAlumniName").textContent = name;
            document.getElementById("rejectAmount").textContent = amount;
            openModal("rejectModal");
        }
    };

    window.openVolunteerModal = function(volunteer = null) {
        const modal = document.getElementById("volunteerModal");
        if (modal) {
            const idInput = document.getElementById("volId");
            const nameInput = document.getElementById("volFullName");
            const emailInput = document.getElementById("volEmail");
            const phoneInput = document.getElementById("volPhone");
            const roleInput = document.getElementById("volRole");
            const statusInput = document.getElementById("volStatus");
            const notesInput = document.getElementById("volNotes");

            if (volunteer) {
                document.getElementById("volModalTitle").textContent = "Edit Volunteer";
                idInput.value = volunteer.id || "";
                nameInput.value = volunteer.full_name || "";
                emailInput.value = volunteer.email || "";
                phoneInput.value = volunteer.phone || "";
                roleInput.value = volunteer.role || "";
                statusInput.value = volunteer.status || "active";
                notesInput.value = volunteer.notes || "";
            } else {
                document.getElementById("volModalTitle").textContent = "Add New Volunteer";
                idInput.value = "";
                nameInput.value = "";
                emailInput.value = "";
                phoneInput.value = "";
                roleInput.value = "";
                statusInput.value = "active";
                notesInput.value = "";
            }
            openModal("volunteerModal");
        }
    };

    window.openDeleteAlumnusModal = function(alumniId, alumniName) {
        const modal = document.getElementById("deleteSingleAlumnusModal");
        if (modal) {
            const form = modal.querySelector("form");
            const prefix = window.ADMIN_PREFIX || "/admin";
            form.action = `${prefix}/alumni/${alumniId}/delete`;
            const nameEl = document.getElementById("deleteAlumnusTargetName");
            if (nameEl) {
                nameEl.textContent = `${alumniName} (ID #${alumniId})`;
            }
            openModal("deleteSingleAlumnusModal");
        }
    };

    window.openDeleteContribModal = function(contribId, amount, name) {
        const modal = document.getElementById("deleteContribModal");
        if (modal) {
            const form = modal.querySelector("form");
            const prefix = window.ADMIN_PREFIX || "/admin";
            form.action = `${prefix}/contributions/${contribId}/delete`;
            const infoEl = document.getElementById("deleteContribInfo");
            if (infoEl) {
                infoEl.textContent = `#${contribId} — ${amount} by ${name}`;
            }
            openModal("deleteContribModal");
        }
    };
});


