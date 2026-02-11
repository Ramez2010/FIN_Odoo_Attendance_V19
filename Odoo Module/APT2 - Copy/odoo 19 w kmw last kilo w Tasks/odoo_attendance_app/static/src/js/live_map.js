/** @odoo-module **/
import { registry } from "@web/core/registry";
import { Component, onWillStart, onMounted, useRef, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { loadJS } from "@web/core/assets";

export class LiveMapAction extends Component {
    setup() {
        this.orm = useService("orm");
        this.http = useService("http");
        this.mapContainer = useRef("mapContainer");
        this.state = useState({
            employees: [],
            locations: [],
            loading: false,
            error: null,
            selectedEmployeeId: null,
            selectedEmployeeIds: new Set(),
            fetchingLocations: false,
            filterText: "",
        });

        this.map = null;
        this.markers = {};
        this.apiKey = "";

        onWillStart(async () => {
            await this.loadMapsApi();
            await this.fetchCheckedInEmployees();
        });

        onMounted(() => {
            this.renderMap();
        });
    }

    async loadMapsApi() {
        try {
            if (window.google && window.google.maps) {
                return;
            }
            this.apiKey = await this.orm.call("ir.config_parameter", "get_param", ["odoo_attendance_app.google_maps_api_key"]);
            if (!this.apiKey) {
                this.apiKey = await this.orm.call("ir.config_parameter", "get_param", ["google_maps_api_key"]);
            }
            if (!this.apiKey) {
                this.state.error = "Google Maps API Key is not configured.";
                return;
            }
            await loadJS(`https://maps.googleapis.com/maps/api/js?key=${this.apiKey}&libraries=places,geometry`);
        } catch (e) {
            this.state.error = "Failed to load Google Maps API.";
            console.error(e);
        }
    }

    async fetchCheckedInEmployees({ preserveSelection = false } = {}) {
        if (this.state.loading) return;
        this.state.loading = true;
        try {
            const result = await this.http.get('/api/odoo-attendance/location/checked-in-employees');
            let employees = [];
            if (Array.isArray(result)) {
                employees = result;
            } else if (result && (result.data || result.results)) {
                employees = result.data || result.results;
            }
            this.state.employees = employees;
            if (preserveSelection) {
                const current = this.state.selectedEmployeeIds;
                const allowed = new Set(this.state.employees.map(e => e.id));
                this.state.selectedEmployeeIds = new Set(
                    Array.from(current).filter(id => allowed.has(id))
                );
            } else {
                this.selectAllEmployees(true); // Select all by default
            }
            await this.fetchLatestLocations();
        } catch (e) {
            console.error(e);
            this.state.error = "Failed to fetch checked-in employees.";
        } finally {
            this.state.loading = false;
        }
    }

    async fetchLatestLocations({ fitAll = false } = {}) {
        try {
            const data = await this.orm.searchRead(
                "hr.employee.location.latest",
                [["employee_id", "in", this.state.employees.map(e => e.id)]],
                ["employee_id", "latitude", "longitude", "timestamp_utc", "reachable_status", "unreachable_reason"]
            );

            this.state.locations = data.map(d => ({
                id: d.id,
                employee_id: d.employee_id[0],
                name: d.employee_id[1],
                lat: d.latitude,
                lng: d.longitude,
                timestamp: d.timestamp_utc,
                is_reachable: d.reachable_status === 'reachable',
                unreachable_reason: d.unreachable_reason,
                time_ago: this.getTimeAgo(d.timestamp_utc),
            }));

            this.updateMarkers({ fitAll });
        } catch (e) {
            console.error(e);
            this.state.error = "Failed to fetch location data.";
        }
    }

    onEmployeeSelectionChange(emp, checked) {
        if (checked) {
            this.state.selectedEmployeeIds.add(emp.id);
        } else {
            this.state.selectedEmployeeIds.delete(emp.id);
        }
    }

    selectAllEmployees(checked) {
        if (checked) {
            this.state.selectedEmployeeIds = new Set(this.state.employees.map(e => e.id));
        } else {
            this.state.selectedEmployeeIds.clear();
        }
    }

    get filteredEmployees() {
        const q = (this.state.filterText || "").trim().toLowerCase();
        if (!q) {
            return this.state.employees;
        }
        return this.state.employees.filter(emp => {
            const name = (emp.name || "").toLowerCase();
            return name.includes(q);
        });
    }

    get areAllSelected() {
        return this.state.employees.length > 0 && this.state.selectedEmployeeIds.size === this.state.employees.length;
    }

    async requestLiveLocations() {
        if (this.state.fetchingLocations || this.state.selectedEmployeeIds.size === 0) return;

        await this.fetchCheckedInEmployees({ preserveSelection: true });
        const selectedIds = Array.from(this.state.selectedEmployeeIds);

        this.state.fetchingLocations = true;
        try {
            await this.orm.call("hr.employee", "action_request_live_location", [selectedIds]);
            setTimeout(async () => {
                await this.fetchLatestLocations({ fitAll: true });
                this.state.fetchingLocations = false;
            }, 7000);
        } catch (e) {
            console.error("Failed to request live locations", e);
            this.state.fetchingLocations = false;
        }
    }

    getTimeAgo(timestampStr) {
        if (!timestampStr) return '';
        const date = new Date(timestampStr.replace(' ', 'T') + 'Z');
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        if (diffMins < 1) return 'Just now';
        return `${diffMins} min ago`;
    }

    renderMap() {
        if (!window.google || !window.google.maps || this.state.error) return;
        if (!this.mapContainer.el) return;

        this.map = new google.maps.Map(this.mapContainer.el, {
            center: { lat: 0, lng: 0 },
            zoom: 2,
            mapTypeControl: false,
            streetViewControl: false,
        });

        this.updateMarkers();
    }

    updateMarkers({ fitAll = false } = {}) {
        if (!this.map) return;

        const currentIds = new Set(this.state.locations.map(e => e.employee_id));
        for (const id in this.markers) {
            if (!currentIds.has(parseInt(id))) {
                this.markers[id].setMap(null);
                delete this.markers[id];
            }
        }

        const bounds = new google.maps.LatLngBounds();
        let hasPoints = false;

        this.state.locations.forEach(loc => {
            if (!loc.lat || !loc.lng) {
                if (this.markers[loc.employee_id]) {
                    this.markers[loc.employee_id].setMap(null);
                    delete this.markers[loc.employee_id];
                }
                return;
            }

            const pos = { lat: loc.lat, lng: loc.lng };
            hasPoints = true;
            bounds.extend(pos);
            
            const employee = this.state.employees.find(e => e.id === loc.employee_id);

            const markerIcon = {
                path: google.maps.SymbolPath.CIRCLE,
                fillColor: loc.is_reachable ? "#28a745" : "#dc3545",
                fillOpacity: 0.9,
                strokeWeight: 2,
                strokeColor: "#ffffff",
                scale: 10,
                labelOrigin: new google.maps.Point(0, -2.5)
            };

            const markerLabel = {
                text: employee ? employee.name : '',
                color: "#1d1d1d",
                fontSize: "13px",
                fontWeight: "bold",
            };

            let marker = this.markers[loc.employee_id];
            if (!marker) {
                marker = new google.maps.Marker({
                    position: pos,
                    map: this.map,
                    title: employee ? employee.name : '',
                    icon: markerIcon,
                    label: markerLabel,
                });
                marker.addListener("click", () => {
                    this.onMarkerClick(loc);
                });
                this.markers[loc.employee_id] = marker;
            } else {
                marker.setPosition(pos);
                marker.setIcon(markerIcon);
                marker.setLabel(markerLabel);
            }
        });

        if (fitAll && hasPoints) {
            this.state.selectedEmployeeId = null;
            if (this.state.locations.length > 1) {
                this.map.fitBounds(bounds);
            } else if (this.state.locations.length === 1) {
                const loc = this.state.locations[0];
                this.map.setCenter({ lat: loc.lat, lng: loc.lng });
                this.map.setZoom(15);
            }
            return;
        }

        if (hasPoints && !this.state.selectedEmployeeId) {
            if (this.state.locations.length > 1) {
                this.map.fitBounds(bounds);
            } else if (this.state.locations.length === 1) {
                const loc = this.state.locations[0];
                this.map.setCenter({ lat: loc.lat, lng: loc.lng });
                this.map.setZoom(15);
            }
        }
    }

    onMarkerClick(loc) {
        this.state.selectedEmployeeId = loc.employee_id;
        if (loc.lat && loc.lng && this.map) {
            this.map.panTo({ lat: loc.lat, lng: loc.lng });
            this.map.setZoom(15);
        }
    }

    zoomToEmployee(employeeId) {
        const loc = this.state.locations.find(l => l.employee_id === employeeId);
        if (!loc || !loc.lat || !loc.lng || !this.map) {
            return;
        }
        this.state.selectedEmployeeId = employeeId;
        this.map.panTo({ lat: loc.lat, lng: loc.lng });
        this.map.setZoom(15);
    }

    async refreshData() {
        await this.fetchCheckedInEmployees();
    }
}

LiveMapAction.template = "odoo_attendance_app.LiveMap";
registry.category("actions").add("odoo_attendance_app.live_map", LiveMapAction);
