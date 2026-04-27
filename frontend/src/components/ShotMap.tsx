import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

export interface Shot {
  x: number;
  y: number;
  goal_mouth_y: number;
  goal_mouth_z: number;
  result: 'Goal' | 'SavedShot' | 'MissedShot' | 'BlockedShot';
  is_big_chance: boolean;
  is_left_foot: boolean;
  is_right_foot: boolean;
  is_header: boolean;
  xT: number | null;
  minute: number;
}

interface ShotMapProps {
  playerName: string;
  shots: Shot[];
  season?: string;
}

type FilterType = 'All' | 'Goal' | 'SavedShot' | 'MissedShot' | 'BlockedShot';

export const ShotMap: React.FC<ShotMapProps> = ({ playerName, shots, season = "24/25 Season" }) => {
  const [filter, setFilter] = useState<FilterType>('All');
  const [hoveredShot, setHoveredShot] = useState<{shot: Shot, x: number, y: number} | null>(null);

  // Close tooltip if user scrolls
  useEffect(() => {
    const handleScroll = () => setHoveredShot(null);
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  // Aggregate stats
  const totalShots = shots.length;
  const goals = shots.filter(s => s.result === 'Goal').length;
  const shotsOnTarget = shots.filter(s => s.result === 'Goal' || s.result === 'SavedShot').length;

  const filteredShots = filter === 'All' ? shots : shots.filter(s => s.result === filter);

  // Sorting so Goals are drawn on top, then Saved, then Missed, then Blocked
  const priority = {
    'Goal': 4,
    'SavedShot': 3,
    'MissedShot': 2,
    'BlockedShot': 1
  };
  
  const sortedShots = [...filteredShots].sort((a, b) => priority[a.result] - priority[b.result]);

  return (
    <div className="shot-map-container" onMouseLeave={() => setHoveredShot(null)}>
      {/* Header and Stats */}
      <div className="shot-map-header">
         <div className="shot-map-title-wrap">
           <h1 className="shot-map-title">{playerName} Shots</h1>
           <p className="shot-map-subtitle">
             (All shots taken during the {season} season)
           </p>
         </div>

         {/* Legend - Moved to center below subtitle */}
         <div className="shot-map-legend">
           <div className="shot-map-legend-item">
               Goal
               <div className="shot-map-legend-circle" style={{ backgroundColor: '#22C55E', borderColor: '#166534' }}></div>
           </div>
           <div className="shot-map-legend-item">
               Saved
               <div className="shot-map-legend-circle" style={{ backgroundColor: '#3B82F6', borderColor: '#1E3A8A' }}></div>
           </div>
           <div className="shot-map-legend-item">
               Missed
               <div className="shot-map-legend-circle" style={{ backgroundColor: '#F97316', borderColor: '#9A3412' }}></div>
           </div>
           <div className="shot-map-legend-item">
               Blocked
               <div className="shot-map-legend-circle" style={{ backgroundColor: '#9CA3AF', borderColor: '#374151' }}></div>
           </div>
         </div>
      </div>

      {/* Stats Row */}
      <div className="shot-map-stats">
        <div className="shot-map-stat-item">
          <span className="shot-map-stat-value" style={{ color: '#22C55E' }}>{goals}</span>
          <span className="shot-map-stat-label">Goals</span>
        </div>
        <div className="shot-map-stat-item">
          <span className="shot-map-stat-value" style={{ color: '#3B82F6' }}>{shotsOnTarget}</span>
          <span className="shot-map-stat-label">On Target</span>
        </div>
        <div className="shot-map-stat-item">
          <span className="shot-map-stat-value" style={{ color: '#112240' }}>{totalShots}</span>
          <span className="shot-map-stat-label">Total Shots</span>
        </div>
      </div>

      {/* Filters */}
      <div className="shot-map-filters">
        <button 
          className={`shot-map-filter-btn ${filter === 'All' ? 'active' : ''}`}
          onClick={() => setFilter('All')}
        >
          All Shots ({totalShots})
        </button>
        <button 
          className={`shot-map-filter-btn ${filter === 'Goal' ? 'active' : ''}`}
          onClick={() => setFilter('Goal')}
        >
          Goals ({goals})
        </button>
        <button 
          className={`shot-map-filter-btn ${filter === 'SavedShot' ? 'active' : ''}`}
          onClick={() => setFilter('SavedShot')}
        >
          Saved ({shots.filter(s => s.result === 'SavedShot').length})
        </button>
        <button 
          className={`shot-map-filter-btn ${filter === 'MissedShot' ? 'active' : ''}`}
          onClick={() => setFilter('MissedShot')}
        >
          Missed ({shots.filter(s => s.result === 'MissedShot').length})
        </button>
        <button 
          className={`shot-map-filter-btn ${filter === 'BlockedShot' ? 'active' : ''}`}
          onClick={() => setFilter('BlockedShot')}
        >
          Blocked ({shots.filter(s => s.result === 'BlockedShot').length})
        </button>
      </div>

      {/* Custom Tooltip */}
      {hoveredShot && (
        <div 
          className="shot-tooltip" 
          style={{ 
            left: `${hoveredShot.x + 15}px`, 
            top: `${hoveredShot.y + 15}px` 
          }}
        >
          <div className="shot-tooltip-row">
            <span className="shot-tooltip-label">Minute</span>
            <span className="shot-tooltip-value">{hoveredShot.shot.minute}'</span>
          </div>
          <div className="shot-tooltip-row">
            <span className="shot-tooltip-label">Outcome</span>
            <span className="shot-tooltip-value" style={{
              color: hoveredShot.shot.result === 'Goal' ? '#4ade80' : 
                     hoveredShot.shot.result === 'SavedShot' ? '#60a5fa' :
                     hoveredShot.shot.result === 'MissedShot' ? '#fb923c' : '#d1d5db'
            }}>
              {hoveredShot.shot.result.replace('Shot', '')}
            </span>
          </div>
          <div className="shot-tooltip-row">
            <span className="shot-tooltip-label">Big Chance</span>
            <span className="shot-tooltip-value">{hoveredShot.shot.is_big_chance ? 'Yes' : 'No'}</span>
          </div>
          {hoveredShot.shot.xT !== null && hoveredShot.shot.xT > 0 && (
            <div className="shot-tooltip-row">
              <span className="shot-tooltip-label">xT Value</span>
              <span className="shot-tooltip-value">{hoveredShot.shot.xT.toFixed(3)}</span>
            </div>
          )}
        </div>
      )}

      {/* SVG Pitch - The Classic Shot Map */}
      <div className="shot-map-pitch">
        <svg viewBox="0 -10 100 70" style={{ width: '100%', height: '100%', maxWidth: '800px', overflow: 'visible' }}>
          {/* Pitch Markings */}
          <g stroke="#111" strokeWidth="0.8" fill="none" strokeLinecap="round" strokeLinejoin="round">
             {/* Goal line (spans full width) */}
             <line x1="0" y1="0" x2="100" y2="0" strokeWidth="1.2" />
             
             {/* Penalty Box */}
             <rect x="21.1" y="0" width="57.8" height="17" />
             
             {/* Six Yard Box */}
             <rect x="36.8" y="0" width="26.4" height="5.8" />
             
             {/* Goal Frame */}
             <rect x="45.2" y="-3.5" width="9.6" height="3.5" strokeWidth="1.5" fill="#111" />
             
             {/* Penalty Arc */}
             <path d="M 40.5 17 A 8.7 8.7 0 0 0 59.5 17" />
             
             {/* Penalty Spot */}
             <circle cx="50" cy="11.5" r="0.5" fill="#111" stroke="none" />
          </g>

          {/* Shot Markers */}
          <AnimatePresence>
            {sortedShots.map((shot, idx) => {
               // Coordinate mapping:
               const cx = shot.y;
               const cy = 100 - shot.x;
               
               // Base size + scaler based on quality
               let r = 1.5;
               if (shot.xT) r += shot.xT * 30;
               if (shot.is_big_chance) r += 2.5;

               // Enhanced color palette for better contrast
               let fill = '#9CA3AF'; // Blocked
               let stroke = '#374151';
               if (shot.result === 'Goal') {
                   fill = '#22C55E'; // Vibrant Green
                   stroke = '#166534';
               } else if (shot.result === 'SavedShot') {
                   fill = '#3B82F6'; // Bright Blue
                   stroke = '#1E3A8A';
               } else if (shot.result === 'MissedShot') {
                   fill = '#F97316'; // Vibrant Orange
                   stroke = '#9A3412';
               }

               return (
                 <motion.g 
                   key={`${idx}-${shot.minute}-${shot.x}`} 
                   initial={{ scale: 0, opacity: 0 }} 
                   animate={{ scale: 1, opacity: 1 }} 
                   exit={{ scale: 0, opacity: 0 }}
                   transition={{ type: 'spring', bounce: 0.4 }}
                 >
                   <circle
                     cx={cx}
                     cy={cy}
                     r={r}
                     fill={fill}
                     fillOpacity={0.8}
                     stroke={stroke}
                     strokeWidth={0.3}
                     className="shot-marker"
                     onMouseEnter={(e) => setHoveredShot({ shot, x: e.clientX, y: e.clientY })}
                     onMouseMove={(e) => {
                       if (hoveredShot) setHoveredShot({ shot, x: e.clientX, y: e.clientY })
                     }}
                     onMouseLeave={() => setHoveredShot(null)}
                   />
                 </motion.g>
               );
            })}
          </AnimatePresence>
        </svg>
      </div>

    </div>
  );
};
