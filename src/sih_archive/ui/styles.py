"""
Heritage Design System Styles & Design Tokens for SIH26096 ("Heritage × Modern Research Infrastructure").

Institutional Museum/Library Grade Design System:
- Palette:
  - Deep Navy: #0f172a, #1e293b
  - Warm Ivory / Parchment: #fdfbf7, #f8fafc, #f1f5f9
  - Muted Bronze / Gold: #b45309, #d97706, #78350f
  - Subtle Verified Green: #059669, #10b981
  - Neutral Graphite: #334155, #475569
  - Restrained Red Alert: #b91c1c
- Typography:
  - Headings: 'Cinzel', 'Playfair Display', Georgia, serif stack
  - Body & Metadata: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif
  - Monospace: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace
- Restrained visual structure:
  - Generous whitespace, clean architectural borders, subtle cards
  - Zero neon glows, zero excessive gradients, zero omnipresent glassmorphism
"""

from typing import Any, Dict

THEME_TOKENS: Dict[str, Any] = {
    "colors": {
        "primary_dark": "#0f172a",
        "primary": "#1e293b",
        "navy_slate": "#334155",
        "parchment": "#fdfbf7",
        "ivory": "#f8fafc",
        "parchment_deep": "#f1f5f9",
        "bronze": "#b45309",
        "gold": "#d97706",
        "bronze_dark": "#78350f",
        "green_verified": "#059669",
        "green_subtle": "#10b981",
        "green_bg": "#ecfdf5",
        "graphite": "#334155",
        "graphite_light": "#475569",
        "muted_slate": "#64748b",
        "alert_red": "#b91c1c",
        "alert_bg": "#fef2f2",
        "alert_border": "#fecaca",
        "warning_bg": "#fffbeb",
        "warning_border": "#fcd34d",
        "warning_text": "#92400e",
        "border": "#e2e8f0",
        "border_parchment": "#e5dfd3",
        "border_bronze": "#d4b996",
        "card_bg": "#ffffff",
    },
    "typography": {
        "heading_serif": "'Cinzel', 'Playfair Display', Georgia, serif",
        "body_sans": "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
        "mono": "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace",
    },
    "layout": {
        "container_max_width": "1360px",
        "touch_target_min": "48px",
        "border_radius_sm": "4px",
        "border_radius_md": "8px",
        "border_radius_lg": "12px",
    },
    "elevation": {
        "subtle": "0 1px 3px rgba(15, 23, 42, 0.06), 0 1px 2px rgba(15, 23, 42, 0.04)",
        "card": "0 4px 6px -1px rgba(15, 23, 42, 0.07), 0 2px 4px -2px rgba(15, 23, 42, 0.05)",
        "modal": "0 20px 25px -5px rgba(15, 23, 42, 0.15), 0 8px 10px -6px rgba(15, 23, 42, 0.1)",
    },
}


def get_styles() -> str:
    """Returns comprehensive CSS styling for the institutional digital heritage platform."""
    return """
    /* ==========================================================================
       HERITAGE DESIGN SYSTEM: MODERN RESEARCH × ARCHIVAL INTEGRITY
       ========================================================================== */

    :root {
        /* Colors: Museum & Library Grade */
        --primary-dark: #0f172a;
        --primary: #1e293b;
        --navy-slate: #334155;
        --bg-parchment: #fdfbf7;
        --bg-ivory: #f8fafc;
        --bg-parchment-deep: #f1f5f9;
        --card-bg: #ffffff;
        
        --accent-bronze: #b45309;
        --accent-gold: #d97706;
        --accent-bronze-dark: #78350f;
        
        --text-graphite: #334155;
        --text-heading: #0f172a;
        --text-muted: #64748b;
        --text-light: #94a3b8;
        
        --border-color: #e2e8f0;
        --border-parchment: #e5dfd3;
        --border-bronze: #d4b996;
        
        --status-verified: #059669;
        --status-verified-light: #10b981;
        --status-verified-bg: #ecfdf5;
        
        --status-alert: #b91c1c;
        --status-alert-bg: #fef2f2;
        --status-alert-border: #fecaca;
        
        --status-warning-bg: #fffbeb;
        --status-warning-border: #fcd34d;
        --status-warning-text: #92400e;

        /* Typography */
        --font-serif: 'Cinzel', 'Playfair Display', Georgia, 'Times New Roman', serif;
        --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        --font-mono: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', monospace;

        /* Layout & Sizing */
        --touch-target: 48px;
        --max-width: 1360px;
        --shadow-subtle: 0 1px 3px rgba(15, 23, 42, 0.06), 0 1px 2px rgba(15, 23, 42, 0.04);
        --shadow-card: 0 4px 6px -1px rgba(15, 23, 42, 0.07), 0 2px 4px -2px rgba(15, 23, 42, 0.05);
    }

    * {
        box-sizing: border-box;
        margin: 0;
        padding: 0;
    }

    body {
        background-color: var(--bg-parchment);
        color: var(--text-graphite);
        font-family: var(--font-sans);
        font-size: 15px;
        line-height: 1.6;
        min-height: 100vh;
        display: flex;
        flex-direction: column;
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
    }

    h1, h2, h3, h4, .serif-heading {
        font-family: var(--font-serif);
        color: var(--text-heading);
        font-weight: 700;
        letter-spacing: -0.01em;
        line-height: 1.25;
    }

    a {
        color: var(--accent-bronze);
        text-decoration: none;
        transition: color 0.15s ease;
    }

    a:hover {
        color: var(--accent-gold);
    }

    /* --------------------------------------------------------------------------
       1. PERSISTENT DEMO DISCLAIMER BANNER
       -------------------------------------------------------------------------- */
    .demo-banner {
        background: #78350f;
        border-bottom: 2px solid #b45309;
        color: #fef3c7;
        padding: 0.65rem 1.5rem;
        font-size: 0.85rem;
        font-weight: 600;
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 12px;
        position: sticky;
        top: 0;
        z-index: 1000;
        box-shadow: 0 2px 4px rgba(0,0,0,0.12);
    }

    .demo-banner-content {
        display: flex;
        align-items: center;
        gap: 8px;
        flex-wrap: wrap;
    }

    .demo-banner-badge {
        background: #059669;
        color: #ffffff;
        font-size: 0.72rem;
        font-weight: 700;
        padding: 2px 8px;
        border-radius: 9999px;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        white-space: nowrap;
    }

    /* --------------------------------------------------------------------------
       2. GLOBAL NAVIGATION HEADER
       -------------------------------------------------------------------------- */
    .global-header {
        background: var(--primary-dark);
        color: #f8fafc;
        border-bottom: 3px solid var(--accent-bronze);
    }

    .header-top {
        max-width: var(--max-width);
        margin: 0 auto;
        padding: 1rem 1.5rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 1.5rem;
    }

    .header-branding {
        display: flex;
        align-items: center;
        gap: 14px;
        text-decoration: none;
    }

    .header-emblem {
        width: 44px;
        height: 44px;
        background: linear-gradient(135deg, #1e293b, #0f172a);
        border: 2px solid var(--accent-gold);
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.4rem;
        color: #fef3c7;
        flex-shrink: 0;
    }

    .header-title-block h1 {
        font-size: 1.25rem;
        color: #ffffff;
        letter-spacing: 0.02em;
        margin-bottom: 2px;
    }

    .header-subtitle {
        font-size: 0.8rem;
        color: #94a3b8;
        font-weight: 400;
        letter-spacing: 0.01em;
    }

    .header-tools {
        display: flex;
        align-items: center;
        gap: 12px;
    }

    .btn-kiosk-toggle {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: #334155;
        border: 1px solid #475569;
        color: #f8fafc;
        padding: 0.5rem 0.9rem;
        border-radius: 6px;
        font-size: 0.82rem;
        font-weight: 600;
        transition: all 0.2s ease;
    }

    .btn-kiosk-toggle:hover {
        background: var(--accent-bronze);
        border-color: var(--accent-gold);
        color: #ffffff;
    }

    /* Navigation View Tabs */
    .header-nav {
        background: #0b1120;
        border-top: 1px solid #1e293b;
    }

    .nav-container {
        max-width: var(--max-width);
        margin: 0 auto;
        padding: 0 1.5rem;
        display: flex;
        gap: 4px;
        overflow-x: auto;
        scrollbar-width: none;
    }

    .nav-container::-webkit-scrollbar {
        display: none;
    }

    .nav-tab {
        background: transparent;
        border: none;
        border-bottom: 3px solid transparent;
        color: #94a3b8;
        padding: 0.85rem 1.1rem;
        font-size: 0.88rem;
        font-weight: 600;
        cursor: pointer;
        display: inline-flex;
        align-items: center;
        gap: 8px;
        white-space: nowrap;
        transition: all 0.2s ease;
    }

    .nav-tab:hover {
        color: #f8fafc;
        background: rgba(255, 255, 255, 0.03);
    }

    .nav-tab.active {
        color: #fef3c7;
        border-bottom-color: var(--accent-gold);
        background: rgba(217, 119, 6, 0.08);
    }

    /* --------------------------------------------------------------------------
       3. VIEW CONTAINER & TAB PANELS
       -------------------------------------------------------------------------- */
    .app-viewport {
        max-width: var(--max-width);
        width: 100%;
        margin: 0 auto;
        padding: 2rem 1.5rem;
        flex: 1;
    }

    .view-panel {
        display: none;
        animation: fadeIn 0.25s ease-in-out;
    }

    .view-panel.active {
        display: block;
    }

    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(4px); }
        to { opacity: 1; transform: translateY(0); }
    }

    /* --------------------------------------------------------------------------
       4. DIGITAL HERITAGE PORTAL: HERO SECTION
       -------------------------------------------------------------------------- */
    .portal-hero {
        background: linear-gradient(180deg, #ffffff 0%, var(--bg-ivory) 100%);
        border: 1px solid var(--border-parchment);
        border-radius: 12px;
        padding: 3.5rem 2.5rem;
        margin-bottom: 2.5rem;
        box-shadow: var(--shadow-card);
        text-align: center;
        position: relative;
    }

    .portal-hero-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: #fef3c7;
        color: var(--accent-bronze-dark);
        border: 1px solid #fde68a;
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        margin-bottom: 1.25rem;
    }

    .portal-hero h2 {
        font-size: 2.6rem;
        color: var(--primary-dark);
        margin-bottom: 1.25rem;
        max-width: 960px;
        margin-left: auto;
        margin-right: auto;
    }

    .portal-hero-subtitle {
        font-size: 1.15rem;
        color: var(--text-graphite);
        max-width: 820px;
        margin: 0 auto 2rem auto;
        line-height: 1.6;
    }

    .hero-cta-group {
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 16px;
        flex-wrap: wrap;
        margin-bottom: 2.5rem;
    }

    .btn-primary {
        background: var(--primary-dark);
        color: #ffffff;
        border: 1px solid var(--primary);
        padding: 0.85rem 1.8rem;
        border-radius: 8px;
        font-size: 1rem;
        font-weight: 600;
        cursor: pointer;
        display: inline-flex;
        align-items: center;
        gap: 10px;
        transition: all 0.2s ease;
        box-shadow: var(--shadow-subtle);
    }

    .btn-primary:hover {
        background: #1e293b;
        border-color: var(--accent-bronze);
        transform: translateY(-1px);
        color: #ffffff;
    }

    .btn-secondary {
        background: #ffffff;
        color: var(--primary-dark);
        border: 1px solid var(--border-bronze);
        padding: 0.85rem 1.8rem;
        border-radius: 8px;
        font-size: 1rem;
        font-weight: 600;
        cursor: pointer;
        display: inline-flex;
        align-items: center;
        gap: 10px;
        transition: all 0.2s ease;
    }

    .btn-secondary:hover {
        background: #fdfbf7;
        border-color: var(--accent-bronze);
        color: var(--accent-bronze);
    }

    /* Institutional Stats Bar */
    .hero-stats-bar {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1.5rem;
        border-top: 1px solid var(--border-parchment);
        padding-top: 2rem;
        max-width: 1000px;
        margin: 0 auto;
    }

    .stat-item {
        text-align: center;
    }

    .stat-value {
        font-family: var(--font-serif);
        font-size: 1.8rem;
        font-weight: 700;
        color: var(--accent-bronze);
        margin-bottom: 2px;
    }

    .stat-label {
        font-size: 0.82rem;
        color: var(--text-muted);
        text-transform: uppercase;
        letter-spacing: 0.04em;
        font-weight: 600;
    }

    /* --------------------------------------------------------------------------
       5. DISCOVERY PATHWAYS (ONE ARCHIVE. MANY WAYS TO EXPLORE.)
       -------------------------------------------------------------------------- */
    .section-header {
        margin-bottom: 1.75rem;
    }

    .section-title-wrap {
        display: flex;
        align-items: baseline;
        justify-content: space-between;
        border-bottom: 1px solid var(--border-parchment);
        padding-bottom: 0.75rem;
        margin-bottom: 0.5rem;
    }

    .section-title {
        font-size: 1.5rem;
        color: var(--primary-dark);
    }

    .section-subtitle {
        font-size: 0.92rem;
        color: var(--text-muted);
    }

    .pathways-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
        gap: 1.5rem;
        margin-bottom: 3.5rem;
    }

    .pathway-card {
        background: var(--card-bg);
        border: 1px solid var(--border-parchment);
        border-radius: 10px;
        padding: 1.6rem;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        box-shadow: var(--shadow-subtle);
        transition: all 0.2s ease;
        position: relative;
        overflow: hidden;
    }

    .pathway-card:hover {
        border-color: var(--accent-bronze);
        box-shadow: var(--shadow-card);
        transform: translateY(-2px);
    }

    .pathway-top {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        margin-bottom: 1rem;
    }

    .pathway-icon {
        width: 44px;
        height: 44px;
        background: #fdfbf7;
        border: 1px solid var(--border-bronze);
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.35rem;
    }

    .pathway-badge {
        font-size: 0.72rem;
        font-weight: 700;
        padding: 3px 8px;
        border-radius: 4px;
        background: var(--bg-parchment-deep);
        color: var(--navy-slate);
        border: 1px solid var(--border-color);
        letter-spacing: 0.02em;
    }

    .pathway-card h3 {
        font-size: 1.2rem;
        margin-bottom: 4px;
        color: var(--primary-dark);
    }

    .pathway-tagline {
        font-size: 0.85rem;
        font-weight: 600;
        color: var(--accent-bronze);
        margin-bottom: 0.75rem;
    }

    .pathway-desc {
        font-size: 0.88rem;
        color: var(--text-graphite);
        line-height: 1.55;
        margin-bottom: 1.25rem;
        flex: 1;
    }

    .pathway-btn {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        font-size: 0.88rem;
        font-weight: 600;
        color: var(--accent-bronze);
        background: none;
        border: none;
        cursor: pointer;
        padding: 0;
        transition: color 0.15s ease;
    }

    .pathway-btn:hover {
        color: var(--accent-gold);
    }

    /* --------------------------------------------------------------------------
       6. FEATURED ARCHIVAL TREASURES
       -------------------------------------------------------------------------- */
    .treasures-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        gap: 1.5rem;
        margin-bottom: 2.5rem;
    }

    .treasure-card {
        background: var(--card-bg);
        border: 1px solid var(--border-parchment);
        border-radius: 10px;
        overflow: hidden;
        display: flex;
        flex-direction: column;
        box-shadow: var(--shadow-subtle);
        transition: all 0.2s ease;
    }

    .treasure-card:hover {
        border-color: var(--border-bronze);
        box-shadow: var(--shadow-card);
    }

    .treasure-header {
        background: #fdfbf7;
        border-bottom: 1px solid var(--border-parchment);
        padding: 1rem 1.25rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .treasure-body {
        padding: 1.25rem;
        flex: 1;
        display: flex;
        flex-direction: column;
    }

    .treasure-body h4 {
        font-size: 1.1rem;
        margin-bottom: 4px;
        color: var(--primary-dark);
    }

    .treasure-meta {
        font-size: 0.82rem;
        color: var(--text-muted);
        margin-bottom: 0.75rem;
    }

    .treasure-summary {
        font-size: 0.88rem;
        color: var(--text-graphite);
        line-height: 1.5;
        margin-bottom: 1.25rem;
        flex: 1;
    }

    .treasure-actions {
        display: flex;
        gap: 8px;
        border-top: 1px solid var(--border-color);
        padding-top: 0.9rem;
    }

    .btn-sm {
        padding: 0.45rem 0.85rem;
        border-radius: 6px;
        font-size: 0.82rem;
        font-weight: 600;
        cursor: pointer;
        display: inline-flex;
        align-items: center;
        gap: 5px;
        transition: all 0.15s ease;
    }

    .btn-sm-primary {
        background: var(--primary-dark);
        color: #ffffff;
        border: 1px solid var(--primary);
    }

    .btn-sm-primary:hover {
        background: #1e293b;
        color: #ffffff;
    }

    .btn-sm-secondary {
        background: var(--bg-parchment);
        color: var(--primary-dark);
        border: 1px solid var(--border-parchment);
    }

    .btn-sm-secondary:hover {
        background: #ffffff;
        border-color: var(--accent-bronze);
    }

    /* --------------------------------------------------------------------------
       7. MULTI-FACETED ARCHIVE EXPLORER
       -------------------------------------------------------------------------- */
    .explorer-toolbar {
        background: var(--card-bg);
        border: 1px solid var(--border-parchment);
        border-radius: 10px;
        padding: 1.5rem;
        margin-bottom: 1.75rem;
        box-shadow: var(--shadow-subtle);
    }

    .toolbar-title {
        font-size: 1rem;
        font-weight: 700;
        color: var(--primary-dark);
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    .filter-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 12px;
        margin-bottom: 1rem;
    }

    .filter-group label {
        display: block;
        font-size: 0.78rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        color: var(--text-muted);
        margin-bottom: 4px;
    }

    .filter-select, .filter-input {
        width: 100%;
        padding: 0.55rem 0.75rem;
        border: 1px solid var(--border-color);
        border-radius: 6px;
        background: var(--bg-ivory);
        color: var(--text-graphite);
        font-size: 0.88rem;
        font-family: inherit;
        transition: border-color 0.15s ease;
    }

    .filter-select:focus, .filter-input:focus {
        outline: none;
        border-color: var(--accent-bronze);
        background: #ffffff;
    }

    .filter-actions {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding-top: 0.75rem;
        border-top: 1px solid var(--border-color);
    }

    .results-count {
        font-size: 0.85rem;
        color: var(--text-muted);
        font-weight: 500;
    }

    .btn-reset {
        background: none;
        border: 1px solid var(--border-color);
        color: var(--text-muted);
        padding: 0.4rem 0.8rem;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.15s ease;
    }

    .btn-reset:hover {
        background: #f1f5f9;
        color: var(--primary-dark);
    }

    /* Catalog Cards Grid */
    .catalog-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
        gap: 1.5rem;
        margin-bottom: 3rem;
    }

    .catalog-card {
        background: var(--card-bg);
        border: 1px solid var(--border-parchment);
        border-radius: 10px;
        padding: 1.5rem;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        box-shadow: var(--shadow-subtle);
        transition: all 0.2s ease;
    }

    .catalog-card:hover {
        border-color: var(--accent-bronze);
        box-shadow: var(--shadow-card);
    }

    .catalog-card-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        margin-bottom: 0.75rem;
        gap: 10px;
    }

    .catalog-card-title {
        font-size: 1.15rem;
        color: var(--primary-dark);
        line-height: 1.35;
    }

    .catalog-card-subtitle {
        font-size: 0.82rem;
        color: var(--text-muted);
        font-style: italic;
        margin-bottom: 0.6rem;
    }

    .badge-pill {
        display: inline-block;
        font-size: 0.72rem;
        font-weight: 700;
        padding: 2px 8px;
        border-radius: 4px;
        text-transform: uppercase;
        letter-spacing: 0.03em;
    }

    .badge-verified {
        background: var(--status-verified-bg);
        color: var(--status-verified);
        border: 1px solid #a7f3d0;
    }

    .badge-public {
        background: #eff6ff;
        color: #1d4ed8;
        border: 1px solid #bfdbfe;
    }

    .badge-lang {
        background: #f1f5f9;
        color: var(--navy-slate);
        border: 1px solid var(--border-color);
        font-family: var(--font-mono);
    }

    .catalog-card-meta {
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
        margin-bottom: 0.9rem;
    }

    .catalog-card-summary {
        font-size: 0.88rem;
        color: var(--text-graphite);
        line-height: 1.55;
        margin-bottom: 1.25rem;
        flex: 1;
    }

    .catalog-card-institution {
        font-size: 0.78rem;
        color: var(--text-muted);
        border-top: 1px solid var(--border-color);
        padding-top: 0.75rem;
        margin-bottom: 1rem;
    }

    .catalog-card-actions {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 8px;
    }

    /* --------------------------------------------------------------------------
       8. EVIDENCE-GROUNDED SEARCH & INTEGRATED WORKSPACE
       -------------------------------------------------------------------------- */
    .search-workspace-card {
        background: var(--card-bg);
        border: 1px solid var(--border-parchment);
        border-radius: 12px;
        padding: 1.75rem;
        margin-bottom: 2.5rem;
        box-shadow: var(--shadow-card);
    }

    .search-workspace-card .card-title {
        font-size: 1.25rem;
        color: var(--primary-dark);
        margin-bottom: 0.5rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .search-box-row {
        display: flex;
        gap: 10px;
        margin-top: 1.25rem;
        margin-bottom: 1rem;
        flex-wrap: wrap;
    }

    .search-input-main {
        flex: 1;
        min-width: 280px;
        padding: 0.75rem 1rem;
        border: 1px solid var(--border-bronze);
        border-radius: 8px;
        font-size: 1rem;
        background: #ffffff;
    }

    .search-input-main:focus {
        outline: none;
        border-color: var(--accent-bronze);
        box-shadow: 0 0 0 2px rgba(180, 83, 9, 0.15);
    }

    .search-select-mode {
        padding: 0.75rem 1rem;
        border: 1px solid var(--border-color);
        border-radius: 8px;
        background: #ffffff;
        font-size: 0.9rem;
        font-weight: 500;
        color: var(--primary-dark);
    }

    .btn-search-exec {
        background: var(--accent-bronze);
        color: #ffffff;
        border: 1px solid var(--accent-bronze-dark);
        padding: 0.75rem 1.5rem;
        border-radius: 8px;
        font-size: 0.95rem;
        font-weight: 600;
        cursor: pointer;
        display: inline-flex;
        align-items: center;
        gap: 8px;
        transition: all 0.15s ease;
    }

    .btn-search-exec:hover {
        background: #92400e;
    }

    /* Live Search Results Container */
    .search-status-bar {
        font-size: 0.82rem;
        color: var(--text-muted);
        padding: 0.5rem 0;
        display: flex;
        justify-content: space-between;
        border-bottom: 1px solid var(--border-color);
        margin-bottom: 1rem;
    }

    .search-results-list {
        display: flex;
        flex-direction: column;
        gap: 1rem;
    }

    .search-result-card {
        background: var(--bg-ivory);
        border: 1px solid var(--border-color);
        border-left: 4px solid var(--accent-bronze);
        border-radius: 0 8px 8px 0;
        padding: 1.25rem;
        transition: all 0.15s ease;
    }

    .search-result-card:hover {
        background: #ffffff;
        box-shadow: var(--shadow-subtle);
    }

    .result-card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.6rem;
        flex-wrap: wrap;
        gap: 8px;
    }

    .result-doc-info {
        font-size: 0.85rem;
        font-weight: 700;
        color: var(--primary-dark);
        display: flex;
        align-items: center;
        gap: 8px;
    }

    .result-score-badge {
        font-family: var(--font-mono);
        font-size: 0.75rem;
        background: #f1f5f9;
        color: var(--navy-slate);
        padding: 2px 6px;
        border-radius: 4px;
        border: 1px solid var(--border-color);
    }

    .result-snippet {
        font-size: 0.92rem;
        line-height: 1.6;
        color: var(--text-graphite);
        margin-bottom: 1rem;
    }

    .result-card-footer {
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 8px;
    }

    /* DIRECT JUMP INTERACTION BUTTON */
    .btn-evidence-jump {
        background: var(--primary-dark);
        color: #fef3c7;
        border: 1px solid var(--accent-bronze);
        padding: 0.5rem 1rem;
        border-radius: 6px;
        font-size: 0.82rem;
        font-weight: 700;
        letter-spacing: 0.03em;
        cursor: pointer;
        display: inline-flex;
        align-items: center;
        gap: 6px;
        transition: all 0.2s ease;
    }

    .btn-evidence-jump:hover {
        background: #1e293b;
        border-color: var(--accent-gold);
        transform: translateY(-1px);
    }

    /* --------------------------------------------------------------------------
       9. TWO-COLUMN RESEARCH WORKSPACE: QA & INTEGRITY GATES
       -------------------------------------------------------------------------- */
    .workspace-dual-grid {
        display: grid;
        grid-template-columns: 2fr 1fr;
        gap: 1.5rem;
        margin-bottom: 2.5rem;
    }

    @media (max-width: 960px) {
        .workspace-dual-grid {
            grid-template-columns: 1fr;
        }
    }

    .card {
        background: var(--card-bg);
        border: 1px solid var(--border-parchment);
        border-radius: 10px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: var(--shadow-subtle);
    }

    .card-title {
        font-size: 1.15rem;
        font-weight: 600;
        margin-bottom: 1rem;
        color: var(--primary-dark);
        display: flex;
        align-items: center;
        justify-content: space-between;
    }

    .gate-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 0.85rem;
    }

    .gate-table td {
        padding: 8px 6px;
        border-bottom: 1px solid var(--border-color);
    }

    .gate-pill {
        display: inline-block;
        font-size: 0.72rem;
        font-weight: 700;
        padding: 2px 8px;
        border-radius: 12px;
        letter-spacing: 0.02em;
    }

    .gate-pass {
        background: var(--status-verified-bg);
        border: 1px solid #86efac;
        color: #166534;
    }

    .gate-blocked {
        background: var(--status-alert-bg);
        border: 1px solid var(--status-alert-border);
        color: var(--status-alert);
    }

    .gate-locked {
        background: var(--status-warning-bg);
        border: 1px solid var(--status-warning-border);
        color: var(--status-warning-text);
    }

    .refusal-alert {
        background: var(--status-alert-bg);
        border: 1px solid var(--status-alert-border);
        color: var(--status-alert);
        padding: 1rem;
        border-radius: 8px;
        font-size: 0.92rem;
        font-weight: 600;
    }

    .citation-box {
        background: #f0fdf4;
        border: 1px solid #bbf7d0;
        border-radius: 6px;
        padding: 0.85rem;
        margin-top: 0.75rem;
    }

    .citation-badge {
        display: inline-block;
        background: var(--status-verified);
        color: #ffffff;
        font-size: 0.72rem;
        font-weight: 700;
        padding: 2px 6px;
        border-radius: 4px;
        letter-spacing: 0.04em;
    }

    /* --------------------------------------------------------------------------
       10. ARCHIVAL MANUSCRIPT VIEWER (R4 3-COLUMN WORKSPACE)
       -------------------------------------------------------------------------- */
    .viewer-layout {
        display: grid;
        grid-template-columns: 260px minmax(480px, 1fr) 340px;
        gap: 1.5rem;
        min-height: 720px;
        margin-bottom: 2rem;
    }

    .viewer-left-col {
        display: flex;
        flex-direction: column;
        gap: 1rem;
    }

    .thumbnail-strip {
        display: flex;
        flex-direction: column;
        gap: 10px;
        max-height: 680px;
        overflow-y: auto;
        padding-right: 4px;
    }

    .thumbnail-card {
        background: #ffffff;
        border: 2px solid var(--border-color);
        border-radius: 8px;
        padding: 8px;
        cursor: pointer;
        display: flex;
        flex-direction: column;
        gap: 6px;
        transition: all 0.2s ease;
        text-align: left;
    }

    .thumbnail-card:hover {
        border-color: var(--accent-bronze);
        transform: translateY(-1px);
        box-shadow: var(--shadow-subtle);
    }

    .thumbnail-card.active {
        border-color: var(--accent-bronze);
        background: #fdfbf7;
        box-shadow: 0 0 0 2px rgba(180, 83, 9, 0.25);
    }

    .thumbnail-img-wrap {
        width: 100%;
        height: 120px;
        background: #1e293b;
        border-radius: 4px;
        overflow: hidden;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .thumbnail-img-wrap img {
        width: 100%;
        height: 100%;
        object-fit: cover;
        opacity: 0.9;
    }

    .thumbnail-title {
        font-size: 0.85rem;
        font-weight: 700;
        color: var(--primary-dark);
        line-height: 1.3;
    }

    .thumbnail-meta-row {
        display: flex;
        gap: 4px;
        align-items: center;
        flex-wrap: wrap;
    }

    /* Center Column: High-Res Viewer & Toolbar */
    .viewer-center-col {
        display: flex;
        flex-direction: column;
        background: #0f172a;
        border: 1px solid #334155;
        border-radius: 10px;
        overflow: hidden;
        box-shadow: var(--shadow-card);
    }

    .viewer-toolbar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        background: #020617;
        padding: 10px 16px;
        border-bottom: 2px solid var(--accent-bronze);
        flex-wrap: wrap;
        gap: 8px;
        z-index: 20;
    }

    .viewer-tool-group {
        display: flex;
        align-items: center;
        gap: 6px;
        flex-wrap: wrap;
    }

    .viewer-tool-btn {
        background: #1e293b;
        color: #f8fafc;
        border: 1px solid #475569;
        padding: 6px 12px;
        border-radius: 4px;
        font-size: 0.82rem;
        font-weight: 600;
        cursor: pointer;
        display: inline-flex;
        align-items: center;
        gap: 6px;
        transition: all 0.15s ease;
    }

    .viewer-tool-btn:hover {
        background: #334155;
        border-color: var(--accent-gold);
        color: #fef3c7;
    }

    .viewer-tool-btn.active {
        background: var(--accent-bronze);
        border-color: var(--accent-gold);
        color: #ffffff;
    }

    .zoom-indicator {
        font-family: var(--font-mono);
        font-size: 0.82rem;
        font-weight: 700;
        background: #0f172a;
        color: #fef08a;
        padding: 4px 10px;
        border-radius: 4px;
        border: 1px solid #334155;
    }

    .viewer-canvas-container {
        position: relative;
        flex: 1;
        min-height: 600px;
        background: #1e293b;
        overflow: hidden;
        display: flex;
        align-items: center;
        justify-content: center;
        user-select: none;
    }

    .viewer-viewport-wrap {
        position: relative;
        display: inline-block;
        transition: transform 0.05s ease-out;
    }

    .viewer-page-img {
        max-height: 580px;
        max-width: 100%;
        object-fit: contain;
        display: block;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.6);
    }

    .viewer-bbox-layer {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        pointer-events: none;
    }

    .evidence-bbox {
        position: absolute;
        border: 2px solid #b45309;
        background: rgba(217, 119, 6, 0.22);
        border-radius: 2px;
        pointer-events: auto;
        box-shadow: 0 0 0 1px rgba(254, 240, 138, 0.35);
        transition: all 0.2s ease;
    }

    .evidence-tag {
        position: absolute;
        top: -18px;
        left: 0;
        background: #b45309;
        color: #ffffff;
        font-size: 9px;
        font-weight: 700;
        padding: 1px 5px;
        border-radius: 2px;
        white-space: nowrap;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
        letter-spacing: 0.03em;
    }

    .viewer-degrade-msg {
        position: absolute;
        bottom: 16px;
        left: 50%;
        transform: translateX(-50%);
        background: rgba(15, 23, 42, 0.95);
        color: #fde68a;
        border: 1px solid #b45309;
        padding: 8px 18px;
        border-radius: 6px;
        font-size: 0.85rem;
        font-weight: 600;
        text-align: center;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);
        z-index: 15;
    }

    /* Right Column: Metadata, Transcript, Token Regions */
    .viewer-right-col {
        display: flex;
        flex-direction: column;
        gap: 1rem;
    }

    .viewer-metadata-box {
        background: var(--bg-ivory);
        border: 1px solid var(--border-color);
        border-radius: 6px;
        padding: 12px;
        font-size: 0.85rem;
        display: flex;
        flex-direction: column;
        gap: 6px;
    }

    .viewer-transcript-box {
        flex: 1;
        background: var(--bg-parchment);
        border: 1px solid var(--border-parchment);
        border-radius: 6px;
        padding: 12px;
        font-size: 0.88rem;
        line-height: 1.6;
        overflow-y: auto;
        max-height: 280px;
        font-family: inherit;
        white-space: pre-wrap;
    }

    .viewer-regions-list {
        display: flex;
        flex-direction: column;
        gap: 6px;
        max-height: 200px;
        overflow-y: auto;
        border: 1px solid var(--border-color);
        border-radius: 6px;
        padding: 8px;
        background: #ffffff;
    }

    .region-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 5px 8px;
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 4px;
        font-size: 0.78rem;
        cursor: pointer;
        transition: all 0.15s ease;
    }

    .region-row:hover {
        background: #fef3c7;
        border-color: #b45309;
    }

    .region-row.active {
        background: #fef08a;
        border-color: #b45309;
        font-weight: 700;
    }

    .btn-inspect-provenance {
        background: var(--primary-dark);
        color: #fef3c7;
        border: 1px solid var(--accent-bronze);
        padding: 0.65rem 1rem;
        border-radius: 6px;
        font-size: 0.82rem;
        font-weight: 700;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 6px;
        width: 100%;
        transition: all 0.2s ease;
    }

    .btn-inspect-provenance:hover {
        background: #1e293b;
        border-color: var(--accent-gold);
    }

    /* --------------------------------------------------------------------------
       11. RESEARCH ASSISTANT (R5 3-COLUMN WORKSPACE & EVIDENCE DRAWER)
       -------------------------------------------------------------------------- */
    .assistant-layout {
        display: grid;
        grid-template-columns: 240px minmax(400px, 1fr) 340px;
        gap: 1.5rem;
        min-height: 680px;
        margin-bottom: 2.5rem;
    }

    .assistant-left-col {
        display: flex;
        flex-direction: column;
        gap: 1.25rem;
    }

    .session-history-pane {
        background: #ffffff;
        border: 1px solid var(--border-parchment);
        border-radius: 8px;
        padding: 1.25rem;
    }

    .history-section-title {
        font-size: 0.85rem;
        font-weight: 700;
        text-transform: uppercase;
        color: var(--text-muted);
        letter-spacing: 0.05em;
        margin-bottom: 0.75rem;
    }

    .history-list {
        display: flex;
        flex-direction: column;
        gap: 8px;
    }

    .history-item {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        padding: 8px 10px;
        font-size: 0.82rem;
        color: var(--primary-dark);
        cursor: pointer;
        line-height: 1.4;
        transition: all 0.15s ease;
        text-align: left;
    }

    .history-item:hover {
        background: #fef3c7;
        border-color: var(--accent-bronze);
    }

    .citation-tag-group {
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
    }

    .citation-tag-pill {
        background: #f1f5f9;
        border: 1px solid var(--border-color);
        color: var(--accent-bronze-dark);
        font-size: 0.75rem;
        font-weight: 600;
        padding: 3px 8px;
        border-radius: 9999px;
        cursor: pointer;
        transition: all 0.15s ease;
    }

    .citation-tag-pill:hover {
        background: #fde68a;
        border-color: #b45309;
    }

    .assistant-center-col {
        display: flex;
        flex-direction: column;
        gap: 1.25rem;
    }

    .assistant-answer-stream {
        display: flex;
        flex-direction: column;
        gap: 1rem;
    }

    .research-answer-card {
        background: #ffffff;
        border: 1px solid var(--border-parchment);
        border-left: 4px solid var(--status-verified);
        border-radius: 0 8px 8px 0;
        padding: 1.5rem;
        box-shadow: var(--shadow-subtle);
    }

    .answer-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.75rem;
        flex-wrap: wrap;
        gap: 8px;
    }

    .answer-attribution-badge {
        background: var(--status-verified-bg);
        border: 1px solid #86efac;
        color: #166534;
        font-size: 0.75rem;
        font-weight: 700;
        padding: 2px 8px;
        border-radius: 9999px;
        letter-spacing: 0.04em;
    }

    .answer-text-content {
        font-size: 0.95rem;
        line-height: 1.65;
        color: var(--text-graphite);
    }

    .refusal-card {
        background: var(--status-alert-bg);
        border: 1px solid var(--status-alert-border);
        border-left: 4px solid var(--status-alert);
        border-radius: 0 8px 8px 0;
        padding: 1.5rem;
    }

    .refusal-header {
        display: flex;
        align-items: center;
        gap: 8px;
        font-weight: 700;
        color: var(--status-alert);
        font-size: 1rem;
        margin-bottom: 0.5rem;
    }

    .refusal-body {
        font-size: 0.92rem;
        color: #7f1d1d;
        line-height: 1.5;
        margin-bottom: 0.75rem;
    }

    .refusal-gate-note {
        font-size: 0.8rem;
        color: #991b1b;
        background: #fee2e2;
        padding: 6px 10px;
        border-radius: 4px;
        border-left: 3px solid #b91c1c;
    }

    /* Assistant Right Column: Persistent Evidence Drawer */
    .assistant-right-col {
        display: flex;
        flex-direction: column;
    }

    .evidence-drawer-pane {
        background: #ffffff;
        border: 1px solid var(--border-parchment);
        border-radius: 8px;
        padding: 1.25rem;
        display: flex;
        flex-direction: column;
        gap: 1rem;
        height: 100%;
    }

    .evidence-drawer-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 1px solid var(--border-color);
        padding-bottom: 0.75rem;
    }

    .citation-inspector-card {
        background: #fdfbf7;
        border: 1px solid var(--border-bronze);
        border-radius: 6px;
        padding: 12px;
        display: flex;
        flex-direction: column;
        gap: 8px;
        box-shadow: 0 1px 3px rgba(180, 83, 9, 0.08);
    }

    .citation-source-meta {
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 0.82rem;
        font-weight: 700;
        color: var(--primary-dark);
    }

    .citation-bbox-meta {
        font-family: var(--font-mono);
        font-size: 0.74rem;
        color: var(--text-muted);
        background: #f1f5f9;
        padding: 3px 6px;
        border-radius: 4px;
    }

    .citation-claim-text {
        font-size: 0.85rem;
        font-style: italic;
        color: var(--accent-bronze-dark);
        line-height: 1.5;
        border-left: 2px solid var(--accent-bronze);
        padding-left: 8px;
    }

    .btn-citation-jump {
        background: var(--accent-bronze);
        color: #ffffff;
        border: none;
        padding: 5px 10px;
        border-radius: 4px;
        font-size: 0.78rem;
        font-weight: 700;
        cursor: pointer;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 4px;
        transition: all 0.15s ease;
    }

    .btn-citation-jump:hover {
        background: var(--accent-gold);
    }

    /* --------------------------------------------------------------------------
       12. PROVENANCE CHAIN MODAL & DRAWER (R6 6-STAGE INTERACTIVE CONTINUITY)
       -------------------------------------------------------------------------- */
    .provenance-modal-content {
        background: #ffffff;
        border: 1px solid var(--border-parchment);
        border-radius: 12px;
        max-width: 780px;
        width: 100%;
        max-height: 85vh;
        overflow-y: auto;
        padding: 2rem;
        box-shadow: var(--shadow-card);
        position: relative;
    }

    .provenance-chain-bar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 4px;
        background: #0f172a;
        padding: 10px 14px;
        border-radius: 8px;
        margin-bottom: 1.5rem;
        overflow-x: auto;
    }

    .provenance-step-item {
        font-size: 0.72rem;
        font-weight: 700;
        color: #94a3b8;
        padding: 4px 8px;
        border-radius: 4px;
        cursor: pointer;
        white-space: nowrap;
        transition: all 0.15s ease;
    }

    .provenance-step-item:hover, .provenance-step-item.active {
        color: #fef3c7;
        background: #334155;
    }

    .provenance-step-arrow {
        color: var(--accent-gold);
        font-size: 0.75rem;
        font-weight: 700;
    }

    .provenance-stage-card {
        background: #f8fafc;
        border: 1px solid var(--border-color);
        border-left: 4px solid var(--accent-bronze);
        border-radius: 0 8px 8px 0;
        padding: 14px 18px;
        margin-bottom: 12px;
    }

    .provenance-stage-title {
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-weight: 700;
        color: var(--primary-dark);
        font-size: 0.92rem;
        margin-bottom: 4px;
    }

    .provenance-hash-box {
        font-family: var(--font-mono);
        font-size: 0.74rem;
        color: #475569;
        word-break: break-all;
        background: #ffffff;
        border: 1px solid #e2e8f0;
        padding: 4px 8px;
        border-radius: 4px;
        margin-top: 6px;
    }

    .provenance-details-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 6px;
        font-size: 0.78rem;
        color: var(--text-graphite);
        margin-top: 8px;
    }

    /* --------------------------------------------------------------------------
       13. INTERACTIVE HERITAGE TIMELINE (R6 CHRONOLOGICAL 1916-1956)
       -------------------------------------------------------------------------- */
    .timeline-era-bar {
        display: flex;
        align-items: center;
        gap: 8px;
        flex-wrap: wrap;
        margin-bottom: 2rem;
        background: #ffffff;
        padding: 12px 16px;
        border: 1px solid var(--border-parchment);
        border-radius: 8px;
    }

    .era-pill {
        padding: 6px 14px;
        border-radius: 9999px;
        border: 1px solid var(--border-bronze);
        background: #ffffff;
        color: var(--primary-dark);
        font-size: 0.82rem;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.2s ease;
    }

    .era-pill:hover {
        background: #fdfbf7;
        border-color: var(--accent-bronze);
    }

    .era-pill.active {
        background: var(--accent-bronze);
        color: #ffffff;
        border-color: var(--accent-gold);
    }

    .timeline-events-container {
        display: flex;
        flex-direction: column;
        gap: 1.5rem;
        max-width: 960px;
        margin: 0 auto;
    }

    .timeline-card {
        background: #ffffff;
        border: 1px solid var(--border-parchment);
        border-left: 4px solid var(--accent-bronze);
        border-radius: 0 10px 10px 0;
        padding: 1.5rem;
        box-shadow: var(--shadow-subtle);
        transition: all 0.2s ease;
    }

    .timeline-card:hover {
        box-shadow: var(--shadow-card);
        transform: translateY(-1px);
    }

    .timeline-card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
        flex-wrap: wrap;
        gap: 8px;
    }

    .timeline-date-badge {
        font-family: var(--font-mono);
        font-size: 0.82rem;
        font-weight: 700;
        color: var(--accent-bronze-dark);
        background: #fef3c7;
        padding: 2px 8px;
        border-radius: 4px;
        border: 1px solid #fde68a;
    }

    .timeline-quote {
        font-style: italic;
        color: var(--accent-bronze-dark);
        font-size: 0.9rem;
        border-left: 2px solid var(--border-bronze);
        padding-left: 12px;
        margin: 10px 0;
        line-height: 1.5;
    }

    .btn-inspect-document {
        background: var(--primary-dark);
        color: #fef3c7;
        border: 1px solid var(--accent-bronze);
        padding: 0.5rem 1rem;
        border-radius: 6px;
        font-size: 0.82rem;
        font-weight: 700;
        cursor: pointer;
        display: inline-flex;
        align-items: center;
        gap: 6px;
        margin-top: 8px;
        transition: all 0.2s ease;
    }

    .btn-inspect-document:hover {
        background: #1e293b;
        border-color: var(--accent-gold);
    }

    /* --------------------------------------------------------------------------
       14. FOOTER & RESPONSIVE LAYOUT
       -------------------------------------------------------------------------- */
    .global-footer {
        background: var(--primary-dark);
        color: #94a3b8;
        border-top: 3px solid var(--accent-bronze);
        padding: 2.5rem 1.5rem;
        margin-top: auto;
    }

    .footer-container {
        max-width: var(--max-width);
        margin: 0 auto;
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 1.5rem;
        font-size: 0.88rem;
    }

    .footer-attribution {
        color: #cbd5e1;
    }

    .footer-links {
        display: flex;
        gap: 16px;
    }

    .footer-links a {
        color: #94a3b8;
    }

    .footer-links a:hover {
        color: #f8fafc;
    }

    /* --------------------------------------------------------------------------
       MULTILINGUAL ACCESS & TRANSLATION LAYER (R7)
       -------------------------------------------------------------------------- */
    .multilingual-bar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: #fdfbf7;
        border: 1px solid var(--border-parchment);
        border-radius: 6px;
        padding: 6px 10px;
        margin-bottom: 8px;
        flex-wrap: wrap;
        gap: 8px;
    }

    .lang-toggle-group {
        display: inline-flex;
        border: 1px solid var(--border-bronze);
        border-radius: 4px;
        overflow: hidden;
        background: #ffffff;
    }

    .lang-btn {
        background: none;
        border: none;
        padding: 5px 12px;
        font-size: 0.8rem;
        font-weight: 600;
        color: var(--text-graphite);
        cursor: pointer;
        transition: all 0.15s ease;
    }

    .lang-btn.active {
        background: var(--accent-bronze);
        color: #ffffff;
    }

    .lang-btn:hover:not(.active) {
        background: #f8fafc;
        color: var(--primary-dark);
    }

    .view-original-fallback {
        font-size: 0.8rem;
        color: var(--accent-bronze);
        font-weight: 600;
        text-decoration: underline;
        cursor: pointer;
        display: inline-flex;
        align-items: center;
        gap: 4px;
    }

    .view-original-fallback:hover {
        color: var(--accent-gold);
    }

    .lang-metadata-tag {
        display: inline-block;
        padding: 2px 7px;
        border-radius: 4px;
        font-size: 0.72rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        background: #f1f5f9;
        color: #334155;
        border: 1px solid #cbd5e1;
    }

    .lang-metadata-tag[data-lang="en"], .lang-metadata-tag.lang-en {
        background: #eff6ff;
        color: #1e40af;
        border-color: #bfdbfe;
    }
    .lang-metadata-tag[data-lang="hi"], .lang-metadata-tag.lang-hi {
        background: #fef3c7;
        color: #92400e;
        border-color: #fde68a;
    }
    .lang-metadata-tag[data-lang="mr"], .lang-metadata-tag.lang-mr {
        background: #fdf2f8;
        color: #9d174d;
        border-color: #fbcfe8;
    }

    .translation-side-by-side {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 10px;
        margin-top: 6px;
    }

    .translation-col {
        background: #ffffff;
        border: 1px solid var(--border-color);
        border-radius: 6px;
        padding: 10px;
        font-size: 0.88rem;
        line-height: 1.55;
    }

    .translation-col-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 6px;
        font-weight: 700;
        font-size: 0.76rem;
        text-transform: uppercase;
        color: var(--text-muted);
        border-bottom: 1px solid #f1f5f9;
        padding-bottom: 4px;
    }

    /* --------------------------------------------------------------------------
       AUDIO-VISUAL MEDIA LIBRARY & SYNCED TRANSCRIPT (R7)
       -------------------------------------------------------------------------- */
    .media-workspace-grid {
        display: grid;
        grid-template-columns: 1.15fr 0.85fr;
        gap: 1.5rem;
        margin-top: 1rem;
    }

    .media-selector-bar {
        display: flex;
        gap: 10px;
        overflow-x: auto;
        padding-bottom: 8px;
        margin-bottom: 1.25rem;
    }

    .media-selector-card {
        flex: 1;
        min-width: 220px;
        background: #ffffff;
        border: 1px solid var(--border-color);
        border-radius: 8px;
        padding: 12px 14px;
        cursor: pointer;
        transition: all 0.2s ease;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }

    .media-selector-card:hover {
        border-color: var(--accent-bronze);
        transform: translateY(-2px);
        box-shadow: var(--shadow-card);
    }

    .media-selector-card.active {
        border: 2px solid var(--accent-bronze);
        background: #fdfbf7;
        box-shadow: var(--shadow-card);
    }

    .media-player-container {
        background: #0f172a;
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid #334155;
        box-shadow: var(--shadow-card);
        color: #f8fafc;
        display: flex;
        flex-direction: column;
    }

    .media-screen {
        background: radial-gradient(circle at center, #1e293b 0%, #020617 100%);
        min-height: 220px;
        padding: 2rem;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        text-align: center;
        position: relative;
        border-bottom: 1px solid #334155;
    }

    .waveform-bars {
        display: flex;
        gap: 4px;
        align-items: center;
        height: 48px;
        margin-top: 1rem;
    }

    .waveform-bar {
        width: 4px;
        background: var(--accent-gold);
        border-radius: 2px;
        height: 12px;
        transition: height 0.2s ease;
    }

    .waveform-bar.playing {
        animation: waveAnim 1s ease-in-out infinite alternate;
    }

    @keyframes waveAnim {
        0% { height: 8px; }
        50% { height: 42px; }
        100% { height: 16px; }
    }

    .media-controls {
        background: #090d16;
        padding: 1rem 1.5rem;
        display: flex;
        flex-direction: column;
        gap: 12px;
    }

    .media-scrubber-row {
        display: flex;
        align-items: center;
        gap: 12px;
    }

    .media-scrubber {
        flex: 1;
        -webkit-appearance: none;
        appearance: none;
        height: 6px;
        border-radius: 3px;
        background: #334155;
        outline: none;
        cursor: pointer;
    }

    .media-scrubber::-webkit-slider-thumb {
        -webkit-appearance: none;
        appearance: none;
        width: 16px;
        height: 16px;
        border-radius: 50%;
        background: var(--accent-gold);
        cursor: pointer;
        box-shadow: 0 0 6px rgba(217, 119, 6, 0.5);
    }

    .media-time-display {
        font-family: var(--font-mono);
        font-size: 0.85rem;
        color: #94a3b8;
        min-width: 90px;
        text-align: right;
    }

    .media-buttons-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 12px;
    }

    .media-btn-play {
        min-height: 48px;
        min-width: 48px;
        background: var(--accent-bronze);
        color: #ffffff;
        border: none;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.3rem;
        cursor: pointer;
        transition: all 0.2s ease;
    }

    .media-btn-play:hover {
        background: var(--accent-gold);
        transform: scale(1.05);
    }

    .media-volume-wrap {
        display: flex;
        align-items: center;
        gap: 8px;
    }

    .media-volume-slider {
        width: 80px;
        height: 5px;
        -webkit-appearance: none;
        background: #334155;
        border-radius: 3px;
        outline: none;
    }

    .synced-transcript-pane {
        background: #ffffff;
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 1.25rem;
        display: flex;
        flex-direction: column;
        max-height: 520px;
        box-shadow: var(--shadow-card);
    }

    .transcript-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding-bottom: 0.75rem;
        border-bottom: 1px solid var(--border-color);
        margin-bottom: 0.75rem;
    }

    .transcript-lines-scroll {
        overflow-y: auto;
        display: flex;
        flex-direction: column;
        gap: 10px;
        padding-right: 4px;
        flex: 1;
    }

    .transcript-line {
        padding: 10px 12px;
        border-radius: 6px;
        border: 1px solid #e2e8f0;
        background: #fdfbf7;
        cursor: pointer;
        transition: all 0.2s ease;
        line-height: 1.5;
    }

    .transcript-line:hover {
        border-color: var(--accent-bronze);
        background: #ffffff;
    }

    .transcript-line.active {
        border: 2px solid var(--accent-gold);
        background: #fffbeb;
        box-shadow: 0 2px 5px rgba(217, 119, 6, 0.15);
    }

    .transcript-time-badge {
        font-family: var(--font-mono);
        font-size: 0.75rem;
        font-weight: 700;
        color: var(--accent-bronze);
        margin-right: 6px;
    }

    .transcript-speaker-name {
        font-weight: 700;
        font-size: 0.85rem;
        color: var(--primary-dark);
        margin-bottom: 2px;
    }

    .transcript-text-body {
        font-size: 0.9rem;
        color: var(--text-graphite);
    }

    .media-context-card {
        background: #ffffff;
        border: 1px solid var(--border-color);
        border-radius: 8px;
        padding: 1.25rem;
        margin-top: 1rem;
        line-height: 1.6;
    }

    /* --------------------------------------------------------------------------
       INSTITUTIONAL ADMIN WORKSPACE & AUDIT (R7)
       -------------------------------------------------------------------------- */
    .admin-summary-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1rem;
        margin-bottom: 1.5rem;
    }

    .admin-metric-card {
        background: #ffffff;
        border: 1px solid var(--border-color);
        border-radius: 8px;
        padding: 1.25rem;
        display: flex;
        flex-direction: column;
        gap: 6px;
        box-shadow: var(--shadow-subtle);
    }

    .admin-metric-title {
        font-size: 0.78rem;
        font-weight: 700;
        text-transform: uppercase;
        color: var(--text-muted);
        letter-spacing: 0.05em;
    }

    .admin-metric-value {
        font-size: 1.5rem;
        font-weight: 800;
        color: var(--primary-dark);
        font-family: var(--font-sans);
    }

    .admin-section-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 1.5rem;
        margin-bottom: 1.5rem;
    }

    .badge-status-verified {
        background: #ecfdf5;
        border: 1px solid #10b981;
        color: #065f46;
        font-weight: 700;
        padding: 3px 8px;
        border-radius: 9999px;
        font-size: 0.75rem;
        display: inline-flex;
        align-items: center;
        gap: 4px;
    }

    .badge-status-processing {
        background: #eff6ff;
        border: 1px solid #60a5fa;
        color: #1e40af;
        font-weight: 700;
        padding: 3px 8px;
        border-radius: 9999px;
        font-size: 0.75rem;
        display: inline-flex;
        align-items: center;
        gap: 4px;
    }

    .badge-status-review {
        background: #fffbeb;
        border: 1px solid #f59e0b;
        color: #92400e;
        font-weight: 700;
        padding: 3px 8px;
        border-radius: 9999px;
        font-size: 0.75rem;
        display: inline-flex;
        align-items: center;
        gap: 4px;
    }

    .badge-status-unknown {
        background: #f1f5f9;
        border: 1px solid #94a3b8;
        color: #475569;
        font-weight: 700;
        padding: 3px 8px;
        border-radius: 9999px;
        font-size: 0.75rem;
        display: inline-flex;
        align-items: center;
        gap: 4px;
    }

    .admin-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 0.86rem;
    }

    .admin-table th {
        background: #f8fafc;
        padding: 8px 12px;
        text-align: left;
        font-weight: 700;
        color: var(--text-muted);
        border-bottom: 2px solid var(--border-color);
        font-size: 0.78rem;
        text-transform: uppercase;
    }

    .admin-table td {
        padding: 10px 12px;
        border-bottom: 1px solid #f1f5f9;
        vertical-align: middle;
    }

    .admin-table tr:hover td {
        background: #f8fafc;
    }

    .admin-sha-tag {
        font-family: var(--font-mono);
        font-size: 0.72rem;
        background: #f1f5f9;
        padding: 2px 6px;
        border-radius: 3px;
        color: var(--navy-slate);
    }

    /* Responsive adjustments */
    @media (max-width: 1024px) {
        .viewer-layout {
            grid-template-columns: 220px 1fr;
        }
        .viewer-right-col {
            grid-column: 1 / -1;
        }
        .assistant-layout {
            grid-template-columns: 1fr;
        }
    }

    @media (max-width: 768px) {
        .portal-hero h2 {
            font-size: 1.85rem;
        }
        .portal-hero {
            padding: 2rem 1.25rem;
        }
        .header-top {
            flex-direction: column;
            align-items: flex-start;
        }
        .catalog-grid {
            grid-template-columns: 1fr;
        }
        .pathways-grid {
            grid-template-columns: 1fr;
        }
        .viewer-layout {
            grid-template-columns: 1fr;
        }
    }
    """

