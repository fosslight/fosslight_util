# Changelog

## v2.2.11 (01/09/2026)
## Changes
## ✨ Improvements

- Look up excluded parents in a set @soimkim (#310)

---

## v2.2.10 (30/08/2026)
## Changes
## 🐛 Hotfixes

- Write log files with utf-8 encoding @soimkim (#309)

## 🔧 Maintenance

- Include DEP sheets and relax empty-row filter @bjk7119 (#300)

---

## v2.2.9 (27/08/2026)
## Changes
## 🐛 Hotfixes

- Download > derive clarified_version from the selected git ref @soimkim (#305)

## 🔧 Maintenance

- Add gradlew and gradlew.bat to exclude list @soimkim (#308)
- Exclude __tests__ directories by default. @soimkim (#307)
- Include improvement label in release drafter Features category. @soimkim (#306)

---

## v2.2.8 (23/08/2026)
## Changes
## 🔧 Maintenance

- Exclude gradle/vite/lockfiles @soimkim (#304)

---

## v2.2.7 (19/08/2026)
## Changes
## 🔧 Maintenance

- Upgrade cyclonedx-python-lib to v11 @JustinWonjaePark (#302)

---

## v2.2.6 (12/08/2026)
## Changes
## 🐛 Hotfixes

- Probe known Maven repos for sources jars @soimkim (#301)

---

## v2.2.5 (02/08/2026)
## Changes
## 🐛 Hotfixes

- Preserve 0.x.y clarified_version and match npm scope tages @soimkim (#297)

---

## v2.2.4 (28/07/2026)
## Changes
## 🔧 Maintenance

- Add size limit guard for git clone and wget downloads @bjk7119 (#295)

---

## v2.2.3 (27/07/2026)
## Changes
## 🚀 Features

- feat(download): support Packagist PHP package source download @soimkim (#296)

---

## v2.2.2 (09/07/2026)
## Changes
## 🔧 Maintenance

- Add shared running time formatting for cover and logs @bjk7119 (#288)

---

## v2.2.1 (09/07/2026)
## Changes
## 🔧 Maintenance

- Resolve repo-prefixed version tags on checkout @soimkim (#293)
- Migrate to REUSE.toml and update GitHub Actions @woocheol-lge (#292)

---

## v2.2.0 (03/07/2026)
## Changes
## 🐛 Hotfixes

- fix(oss_item): fix checksum from file content @dd-jy (#290)

## 🔧 Maintenance

- Write file:// download locations without hyperlink conversion @soimkim (#291)

---

## v2.1.64 (03/07/2026)
## Changes
## 🔧 Maintenance

- Centralize comment delimiter in COMMENT_DELIMITER constant @soimkim (#289)
- Handle None values @JustinWonjaePark (#287)

---

## v2.1.63 (02/07/2026)
## Changes
## 🐛 Hotfixes

- Resolve validated checkout ref before git clone @bjk7119 (#285)

---

## v2.1.62 (01/07/2026)
## Changes
## 🔧 Maintenance

- Hide sheets whose name starts with a dot @soimkim (#286)

---

## v2.1.61 (25/06/2026)
## Changes
## 🔧 Maintenance

- Normalize tar extraction permissions for inaccessible archives @bjk7119 (#284)

---

## v2.1.60 (09/06/2026)
## Changes
## 🔧 Maintenance

- Remove unused column header for bin. analysis @bjk7119 (#282)
- Fix license nick typo @bjk7119 (#275)

---

## v2.1.59 (26/05/2026)
## Changes
## 🔧 Maintenance

- Return resolved download links in downloader output @soimkim (#281)

---

## v2.1.58 (19/05/2026)
## Changes
## 🔧 Maintenance

- Add boundary-aware suffix fallback for git checkout ref resolution @soimkim (#280)

---

## v2.1.57 (14/05/2026)
## Changes
## 🚀 Features

- Support HTTP(S) .src.rpm and .rpm extract after wget @soimkim (#279)

---

## v2.1.56 (14/05/2026)
## Changes
## 🔧 Maintenance

- Revert "Emit major-only clarified_version for android.googlesource URLs" @soimkim (#278)

---

## v2.1.55 (06/05/2026)
## Changes
## 🔧 Maintenance

- Download > Search debina tarball across all suite tiers, not only stable @soimkim (#277)

---

## v2.1.54 (06/05/2026)
## Changes
## 🐛 Hotfixes

- Download > preserve full dotted-numeric versions for clarified_version @soimkim (#276)

---

## v2.1.53 (30/04/2026)
## Changes
## 🐛 Hotfixes

- Improve error handling for failed HTTP downloads @soimkim (#273)

## 🔧 Maintenance

- Hide URL in 'Not a downloadable link' error log @soimkim (#274)

---

## v2.1.52 (27/04/2026)
## Changes
## 🚀 Features

- Resolve Debian search URL to stable source tarball @soimkim (#270)

## 🐛 Hotfixes

- Improve HTTP mirror and direct archive handling @soimkim (#271)

## 🔧 Maintenance

- Emit major-only clarified_version for android.googlesource URLs @soimkim (#272)

---

## v2.1.51 (22/04/2026)
## Changes
## 🐛 Hotfixes

- Keep get_downloadable_url version and parse Maven x.y.z.qualifier as x.y.z @soimkim (#269)

---

## v2.1.50 (22/04/2026)
## Changes
## 🐛 Hotfixes

- Avoid overwriting get_downloadable_url version with archive filename @soimkim (#268)

---

## v2.1.49 (22/04/2026)
## Changes
## 🚀 Features

- Retry with browser and curl-like UA on mirror blocks @soimkim (#266)

## 🐛 Hotfixes

- Parse crates.io version from API/web URL for oss_version @soimkim (#267)

---

## v2.1.48 (15/04/2026)
## Changes
## 🔧 Maintenance

- Pick worksheet title when extended_header has multiple keys @soimkim (#265)

---

## v2.1.47 (09/04/2026)
## Changes
- Security upgrade pyopenssl from 25.3.0 to 26.0.0 @bjk7119 (#263)

## 🔧 Maintenance

- Improve checkout resolution and clarified_version @soimkim (#264)
