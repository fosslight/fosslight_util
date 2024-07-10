# Changelog

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

---

## v1.4.28 (25/07/2023)
## Changes
## 🔧 Maintenance

- Fix the spdx to validate @dd-jy (#125)

---

## v1.4.27 (25/07/2023)
## Changes
## 🐛 Hotfixes

- Fix the index out of range bug @soimkim (#124)

---

## v1.4.26 (14/07/2023)
## Changes
## 🐛 Hotfixes

- Fix the issue for correct mode @dd-jy (#123)

---

## v1.4.25 (02/06/2023)
## Changes
## 🚀 Features

- Add result if path not found in scanner @dd-jy (#122)

## 🔧 Maintenance

- Fix to check exclude for correcting oss info @dd-jy (#121)
- Fix to find the sbom-info.yaml file with pattern @dd-jy (#120)

---

## v1.4.24 (19/05/2023)
## Changes
## 🚀 Features

- Add the correction with sbom-info.yaml @dd-jy (#119)

## 🐛 Hotfixes

- Fix the support default output format @dd-jy (#118)
- Modify condition to check output format @bjk7119 (#116)
- Fix the write_spdx bug @dd-jy (#117)

---

## v1.4.23 (11/05/2023)
## Changes
## 🐛 Hotfixes

- Fix the windows path for license resource @dd-jy (#114)

---

## v1.4.22 (09/05/2023)
## Changes
## 🐛 Hotfixes

- Fix the spdx-tools conflict issue @dd-jy (#115)

---

## v1.4.21 (04/05/2023)
## Changes
## 🚀 Features

- Add to generate spdx format result @dd-jy (#113)

---

## v1.4.20 (05/04/2023)
## Changes
## 🐛 Hotfixes

- Update deploy gh action version @dd-jy (#112)
- Fix the xlsxwriter save issue @dd-jy (#111)
- Fix the bug that can't print excel @soimkim (#110)

---

## v1.4.19 (07/03/2023)
## Changes
## 🚀 Features

- Be available to download src from rubygem @bjk7119 (#108)

---

## v1.4.18 (23/02/2023)
## Changes
## 🚀 Features

- Be available to download yocto url @bjk7119 (#105)

---

## v1.4.17 (23/02/2023)
## Changes
## 🔧 Maintenance

- Update the spdx-license-list-data v3.20 @dd-jy (#107)
- Add package name to log @dd-jy (#106)
