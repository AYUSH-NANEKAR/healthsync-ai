# HealthSync AI

HealthSync AI is a Python-based health monitoring and IoT software application designed to collect, manage, visualize, and analyze health and activity data.

## Project Goals

- Health and activity monitoring
- BLE-based device communication
- Persistent user authentication
- Secure local data storage
- AI-assisted health analysis
- Hospital discovery
- Outbreak analysis
- Future integration with custom IoT hardware

## Current Development Phase

### Phase 1 — Core Software

- PySide6 desktop UI
- Backend architecture
- SQLite persistence
- Authentication and session management
- BLE communication
- Android-based BLE health simulator
- Health and activity data processing

### Phase 2 — Intelligence & Services

- AI Analysis
- Hospital discovery
- Outbreak Analysis
- Free/open data sources
- Development of our own ML/AI components

### Phase 3 — Physical IoT

- ESP32
- Heart-rate and SpO2 sensors
- Temperature sensor
- Motion/activity sensing
- Battery monitoring
- BLE communication

## Health Parameters

### Vitals

- Heart Rate
- SpO2
- Blood Pressure
- Temperature

### Activity

- Steps
- Distance
- Calories
- Active Time

### Device

- Battery
- Device Name
- BLE Connection

### Location

- Human-readable location name
- Example: Chakan, Talegaon, Pune

## Technology

- Python
- PySide6
- SQLite
- Bluetooth Low Energy (BLE)
- Git / GitHub
- Machine Learning / AI
- Open data and APIs where required

## Architecture

The application follows a layered architecture:

UI
?
Services
?
Repositories
?
Database / BLE / External Services

The architecture is designed to keep the user interface independent from hardware and external service implementations.

## Development Philosophy

HealthSync AI is being developed incrementally with an emphasis on:

- Clean architecture
- Security
- Maintainability
- Testing
- Version control
- Hardware independence
- Zero-budget development using free and open-source technologies

## Status

?? Active development
