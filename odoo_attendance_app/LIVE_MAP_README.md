# Live Employees Map - Implementation & Removal Report

## 1. Removed "Live Locations" Feature
Safely removed the following legacy components:
- **Wizard**: `locate.employees.wizard` (Python & XML views removed).
- **Model**: `employee.live.location` (Python model & ACLs removed).
- **Menu**: `Locate Employees` menu item removed from `menu_items.xml`.
- **Cron**: `ir_cron_check_unreachable_locations` removed from `cron.xml`.
- **Manifest**: Removed references to deleted XML files.

## 2. New Feature: Live Employees Map
A completely new, custom module implementation using embedded Google Maps.

### Technical Components
- **Model**: `hr.employee.location.latest`
  - Stores only the single latest location per employee.
  - Automatically computes "Reachable" status based on freshness window.
- **Employee Extension**: Added `tracking_enabled` and `tracking_device_identifier` to `hr.employee`.
- **View**: Custom Client Action `odoo_attendance_app.action_live_map`.
  - **Path**: Employees -> Live Map (or via App root menu).
- **Interface**:
  - Embedded Google Maps (JS API).
  - Sidebar with employee list and real-time status.
  - Manual Refresh button.

### Configuration
1.  **Google Maps API Key**:
    - Go to **Settings -> Technical -> System Parameters**.
    - Create/Edit Key: `odoo_attendance_app.google_maps_api_key`.
    - Value: Your Google Maps JavaScript API Key.
    - *Note:* If not set, it falls back to standard `google_maps_api_key`.

2.  **Freshness Window**:
    - Defines how long a location is considered "Reachable".
    - Go to **Settings -> Technical -> System Parameters**.
    - Key: `odoo_attendance_app.live_location_timeout_minutes` (Default: 2 minutes).

3.  **Employee Setup**:
    - Open an Employee record.
    - Toggle **Live Tracking Enabled**.
    - Optionally set **Device Identifier**.
    - *Only employees with this enabled will appear on the map.*

### Mobile App Integration
The Odoo backend is ready to receive location updates.
- **Endpoint**: `/api/odoo-attendance/location/update`
- **Method**: `POST`
- **Auth**: Requires valid FIN Attendance token (JWT).
- **Payload**:
  ```json
  {
      "gps_lat": 30.0444,
      "gps_lng": 31.2357,
      "gps_accuracy": 10.5
  }
  ```
- **Behavior**: Upserts the latest record for the employee. If `tracking_enabled` is False, the update is ignored.

## Test Checklist
- [ ] **Removal**: Verify "Locate Employees" menu is gone.
- [ ] **Config**: Set a valid Google Maps API Key in System Parameters.
- [ ] **Employee**: Enable tracking for an employee.
- [ ] **Data**: Send a POST request to the endpoint (or use mobile app) to update location.
- [ ] **Map**: Open "Live Map". Verify marker appears.
- [ ] **Offline**: Wait for freshness window (2 mins). Verify status changes to "Not Reachable".
- [ ] **Disable**: Uncheck "Tracking Enabled" for employee. Verify they disappear from map after refresh.
