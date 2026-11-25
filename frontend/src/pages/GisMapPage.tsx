import React, { useState, useEffect, useMemo, useCallback, useRef } from 'react';
import { MapContainer, TileLayer, Popup, Circle, Polyline, useMap } from 'react-leaflet';
import L from 'leaflet';
import {
  MapPin, Layers, ShieldAlert, Copy,
  ArrowUpRight, Search, Receipt, X, RefreshCw
} from 'lucide-react';

import { GisMarker, DuplicateCandidate } from '../types';
import { api } from '../services/api';
import { RiskBadge } from '../components/RiskBadge';
import { TransactionLedgerModal } from '../components/TransactionLedgerModal';

// Helper component to center map dynamically on state/project selection
const MapController: React.FC<{
  center: [number, number];
  zoom: number;
}> = ({ center, zoom }) => {
  const map = useMap();

  useEffect(() => {
    map.invalidateSize();
    const t1 = setTimeout(() => map.invalidateSize(), 150);
    const t2 = setTimeout(() => map.invalidateSize(), 500);
    return () => {
      clearTimeout(t1);
      clearTimeout(t2);
    };
  }, [map]);

  useEffect(() => {
    map.flyTo(center, zoom, { duration: 1.0 });
  }, [center, zoom, map]);

  return null;
};

// High-Performance Native Leaflet Canvas Layer for All Projects (Zero DOM lag, silky 60 FPS)
const FastCanvasLayer: React.FC<{
  markers: GisMarker[];
  onSelectMarker: (marker: GisMarker) => void;
}> = React.memo(({ markers, onSelectMarker }) => {
  const map = useMap();

  useEffect(() => {
    if (!map) return;
    const canvas = L.canvas({ padding: 0.5 });
    const layerGroup = L.layerGroup().addTo(map);

    markers.forEach((m) => {
      const isCritical = m.risk_level === 'CRITICAL';
      const color = isCritical
        ? '#EF4444'
        : m.risk_level === 'HIGH'
        ? '#F97316'
        : m.risk_level === 'MEDIUM'
        ? '#F59E0B'
        : '#10B981';

      const cm = L.circleMarker([m.latitude, m.longitude], {
        renderer: canvas,
        radius: isCritical ? 6 : 4,
        color: '#FFFFFF',
        weight: 1,
        fillColor: color,
        fillOpacity: 0.85,
      });

      cm.on('click', () => {
        onSelectMarker(m);
      });

      layerGroup.addLayer(cm);
    });

    return () => {
      map.removeLayer(layerGroup);
    };
  }, [map, markers, onSelectMarker]);

  return null;
});

// Dedicated Twinkling Radar Ping Layer for Critical Risk Markers (Exact original pulsing ping)
const TwinkleRadarLayer: React.FC<{
  markers: GisMarker[];
  onSelectMarker: (marker: GisMarker) => void;
}> = React.memo(({ markers, onSelectMarker }) => {
  const map = useMap();
  const layerGroupRef = useRef<L.LayerGroup | null>(null);

  useEffect(() => {
    if (!map) return;
    const layerGroup = L.layerGroup().addTo(map);
    layerGroupRef.current = layerGroup;

    // Filter and sort critical markers by severity
    const criticalMarkers = markers
      .filter((m) => m.risk_level === 'CRITICAL')
      .sort((a, b) => b.overall_score - a.overall_score);

    // Exact original icon with red pulsing halo + center red dot with white border
    const twinkleIcon = L.divIcon({
      html: `
        <div style="position: relative; width: 32px; height: 32px; display: flex; align-items: center; justify-content: center; cursor: pointer;">
          <div style="position: absolute; width: 100%; height: 100%; border-radius: 50%; background: #EF4444; opacity: 0.6;" class="animate-ping"></div>
          <div style="
            width: 14px;
            height: 14px;
            background-color: #EF4444;
            border: 2px solid #ffffff;
            border-radius: 50%;
            box-shadow: 0 0 8px rgba(239,68,68,0.85);
            z-index: 10;
          "></div>
        </div>
      `,
      className: 'custom-gis-marker',
      iconSize: [32, 32],
      iconAnchor: [16, 16],
    });

    const updateVisibleTwinkles = () => {
      layerGroup.clearLayers();
      const bounds = map.getBounds();
      const zoom = map.getZoom();

      // Show top critical markers in view based on zoom level (smooth without CPU overload)
      const maxCount = zoom < 7 ? 60 : zoom < 10 ? 120 : 250;
      let count = 0;

      for (let i = 0; i < criticalMarkers.length; i++) {
        const m = criticalMarkers[i];
        if (bounds.contains([m.latitude, m.longitude])) {
          const marker = L.marker([m.latitude, m.longitude], {
            icon: twinkleIcon,
            zIndexOffset: 1000,
          });
          marker.on('click', () => onSelectMarker(m));
          layerGroup.addLayer(marker);

          count++;
          if (count >= maxCount) break;
        }
      }
    };

    updateVisibleTwinkles();

    // Debounced moveend/zoomend to guarantee 60 FPS silky smooth panning with 0 stutter
    let timer: any = null;
    const handleMove = () => {
      clearTimeout(timer);
      timer = setTimeout(updateVisibleTwinkles, 60);
    };

    map.on('moveend', handleMove);
    map.on('zoomend', handleMove);

    return () => {
      clearTimeout(timer);
      map.off('moveend', handleMove);
      map.off('zoomend', handleMove);
      map.removeLayer(layerGroup);
    };
  }, [map, markers, onSelectMarker]);

  return null;
});

interface GisMapPageProps {
  initialProjectId?: string;
  onSelectProject: (projectId: string) => void;
}

export const GisMapPage: React.FC<GisMapPageProps> = ({
  initialProjectId,
  onSelectProject,
}) => {
  const [markers, setMarkers] = useState<GisMarker[]>([]);
  const [duplicates, setDuplicates] = useState<DuplicateCandidate[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedMarker, setSelectedMarker] = useState<GisMarker | null>(null);
  const [txModalProjectId, setTxModalProjectId] = useState<string | null>(null);

  // Filters & Search
  const [stateFilter, setStateFilter] = useState('');
  const [riskFilter, setRiskFilter] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [limitOption, setLimitOption] = useState('5000');
  const [showDuplicateLinks, setShowDuplicateLinks] = useState(false);
  const [showHotspots, setShowHotspots] = useState(true);

  // Map view center & zoom
  const [mapCenter, setMapCenter] = useState<[number, number]>([20.5937, 78.9629]);
  const [mapZoom, setMapZoom] = useState(5);

  const STATE_COORDINATES: Record<string, [number, number]> = {
    'Andaman And Nicobar Islands': [11.7401, 92.6586],
    'Andhra Pradesh': [15.9129, 79.7400],
    'Arunachal Pradesh': [28.2180, 94.7278],
    'Assam': [26.2006, 92.9376],
    'Bihar': [25.0961, 85.3131],
    'Chandigarh': [30.7333, 76.7794],
    'Chhattisgarh': [21.2787, 81.8661],
    'The Dadra And Nagar Haveli And Daman And Diu': [20.1809, 73.0169],
    'Delhi': [28.7041, 77.1025],
    'Goa': [15.2993, 74.1240],
    'Gujarat': [22.2587, 71.1924],
    'Haryana': [29.0588, 76.0856],
    'Himachal Pradesh': [31.1048, 77.1734],
    'Jammu And Kashmir': [33.7782, 76.5762],
    'Jharkhand': [23.6102, 85.2799],
    'Karnataka': [15.3173, 75.7139],
    'Kerala': [10.8505, 76.2711],
    'Ladakh': [34.1526, 77.5771],
    'Lakshadweep': [10.5667, 72.6417],
    'Madhya Pradesh': [22.9734, 78.6569],
    'Maharashtra': [19.7515, 75.7139],
    'Manipur': [24.7168, 93.9412],
    'Meghalaya': [25.4670, 91.3662],
    'Mizoram': [23.1645, 92.9376],
    'Nagaland': [26.1584, 94.5624],
    'Odisha': [20.9517, 85.0985],
    'Puducherry': [11.9416, 79.8083],
    'Punjab': [31.1471, 75.3412],
    'Rajasthan': [27.0238, 74.2179],
    'Sikkim': [27.5330, 88.5122],
    'Tamil Nadu': [11.1271, 78.6569],
    'Telangana': [18.1124, 79.0193],
    'Tripura': [23.9408, 91.9882],
    'Uttar Pradesh': [26.8467, 80.9462],
    'Uttarakhand': [30.0668, 79.0193],
    'West Bengal': [22.9868, 87.8550]
  };

  const handleSelectMarker = useCallback((marker: GisMarker) => {
    setSelectedMarker(marker);
  }, []);

  const fetchMapData = async () => {
    setLoading(true);
    try {
      const effectiveLimit = stateFilter ? 100000 : parseInt(limitOption || '5000', 10);
      const [markerData, dupData] = await Promise.all([
        api.getGisMarkers({
          state: stateFilter || undefined,
          risk_level: riskFilter || undefined,
          search: searchQuery || undefined,
          include_id: initialProjectId || undefined,
          limit: effectiveLimit,
        }),
        api.listDuplicates(),
      ]);
      setMarkers(markerData);
      setDuplicates(dupData);

      // Focus on initial project if provided
      if (initialProjectId) {
        const found = markerData.find(m => m.project_id.toUpperCase() === initialProjectId.toUpperCase());
        if (found) {
          setSelectedMarker(found);
          setMapCenter([found.latitude, found.longitude]);
          setMapZoom(16);
        }
      }
    } catch (err) {
      console.error('Failed to load GIS map data:', err);
    } finally {
      setLoading(false);
    }
  };

  // When initialProjectId is provided, pre-fetch project to set state and coordinates
  useEffect(() => {
    if (initialProjectId) {
      api.getProjectDetail(initialProjectId).then((p: any) => {
        if (p) {
          if (p.state) {
            setStateFilter(p.state);
          }
          setMapCenter([p.latitude, p.longitude]);
          setMapZoom(16);
          setSelectedMarker({
            project_id: p.project_id,
            latitude: p.latitude,
            longitude: p.longitude,
            state: p.state,
            district: p.district,
            constituency: p.constituency,
            project_type: p.project_type,
            mp_id: p.mp_id,
            implementing_agency: p.implementing_agency,
            description: p.description,
            sanctioned_amount: p.sanctioned_amount,
            expenditure: p.expenditure,
            physical_progress: p.physical_progress,
            financial_progress: p.financial_progress,
            status: p.status,
            risk_level: p.risk_score?.risk_level || 'LOW',
            overall_score: p.risk_score?.overall_score || 0,
            primary_reason: p.risk_score?.reasons?.[0] || 'Normal Project'
          });
        }
      }).catch(console.error);
    }
  }, [initialProjectId]);

  useEffect(() => {
    fetchMapData();
  }, [stateFilter, riskFilter, limitOption]);

  const [filterOptions, setFilterOptions] = useState<any>(null);

  useEffect(() => {
    api.getFilterOptions().then(setFilterOptions).catch(console.error);
  }, []);

  // Adjust center when state filter changes
  useEffect(() => {
    if (stateFilter && STATE_COORDINATES[stateFilter]) {
      setMapCenter(STATE_COORDINATES[stateFilter]);
      setMapZoom(8);
    } else if (!stateFilter && !initialProjectId) {
      setMapCenter([20.5937, 78.9629]);
      setMapZoom(5);
    }
  }, [stateFilter]);

  // Build duplicate coordinate pairs for dashed line rendering
  const duplicateLines = useMemo(() => {
    if (!showDuplicateLinks) return [];
    const markerMap = new Map(markers.map(m => [m.project_id, m]));
    const lines: { id: number; positions: [number, number][]; label: string; score: number }[] = [];
    duplicates.forEach(d => {
      const a = markerMap.get(d.project_a_id);
      const b = markerMap.get(d.project_b_id);
      if (a && b) {
        // Calculate true geographic distance between the pair
        const dLat = (a.latitude - b.latitude) * 111.0;
        const dLon = (a.longitude - b.longitude) * 100.0;
        const realDistKm = Math.sqrt(dLat * dLat + dLon * dLon);

        // Only render lines for co-located duplicate pairs (within 25 km in the same area)
        if (realDistKm <= 25.0) {
          lines.push({
            id: d.id,
            positions: [
              [a.latitude, a.longitude],
              [b.latitude, b.longitude],
            ],
            label: `${d.duplicate_score}/100 Match (${realDistKm < 1 ? (realDistKm * 1000).toFixed(0) + 'm' : realDistKm.toFixed(2) + ' km'})`,
            score: d.duplicate_score,
          });
        }
      }
    });
    return lines;
  }, [showDuplicateLinks, markers, duplicates]);

  // Dynamically compute high-risk spatial hotspots from active markers
  const hotspots = useMemo(() => {
    if (!showHotspots) return [];
    const highRiskMarkers = markers.filter(m => m.risk_level === 'HIGH' || m.risk_level === 'CRITICAL');
    const districtGroups: Record<string, { lats: number[]; lons: number[]; count: number; state: string; expenditure: number }> = {};

    highRiskMarkers.forEach(m => {
      const key = `${m.district}, ${m.state}`;
      if (!districtGroups[key]) {
        districtGroups[key] = { lats: [], lons: [], count: 0, state: m.state, expenditure: 0 };
      }
      districtGroups[key].lats.push(m.latitude);
      districtGroups[key].lons.push(m.longitude);
      districtGroups[key].count += 1;
      districtGroups[key].expenditure += m.expenditure;
    });

    const list = Object.entries(districtGroups)
      .filter(([_, data]) => data.count >= 2)
      .map(([districtName, data]) => {
        const avgLat = data.lats.reduce((a, b) => a + b, 0) / data.lats.length;
        const avgLon = data.lons.reduce((a, b) => a + b, 0) / data.lons.length;
        return {
          center: [avgLat, avgLon] as [number, number],
          radius: Math.min(25000, Math.max(12000, data.count * 1500)),
          label: `${districtName} Vigilance Hotspot (${data.count} Flagged Projects, ₹${data.expenditure.toFixed(1)}L)`,
          count: data.count,
          expenditure: data.expenditure
        };
      });

    return list.slice(0, 20);
  }, [showHotspots, markers]);

  return (
    <div className="relative h-[calc(100vh-140px)] flex flex-col space-y-4 pb-4">
      {/* Top Map Filter Controls Overlay */}
      <div className="bg-white/95 border border-slate-200 rounded-2xl p-4 shadow-sm backdrop-blur-md z-20 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-blue-50 border border-blue-200 rounded-lg text-blue-600">
            <MapPin className="w-4 h-4" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-slate-900 tracking-tight">Geospatial Intelligence Map</h2>
            <p className="text-[11px] text-slate-500 font-medium">
              {loading ? (
                <span className="text-blue-600 font-semibold animate-pulse">Loading exact project coordinates...</span>
              ) : (
                <span>
                  Showing <strong className="text-slate-900 font-mono">{markers.length.toLocaleString()}</strong> projects
                  {stateFilter ? ` in ${stateFilter} (100% of state)` : ' across India (exact locations)'}
                </span>
              )}
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2 text-xs">
          {/* Instant Search Box */}
          <div className="relative">
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  fetchMapData();
                }
              }}
              placeholder="Search ID (e.g. MPLAD-77000), place..."
              className="pl-8 pr-2.5 py-1.5 bg-white border border-slate-300 rounded-lg text-xs text-slate-800 placeholder-slate-400 focus:outline-none focus:border-blue-500 w-52 shadow-2xs"
            />
          </div>

          <button
            onClick={fetchMapData}
            className="px-2.5 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-semibold text-xs transition shadow-2xs flex items-center space-x-1 cursor-pointer"
          >
            <span>Search</span>
          </button>

          {/* State Filter */}
          <select
            value={stateFilter}
            onChange={(e) => setStateFilter(e.target.value)}
            className="bg-white border border-slate-300 rounded-lg px-2.5 py-1.5 text-xs text-slate-800 focus:outline-none focus:border-blue-500 shadow-2xs font-medium"
          >
            <option value="">All States ({filterOptions?.states?.length || Object.keys(STATE_COORDINATES).length})</option>
            {(filterOptions?.states || Object.keys(STATE_COORDINATES)).map((st: string) => (
              <option key={st} value={st}>{st}</option>
            ))}
          </select>

          {/* Risk Filter */}
          <select
            value={riskFilter}
            onChange={(e) => setRiskFilter(e.target.value)}
            className="bg-white border border-slate-300 rounded-lg px-2.5 py-1.5 text-xs text-slate-800 focus:outline-none focus:border-blue-500 shadow-2xs font-medium"
          >
            <option value="">All Risk Ratings</option>
            <option value="CRITICAL">Critical Risk Only</option>
            <option value="HIGH">High Risk Only</option>
            <option value="MEDIUM">Medium Risk Only</option>
            <option value="LOW">Low Risk Only</option>
          </select>

          {/* Scope / Limit Selector for Pan-India view */}
          {!stateFilter && (
            <select
              value={limitOption}
              onChange={(e) => setLimitOption(e.target.value)}
              className="bg-white border border-slate-300 rounded-lg px-2.5 py-1.5 text-xs text-slate-800 focus:outline-none focus:border-blue-500 shadow-2xs font-medium"
              title="Marker Density Limit"
            >
              <option value="5000">5,000 Projects (Fast &amp; Smooth)</option>
              <option value="15000">15,000 Projects (Dense)</option>
              <option value="50000">50,000 Projects (Mega)</option>
              <option value="100000">All Projects (95k+ National)</option>
            </select>
          )}

          {/* Toggle Layers */}
          <button
            onClick={() => setShowDuplicateLinks(!showDuplicateLinks)}
            className={`px-2.5 py-1.5 rounded-lg border text-xs font-semibold flex items-center space-x-1.5 transition cursor-pointer ${
              showDuplicateLinks
                ? 'bg-purple-50 text-purple-700 border-purple-200'
                : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
            }`}
          >
            <Copy className="w-3.5 h-3.5" />
            <span>Duplicates</span>
          </button>

          <button
            onClick={() => setShowHotspots(!showHotspots)}
            className={`px-2.5 py-1.5 rounded-lg border text-xs font-semibold flex items-center space-x-1.5 transition cursor-pointer ${
              showHotspots
                ? 'bg-rose-50 text-rose-700 border-rose-200'
                : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
            }`}
          >
            <Layers className="w-3.5 h-3.5" />
            <span>Hotspots</span>
          </button>

          <button
            onClick={fetchMapData}
            className="p-1.5 bg-white hover:bg-slate-50 text-slate-600 rounded-lg border border-slate-200 transition shadow-2xs cursor-pointer"
            title="Refresh GIS View"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-blue-600' : ''}`} />
          </button>
        </div>
      </div>

      {/* Map Container Area */}
      <div className="relative flex-1 min-h-[550px] rounded-2xl overflow-hidden border border-slate-200 shadow-sm bg-slate-100">
        <MapContainer
          center={mapCenter}
          zoom={mapZoom}
          scrollWheelZoom={true}
          preferCanvas={true}
          style={{ height: '100%', width: '100%', minHeight: '550px' }}
        >
          <MapController center={mapCenter} zoom={mapZoom} />

          {/* Clean OpenStreetMap Basemap */}
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />

          {/* Hotspot Circles */}
          {showHotspots &&
            hotspots.map((h, i) => (
              <Circle
                key={`hotspot-${i}`}
                center={h.center}
                radius={h.radius}
                pathOptions={{
                  color: '#EF4444',
                  fillColor: '#EF4444',
                  fillOpacity: 0.12,
                  weight: 2,
                  dashArray: '4, 8',
                }}
              >
                <Popup>
                  <div className="p-2 space-y-1.5 text-xs">
                    <div className="flex items-center space-x-1.5 text-red-600 font-bold">
                      <ShieldAlert className="w-4 h-4" />
                      <span>{h.label}</span>
                    </div>
                    <p className="text-slate-600 text-[11px]">
                      Dense high-risk cluster identified. {h.count} projects flagged with severe milestone delays or cost overruns.
                    </p>
                    <div className="text-[11px] font-mono text-amber-700 font-semibold">
                      Total Capital at Risk: ₹{h.expenditure.toFixed(1)} Lakhs
                    </div>
                  </div>
                </Popup>
              </Circle>
            ))}

          {/* Duplicate Vector Lines */}
          {showDuplicateLinks &&
            duplicateLines.map((line) => (
              <Polyline
                key={`dupline-${line.id}`}
                positions={line.positions}
                pathOptions={{
                  color: '#9333EA',
                  weight: 3,
                  dashArray: '6, 6',
                  opacity: 0.85,
                }}
              >
                <Popup>
                  <div className="p-1 space-y-1 text-xs">
                    <span className="font-bold text-purple-700">Suspected Duplicate / Double Billing Link</span>
                    <p className="text-slate-600 font-mono text-[11px]">{line.label}</p>
                  </div>
                </Popup>
              </Polyline>
            ))}

          {/* High-Performance Canvas Vector Layer for All Markers */}
          <FastCanvasLayer markers={markers} onSelectMarker={handleSelectMarker} />

          {/* Original Twinkling Radar Ping Layer for Critical Risk Markers */}
          <TwinkleRadarLayer markers={markers} onSelectMarker={handleSelectMarker} />

          {/* Active Highlight Ring for Selected Project */}
          {selectedMarker && (
            <Circle
              center={[selectedMarker.latitude, selectedMarker.longitude]}
              radius={350}
              pathOptions={{
                color: '#2563EB',
                fillColor: '#3B82F6',
                fillOpacity: 0.25,
                weight: 2,
                dashArray: '4, 4',
              }}
            />
          )}

          {/* Single Dynamic Active Popup for Clicked / Selected Marker */}
          {selectedMarker && (
            <Popup
              position={[selectedMarker.latitude, selectedMarker.longitude]}
              eventHandlers={{
                remove: () => setSelectedMarker(null)
              }}
            >
              <div className="p-1.5 space-y-2 max-w-xs text-xs">
                <div className="flex items-center justify-between gap-2">
                  <span className="font-mono font-bold text-blue-700 text-sm">{selectedMarker.project_id}</span>
                  <RiskBadge level={selectedMarker.risk_level} score={selectedMarker.overall_score} size="sm" />
                </div>
                <p className="font-semibold text-slate-900 text-xs leading-snug">{selectedMarker.description}</p>
                <div className="text-[11px] text-slate-600">
                  <strong>Location:</strong> {selectedMarker.district}, {selectedMarker.state} ({selectedMarker.constituency})
                </div>
                <div className="text-[10px] text-blue-700 font-mono bg-blue-50 px-1.5 py-0.5 rounded border border-blue-200">
                  Exact GPS: {selectedMarker.latitude.toFixed(5)}° N, {selectedMarker.longitude.toFixed(5)}° E
                </div>
                <div className="pt-1 border-t border-slate-100 flex justify-between font-mono text-[11px]">
                  <span className="text-slate-700 font-semibold">Spent: ₹{selectedMarker.expenditure.toFixed(1)}L</span>
                  <span className="text-slate-700 font-semibold">Phys: {selectedMarker.physical_progress.toFixed(0)}%</span>
                </div>
                <button
                  onClick={() => onSelectProject(selectedMarker.project_id)}
                  className="w-full mt-2 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-bold text-center transition shadow-xs cursor-pointer flex items-center justify-center space-x-1"
                >
                  <span>Open Full Project File</span>
                  <ArrowUpRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </Popup>
          )}
        </MapContainer>

        {/* Floating Live Map Legend & Tally Bar */}
        <div className="absolute left-4 bottom-6 bg-white/95 border border-slate-200 rounded-2xl shadow-lg p-3 z-20 backdrop-blur-md hidden sm:flex items-center space-x-2 text-xs">
          <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Map Legend:</span>

          <button
            onClick={() => setRiskFilter(riskFilter === 'CRITICAL' ? '' : 'CRITICAL')}
            className={`flex items-center space-x-1.5 px-2 py-1 rounded-lg border transition cursor-pointer ${
              riskFilter === 'CRITICAL' ? 'bg-rose-50 border-rose-300 text-rose-700 font-bold' : 'border-transparent text-slate-700 hover:bg-slate-100'
            }`}
          >
            <span className="w-2.5 h-2.5 rounded-full bg-red-500 shrink-0 animate-pulse" />
            <span>Critical ({markers.filter(m => m.risk_level === 'CRITICAL').length})</span>
          </button>

          <button
            onClick={() => setRiskFilter(riskFilter === 'HIGH' ? '' : 'HIGH')}
            className={`flex items-center space-x-1.5 px-2 py-1 rounded-lg border transition cursor-pointer ${
              riskFilter === 'HIGH' ? 'bg-orange-50 border-orange-300 text-orange-700 font-bold' : 'border-transparent text-slate-700 hover:bg-slate-100'
            }`}
          >
            <span className="w-2.5 h-2.5 rounded-full bg-orange-500 shrink-0" />
            <span>High ({markers.filter(m => m.risk_level === 'HIGH').length})</span>
          </button>

          <button
            onClick={() => setRiskFilter(riskFilter === 'MEDIUM' ? '' : 'MEDIUM')}
            className={`flex items-center space-x-1.5 px-2 py-1 rounded-lg border transition cursor-pointer ${
              riskFilter === 'MEDIUM' ? 'bg-amber-50 border-amber-300 text-amber-700 font-bold' : 'border-transparent text-slate-700 hover:bg-slate-100'
            }`}
          >
            <span className="w-2.5 h-2.5 rounded-full bg-amber-500 shrink-0" />
            <span>Medium ({markers.filter(m => m.risk_level === 'MEDIUM').length})</span>
          </button>

          <button
            onClick={() => setRiskFilter(riskFilter === 'LOW' ? '' : 'LOW')}
            className={`flex items-center space-x-1.5 px-2 py-1 rounded-lg border transition cursor-pointer ${
              riskFilter === 'LOW' ? 'bg-emerald-50 border-emerald-300 text-emerald-700 font-bold' : 'border-transparent text-slate-700 hover:bg-slate-100'
            }`}
          >
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 shrink-0" />
            <span>Low ({markers.filter(m => m.risk_level === 'LOW').length})</span>
          </button>
        </div>

        {/* Selected Project Side Drawer Overlay */}
        {selectedMarker && (
          <div className="absolute right-4 top-4 bottom-4 w-80 bg-white/95 border border-slate-200 rounded-2xl shadow-xl p-5 z-30 backdrop-blur-md flex flex-col justify-between overflow-y-auto animate-in slide-in-from-right duration-200">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="font-mono text-base font-bold text-blue-700">{selectedMarker.project_id}</span>
                <button
                  onClick={() => setSelectedMarker(null)}
                  className="text-slate-400 hover:text-slate-700 p-1 rounded-lg hover:bg-slate-100 cursor-pointer"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              <div className="space-y-1">
                <RiskBadge level={selectedMarker.risk_level} score={selectedMarker.overall_score} size="md" />
                <p className="text-xs text-slate-500 mt-1 font-mono">
                  {selectedMarker.district}, {selectedMarker.state} ({selectedMarker.constituency})
                </p>
                <div className="text-[10px] text-blue-700 font-mono bg-blue-50 px-2 py-1 rounded border border-blue-200 mt-1">
                  GPS: {selectedMarker.latitude.toFixed(5)}° N, {selectedMarker.longitude.toFixed(5)}° E
                </div>
              </div>

              <div className="bg-slate-50 p-3.5 rounded-xl border border-slate-200 space-y-2">
                <span className="text-[10px] font-semibold uppercase text-slate-500 tracking-wider">
                  Work Description
                </span>
                <p className="text-xs font-medium text-slate-900 leading-relaxed">
                  {selectedMarker.description}
                </p>
              </div>

              {/* Quick Metrics */}
              <div className="grid grid-cols-2 gap-2 text-center text-xs">
                <div className="bg-slate-50 p-2.5 rounded-lg border border-slate-200">
                  <span className="text-[10px] text-slate-500 block font-medium">Sanctioned</span>
                  <span className="font-bold font-mono text-slate-900">₹{selectedMarker.sanctioned_amount.toFixed(1)}L</span>
                </div>
                <div className="bg-slate-50 p-2.5 rounded-lg border border-slate-200">
                  <span className="text-[10px] text-slate-500 block font-medium">Expenditure</span>
                  <span className="font-bold font-mono text-slate-900">₹{selectedMarker.expenditure.toFixed(1)}L</span>
                </div>
                <div className="bg-slate-50 p-2.5 rounded-lg border border-slate-200">
                  <span className="text-[10px] text-slate-500 block font-medium">Physical</span>
                  <span className="font-bold font-mono text-emerald-700">{selectedMarker.physical_progress.toFixed(0)}%</span>
                </div>
                <div className="bg-slate-50 p-2.5 rounded-lg border border-slate-200">
                  <span className="text-[10px] text-slate-500 block font-medium">Financial</span>
                  <span className="font-bold font-mono text-slate-900">{selectedMarker.financial_progress.toFixed(0)}%</span>
                </div>
              </div>
            </div>

            <div className="pt-3 border-t border-slate-200 space-y-2">
              <button
                onClick={() => setTxModalProjectId(selectedMarker.project_id)}
                className="w-full py-2 bg-white hover:bg-slate-50 text-emerald-700 rounded-xl font-semibold text-xs border border-emerald-200 flex items-center justify-center space-x-1.5 transition shadow-2xs cursor-pointer"
              >
                <Receipt className="w-3.5 h-3.5 text-emerald-600" />
                <span>View Transactions &amp; Payee Trail</span>
              </button>
              <button
                onClick={() => onSelectProject(selectedMarker.project_id)}
                className="w-full py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-xl font-bold text-xs shadow-sm flex items-center justify-center space-x-2 transition cursor-pointer"
              >
                <span>Investigate Full File</span>
                <ArrowUpRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Transactions & Payee Modal */}
      {txModalProjectId && (
        <TransactionLedgerModal
          projectId={txModalProjectId}
          onClose={() => setTxModalProjectId(null)}
          onSelectProject={onSelectProject}
        />
      )}
    </div>
  );
};
