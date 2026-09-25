/**
 * SC&SS JNU Alumni Meet Platform — Public Frontend Scripts
 * SC&SS Editorial Heritage Single Theme Architecture
 * Responsive Hamburger Drawer & Cross-device Optimization
 */

document.addEventListener("DOMContentLoaded", () => {
    // Mobile navigation hamburger toggle (Section 42.3 & Responsive Contract)
    const navToggle = document.getElementById("navToggle") || document.querySelector(".nav-toggle");
    const navLinks = document.getElementById("navLinks") || document.querySelector(".nav-links");

    function closeMobileNav() {
        if (navLinks && navToggle) {
            navLinks.classList.remove("show");
            navToggle.classList.remove("active");
            navToggle.setAttribute("aria-expanded", "false");
        }
    }

    function openMobileNav() {
        if (navLinks && navToggle) {
            navLinks.classList.add("show");
            navToggle.classList.add("active");
            navToggle.setAttribute("aria-expanded", "true");
        }
    }

    if (navToggle && navLinks) {
        navToggle.addEventListener("click", (e) => {
            e.stopPropagation();
            const isCurrentlyOpen = navLinks.classList.contains("show");
            if (isCurrentlyOpen) {
                closeMobileNav();
            } else {
                openMobileNav();
            }
        });

        // Close when clicking any nav link inside drawer
        navLinks.querySelectorAll(".nav-link, .btn").forEach(link => {
            link.addEventListener("click", () => {
                closeMobileNav();
            });
        });

        // Close on clicking outside
        document.addEventListener("click", (e) => {
            if (navLinks.classList.contains("show") && 
                !navLinks.contains(e.target) && 
                !navToggle.contains(e.target)) {
                closeMobileNav();
            }
        });

        // Close on Escape key
        document.addEventListener("keydown", (e) => {
            if (e.key === "Escape" && navLinks.classList.contains("show")) {
                closeMobileNav();
                navToggle.focus();
            }
        });
    }

    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll(".alert");
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.transition = "opacity 0.4s ease, transform 0.4s ease";
            alert.style.opacity = "0";
            alert.style.transform = "translateY(-10px)";
            setTimeout(() => alert.remove(), 400);
        }, 5000);
    });

    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener("click", function(e) {
            const targetId = this.getAttribute("href");
            if (targetId && targetId !== "#") {
                const targetElement = document.querySelector(targetId);
                if (targetElement) {
                    e.preventDefault();
                    closeMobileNav();
                    targetElement.scrollIntoView({ behavior: "smooth", block: "start" });
                }
            }
        });
    });

    // Site Header scroll glass elevation toggle
    const siteHeader = document.querySelector(".site-header");
    if (siteHeader) {
        window.addEventListener("scroll", () => {
            if (window.scrollY > 20) {
                siteHeader.classList.add("is-scrolled");
            } else {
                siteHeader.classList.remove("is-scrolled");
            }
        }, { passive: true });
    }

    // Section Scroll Reveal & Staggered Animations
    function initScrollAnimations() {
        // Tag page sections for smooth reveal
        const animateTargets = document.querySelectorAll(
            ".hero, .section, .timeline-section, .cta-banner, " +
            ".tracker-spotlight-card, .privacy-tiers-explainer, " +
            ".tracker-main-card, .supporter-roll-container, .timeline-node"
        );

        animateTargets.forEach(el => {
            if (!el.classList.contains("reveal-on-scroll")) {
                el.classList.add("reveal-on-scroll");
            }
        });

        // Set stagger indices for multi-item grid components
        document.querySelectorAll(
            ".grid-2, .grid-3, .tracker-kpi-grid, .supporter-cards-grid, " +
            ".then-now-grid, .tracker-metrics-4grid"
        ).forEach(grid => {
            grid.classList.add("reveal-stagger-container");
            Array.from(grid.children).forEach((child, index) => {
                child.classList.add("reveal-stagger-child");
                child.style.setProperty("--stagger-index", index % 6);
            });
        });

        // IntersectionObserver for scroll-triggered entrance
        if ("IntersectionObserver" in window) {
            const observerOptions = {
                root: null,
                rootMargin: "0px 0px -40px 0px",
                threshold: 0.08
            };

            const observer = new IntersectionObserver((entries, obs) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        entry.target.classList.add("is-visible");
                        obs.unobserve(entry.target);
                    }
                });
            }, observerOptions);

            const isEditPreview = Boolean(window.parent !== window || document.querySelector("[data-editable-section]"));

            document.querySelectorAll(".reveal-on-scroll, .reveal-stagger-container, .reveal-stagger-child").forEach(el => {
                const rect = el.getBoundingClientRect();
                if (rect.top < window.innerHeight || isEditPreview) {
                    el.classList.add("is-visible");
                } else {
                    observer.observe(el);
                }
            });
        } else {
            // Fallback for non-supporting browsers
            document.querySelectorAll(".reveal-on-scroll, .reveal-stagger-container, .reveal-stagger-child").forEach(el => {
                el.classList.add("is-visible");
            });
        }
    }

    initScrollAnimations();
});
