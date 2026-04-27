import React, { useState, useMemo } from 'react';
import { motion } from 'framer-motion';

export interface PassVector {
  from_row: number;
  from_col: number;
  to_row: number;
  to_col: number;
  start_zone: string;
  start_depth: string;
  end_zone: string;
  end_depth: string;
  frequency: number;
  success_rate: number;
  avg_xT_gain: number;
  avg_prog_dist: number;
}

interface PassNetworkMapProps {
  playerName: string;
  vectors: PassVector[];
  clusterDistribution?: Record<string, number>;
  season?: string;
}

export const PassNetworkMap: React.FC<PassNetworkMapProps> = ({ 
  playerName, 
  vectors, 
  clusterDistribution,
  season = "25/26" 
}) => {
  const [minXT, setMinXT] = useState<number>(0.0);
  const [hoveredVector, setHoveredVector] = useState<{v: PassVector, x: number, y: number} | null>(null);

  // Filter and sort vectors
  // We keep vectors with frequency >= 3 to remove massive noise, and apply the xT slider
  const activeVectors = useMemo(() => {
    return vectors
      .filter(v => v.frequency >= 3 && v.avg_xT_gain >= minXT)
      .sort((a, b) => a.avg_xT_gain - b.avg_xT_gain); // Draw highest xT last (on top)
  }, [vectors, minXT]);

  // Color logic for xT and clusters suitable for a light background
  const getXTColor = (xT: number) => {
    if (xT <= 0) return '#cbd5e1'; // Neutral/Negative -> Light Slate
    if (xT < 0.02) return '#60a5fa'; // Standard Positive -> Light Blue
    if (xT < 0.05) return '#3b82f6'; // High Positive -> Royal Blue
    if (xT < 0.1) return '#f59e0b'; // Very High -> Amber
    return '#e11d48'; // Elite -> Crimson
  };

  const getClusterColor = (label: string) => {
    const l = label.toLowerCase();
    if (l.includes('progress') || l.includes('line-breaker')) return '#3b82f6';
    if (l.includes('creator') || l.includes('assist')) return '#f59e0b';
    if (l.includes('switch')) return '#8b5cf6'; // Purple for switches
    if (l.includes('recycler') || l.includes('safe')) return '#94a3b8';
    return '#64748b';
  };

  // Convert row/col to pitch percentages
  // Columns: 6 (0 to 5) -> 16.66% each
  // Rows: 5 (0 to 4) -> 20% each
  const getCoords = (r: number, c: number) => {
    return {
      x: (c + 0.5) * (100 / 6),
      y: (r + 0.5) * (100 / 5)
    };
  };

  // Sleek marker colors
  const markerColors = ['#cbd5e1', '#60a5fa', '#3b82f6', '#f59e0b', '#e11d48', '#8b5cf6', '#94a3b8'];

  return (
    <div className="pass-map-container" onMouseLeave={() => setHoveredVector(null)}>
      <div className="pass-map-header">
         <h1 className="pass-map-title">Passing Corridors & Archetype</h1>
         <p className="xt-map-subtitle">
           {playerName} • {season} Season
         </p>
      </div>

      <div className="pass-map-layout">
        {/* Left Side: Pitch Map */}
        <div className="pass-pitch-wrapper">
          <svg viewBox="0 0 100 100" style={{ width: '100%', height: '100%', display: 'block' }} preserveAspectRatio="none">
            <defs>
              {markerColors.map(color => (
                <marker 
                  key={color}
                  id={`arrow-${color.replace('#', '')}`} 
                  viewBox="0 0 10 10" 
                  refX="9" 
                  refY="5" 
                  markerWidth="4" 
                  markerHeight="4" 
                  orient="auto-start-reverse"
                >
                  <path d="M 0 2 L 8 5 L 0 8 z" fill={color} />
                </marker>
              ))}
            </defs>

            {/* Pitch Markings (Light theme) */}
            <g stroke="#cbd5e1" strokeWidth="0.4" fill="none">
              <rect x="0" y="0" width="100" height="100" />
              <line x1="50" y1="0" x2="50" y2="100" />
              <circle cx="50" cy="50" r="13.45" />
              <circle cx="50" cy="50" r="0.5" fill="#cbd5e1" />
              
              <rect x="0" y="21.1" width="15.7" height="57.8" />
              <rect x="0" y="36.8" width="5.2" height="26.4" />
              <path d="M 15.7 39.5 A 13.45 13.45 0 0 1 15.7 60.5" />

              <rect x="84.3" y="21.1" width="15.7" height="57.8" />
              <rect x="94.8" y="36.8" width="5.2" height="26.4" />
              <path d="M 84.3 39.5 A 13.45 13.45 0 0 0 84.3 60.5" />
            </g>

            <g opacity="0.4">
               <text x="50" y="95" fill="#64748b" fontSize="3" fontWeight="bold" textAnchor="middle" letterSpacing="2">
                 ATTACKING DIRECTION ➔
               </text>
            </g>

            {/* Pass Vectors */}
            {activeVectors.map((v, idx) => {
              const start = getCoords(v.from_row, v.from_col);
              const end = getCoords(v.to_row, v.to_col);
              
              const color = getXTColor(v.avg_xT_gain);
              
              // Thickness mapped to frequency. Min 0.3, Max ~2.0
              const thickness = Math.min(Math.max(v.frequency * 0.05, 0.4), 2.5);

              // If start and end are the same zone, draw a circle to indicate "recycled in zone"
              if (v.from_row === v.to_row && v.from_col === v.to_col) {
                return (
                  <motion.circle
                    key={idx}
                    cx={start.x}
                    cy={start.y}
                    r={thickness * 2}
                    fill="none"
                    stroke={color}
                    strokeWidth={thickness}
                    className="pass-vector"
                    initial={{ scale: 0, opacity: 0 }}
                    animate={{ scale: 1, opacity: 0.8 }}
                    onMouseEnter={(e) => setHoveredVector({ v, x: e.clientX, y: e.clientY })}
                    onMouseMove={(e) => {
                      if (hoveredVector) setHoveredVector({ v, x: e.clientX, y: e.clientY });
                    }}
                  />
                );
              }

              // Calculate curved path to prevent reciprocal passes from overlapping
              const dx = end.x - start.x;
              const dy = end.y - start.y;
              // Control point for Bezier curve, offset perpendicular to the line
              const cx = (start.x + end.x) / 2 - dy * 0.15; 
              const cy = (start.y + end.y) / 2 + dx * 0.15;
              const pathData = `M ${start.x} ${start.y} Q ${cx} ${cy} ${end.x} ${end.y}`;

              // Draw Line as a curve
              return (
                <motion.path
                  key={idx}
                  d={pathData}
                  stroke={color}
                  strokeWidth={thickness}
                  fill="none"
                  opacity={0.8}
                  markerEnd={`url(#arrow-${color.replace('#', '')})`}
                  className="pass-vector"
                  initial={{ pathLength: 0, opacity: 0 }}
                  animate={{ pathLength: 1, opacity: 0.8 }}
                  transition={{ duration: 0.5, delay: idx * 0.02 }}
                  onMouseEnter={(e) => setHoveredVector({ v, x: e.clientX, y: e.clientY })}
                  onMouseMove={(e) => {
                    if (hoveredVector) setHoveredVector({ v, x: e.clientX, y: e.clientY });
                  }}
                />
              );
            })}
          </svg>
        </div>

        {/* Right Side: Sidebar */}
        <div className="pass-sidebar">
          
          <div className="pass-slider-container">
            <div className="pass-slider-label">
              <span>Threat Filter (xT)</span>
              <span style={{ color: '#3b82f6' }}>&ge; {minXT.toFixed(3)}</span>
            </div>
            <input 
              type="range" 
              className="pass-slider" 
              min="-0.02" 
              max="0.08" 
              step="0.005" 
              value={minXT} 
              onChange={(e) => setMinXT(parseFloat(e.target.value))} 
            />
            <div style={{ fontSize: '0.75rem', color: '#64748b', marginTop: '4px' }}>
              Slide right to isolate highly progressive & dangerous passes.
            </div>
          </div>

          {clusterDistribution && (
            <div className="pass-clusters-container">
              <h3 className="pass-cluster-title">Passing Archetype</h3>
              
              {Object.entries(clusterDistribution)
                .sort((a, b) => b[1] - a[1]) // Sort descending by %
                .map(([label, pct]) => {
                  const percent = (pct * 100).toFixed(1);
                  const color = getClusterColor(label);
                  return (
                    <div key={label} className="pass-cluster-item">
                      <div className="pass-cluster-header">
                        <span>{label}</span>
                        <span style={{ color }}>{percent}%</span>
                      </div>
                      <div className="pass-cluster-bar-bg">
                        <div 
                          className="pass-cluster-bar-fill" 
                          style={{ width: `${percent}%`, backgroundColor: color }}
                        />
                      </div>
                    </div>
                  );
                })}
            </div>
          )}

        </div>
      </div>

      {/* Tooltip */}
      {hoveredVector && (
        <div 
          className="shot-tooltip" 
          style={{ 
            left: `${hoveredVector.x + 15}px`, 
            top: `${hoveredVector.y + 15}px`,
            borderColor: getXTColor(hoveredVector.v.avg_xT_gain),
            borderWidth: '1px',
            borderStyle: 'solid'
          }}
        >
          <div className="shot-tooltip-row">
            <span className="shot-tooltip-label">Vector</span>
            <span className="shot-tooltip-value">
              {hoveredVector.v.start_zone} ➔ {hoveredVector.v.end_zone}
            </span>
          </div>
          <div className="shot-tooltip-row">
            <span className="shot-tooltip-label">Volume</span>
            <span className="shot-tooltip-value">{hoveredVector.v.frequency} Passes</span>
          </div>
          <div className="shot-tooltip-row">
            <span className="shot-tooltip-label">Success Rate</span>
            <span className="shot-tooltip-value">{(hoveredVector.v.success_rate * 100).toFixed(1)}%</span>
          </div>
          <div className="shot-tooltip-row">
            <span className="shot-tooltip-label">Avg xT</span>
            <span className="shot-tooltip-value" style={{ color: getXTColor(hoveredVector.v.avg_xT_gain) }}>
              {hoveredVector.v.avg_xT_gain > 0 ? '+' : ''}{hoveredVector.v.avg_xT_gain.toFixed(4)}
            </span>
          </div>
        </div>
      )}

    </div>
  );
};
