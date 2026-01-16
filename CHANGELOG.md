# Changelog

## v2.1.35 (16/01/2026)
## Changes
## 🔧 Maintenance

- Exclude paths ending with / @bjk7119 (#243)

---

## v2.1.34 (13/01/2026)
## Changes
## 🐛 Hotfixes

- Fix a bug related to count files @soimkim (#242)

---

## v2.1.33 (13/01/2026)
## Changes
## 🔧 Maintenance

- Add function for getting excluded path @soimkim (#241)

---

## v2.1.32 (12/01/2026)
## Changes
## 🔧 Maintenance

- Use 256 color for 'FOSSLight' ASCII art @bjk7119 (#240)

---

## v2.1.31 (07/01/2026)
## Changes
## 🐛 Hotfixes

- Add defusedxml in requirements.txt @dd-jy (#239)

## 🔧 Maintenance

- Change 'FOSSLight' help msg style @bjk7119 (#238)

---

## v2.1.30 (11/12/2025)
## Changes
## 🚀 Features

- Get license from pom @dd-jy (#237)

---

## v2.1.29 (02/12/2025)
## Changes
## 🐛 Hotfixes

- Fix: Prevent HTML page download when no file found @soimkim (#235)

## 🔧 Maintenance

- Add maven downloadable url fallback routine @dd-jy (#236)

---

## v2.1.28 (06/11/2025)
## Changes
## 🐛 Hotfixes

- Add maven source downloadable format @dd-jy (#234)

---

## v2.1.27 (29/10/2025)
## Changes
## 🔧 Maintenance

- Add tag/branch resolution via ls-remote @dd-jy (#233)

---

## v2.1.26 (01/10/2025)
## Changes
## 🐛 Hotfixes

- Download with latest if version not exists @dd-jy (#232)

---

## v2.1.25 (25/09/2025)
## Changes
## 🐛 Hotfixes

- Prevent entering path instead of link @soimkim (#231)
- Remove duplicated copyright statement @JustinWonjaePark (#230)

---

## v2.1.24 (14/09/2025)
## Changes
## 🐛 Hotfixes

- Fix the whl download bug @dd-jy (#229)

---

## v2.1.23 (14/09/2025)
## Changes
## 🚀 Features

- Suppor pypi wheel download @dd-jy (#228)

---

## v2.1.22 (04/08/2025)
## Changes
## 🚀 Features

- Support download without ver in url using param @dd-jy (#227)

---

## v2.1.21 (22/07/2025)
## Changes
## 🚀 Features

- Add additional argument fosslight_download @dd-jy (#226)

---

## v2.1.20 (17/07/2025)
## Changes
## 🐛 Hotfixes

- Fix the url type to null when not matched @dd-jy (#224)

## 🔧 Maintenance

- Update python support ver 3.10~3.12 @dd-jy (#225)

---

## v2.1.19 (11/07/2025)
## Changes
## 🔧 Maintenance

- Replace npm package with registry.npmjs.org API @dd-jy (#223)

---

## v2.1.18 (08/07/2025)
## Changes
## 🚀 Features

- Support cargo downloadable url @dd-jy (#222)

---

## v2.1.17 (24/06/2025)
## Changes
## 🐛 Hotfixes

- Fix to prevent prompt when calling git clone with API @dd-jy (#221)

---

## v2.1.16 (18/06/2025)
## Changes
## 🐛 Hotfixes

- Encode id and key in url to clone git @dd-jy (#220)

---

## v2.1.15 (11/06/2025)
## Changes
## 🚀 Features

- Add func to get downlodable url for go @dd-jy (#218)

## 🔧 Maintenance

- Replace pkg_resources to importlib.metadata @bjk7119 (#217)

---

## v2.1.14 (05/06/2025)
## Changes
## 🔧 Maintenance

- Remove the lowercase of pypi package name @dd-jy (#216)

---

## v2.1.13 (23/05/2025)
## Changes
## 🔧 Maintenance

- Write as a string when exceeding max. url length @bjk7119 (#215)

---

## v2.1.12 (02/05/2025)
## Changes
## 🚀 Features

- Add dep info in ui result @dd-jy (#214)

## 🐛 Hotfixes

- Fix cyclonedx bug @dd-jy (#213)

---

## v2.1.11 (07/02/2025)
## Changes
## 🐛 Hotfixes

- Fix a bug that occurs when checking out with a tag @soimkim (#212)

---

## v2.1.10 (23/01/2025)
## Changes
## 🔧 Maintenance

- Add the flake8 for src dir @dd-jy (#210)

---

## v2.1.9 (23/01/2025)
## Changes
## 🔧 Maintenance

- Add excluding_files @JustinWonjaePark (#207)

---

## v2.1.8 (17/01/2025)
## Changes
## 🐛 Hotfixes

- Fix AttributeError @soimkim (#209)

---

## v2.1.7 (14/01/2025)
## Changes
## 🐛 Hotfixes

- Fix the pypi downloadable url @dd-jy (#208)

---

## v2.1.6 (05/12/2024)
## Changes
## 🐛 Hotfixes

- Fix the import bug @dd-jy (#206)
- Fix the logger issue @dd-jy (#205)
- Bug fix related to before assignment @soimkim (#203)

## 🔧 Maintenance

- Fix cyclonedx not supported @dd-jy (#204)
- Support cycloneDX format @dd-jy (#202)