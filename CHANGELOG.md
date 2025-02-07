# Changelog

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

---

## v1.4.41 (07/05/2024)
## Changes
## 🚀 Features

- Add depends_on, purl in yaml @dd-jy (#155)

## 🐛 Hotfixes

- Set the default link value when downloading @soimkim (#158)

## 🔧 Maintenance

- Print TLSH, SHA1 to the report @bjk7119 (#160)

---

## v1.4.40 (24/04/2024)
## Changes
## 🚀 Features

- Add Scanner info cover sheet into xlsx @dd-jy (#156)

---

## v1.4.39 (27/03/2024)
## Changes
## 🔧 Maintenance

- Add package url pattern in const @dd-jy (#153)

---

## v1.4.38 (25/03/2024)
## Changes
- Hide specific column if writing excel @bjk7119 (#151)

## 🔧 Maintenance

-  Compare col name with lower case @bjk7119 (#152)

---

## v1.4.37 (18/03/2024)
## Changes
- Hide specific column if writing excel @bjk7119 (#151)

## 🔧 Maintenance

- Add oss version when downloading with git clone @dd-jy (#149)
- Check the return value when downloading @soimkim (#148)

---

## v1.4.36 (29/01/2024)
## Changes
## 🐛 Hotfixes

- Fix the pub download url bug @dd-jy (#147)

## 🔧 Maintenance

- Use common github actions @bjk7119 (#146)

---

## v1.4.35 (19/01/2024)
## Changes
## 🔧 Maintenance

- Replace copyright delimiter to comma for csv output @JustinWonjaePark (#145)
- Add type annotation @soimkim (#144)
- Change '%40' to '@' in npm url @dd-jy (#142)

---

## v1.4.34 (31/10/2023)
## Changes
## 🐛 Hotfixes

- Fix the xlrd issue for python3.11 @dd-jy (#141)

## 🔧 Maintenance

- Add the sheet name for dependency scanner @dd-jy (#140)
- Remove unused log for debugging @soimkim (#139)

---

## v1.4.33 (17/10/2023)
## Changes
## 🐛 Hotfixes

- Fix pygit2 installation error on Windows @soimkim (#138)

---

## v1.4.32 (01/09/2023)
## Changes
## 🔧 Maintenance

- Do not add item if None @soimkim (#137)

---

## v1.4.31 (30/08/2023)
## Changes
## 🐛 Hotfixes

- Update the requirements.txt @dd-jy (#135)

---

## v1.4.30 (30/08/2023)
## Changes
## 🔧 Maintenance

- Add the is_binary variable when printing the ScanCode.json file. @soimkim (#134)
- Fix the vulnerability @dd-jy (#133)
- Fix the vulnerability @dd-jy (#132)
- [Snyk] Security upgrade setuptools from 39.0.1 to 65.5.1 @dd-jy (#131)

---

## v1.4.29 (14/08/2023)
## Changes
## 🚀 Features

- Generate ScanCode json result file @dd-jy (#129)
- Download the latest version of npm @soimkim (#126)

## 🐛 Hotfixes

- Fix the default oss name in oss list @dd-jy (#130)
- Fix the excel merge bug @dd-jy (#128)
- Fix the pub download url @dd-jy (#127)
