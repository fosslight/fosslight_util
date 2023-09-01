# Changelog

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

---

## v1.4.16 (10/02/2023)
## Changes
## 🔧 Maintenance

- Add handling for parsing yaml error @bjk7119 (#104)

---

## v1.4.15 (27/01/2023)
## Changes
## 🔧 Maintenance

- Unify version output format if  msg is none @bjk7119 (#103)
- Change package to get release package @bjk7119 (#102)
- Update version of package for actions @bjk7119 (#101)

---

## v1.4.14 (28/12/2022)
## Changes
## 🔧 Maintenance

- Add frequent license nick list file @bjk7119 (#100)
- Add *sbom_info*.yaml pattern to find oss pkg info file @bjk7119 (#99)

---

## v1.4.13 (25/11/2022)
## Changes
## 🔧 Maintenance

- Add options when parsing yaml @soimkim (#98)

---

## v1.4.12 (23/11/2022)
## 🔧 Maintenance
- Initialize the variable of the OSS Item @soimkim (#97)
- Change the python version to 3.8 in the PR action @dd-jy (#96)

---

## v1.4.11 (10/11/2022)
## Changes
## 🔧 Maintenance

- Fix the pygit2 error @dd-jy (#95)

---

## v1.4.10 (02/09/2022)
## Changes
## 🐛 Hotfixes

- Fix the error for signal @dd-jy (#94)

---

## v1.4.9 (01/09/2022)
## Changes
## 🐛 Hotfixes

- Fix to sigalrm error for windows @dd-jy (#93)

## 🔧 Maintenance

- Add a variable for yocto that loads from yaml @soimkim (#91)
- Change FOSSLIGHT -> FOSSLight in help msg @bjk7119 (#90)

---

## v1.4.8 (12/08/2022)
## Changes
## 🔧 Maintenance

- Add function to convert excel to yaml @bjk7119 (#89)
- Check if the type of item in yaml is list @soimkim (#87)

---

## v1.4.7 (09/08/2022)
## Changes
## 🔧 Maintenance

- Modify to be available .yml file for yaml parsing @bjk7119 (#86)
- Modify to convert `*sbom-info*.yaml` @bjk7119 (#85)

---

## v1.4.6 (04/08/2022)
## Changes
- Set xlrd==1.2.0 to read .xlsx file @bjk7119 (#84)

---

## v1.4.5 (01/08/2022)
## Changes
## 🐛 Hotfixes

- Fix a bug that returns even if there is no result file. @soimkim (#82)

## 🔧 Maintenance

- Check null after removing empty sheet @soimkim (#83)
- Remove unnecessary return variables @soimkim (#81)

---

## v1.4.4 (22/07/2022)
## Changes
## 🔧 Maintenance

- Fix not to create csv if format is empty @dd-jy (#80)

---

## v1.4.3 (19/07/2022)
## Changes
## 🔧 Maintenance

- Print warning msg when there is no matched sheet @bjk7119 (#79)
- Add read_excel.py file @bjk7119 (#78)
