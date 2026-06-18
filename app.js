// 1. Initialize the map centered on Florida with a solid statewide view
var map = L.map('map').setView([27.8, -81.5], 7);

// 2. Add a clean, journalistic basemap (CartoDB Positron)
L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
    attribution: '&copy; OpenStreetMap contributors &copy; CARTO',
    subdomains: 'abcd',
    maxZoom: 12
}).addTo(map);

// 3. Proportional sizing rule: Larger fires get larger circle markers on the map
function getMarkerRadius(acres) {
    if (!acres || acres < 5) return 6;
    if (acres < 50) return 10;
    if (acres < 500) return 16;
    return 24; // Visual emphasis for major structural or brush fires
}

// 4. Build clean, descriptive journalistic cards for the hover tooltips
function onEachFire(feature, layer) {
    if (feature.properties) {
        var name = feature.properties.IncidentName || "Unnamed Incident";
        var acres = feature.properties.DailyAcres ? Math.round(feature.properties.DailyAcres).toLocaleString() : "Not Reported";
        
        // Handle containment numbers gracefully if they haven't been entered yet
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

        // Highlight marker faintly on hover for physical desktop users
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

// 5. Query and map the live scraped database file with a cache-buster timestamp string
var geojsonUrl = "data/wildfires.geojson?t=" + new Date().getTime();

fetch(geojsonUrl)
    .then(function(response) {
        if (!response.ok) {
            throw new Error("No active wildfire database layer discovered.");
        }
        return response.json();
    })
    .then(function(data) {
        L.geoJSON(data, {
            pointToLayer: function (feature, latlng) {
                var acres = feature.properties.DailyAcres;
                return L.circleMarker(latlng, {
                    radius: getMarkerRadius(acres),
                    fillColor: '#e34a33', // Deep blaze orange/red fill
                    color: '#b30000',     // Dark crimson crisp border
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