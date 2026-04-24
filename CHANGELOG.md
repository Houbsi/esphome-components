# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added

- **sec_touch fan**: opt-in `split_special_modes` configuration flag. When `true`, the fan entity exposes only speeds 1–6 (continuous ventilation) while levels 7–11 (Burst / Automatic Humidity / Automatic CO2 / Automatic Time / Sleep) remain reachable through the existing preset_mode dropdown. Default is `false` — existing users see no behavior change. See [`examples/split-mode.yaml`](examples/split-mode.yaml).
