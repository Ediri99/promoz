# KFC Sri Lanka Promo Page — Brainstorm & Plan

## 📌 Project Overview
A single-page web app that displays current offers and promotions from KFC Sri Lanka, styled with a glassmorphism UI.

---

## 🎨 Design Direction

### Visual Style — Glassmorphism on Dark
- **Background:** Deep dark red / near-black gradient (e.g. `#1a0000` → `#2d0000` or a moody dark image/pattern)
- **Cards:** Frosted glass effect — semi-transparent white/red tint, `backdrop-filter: blur()`, soft border with `rgba` white
- **Accents:** KFC brand red (`#e4002b`) for highlights, CTAs, and badges
- **Typography:** Bold, modern sans-serif (e.g. Google Fonts: *Poppins* or *Inter*)
- **Glow effects:** Subtle red glow on hover for interactive elements

### Layout
- **Header:** KFC logo / brand name + tagline ("Hot deals. Finger Lickin' Good.")
- **Filter bar:** Tabs or pill buttons — All | Discounts | Combos | Limited Time | New Items
- **Card grid:** Responsive 3-col → 2-col → 1-col grid
- **Footer:** Simple branding line

---

## 🃏 Offer Card Anatomy
Each card contains:
- 🖼 Offer image (food photo or promo graphic)
- 🏷 Category badge (e.g. "LIMITED TIME", "NEW", "COMBO")
- 📝 Offer title (e.g. "Zinger Double Meal")
- 💬 Short description
- 💰 Price / discount info (e.g. "Rs. 890" or "20% OFF")
- ⏰ Validity date (optional)
- 🔗 "Order Now" button

---

## 🌐 Data Source Strategy

### Goal: Fetch from a real URL
**Target:** KFC Sri Lanka website — `https://kfc.lk` or their promotions page

**Approach options:**
1. **Scrape + cache** — Run a Node/Python script that scrapes `kfc.lk/promotions`, extracts offer data into a JSON, then the page loads that JSON. This keeps the page fast and avoids CORS issues.
2. **CORS proxy** — Use a public CORS proxy to fetch the KFC site client-side (fragile, not recommended for production).
3. **Hardcoded seed + refresh script** — Seed the page with real-looking current offers (manually verified from kfc.lk), with a note on how to refresh them. Best balance of reliability and authenticity.

**Recommended:** Option 3 (seed from real data) for the initial build, with a `fetch-promos.js` scraper script included for future updates.

---

## 🗂 File Structure
```
promoZ/
├── brainstorm.md          ← this file
├── index.html             ← main page (self-contained, all CSS+JS inline)
├── promos.json            ← offer data (auto-generated or manually maintained)
└── fetch-promos.js        ← Node.js scraper script (optional, for future updates)
```

---

## 🧩 Offer Categories (from answers)
| Category | Badge Color | Icon |
|---|---|---|
| Discount Deals | Red | 🏷 |
| Combo Meals | Orange | 🍗 |
| Limited-Time Offers | Yellow | ⏳ |
| New Product Launches | Green | ✨ |

---

## ✅ Implementation Checklist
- [ ] Research current KFC Sri Lanka promotions (scrape or verify manually)
- [ ] Build `promos.json` with real offer data
- [ ] Build `index.html` with glassmorphism design
- [ ] Add category filter (All / Discounts / Combos / Limited Time / New)
- [ ] Make it fully responsive (mobile-friendly)
- [ ] Test dark theme & hover effects
- [ ] Save to promoZ folder

---

## 💡 Nice-to-Have (stretch goals)
- Countdown timer on limited-time cards
- Skeleton loading animation while data fetches
- Subtle particle/smoke background animation
- Share button per offer card

