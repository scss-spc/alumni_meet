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
            ".hero:not(.hero-night), .section, .timeline-section, .cta-banner, " +
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

    // Share invitation: native share sheet on phones, otherwise a small menu (copy / WhatsApp / email)
    const shareBoxes = document.querySelectorAll("[data-share]");
    const closeShareMenus = (except) => {
        shareBoxes.forEach(box => {
            if (box === except) return;
            const menu = box.querySelector(".share-menu");
            const trigger = box.querySelector("[data-share-trigger]");
            if (menu) menu.hidden = true;
            if (trigger) trigger.setAttribute("aria-expanded", "false");
        });
    };
    const copyText = async (text) => {
        if (navigator.clipboard && window.isSecureContext) {
            try {
                await navigator.clipboard.writeText(text);
                return;
            } catch (err) {
                // Clipboard API can be blocked (permissions, embedded views); fall back below.
            }
        }
        const field = document.createElement("textarea");
        field.value = text;
        field.setAttribute("readonly", "");
        field.style.position = "fixed";
        field.style.opacity = "0";
        document.body.appendChild(field);
        field.select();
        const ok = document.execCommand("copy");
        field.remove();
        if (!ok) throw new Error("copy failed");
    };
    shareBoxes.forEach(box => {
        const trigger = box.querySelector("[data-share-trigger]");
        const menu = box.querySelector(".share-menu");
        const status = box.querySelector(".share-status");
        const copyBtn = box.querySelector("[data-share-copy]");
        const data = { title: box.dataset.shareTitle, text: box.dataset.shareText, url: box.dataset.shareUrl };

        trigger.addEventListener("click", async (e) => {
            e.stopPropagation();
            const isTouch = window.matchMedia("(pointer: coarse)").matches;
            if (isTouch && navigator.share) {
                try {
                    await navigator.share(data);
                    return;
                } catch (err) {
                    if (err && err.name === "AbortError") return;
                }
            }
            const willOpen = menu.hidden;
            closeShareMenus(box);
            menu.hidden = !willOpen;
            trigger.setAttribute("aria-expanded", String(willOpen));
            if (status) status.textContent = "";
        });

        menu.addEventListener("click", (e) => e.stopPropagation());

        if (copyBtn) {
            copyBtn.addEventListener("click", async () => {
                try {
                    await copyText(data.url);
                    if (status) status.textContent = "Link copied!";
                } catch (err) {
                    if (status) status.textContent = "Copy failed. Select the link above.";
                }
            });
        }
    });
    if (shareBoxes.length) {
        document.addEventListener("click", () => closeShareMenus());
        document.addEventListener("keydown", (e) => {
            if (e.key === "Escape") closeShareMenus();
        });
    }

    // "Darkness unto Light" easter egg: clicking the moon brings a brief dawn over SC&SS
    const dawnHero = document.querySelector(".hero-night");
    const dawnToggle = document.querySelector("[data-dawn-toggle]");
    if (dawnHero && dawnToggle) {
        const live = dawnHero.querySelector("[data-dawn-live]");
        const sceneSvg = dawnHero.querySelector(".hero-scene-svg");
        const DAWN_MS = 9000;
        let dawnTimer = null;

        // Place the sun on the roofline of the perforated upper block (poster coords 560, 928), so it rises from behind the school.
        const placeSun = () => {
            const heroBox = dawnHero.getBoundingClientRect();
            let x = heroBox.width * 0.7;
            let y = heroBox.height * 0.45;
            let size = 90;
            if (sceneSvg && sceneSvg.getScreenCTM) {
                const ctm = sceneSvg.getScreenCTM();
                if (ctm) {
                    const pt = sceneSvg.createSVGPoint();
                    pt.x = 560;
                    pt.y = 928;
                    const p = pt.matrixTransform(ctm);
                    x = p.x - heroBox.left;
                    y = p.y - heroBox.top;
                    size = Math.max(40, 96 * ctm.a);
                }
            }
            dawnHero.style.setProperty("--sun-x", x.toFixed(1) + "px");
            dawnHero.style.setProperty("--sun-y", y.toFixed(1) + "px");
            dawnHero.style.setProperty("--sun-size", size.toFixed(1) + "px");
        };

        const setDawn = (on) => {
            clearTimeout(dawnTimer);
            if (on) {
                placeSun();
                // Re-measure once the scene's entrance animation has settled.
                setTimeout(placeSun, 1300);
            }
            dawnHero.classList.toggle("is-dawn", on);
            dawnToggle.setAttribute("aria-pressed", String(on));
            if (live) live.textContent = on ? "Tamaso mā jyotirgamaya: Darkness unto Light." : "";
            if (on) dawnTimer = setTimeout(() => setDawn(false), DAWN_MS);
        };

        dawnToggle.addEventListener("click", () => setDawn(!dawnHero.classList.contains("is-dawn")));
        window.addEventListener("resize", () => {
            if (dawnHero.classList.contains("is-dawn")) placeSun();
        });
    }

    // Hero night sky: scatter twinkling stars (decorative; skipped when motion is reduced)
    const starfield = document.querySelector("[data-starfield]");
    if (starfield && !window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
        const count = window.innerWidth < 640 ? 45 : 90;
        const frag = document.createDocumentFragment();
        for (let i = 0; i < count; i++) {
            const star = document.createElement("span");
            const sparkle = Math.random() < 0.08;
            star.className = sparkle ? "star star-sparkle" : "star";
            star.style.left = (Math.random() * 100).toFixed(2) + "%";
            star.style.top = (Math.random() * 70).toFixed(2) + "%";
            star.style.setProperty("--size", sparkle
                ? (10 + Math.random() * 8).toFixed(1) + "px"
                : (1 + Math.random() * 2).toFixed(1) + "px");
            star.style.setProperty("--dur", (2.2 + Math.random() * 3.8).toFixed(2) + "s");
            star.style.setProperty("--delay", (-Math.random() * 6).toFixed(2) + "s");
            frag.appendChild(star);
        }
        starfield.appendChild(frag);
    }
});
