# Test Cases — OneHUB CMS Sprint 277 (TO SIT)

**Release:** v3.198.276.122 | **Period:** 30.06.2026 – 06.07.2026
**Environment:** https://ngw-stage.lighthouselabs.io/de/mofa.html

---

## One-HUB-GF-01 — VW ID Login

| # | Step | Expected Result |
|---|---|---|
| 1 | Navigate to the site and click the login button | Login page is displayed |
| 2 | Enter valid credentials and submit | Login is successful |
| 3 | Navigate to MyVolkswagen section | MyVolkswagen page loads correctly |
| 4 | Navigate to Einstellungen | Settings page opens without error |
| 5 | Click logout | User is logged out and redirected to the homepage |

**TA:** Yes | **Status:** Completed | **Platforms:** iPhone 16 iOS Safari, iPad iOS Safari, Tablet Android Chrome, Samsung Galaxy Android Chrome, Chrome Desktop, FireFox

---

## One-HUB-GF-02 — VW ID Account Management

| # | Step | Expected Result |
|---|---|---|
| 1 | Navigate to login and click "Password vergessen" | Password reset flow is initiated |
| 2 | Complete reset flow | Password reset confirmation is received |
| 3 | Navigate to account creation and create a new account | New account is created successfully |
| 4 | After removing or creating a new account, observe the merge consent screen | Merge Consent dialog appears as expected |

**TA:** No | **Status:** Not automated

---

## One-HUB-GF-03 — Navigation Flyout

| # | Step | Expected Result |
|---|---|---|
| 1 | Click the burger menu icon | Navigation Flyout opens |
| 2 | Click a Level 1 navigation item | Level 1 page navigates correctly |
| 3 | Open flyout and click a Level 2 item | Level 2 page navigates correctly |
| 4 | Open flyout and click a Level 3 item | Level 3 page navigates correctly |
| 5 | Open flyout and click the close button | Navigation Flyout closes |

**TA:** Yes | **Status:** Completed | **Platforms:** iPhone 16 iOS Safari, iPad iOS Safari, Tablet Android Chrome, Samsung Galaxy Android Chrome, Chrome Desktop, FireFox

---

## One-HUB-GF-04 — Navigation Flyout Links

| # | Step | Expected Result |
|---|---|---|
| 1 | Open flyout and click top links | Top links navigate to correct destinations |
| 2 | Click the teaser link | Teaser link navigates correctly |
| 3 | Switch language using the language switch | Language switches and content updates |
| 4 | Click Imprint link | Imprint page opens |
| 5 | Click Cookie Policy link | Cookie Policy page opens |
| 6 | Click Legal Statement link | Legal Statement page opens |
| 7 | Click Privacy Policy link | Privacy Policy page opens |
| 8 | Click Lizenzhinweise Dritter link | Lizenzhinweise Dritter page opens |

**TA:** No | **Status:** Not automated

---

## One-HUB-GF-05 — Top Bar

| # | Step | Expected Result |
|---|---|---|
| 1 | Click the VW Logo in the Top Bar | User is redirected to the homepage |
| 2 | Scroll down on any page | White bar with burger menu is visible |
| 3 | Scroll back up | Full Top Bar with burger menu, VW Logo and icons is displayed |

**TA:** Yes | **Status:** Completed | **Platforms:** iPhone 16 iOS Safari, iPad iOS Safari, Tablet Android Chrome, Samsung Galaxy Android Chrome, Chrome Desktop, FireFox

---

## One-HUB-GF-08 — Search

| # | Step | Expected Result |
|---|---|---|
| 1 | Click the Search icon | Search panel opens |
| 2 | Click the Search icon again | Search panel closes |
| 3 | Navigate to publisher site and check for Search icon | Search icon is visible |
| 4 | Enter a search term and submit | Search results are displayed correctly |

**TA:** No | **Status:** Not automated

---

## One-HUB-GF-09 — MOFA (Showroom Journey)

| # | Step | Expected Result |
|---|---|---|
| 1 | Open Navigation Flyout and select "Modelle entdecken" | MOFA Overview page loads |
| 2 | Select a car model | Car model page is displayed |
| 3 | Select a Trim level | Trim details are displayed correctly |

**TA:** Yes | **Status:** Completed | **Platforms:** iPhone 16 iOS Safari, iPad iOS Safari, Tablet Android Chrome, Samsung Galaxy Android Chrome, Chrome Desktop, FireFox

---

## One-HUB-GF-10 — Configurator

| # | Step | Expected Result |
|---|---|---|
| 1 | Open Navigation Flyout and select "Konfigurator" | Configurator journey starts |
| 2 | Select a car model | Car model is selected |
| 3 | Select a Trim level | Trim is selected |
| 4 | Proceed to the configurator and configure the car | Car is configured without errors |

**TA:** Yes | **Status:** Completed | **Platforms:** iPhone 16 iOS Safari, iPad iOS Safari, Tablet Android Chrome, Samsung Galaxy Android Chrome, Chrome Desktop, FireFox

---

## One-HUB-GF-11 — Media Elements

| # | Step | Expected Result |
|---|---|---|
| 1 | Navigate to a page with images in sections | Images are sharp and not blurred |
| 2 | Navigate to a page with animations | Animations render correctly and are not blurred |
| 3 | Navigate to a page with videos | Videos play correctly and are not blurred |

**TA:** No | **Status:** Not automated

---

## One-HUB-GF-12 — Tables

| # | Step | Expected Result |
|---|---|---|
| 1 | Navigate to a page with an existing table | Table content is complete and matches publisher configuration |

**TA:** Yes | **Status:** Completed | **Platforms:** iPhone 16 iOS Safari, iPad iOS Safari, Tablet Android Chrome, Samsung Galaxy Android Chrome, Chrome Desktop, FireFox

---

## One-HUB-GF-13 — External Link Lightbox (CMS Authoring)

| # | Step | Expected Result |
|---|---|---|
| 1 | Create the External Link Lightbox template in AEM | Template is created successfully |
| 2 | Configure Headline, Richtext and Button | Components are arranged correctly |
| 3 | Configure an external link | External link is saved |
| 4 | Create an external link | Link is created and persisted |
| 5 | Edit the External Link Lightbox | Changes are saved correctly |
| 6 | Create an internal link | Internal link is created |
| 7 | Add a link to the whitelist | Whitelisted link is displayed in the lightbox |
| 8 | Add a link to the blacklist | Blacklisted link is NOT displayed in the lightbox |

**TA:** Yes | **Status:** Completed | **Platforms:** iPhone 16 iOS Safari, iPad iOS Safari, Tablet Android Chrome, Samsung Galaxy Android Chrome, Chrome Desktop, FireFox

---

## One-HUB-GF-14 — External Link Lightbox (Render)

| # | Step | Expected Result |
|---|---|---|
| 1 | Click an external link on the published page | External Link Lightbox appears as overlay |

**TA:** Yes | **Status:** Completed | **Platforms:** iPhone 16 iOS Safari, iPad iOS Safari, Tablet Android Chrome, Samsung Galaxy Android Chrome, Chrome Desktop, FireFox

---

## One-HUB-GF-15 — Global Disclaimer

| # | Step | Expected Result |
|---|---|---|
| 1 | Navigate to MOFA Overview page | Global disclaimer is displayed |
| 2 | Navigate to Showroom page | Global disclaimer is displayed |
| 3 | Navigate to Homepage | Global disclaimer is displayed |
| 4 | Navigate to Editorial Page | Global disclaimer is displayed |
| 5 | Open a content layer | Global disclaimer is displayed |
| 6 | Navigate to Integrator Template page | Global disclaimer is displayed |

**TA:** Yes | **Status:** Completed | **Platforms:** iPhone 16 iOS Safari, iPad iOS Safari, Tablet Android Chrome, Samsung Galaxy Android Chrome, Chrome Desktop, FireFox

---

## One-HUB-GF-16 — Integrator Template

| # | Step | Expected Result |
|---|---|---|
| 1 | Open Navigation Flyout and select "Integrator" | Integrator template page loads |
| 2 | Verify Topbar and Footer on Integrator template | Topbar and Footer are displayed properly |
| 3 | Open Navigation Flyout → "Modelle und Konfigurator" → "Modelle Entdecken" | MOFA Overview page loads without error messages |

**TA:** Yes | **Status:** Completed | **Platforms:** iPhone 16 iOS Safari, iPad iOS Safari, Tablet Android Chrome, Samsung Galaxy Android Chrome, Chrome Desktop, FireFox

---

## One-HUB-GF-18 — Unsupported Browser Notification

| # | Step | Expected Result |
|---|---|---|
| 1 | Access the site using an outdated/unsupported browser | Unsupported browser notification banner is displayed |

**TA:** Yes | **Status:** Completed | **Platforms:** iPhone 16 iOS Safari, iPad iOS Safari, Tablet Android Chrome, Samsung Galaxy Android Chrome, Chrome Desktop, FireFox

---

## One-HUB-GF-19 — Breadcrumbs

| # | Step | Expected Result |
|---|---|---|
| 1 | Navigate to Homepage | No breadcrumbs are visible |
| 2 | Navigate to Editorial Overview Page (desktop/tablet) | Breadcrumbs are visible |
| 3 | Click a breadcrumb on Editorial Overview Page | Navigation goes backwards correctly |
| 4 | Resize to mobile viewport (<560px) on Editorial Overview Page | Breadcrumbs are not visible |
| 5 | Navigate to Editorial Page (desktop/tablet) | Breadcrumbs are visible |
| 6 | Click a breadcrumb on Editorial Page | Navigation goes backwards correctly |
| 7 | Resize to mobile on Editorial Page | Breadcrumbs are not visible |
| 8 | Navigate to Showroom Page (desktop/tablet) | Full path breadcrumbs are visible under stage |
| 9 | Click a breadcrumb on Showroom Page | Navigation goes backwards correctly |
| 10 | Resize to mobile on Showroom Page | Breadcrumbs are not visible |
| 11 | Navigate to Model Overview Page (desktop/tablet) | Breadcrumbs are visible |
| 12 | Navigate to Feature App Page (desktop/tablet) | Breadcrumbs are visible |

**TA:** Yes | **Status:** Completed | **Platforms:** iPhone 16 iOS Safari, iPad iOS Safari, Tablet Android Chrome, Samsung Galaxy Android Chrome, Chrome Desktop, FireFox

---

## One-HUB-GF-20 — In-Page Navigation

| # | Step | Expected Result |
|---|---|---|
| 1 | Click each item in the In-Page Navigation bar | Page scrolls to the corresponding section |
| 2 | Scroll down below the Stage | In-Page navigation bar is displayed |
| 3 | Scroll the page up and down | In-Page navigation bar remains visible |
| 4 | Verify position while scrolling | In-Page navigation bar sticks at the top |
| 5 | Compare configured inpage titles with publisher | Titles match publisher configuration |
| 6 | Configure an external link in the inpage navigation bar | External link navigates correctly |
| 7 | Configure an internal link in the inpage navigation bar | Internal link navigates correctly |

**TA:** Yes | **Status:** Completed | **Platforms:** iPhone 16 iOS Safari, iPad iOS Safari, Tablet Android Chrome, Samsung Galaxy Android Chrome, Chrome Desktop, FireFox

---

## One-HUB-GF-21 — Anchor

| # | Step | Expected Result |
|---|---|---|
| 1 | On the Showroom Page, click each anchor/focus link | Page scrolls to the corresponding section |

**TA:** Yes | **Status:** Completed | **Platforms:** iPhone 16 iOS Safari, iPad iOS Safari, Tablet Android Chrome, Samsung Galaxy Android Chrome, Chrome Desktop, FireFox

---

## One-HUB-GF-22 — Alias

| # | Step | Expected Result |
|---|---|---|
| 1 | Set an alias for a page in AEM | Alias is saved successfully |
| 2 | Access the site using the alias URL | Page loads correctly via the alias |

**TA:** Yes | **Status:** Completed | **Platforms:** iPhone 16 iOS Safari, iPad iOS Safari, Tablet Android Chrome, Samsung Galaxy Android Chrome, Chrome Desktop, FireFox

---

## One-HUB-GF-23 — Skip Links

| # | Step | Expected Result |
|---|---|---|
| 1 | Enable Skip Links in page properties | Skip Links are enabled |
| 2 | Disable Skip Links in page properties | Skip Links are disabled |
| 3 | With Skip Links enabled, access the page | Skip Links are displayed on the page |

**TA:** No | **Status:** Not automated

---

## One-HUB-GF-24 — NBAB (Activation)

| # | Step | Expected Result |
|---|---|---|
| 1 | Activate NBAB via Page Properties | NBAB is activated |
| 2 | Set NBAB to inherit via Page Properties | NBAB inheritance is configured |
| 3 | Deactivate NBAB via Page Properties | NBAB is deactivated |

**TA:** Yes | **Status:** Completed | **Platforms:** iPhone 16 iOS Safari, iPad iOS Safari, Tablet Android Chrome, Samsung Galaxy Android Chrome, Chrome Desktop, FireFox

---

## One-HUB-GF-25 — NBAB (Display Behavior)

| # | Step | Expected Result |
|---|---|---|
| 1 | Activate NBAB and open the published page | NBAB is displayed on the page |
| 2 | Open a child page with inherited NBAB | NBAB is visible on the child page |
| 3 | Override inherited NBAB on child page | Child page NBAB config overrides the parent |
| 4 | Deactivate NBAB and open the page | NBAB is not displayed |
| 5 | Configure up to 5 NBAB actions per section | All 5 actions are saved and displayed |
| 6 | Configure up to 5 NBAB actions per page | All 5 actions are saved and displayed |
| 7 | View on mobile viewport | NBABs are hidden until primary NBAB is clicked |
| 8 | View on tablet/desktop viewport | All NBABs are visible by default |

**TA:** Yes | **Status:** Completed | **Platforms:** iPhone 16 iOS Safari, iPad iOS Safari, Tablet Android Chrome, Samsung Galaxy Android Chrome, Chrome Desktop, FireFox

---

## One-HUB-GF-26 — NBAB (A/B Variants)

| # | Step | Expected Result |
|---|---|---|
| 1 | Verify 50% of users see Variant A (Circular) on mobile | NBABs hidden until primary NBAB clicked |
| 2 | Verify Variant A on tablet/desktop | All NBABs visible by default |
| 3 | Verify 50% of users see Variant B (Horizontal) on mobile with 1 NBAB | Single NBAB button shown on the right of the sticky panel |
| 4 | Verify Variant B on mobile with multiple NBABs | NBABs displayed after expanding the menu icon on the left |
| 5 | Verify Variant B on desktop | All NBABs visible by default |

**TA:** No | **Status:** Not automated

---

## One-HUB-GF-27 — URL Mapping

| # | Step | Expected Result |
|---|---|---|
| 1 | Open URL Mapping and edit an existing entry | Entry is editable |
| 2 | Save the URL entry | Entry is saved successfully |
| 3 | Publish the URL mapping | URL mapping is published and active |

**TA:** No | **Status:** Not automated

---

## One-HUB-GF-28 — Editorial Overview Page (Glossary S121)

| # | Step | Expected Result |
|---|---|---|
| 1 | Navigate to an Editorial Overview Page with S121 component | S121 with all items is displayed |
| 2 | Verify Glossary alphabet and groups/items are configured | Glossary alphabet letters are rendered |
| 3 | View the published page | Glossary alphabet is displayed on the page |

**TA:** Yes | **Status:** Completed

---

## One-HUB-GF-29 — Accessibility

| # | Step | Expected Result |
|---|---|---|
| 1 | Use keyboard (Tab/Enter) to navigate all interactive elements | Every element is reachable via keyboard |
| 2 | Use a screen reader on the page | Every element is correctly read out by the screen reader |

**TA:** No | **Status:** Not automated

---

## One-HUB-GF-30 — Wishlist

| # | Step | Expected Result |
|---|---|---|
| 1 | Add a car to the wishlist | Car is added successfully |
| 2 | Check the navigation bar | Wishlist icon is visible in the navigation bar |
| 3 | Add multiple cars and check the counter | Counter on wishlist icon matches the number of items |
| 4 | Add items via Garage and GSL | Items added via Garage & GSL appear in the wishlist |
| 5 | Open the publisher and check wishlist | Wishlist is displayed correctly in publisher |

**TA:** Not specified | **Status:** Not automated

---

## One-HUB-GF-31 — Shopping Cart

| # | Step | Expected Result |
|---|---|---|
| 1 | Check the navigation bar | Shopping Cart icon is visible |
| 2 | Open the publisher and verify Shopping Cart | Shopping Cart is displayed in publisher |
| 3 | Add items through configured shops | Items are added to the shopping cart |
| 4 | Open the shopping cart | Added items are displayed |
| 5 | Remove an item from the shopping cart | Item is removed from the cart |

**TA:** Not specified | **Status:** Not automated

---

## Coverage Summary

| Category | Count |
|---|---|
| Total Checkpoints | 28 |
| Automated (TA = Yes) | 18 |
| Manual only (TA = No) | 9 |
| Not specified | 2 |
| Completed | 18 |
| Pending / Not run | 10 |
