import os
import time
import threading
import pytest
from werkzeug.serving import make_server
from playwright.sync_api import sync_playwright

from app import create_app

# Required viewports according to design.md Section 24 and PROJECT_INSTRUCTIONS.md Section 24
VIEWPORTS = [
    # Mobile & Narrow Phones
    {"name": "mobile_320", "width": 320, "height": 700},
    {"name": "mobile_360", "width": 360, "height": 740},
    {"name": "mobile_375", "width": 375, "height": 812},
    {"name": "mobile_390", "width": 390, "height": 844},
    {"name": "mobile_430", "width": 430, "height": 932},
    # Tablet
    {"name": "tablet_768", "width": 768, "height": 1024},
    {"name": "tablet_820", "width": 820, "height": 1180},
    # Desktop
    {"name": "desktop_1024", "width": 1024, "height": 768},
    {"name": "desktop_1280", "width": 1280, "height": 800},
    {"name": "desktop_1440", "width": 1440, "height": 900},
]

PAGES = [
    "/",
    "/meet",
    "/contribute",
    "/about",
    "/alumni",
    "/admin/login",
]

class LiveServerThread(threading.Thread):
    def __init__(self, app, host="127.0.0.1", port=5003):
        super().__init__()
        self.server = make_server(host, port, app)
        self.ctx = app.app_context()
        self.ctx.push()

    def run(self):
        self.server.serve_forever()

    def shutdown(self):
        self.server.shutdown()

@pytest.fixture(scope="session")
def server_url():
    app = create_app()
    app.config["TESTING"] = True
    port = 5003
    server = LiveServerThread(app, port=port)
    server.start()
    url = f"http://127.0.0.1:{port}"
    time.sleep(0.5)
    yield url
    server.shutdown()

@pytest.fixture(scope="session")
def browser_instance():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        yield browser
        browser.close()

def test_single_theme_rule_enforcement(server_url, browser_instance):
    """
    design.md Section 29 (Single Theme Rule):
    There is only ONE theme: SC&SS Editorial Heritage.
    Multi-theme dropdown selectors (Apple, Academic, Film) must NOT exist.
    """
    page = browser_instance.new_page(viewport={"width": 1280, "height": 800})
    page.goto(f"{server_url}/", wait_until="domcontentloaded")

    # Check for legacy theme dropdown or theme selector items in HTML
    theme_dropdown = page.query_selector("#themeDropdown")
    mobile_theme_items = page.query_selector(".mobile-theme-item")

    assert theme_dropdown is None, "FOUND MULTI-THEME DROPDOWN (#themeDropdown)! Section 29 mandates Single Theme Rule (SC&SS Editorial Heritage only)."
    assert mobile_theme_items is None, "FOUND MOBILE THEME SELECTOR (.mobile-theme-item)! Section 29 mandates Single Theme Rule."
    page.close()

@pytest.mark.parametrize("viewport", VIEWPORTS, ids=lambda v: v["name"])
@pytest.mark.parametrize("path", PAGES)
def test_no_horizontal_overflow(server_url, browser_instance, viewport, path):
    """
    design.md Section 24.3 & 24.8 & PROJECT_INSTRUCTIONS.md Section 24.2:
    Prevent horizontal page overflow at every supported viewport.
    document.documentElement.scrollWidth <= viewport.width
    For tables inside .table-responsive (documented table scrolling), the container itself must stay within viewport.
    """
    page = browser_instance.new_page(viewport={"width": viewport["width"], "height": viewport["height"]})
    page.goto(f"{server_url}{path}", wait_until="domcontentloaded")

    overflow_data = page.evaluate("""
        () => {
            const vpWidth = window.innerWidth;
            const docScrollWidth = document.documentElement.scrollWidth;
            const bodyScrollWidth = document.body.scrollWidth;
            const overflowing = [];

            const elements = document.querySelectorAll('*');
            for (const el of elements) {
                const rect = el.getBoundingClientRect();
                const style = window.getComputedStyle(el);
                
                if (style.display === 'none' || style.visibility === 'hidden') continue;

                // Check if element is inside an intentional overflow-x container (.table-responsive)
                let isInsideScrollableContainer = false;
                let parent = el.parentElement;
                while (parent && parent !== document.body) {
                    const parentStyle = window.getComputedStyle(parent);
                    if ((parentStyle.overflowX === 'auto' || parentStyle.overflowX === 'scroll') && 
                        parent.getBoundingClientRect().right <= vpWidth + 1.5) {
                        isInsideScrollableContainer = true;
                        break;
                    }
                    parent = parent.parentElement;
                }

                if (isInsideScrollableContainer) continue;

                // Allow 1.5px tolerance for subpixel rounding
                if (rect.right > vpWidth + 1.5) {
                    overflowing.push({
                        tag: el.tagName,
                        id: el.id || '',
                        className: (el.className || '').toString().slice(0, 50),
                        rectRight: Math.round(rect.right),
                        rectWidth: Math.round(rect.width),
                        vpWidth: vpWidth
                    });
                }
            }

            return {
                vpWidth,
                docScrollWidth,
                bodyScrollWidth,
                overflowingCount: overflowing.length,
                overflowingElements: overflowing.slice(0, 5)
            };
        }
    """)

    page.close()

    assert overflow_data["docScrollWidth"] <= viewport["width"] + 1.5, (
        f"Horizontal document overflow on {path} at {viewport['name']} ({viewport['width']}px): "
        f"document.scrollWidth={overflow_data['docScrollWidth']}px > viewport={viewport['width']}px."
    )

    assert overflow_data["bodyScrollWidth"] <= viewport["width"] + 1.5, (
        f"Horizontal body overflow on {path} at {viewport['name']} ({viewport['width']}px): "
        f"body.scrollWidth={overflow_data['bodyScrollWidth']}px > viewport={viewport['width']}px."
    )

    assert overflow_data["overflowingCount"] == 0, (
        f"Elements extending past viewport on {path} at {viewport['name']} ({viewport['width']}px): "
        f"{overflow_data['overflowingElements']}"
    )

@pytest.mark.parametrize("viewport", VIEWPORTS, ids=lambda v: v["name"])
@pytest.mark.parametrize("path", PAGES)
def test_primary_content_visibility_and_preservation(server_url, browser_instance, viewport, path):
    """
    design.md Section 24.3:
    Keep primary content inside the viewport, allow text to wrap, do not hide important content solely for mobile.
    """
    page = browser_instance.new_page(viewport={"width": viewport["width"], "height": viewport["height"]})
    page.goto(f"{server_url}{path}", wait_until="domcontentloaded")

    # Verify primary main element and headings exist and are visible
    h1 = page.query_selector("h1")
    if h1:
        box = h1.bounding_box()
        assert box is not None and box["width"] > 0 and box["height"] > 0, f"h1 is clipped or hidden on {path} at {viewport['name']}"
        assert box["x"] >= 0 and box["x"] + box["width"] <= viewport["width"] + 2, f"h1 overflows boundary on {path} at {viewport['name']}"

    # Check visible primary CTA button in main content area
    ctas = page.query_selector_all("main .btn-primary, main .btn-paper, .hero .btn-primary, .tracker-hero-section .btn-primary, .cta-banner .btn-paper")
    visible_cta = None
    for cta in ctas:
        box = cta.bounding_box()
        if box and box["width"] > 0 and box["height"] > 0:
            visible_cta = box
            break

    if len(ctas) > 0:
        assert visible_cta is not None, f"No visible main CTA button found on {path} at {viewport['name']}"
        assert visible_cta["width"] <= viewport["width"], f"CTA button width ({visible_cta['width']}px) exceeds viewport ({viewport['width']}px) on {path} at {viewport['name']}"

    page.close()

@pytest.mark.parametrize("viewport", [v for v in VIEWPORTS if v["width"] < 768], ids=lambda v: v["name"])
def test_mobile_navigation_toggle_and_drawer(server_url, browser_instance, viewport):
    """
    design.md Section 24.4:
    Mobile: Logo/identity + menu control.
    Navigation links become a vertical menu when opened. Must not cause horizontal overflow.
    """
    page = browser_instance.new_page(viewport={"width": viewport["width"], "height": viewport["height"]})
    page.goto(f"{server_url}/", wait_until="networkidle")

    nav_toggle = page.query_selector("#navToggle")
    assert nav_toggle is not None, f"Missing #navToggle hamburger button at {viewport['name']}"
    
    toggle_box = nav_toggle.bounding_box()
    assert toggle_box is not None and toggle_box["width"] > 0, f"#navToggle button is not visible at {viewport['name']}"

    # Click mobile hamburger toggle
    nav_toggle.click()
    page.wait_for_timeout(300)

    # Verify document does not overflow when menu is open
    doc_scroll_width = page.evaluate("document.documentElement.scrollWidth")
    assert doc_scroll_width <= viewport["width"] + 1.5, f"Opening mobile menu caused horizontal overflow ({doc_scroll_width}px > {viewport['width']}px) at {viewport['name']}"

    page.close()

@pytest.mark.parametrize("viewport", [v for v in VIEWPORTS if v["width"] >= 1024], ids=lambda v: v["name"])
def test_desktop_navigation_inline(server_url, browser_instance, viewport):
    """
    design.md Section 24.4:
    Desktop: Logo/identity + navigation links + primary action inline. Hamburger hidden.
    """
    page = browser_instance.new_page(viewport={"width": viewport["width"], "height": viewport["height"]})
    page.goto(f"{server_url}/", wait_until="networkidle")

    # Hamburger should be hidden on desktop
    nav_toggle = page.query_selector("#navToggle")
    if nav_toggle:
        toggle_box = nav_toggle.bounding_box()
        assert toggle_box is None or toggle_box["width"] == 0 or toggle_box["height"] == 0, f"#navToggle should be hidden on desktop at {viewport['name']}"

    # Desktop nav links should be visible
    nav_links = page.query_selector(".nav-links")
    assert nav_links is not None, "Missing .nav-links on desktop"
    links_box = nav_links.bounding_box()
    assert links_box is not None and links_box["width"] > 0 and links_box["height"] > 0, f".nav-links not visible on desktop at {viewport['name']}"

    page.close()

@pytest.mark.parametrize("viewport", VIEWPORTS, ids=lambda v: v["name"])
def test_images_responsive_fluidity(server_url, browser_instance, viewport):
    """
    design.md Section 24.7:
    Images must be fluid (max-width: 100%, height: auto).
    Never allow images to force container wider than viewport.
    """
    page = browser_instance.new_page(viewport={"width": viewport["width"], "height": viewport["height"]})
    page.goto(f"{server_url}/", wait_until="networkidle")

    img_data = page.evaluate("""
        () => {
            const imgs = document.querySelectorAll('img, svg.brand-logo');
            const vpWidth = window.innerWidth;
            const invalid = [];
            for (const img of imgs) {
                const rect = img.getBoundingClientRect();
                if (rect.width > vpWidth + 1.5) {
                    invalid.push({
                        src: img.src || img.tagName,
                        width: rect.width,
                        vpWidth: vpWidth
                    });
                }
            }
            return invalid;
        }
    """)

    page.close()
    assert len(img_data) == 0, f"Images overflowing viewport at {viewport['name']}: {img_data}"
