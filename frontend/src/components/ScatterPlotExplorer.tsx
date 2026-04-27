import React, { useState, useMemo, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { fetchScatterData, type ScatterPlayer } from '../api/client';

const METRICS: Record<string, string> = {
  goals_p90: "Goals",
  npg_p90: "Non-Penalty Goals",
  xG_p90: "Expected Goals (xG)",
  npxG_p90: "Non-Penalty xG",
  assists_p90: "Assists",
  xA_p90: "Expected Assists (xA)",
  xGChain_p90: "xG Chain",
  xGBuildup_p90: "xG Buildup",
  shots: "Shots",
  big_chances: "Big Chances",
  touches_in_box: "Touches in Box",
  box_entries: "Box Entries",
  xT_p90: "Expected Threat",
  key_passes: "Key Passes",
  progressive_passes: "Prog. Passes",
  progressive_carries: "Prog. Carries",
  dribbles: "Dribbles",
  pass_completion_pct: "Pass Cmp %",
  crosses: "Crosses",
  tackles: "Tackles",
  interceptions: "Interceptions",
  clearances: "Clearances",
  high_regains: "High Regains",
  defensive_actions: "Def. Actions",
  aerial_duels_won: "Aerials Won",
  ball_recoveries: "Ball Recoveries",
  tackle_win_pct: "Tackle Win %",
};

const LEAGUE_COLORS: Record<string, string> = {
  "Premier League": "#FF0055", // Vibrant Pink-Red
  "La Liga": "#FFB800", // Bright Gold
  "Serie A": "#00D0FF", // Bright Cyan
  "Bundesliga": "#00FF66", // Neon Green
  "Ligue 1": "#B700FF", // Neon Purple
  "Eredivisie": "#FF6B00", // Fiery Orange
  "Primeira Liga": "#FFE600", // Vivid Yellow
};

interface Props {
  theme: "blue" | "orange" | "red" | "green" | "purple";
  season?: string;
  targetPlayerName?: string;
}

export const ScatterPlotExplorer: React.FC<Props> = ({ theme, season = "2025/2026", targetPlayerName }) => {
  const [data, setData] = useState<ScatterPlayer[]>([]);
  const [loading, setLoading] = useState(true);
  
  const [xMetric, setXMetric] = useState<string>("xG_p90");
  const [yMetric, setYMetric] = useState<string>("xA_p90");
  
  const [minMinutes, setMinMinutes] = useState<number>(900);
  
  const [hovered, setHovered] = useState<ScatterPlayer | null>(null);
  const [apiError, setApiError] = useState<string>("");

  useEffect(() => {
    let active = true;
    setLoading(true);
    fetchScatterData(season, 10).then(res => {
      if (active) {
        setData(res);
        setLoading(false);
      }
    }).catch(err => {
      console.error(err);
      if (active) {
        setApiError(err?.message || String(err));
        setLoading(false);
      }
    });
    return () => { active = false; };
  }, [season]);

  const targetPlayer = useMemo(() => {
    if (!targetPlayerName || data.length === 0) return null;
    return data.find(p => p.player_name.toLowerCase() === targetPlayerName.toLowerCase()) || null;
  }, [data, targetPlayerName]);

  const filteredData = useMemo(() => {
    const targetPos = targetPlayer?.pos_group;
    return data.filter(p => {
      if (p.minutes_played < minMinutes) return false;
      // Lock filter to target player's exact position group
      if (targetPos && p.pos_group !== targetPos) return false;
      // Ensure both stats exist
      if (p.stats[xMetric] === undefined || p.stats[yMetric] === undefined) return false;
      return true;
    });
  }, [data, minMinutes, targetPlayer, xMetric, yMetric]);

  // Calculate domains with 5% padding
  const { xMin, xMax, yMin, yMax } = useMemo(() => {
    if (filteredData.length === 0) return { xMin: 0, xMax: 1, yMin: 0, yMax: 1 };
    
    let xmn = Infinity, xmx = -Infinity;
    let ymn = Infinity, ymx = -Infinity;
    
    filteredData.forEach(p => {
      const x = p.stats[xMetric] || 0;
      const y = p.stats[yMetric] || 0;
      if (x < xmn) xmn = x;
      if (x > xmx) xmx = x;
      if (y < ymn) ymn = y;
      if (y > ymx) ymx = y;
    });

    const xPad = (xmx - xmn) * 0.05 || 0.1;
    const yPad = (ymx - ymn) * 0.05 || 0.1;

    return {
      xMin: Math.max(0, xmn - xPad),
      xMax: xmx + xPad,
      yMin: Math.max(0, ymn - yPad),
      yMax: ymx + yPad
    };
  }, [filteredData, xMetric, yMetric]);

  const width = 800;
  const height = 550;
  const margin = { top: 40, right: 40, bottom: 60, left: 60 };
  const innerWidth = width - margin.left - margin.right;
  const innerHeight = height - margin.top - margin.bottom;

  const xScale = (val: number) => margin.left + ((val - xMin) / (xMax - xMin)) * innerWidth;
  const yScale = (val: number) => margin.top + innerHeight - ((val - yMin) / (yMax - yMin)) * innerHeight;

  const bgColors: Record<string, string> = {
    blue: "#f0f6ff",
    orange: "#fff4eb",
    red: "#fef2f2",
    green: "#f0fdf4",
    purple: "#f5f3ff",
  };
  const bgColor = bgColors[theme] || "#fdf5e6";

  if (loading) {
    return <div style={{ width: "100%", height: 600, display: "flex", alignItems: "center", justifyContent: "center", background: bgColor, borderRadius: 12 }}>Loading European Data...</div>;
  }

  return (
    <div style={{
      width: "100%",
      backgroundColor: bgColor,
      borderRadius: "12px",
      padding: "2rem",
      boxShadow: "0 10px 15px -3px rgba(0, 0, 0, 0.1)",
      border: "1px solid #e8dcc4",
      fontFamily: "sans-serif",
      position: "relative"
    }}>
      
      {/* Header & Controls */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", marginBottom: "1.5rem" }}>
        <div>
          <h2 style={{ margin: 0, fontSize: "1.8rem", fontWeight: 900, color: "#111", letterSpacing: "-0.02em" }}>
            European Transfer Landscape
          </h2>
          <div style={{ display: "flex", gap: "1rem", marginTop: "0.5rem" }}>
             {/* League Legend */}
             {Object.keys(LEAGUE_COLORS).slice(0, 5).map(league => (
               <div 
                 key={league} 
                 style={{ display: "flex", alignItems: "center", gap: "6px" }}
               >
                 <div style={{ width: 12, height: 12, borderRadius: "50%", background: LEAGUE_COLORS[league], border: "1.5px solid #111" }} />
                 <span style={{ fontSize: "0.85rem", fontWeight: 600, color: "#111" }}>{league}</span>
               </div>
             ))}
          </div>
        </div>

        {/* Dropdowns */}
        <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem", alignItems: "flex-end" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
            <span style={{ fontSize: "0.75rem", fontWeight: 700, textTransform: "uppercase", color: "#64748b" }}>Min Mins</span>
            <input 
              type="range" 
              min="0" max="2500" step="100" 
              value={minMinutes} 
              onChange={e => setMinMinutes(Number(e.target.value))}
              style={{ width: "80px" }}
            />
            <span style={{ fontSize: "0.75rem", fontWeight: 700, color: "#111", width: "36px", textAlign: "right" }}>{minMinutes}</span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
            <span style={{ fontSize: "0.75rem", fontWeight: 700, textTransform: "uppercase", color: "#64748b" }}>Y-Axis</span>
            <select 
              value={yMetric} 
              onChange={e => setYMetric(e.target.value)}
              style={{ padding: "4px 8px", borderRadius: 4, border: "1px solid #cbd5e1", fontSize: "0.85rem", fontWeight: 600, width: 180 }}
            >
              {Object.entries(METRICS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
            </select>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
            <span style={{ fontSize: "0.75rem", fontWeight: 700, textTransform: "uppercase", color: "#64748b" }}>X-Axis</span>
            <select 
              value={xMetric} 
              onChange={e => setXMetric(e.target.value)}
              style={{ padding: "4px 8px", borderRadius: 4, border: "1px solid #cbd5e1", fontSize: "0.85rem", fontWeight: 600, width: 180 }}
            >
              {Object.entries(METRICS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
            </select>
          </div>
        </div>
      </div>

      {/* The Scatter Plot */}
      <div style={{ position: "relative", width: "100%", overflowX: "auto" }}>
        <svg viewBox={`0 0 ${width} ${height}`} style={{ width: "100%", height: "auto", display: "block" }}>
          {/* Grid lines */}
          {[0, 0.25, 0.5, 0.75, 1].map(pct => {
            const y = margin.top + pct * innerHeight;
            const x = margin.left + pct * innerWidth;
            return (
              <g key={`grid-${pct}`}>
                <line x1={margin.left} x2={width - margin.right} y1={y} y2={y} stroke="#cbd5e1" strokeDasharray="4 4" strokeWidth={1} />
                <line x1={x} x2={x} y1={margin.top} y2={height - margin.bottom} stroke="#cbd5e1" strokeDasharray="4 4" strokeWidth={1} />
              </g>
            );
          })}

          {/* Axes Lines */}
          <line x1={margin.left} x2={width - margin.right} y1={height - margin.bottom} y2={height - margin.bottom} stroke="#111" strokeWidth={1.5} />
          <line x1={margin.left} x2={margin.left} y1={margin.top} y2={height - margin.bottom} stroke="#111" strokeWidth={1.5} />

          {/* Axes Labels */}
          <text x={width / 2} y={height - 20} textAnchor="middle" fontSize="13" fontWeight="800" fill="#111">{METRICS[xMetric]} (per 90)</text>
          <text x={-height / 2} y={20} textAnchor="middle" transform="rotate(-90)" fontSize="13" fontWeight="800" fill="#111">{METRICS[yMetric]} (per 90)</text>

          {/* Nodes */}
          {filteredData.map(p => {
            const xVal = p.stats[xMetric] || 0;
            const yVal = p.stats[yMetric] || 0;
            const cx = xScale(xVal);
            const cy = yScale(yVal);
            const color = LEAGUE_COLORS[p.league] || "#64748b";
            const isTarget = p.player_name.toLowerCase() === targetPlayerName?.toLowerCase();
            const isHovered = hovered?.player_id === p.player_id;
            
            // Highlight target, dim others unless hovered
            let opacity = 0.3;
            if (hovered) {
              opacity = isHovered ? 1 : 0.1;
            } else {
              if (isTarget) opacity = 1;
            }
            
            const r = isHovered ? 7 : (isTarget ? 7 : 4.5);

            return (
              <g key={p.player_id} 
                 onMouseEnter={() => setHovered(p)} 
                 onMouseLeave={() => setHovered(null)}
                 style={{ cursor: "pointer", transition: "opacity 0.2s" }}
                 opacity={opacity}
              >
                {/* Target Glow */}
                {isTarget && !hovered && (
                   <circle cx={cx} cy={cy} r={r + 5} fill="none" stroke={color} strokeWidth={2} opacity={1} />
                )}
                {/* Node */}
                <circle 
                  cx={cx} 
                  cy={cy} 
                  r={r} 
                  fill={color} 
                  stroke="#111" 
                  strokeWidth={1.5} 
                />
                {/* Always show label for Target, or if hovered, or randomly for top players (just target/hover for clean UI) */}
                {(isTarget || isHovered) && (
                  <text x={cx + 8} y={cy + 4} fontSize="11" fontWeight="700" fill="#111" style={{ pointerEvents: "none" }}>
                    {p.player_name.split(" ").pop()}
                  </text>
                )}
              </g>
            );
          })}

          {/* Highlight Arrow for Target Player */}
          {targetPlayer && (
             <g style={{ pointerEvents: "none" }}>
               {/* Arrowhead marker definition (could be at top of svg, but fine here) */}
               <defs>
                 <marker id="arrow" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                   <path d="M 0 0 L 10 5 L 0 10 z" fill="#111" />
                 </marker>
               </defs>
               
               <path 
                 d={`M ${xScale(targetPlayer.stats[xMetric] || 0) + 60} ${yScale(targetPlayer.stats[yMetric] || 0) - 50} Q ${xScale(targetPlayer.stats[xMetric] || 0) + 40} ${yScale(targetPlayer.stats[yMetric] || 0) - 60} ${xScale(targetPlayer.stats[xMetric] || 0) + 12} ${yScale(targetPlayer.stats[yMetric] || 0) - 12}`} 
                 fill="none" 
                 stroke="#111" 
                 strokeWidth="2" 
                 markerEnd="url(#arrow)"
               />
               
               <text 
                 x={xScale(targetPlayer.stats[xMetric] || 0) + 65} 
                 y={yScale(targetPlayer.stats[yMetric] || 0) - 52} 
                 fontSize="14" 
                 fontWeight="900" 
                 fill="#111"
               >
                 {targetPlayer.player_name.split(" ").pop()}
               </text>
             </g>
          )}

          {/* Hover Crosshairs */}
          {hovered && (
             <g style={{ pointerEvents: "none" }}>
               <line 
                 x1={margin.left} x2={xScale(hovered.stats[xMetric] || 0)} 
                 y1={yScale(hovered.stats[yMetric] || 0)} y2={yScale(hovered.stats[yMetric] || 0)} 
                 stroke="#111" strokeDasharray="2 2" strokeWidth={1} opacity={0.4} 
               />
               <line 
                 x1={xScale(hovered.stats[xMetric] || 0)} x2={xScale(hovered.stats[xMetric] || 0)} 
                 y1={height - margin.bottom} y2={yScale(hovered.stats[yMetric] || 0)} 
                 stroke="#111" strokeDasharray="2 2" strokeWidth={1} opacity={0.4} 
               />
             </g>
          )}
        </svg>

        {/* Hover Tooltip */}
        <AnimatePresence>
          {hovered && (
            <motion.div
              initial={{ opacity: 0, y: 5 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 5 }}
              style={{
                position: "absolute",
                top: 20,
                right: 20,
                background: "#fff",
                border: "2px solid #111",
                borderRadius: 8,
                padding: "1rem",
                pointerEvents: "none",
                boxShadow: "4px 4px 0 rgba(0,0,0,0.1)",
                zIndex: 10
              }}
            >
              <div style={{ fontSize: "1.1rem", fontWeight: 800, color: "#111", marginBottom: 2 }}>{hovered.player_name}</div>
              <div style={{ fontSize: "0.8rem", color: "#64748b", fontWeight: 600, marginBottom: 8 }}>{hovered.league} • {hovered.minutes_played.toLocaleString()} mins</div>
              <div style={{ display: "grid", gridTemplateColumns: "1fr auto", gap: "4px 12px", fontSize: "0.85rem", fontWeight: 700 }}>
                <span style={{ color: "#64748b" }}>{METRICS[xMetric]}:</span>
                <span style={{ color: "#111", textAlign: "right" }}>{(hovered.stats[xMetric] || 0).toFixed(2)}</span>
                <span style={{ color: "#64748b" }}>{METRICS[yMetric]}:</span>
                <span style={{ color: "#111", textAlign: "right" }}>{(hovered.stats[yMetric] || 0).toFixed(2)}</span>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
      
      {/* Sub-footer note */}
      <div style={{ display: "flex", justifyContent: "space-between", marginTop: "1rem", fontSize: "0.75rem", color: "#94a3b8" }}>
        <span style={{ fontStyle: "italic" }}>
          {targetPlayer ? `Showing ${targetPlayer.pos_group}s | ` : ""}
          Minimum minutes: {minMinutes}. Color indicated by league.
        </span>
        <span>
          Debug: IsArr={Array.isArray(data) ? "Y" : "N"} 
          | Len={data?.length} 
          | Type={typeof data} 
          | Filt={filteredData?.length} 
          {apiError && `| Err: ${apiError}`}
          {!Array.isArray(data) && data ? ` | Dump: ${JSON.stringify(data).substring(0, 50)}` : ''}
        </span>
      </div>
    </div>
  );
};
