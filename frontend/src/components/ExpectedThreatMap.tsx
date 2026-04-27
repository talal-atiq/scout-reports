import React, { useState, useMemo } from 'react';
import { motion } from 'framer-motion';

export interface ExpectedThreatMapProps {
  playerName: string;
  grid: number[][]; // 5 rows x 6 cols (Total xT)
  perTouchGrid: number[][]; // 5 rows x 6 cols (xT per touch)
  touchDensity?: number[][]; // 5 rows x 6 cols (Touch volume/percentages)
  season?: string;
}

export const ExpectedThreatMap: React.FC<ExpectedThreatMapProps> = ({ 
  playerName, 
  grid, 
  perTouchGrid, 
  touchDensity,
  season = "25/26" 
}) => {
  const [viewMode, setViewMode] = useState<'total' | 'efficiency'>('total');
  const [hoveredCell, setHoveredCell] = useState<{r: number, c: number, x: number, y: number} | null>(null);

  const numRows = grid.length || 5;
  const numCols = grid[0]?.length || 6;

  // The Pitch is 100x100 for easy percentages. 
  // SVG coordinates: (0,0) is top-left.
  // Attack direction is Left -> Right (0 -> 100 on X axis).
  const cellWidth = 100 / numCols;
  const cellHeight = 100 / numRows;

  // Calculate maximums for color scaling
  const maxTotalXT = useMemo(() => Math.max(...grid.flat()), [grid]);
  
  // For efficiency, we need to filter out noise. If touch density is very low, ignore it for max calculation.
  const maxPerTouchXT = useMemo(() => {
    let max = 0;
    for (let r = 0; r < numRows; r++) {
      for (let c = 0; c < numCols; c++) {
        // If we have touch density data, only consider cells with > 1% of total touches as valid max candidates
        if (touchDensity && touchDensity[r] && touchDensity[r][c] < 0.01) continue;
        if (perTouchGrid[r][c] > max) max = perTouchGrid[r][c];
      }
    }
    // Fallback if all are filtered out
    if (max === 0) max = Math.max(...perTouchGrid.flat());
    return max;
  }, [perTouchGrid, touchDensity, numRows, numCols]);

  const activeGrid = viewMode === 'total' ? grid : perTouchGrid;
  const activeMax = viewMode === 'total' ? maxTotalXT : maxPerTouchXT;

  // Sequential Color Scale Function (Light Slate -> Royal Blue -> Amber -> Crimson)
  const getGlowColor = (val: number, max: number, r: number, c: number) => {
    // Noise filtering for efficiency mode
    if (viewMode === 'efficiency' && touchDensity && touchDensity[r] && touchDensity[r][c] < 0.01) {
      return 'rgba(248, 250, 252, 0)'; // Return transparent
    }

    const ratio = Math.min(Math.max(val / (max || 1), 0), 1);
    
    // Scale breakpoints
    if (ratio < 0.1) return 'rgba(248, 250, 252, 0)';
    if (ratio < 0.4) {
      // Light Slate to Royal Blue
      const alpha = (ratio - 0.1) / 0.3;
      return `rgba(59, 130, 246, ${alpha * 0.5})`; 
    }
    if (ratio < 0.7) {
      // Royal Blue to Amber
      const blend = (ratio - 0.4) / 0.3; // 0 to 1
      const red = Math.round(59 + (245 - 59) * blend);
      const green = Math.round(130 + (158 - 130) * blend);
      const blue = Math.round(246 + (11 - 246) * blend);
      return `rgba(${red}, ${green}, ${blue}, ${0.5 + blend * 0.3})`; 
    }
    // Amber to Crimson
    const blend = (ratio - 0.7) / 0.3; // 0 to 1
    const red2 = Math.round(245 + (225 - 245) * blend);
    const green2 = Math.round(158 + (29 - 158) * blend);
    const blue2 = Math.round(11 + (72 - 11) * blend);
    return `rgba(${red2}, ${green2}, ${blue2}, ${0.8 + blend * 0.2})`;
  };

  return (
    <div className="xt-map-container" onMouseLeave={() => setHoveredCell(null)}>
      
      <div className="xt-map-header">
         <h1 className="xt-map-title">Expected Threat (xT)</h1>
         <p className="xt-map-subtitle">
           Attacking Danger Generation • {season}
         </p>
         
         <div className="xt-map-controls">
           <button 
             className={`xt-map-btn ${viewMode === 'total' ? 'active' : ''}`}
             onClick={() => setViewMode('total')}
           >
             Total Volume
           </button>
           <button 
             className={`xt-map-btn ${viewMode === 'efficiency' ? 'active' : ''}`}
             onClick={() => setViewMode('efficiency')}
           >
             Efficiency (Per Touch)
           </button>
         </div>
      </div>

      <div className="xt-map-pitch-wrapper">
        <svg viewBox="0 0 100 100" style={{ width: '100%', height: '100%', display: 'block' }} preserveAspectRatio="none">
          {/* Defs for blur filter */}
          <defs>
            <filter id="xt-blur" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="4" result="blur" />
              {/* Optional: Add a slight contrast boost so the colors pop after blurring */}
              <feComponentTransfer>
                <feFuncA type="linear" slope="1.2" />
              </feComponentTransfer>
            </filter>
          </defs>

          {/* Light Pitch Background */}
          <rect x="0" y="0" width="100" height="100" fill="#f8fafc" />
          
          {/* Pitch Markings */}
          <g stroke="#cbd5e1" strokeWidth="0.4" fill="none">
            {/* Outline */}
            <rect x="0" y="0" width="100" height="100" />
            {/* Halfway line */}
            <line x1="50" y1="0" x2="50" y2="100" />
            {/* Center Circle */}
            <circle cx="50" cy="50" r="13.45" />
            {/* Center Spot */}
            <circle cx="50" cy="50" r="0.5" fill="#cbd5e1" />
            
            {/* Defensive Penalty Area (Left) */}
            <rect x="0" y="21.1" width="15.7" height="57.8" />
            {/* Defensive 6 Yard Box */}
            <rect x="0" y="36.8" width="5.2" height="26.4" />
            {/* Defensive Arc */}
            <path d="M 15.7 39.5 A 13.45 13.45 0 0 1 15.7 60.5" />

            {/* Attacking Penalty Area (Right) */}
            <rect x="84.3" y="21.1" width="15.7" height="57.8" />
            {/* Attacking 6 Yard Box */}
            <rect x="94.8" y="36.8" width="5.2" height="26.4" />
            {/* Attacking Arc */}
            <path d="M 84.3 39.5 A 13.45 13.45 0 0 0 84.3 60.5" />
          </g>

          {/* Directional Arrow Overlay */}
          <g opacity="0.4">
             <text x="50" y="95" fill="#64748b" fontSize="3" fontWeight="bold" textAnchor="middle" letterSpacing="2">
               ATTACKING DIRECTION ➔
             </text>
          </g>

          {/* Heatmap Layer with CSS Blur */}
          <g filter="url(#xt-blur)">
            {activeGrid.map((row, r) => (
              row.map((val, c) => {
                const color = getGlowColor(val, activeMax, r, c);
                return (
                  <rect 
                    key={`xt-${r}-${c}`}
                    x={c * cellWidth}
                    y={r * cellHeight}
                    width={cellWidth}
                    height={cellHeight}
                    fill={color}
                  />
                );
              })
            ))}
          </g>

          {/* Invisible Interactive Grid (Overlaying the blurred layer for crisp tooltips) */}
          <g>
            {activeGrid.map((row, r) => (
              row.map((val, c) => (
                <rect 
                  key={`interactive-${r}-${c}`}
                  x={c * cellWidth}
                  y={r * cellHeight}
                  width={cellWidth}
                  height={cellHeight}
                  fill="transparent"
                  stroke="transparent"
                  className="xt-grid-cell"
                  onMouseEnter={(e) => setHoveredCell({ r, c, x: e.clientX, y: e.clientY })}
                  onMouseMove={(e) => {
                    if (hoveredCell) setHoveredCell({ r, c, x: e.clientX, y: e.clientY });
                  }}
                />
              ))
            ))}
          </g>
        </svg>

        {/* Custom Tooltip */}
        {hoveredCell && (
          <div 
            className="shot-tooltip" 
            style={{ 
              left: `${hoveredCell.x + 15}px`, 
              top: `${hoveredCell.y + 15}px`,
              borderColor: '#00F0FF',
              borderWidth: '1px',
              borderStyle: 'solid'
            }}
          >
            <div className="shot-tooltip-row">
              <span className="shot-tooltip-label">Zone</span>
              <span className="shot-tooltip-value">R{hoveredCell.r + 1} - C{hoveredCell.c + 1}</span>
            </div>
            <div className="shot-tooltip-row">
              <span className="shot-tooltip-label">{viewMode === 'total' ? 'Total xT' : 'xT / Touch'}</span>
              <span className="shot-tooltip-value" style={{ color: '#3b82f6' }}>
                {activeGrid[hoveredCell.r][hoveredCell.c].toFixed(4)}
              </span>
            </div>
            {touchDensity && (
              <div className="shot-tooltip-row">
                <span className="shot-tooltip-label">Touch Vol.</span>
                <span className="shot-tooltip-value">
                  {(touchDensity[hoveredCell.r][hoveredCell.c] * 100).toFixed(1)}%
                </span>
              </div>
            )}
            {viewMode === 'efficiency' && touchDensity && touchDensity[hoveredCell.r][hoveredCell.c] < 0.01 && (
              <div className="shot-tooltip-row" style={{ marginTop: '4px', borderTop: 'none', color: '#EF4444', fontSize: '0.7rem' }}>
                *Low Sample Size
              </div>
            )}
          </div>
        )}
      </div>
      
    </div>
  );
};
