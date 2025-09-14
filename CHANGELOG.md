# Changelog

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
---

## v2.1.2 (28/11/2024)
## Changes
## 🚀 Features

- Add params for cloning private git @soimkim (#201)
- Add function for downloading git with ssh_key @soimkim (#199)

## 🔧 Maintenance

- Don't change prefix for ssh link @soimkim (#200)
- Print option name with error msg @bjk7119 (#198)

---

## v2.1.1 (16/10/2024)
## Changes
## 🔧 Maintenance

- Remove spdx for macos @dd-jy (#197)
- Update compare yaml test case @dd-jy (#196)
- Remove unnecessary req-dev.txt @dd-jy (#195)

---

## v2.1.0 (08/10/2024)
## Changes
## 🚀 Features

- Update spdx function @dd-jy (#192)

## 🐛 Hotfixes

- Fix the spdx bug @dd-jy (#193, #194)
- Fix the tox bug @dd-jy (#188)

## 🔧 Maintenance

- Improving download performance when cloning based on specific branches or tags @MoonJeWoong (#190)
- Refactor existing tox test to pytest @MoonJeWoong (#189)
- Fix tox version & delete tox-wheel @bjk7119 (#186)
---

## v2.0.0 (06/09/2024)
## Changes
## 🐛 Hotfixes

- Fix printing windows version @s-cu-bot (#179)

## 🔧 Maintenance

- Refactoring OssItem @dd-jy (#175)
- Adding external calling function parameter type hints @MoonJeWoong (#177)
- Alter modules xlrd to pandas @cjho0316 (#174)

---

## v1.4.48 (22/07/2024)
## Changes
## 🐛 Hotfixes

- Fix csv format column name bug @Hosim33 (#171)

## 🔧 Maintenance

- Update CoverItem init for dynamic package versions @YongGoose (#173)

---

## v1.4.47 (16/07/2024)
## Changes
## 🐛 Hotfixes

- Fix default file extension bug @JustinWonjaePark (#168)

---

## v1.4.46 (10/07/2024)
## Changes
## 🚀 Features

- Enable multiple input for -f and -o option @JustinWonjaePark (#166)

## 🔧 Maintenance

- Fix to add sbom info one time @dd-jy (#167)

---

## v1.4.45 (10/06/2024)
## Changes
## 🐛 Hotfixes

- Fix the download alarm error @dd-jy (#163)

## 🔧 Maintenance

- Modify column name @bjk7119 (#164)

---

## v1.4.44 (29/05/2024)
## Changes
## 🔧 Maintenance

- Print TLSH, SHA1 to row from loaded yaml @bjk7119 (#162)

---

## v1.4.43 (16/05/2024)
## Changes
## 🔧 Maintenance

- Add log and cover item for excluded path @SeongjunJo (#161)

---

## v1.4.42 (08/05/2024)
## Changes
## 🚀 Features

- Add functions to clone private repository and ssh url @SeongjunJo (#159)
