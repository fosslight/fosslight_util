# Changelog

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

---

## v1.4.2 (15/07/2022)
## Changes
## 🐛 Hotfixes

- Fix bug where relpath is printed differently in yaml @soimkim (#77)

## 🔧 Maintenance

- Change error msg of parsing yaml error @bjk7119 (#76)

---

## v1.4.1 (12/07/2022)
## Changes
## 🚀 Features

- Add the function to compare yaml @dd-jy (#74)

## 🐛 Hotfixes

- Fix the error to write opossum @dd-jy (#75)

---

## v1.4.0 (16/06/2022)
## Changes
## 🚀 Features

- Add to write yaml @dd-jy (#68)

## 🐛 Hotfixes

- Add field for FOSSLight Report's BIN (*) Sheet @soimkim (#73)
- Fix the bug with ./ for path @soimkim (#72)

## 🔧 Maintenance

- Add a yaml field for file @soimkim (#71)
- Change parsing_yaml return value @bjk7119 (#70)
- Apply parsing new yaml format @bjk7119 (#69)

---

## v1.3.20 (11/05/2022)
## Changes
## 🔧 Maintenance

- Add resue output format for check_output_format fct. @bjk7119 (#67)

---

## v1.3.19 (10/05/2022)
## Changes
## 🔧 Maintenance

- Update SPDX lcense list data v3.17 @dd-jy (#66)

---

## v1.3.18 (02/05/2022)
## Changes
## 🔧 Maintenance

- Modify relative path in parsing yaml function @bjk7119 (#65)

---

## v1.3.17 (29/04/2022)
## Changes
## 🔧 Maintenance

- Add yaml parsing code @bjk7119 (#64)

---

## v1.3.16 (22/04/2022)
## Changes
## 🐛 Hotfixes

- Fix the unbound error (write_excel.py) @dd-jy (#63)

---

## v1.3.15 (14/04/2022)
## Changes
## 🐛 Hotfixes

- Fix the bug where csv name is output differently @soimkim (#62)
- Fix formatting errors that occur when dir is input @soimkim (#60)

## 🔧 Maintenance

- Add a commit message checker @soimkim (#59)
