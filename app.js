// 1. Initialize the map centered on Florida
var map = L.map('map').setView([27.8, -81.5], 7);

// 2. Add a clean, journalistic basemap (CartoDB Positron)
L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
    attribution: '&copy; OpenStreetMap contributors &copy; CARTO',
    subdomains: 'abcd',
    maxZoom: 12
}).addTo(map);

// 3. Proportional sizing rule: Larger fires get larger circle markers
function getMarkerRadius(acres) {
    if (!acres || acres < 5) return 6;
    if (acres < 50) return 10;
    if (acres < 500) return 16;
    return 24; // Big footprint for massive brush/forest fires
}

// 4. Build clean, descriptive tooltips for map interactions
function onEachFire(feature, layer) {
    if (feature.properties) {
        var name = feature.properties.IncidentName || "Unnamed Incident";
        
        // 2026 property update: Map 'IncidentSize' instead of 'DailyAcres'
        var acres = feature.properties.IncidentSize ? Math.round(feature.properties.IncidentSize).toLocaleString() : "Not Reported";
        
        var containment = "Not Reported";
        if (feature.properties.PercentContained !== null && feature.properties.PercentContained !== undefined) {
            containment = feature.properties.PercentContained + "%";
        }

        var tooltipContent = `
            <div style="font-family: Arial, sans-serif; padding: 3px; line-height: 1.4;">
                <strong style="font-size: 14px; color: #d95f02; text-transform: uppercase;">🔥 ${name} Fire</strong><br/>
                <hr style="border: 0; border-top: 1px solid #eeeeee; margin: 6px 0;"/>
                <span style="font-size: 12px; color: #333333;">
                    <strong>Estimated Size:</strong> ${acres} Acres<br/>
                    <strong>Containment:</strong> ${containment}
                </span>
            </div>
        `;
        
        layer.bindTooltip(tooltipContent, { 
            sticky: true,
            className: 'custom-wildfire-tooltip'
        });

        // Highlight marker weight faintly on mouse hover
        layer.on({
            mouseover: function (e) {
                e.target.setStyle({ fillOpacity: 0.8, weight: 3 });
            },
            mouseout: function (e) {
                e.target.setStyle({ fillOpacity: 0.6, weight: 2 });
            }
        });
    }
}

// 5. Query and map the live local GeoJSON data feed
var geojsonUrl = "data/wildfires.geojson?t=" + new Date().getTime();

fetch(geojsonUrl)
    .then(function(response) {
        if (!response.ok) {
            throw new Error("No active wildfire data file found.");
        }
        return response.json();
    })
    .then(function(data) {
        L.geoJSON(data, {
            pointToLayer: function (feature, latlng) {
                // 2026 property update: Size dynamically using 'IncidentSize'
                var acres = feature.properties.IncidentSize;
                return L.circleMarker(latlng, {
                    radius: getMarkerRadius(acres),
                    fillColor: '#e34a33', // Flame orange
                    color: '#b30000',     // Dark borders
                    weight: 2,
                    fillOpacity: 0.6
                });
            },
            onEachFeature: onEachFire
        }).addTo(map);
    })
    .catch(function(error) {
        console.log("Wildfire Tracker Log:", error.message);
    });