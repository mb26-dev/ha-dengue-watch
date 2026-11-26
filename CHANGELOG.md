# Changelog

## 0.2.0 - 2026-11-26

Dengue Watch Thailand is now **Mosquito Watch Thailand**.

- Four mosquito-borne diseases: dengue, malaria, chikungunya and Zika.
- Several provinces in one entry, picked in the UI. Setup preselects your province and its neighbours; change them any time under *Configure*.
- New **Mosquito Watch card**, registered automatically: map of your provinces coloured by level, disease tabs, 12-week chart against the median, ranking. No YAML needed.
- Exports run one after another in the background with a pause, every 6 hours, cached on disk so values are there right after a restart.
- Existing entries are migrated; `sensor.dengue_<province>_level` keeps its entity ID.
- New banner.

## 0.1.1 - 2026-11-26

- New icon and logo: the illustrated mosquito on a blood drop, the same as in the Tropical Weather Card.
- Level sensor icon `mdi:virus-outline`.

## 0.1.0 - 2026-11-26

- First release: dengue level, cases in the last 4 weeks and cases this year for any Thai province, from the DDC Digital Disease Surveillance (Report 506), compared with the 5-year median.
