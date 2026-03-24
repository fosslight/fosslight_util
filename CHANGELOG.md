# Changelog

## v2.1.44 (24/03/2026)
## Changes
## 🔧 Maintenance

- Modified to search for a version that matches all major.minor.patch when provided as input @soimkim (#259)

---

## v2.1.43 (23/03/2026)
## Changes
## 🐛 Hotfixes

- Improve downloadability check and compressed file detection @dd-jy (#258)

---

## v2.1.42 (05/03/2026)
## Changes
## 🔧 Maintenance

- Remove "Type of change" section from PR default template @woocheol-lge (#257)
- Update CodeRabbit config @soimkim (#256)

---

## v2.1.41 (05/02/2026)
## Changes
## 🚀 Features

- download: improve decide_checkout ref resolution @soimkim (#253)

---

## v2.1.40 (03/02/2026)
## Changes
## 🔧 Maintenance

- Apply glob pattern matching for excluding @soimkim (#252)

---

## v2.1.39 (30/01/2026)
## Changes
## 🐛 Hotfixes

- Fix a bug that causes github's login prompt to be activated @soimkim (#247)

## 🔧 Maintenance

- Update help message @bjk7119 (#249)
- Modify excel sheet order (DEP,SRC,BIN) @dd-jy (#251)
- Fix spdx-tools==0.8.2 @bjk7119 (#248)

---

## v2.1.38 (26/01/2026)
## Changes
- Sort scanner info comment order @dd-jy (#246)

---

## v2.1.37 (20/01/2026)
## Changes
## 🔧 Maintenance

- Exclude scanner specific files / @soimkim  (#245)

---

## v2.1.36 (19/01/2026)
## Changes
## 🐛 Hotfixes

- Handle SSL verification failures at get_license_from_pom @JustinWonjaePark (#244)

---

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
