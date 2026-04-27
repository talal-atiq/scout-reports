import React from 'react';
import { motion } from 'framer-motion';

const METRIC_LABELS: Record<string, string> = {
  shots: "Shots",
  big_chances: "Big Chances",
  touches_in_box: "Touches in Box",
  box_entries: "Box Entries",
  xT_p90: "Expected Threat",
  key_passes: "Key Passes",
  progressive_passes: "Prog. Passes",
  through_balls: "Through Balls",
  progressive_carries: "Prog. Carries",
  dribbles: "Dribbles",
  pass_completion_pct: "Pass Cmp %",
  crosses: "Crosses",
  tackles: "Tackles",
  interceptions: "Interceptions",
  clearances: "Clearances",
  high_regains: "High Regains",
  tackle_win_pct: "Tackle Win %",
  defensive_actions: "Def. Actions",
  aerial_duels_won: "Aerials Won",
};

const GROUPS = [
  {
    title: "Attacking & Final Third",
    keys: ["shots", "big_chances", "touches_in_box", "box_entries", "xT_p90"]
  },
  {
    title: "Possession & Creativity",
    keys: ["key_passes", "progressive_passes", "through_balls", "progressive_carries", "dribbles", "pass_completion_pct", "crosses"]
  },
  {
    title: "Defending",
    keys: ["tackles", "interceptions", "clearances", "high_regains", "tackle_win_pct", "defensive_actions", "aerial_duels_won"]
  }
];

interface Props {
  percentiles: Record<string, number>;
  rawStats: Record<string, number>;
  theme: "blue" | "orange" | "red" | "green" | "purple";
}

const getBarColor = (theme: string, val: number) => {
  // L goes from 95 (lightest) at 0% to 40 (darkest) at 100%
  const l = 95 - (val / 100) * 50; 
  switch(theme) {
     case 'blue': return `hsl(215, 80%, ${l}%)`;
     case 'red': return `hsl(0, 75%, ${l}%)`;
     case 'orange': return `hsl(25, 90%, ${l}%)`;
     case 'green': return `hsl(140, 60%, ${l}%)`;
     case 'purple': return `hsl(260, 80%, ${l}%)`;
     default: return `hsl(215, 80%, ${l}%)`;
  }
};

const formatRaw = (key: string, val: number | undefined) => {
  if (val === undefined || val === null) return "-";
  if (key === 'pass_completion_pct' || key === 'tackle_win_pct') {
    return `${val.toFixed(1)}%`;
  }
  return val.toFixed(2);
};

export const PercentileBarChart: React.FC<Props> = ({ percentiles, rawStats, theme }) => {
  
  return (
    <motion.div 
      className="shot-map-container"
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      transition={{ duration: 0.3 }}
      style={{
        width: "100%",
        maxWidth: "800px",
        margin: "0 auto",
        padding: "2.5rem",
        backgroundColor: "#ffffff",
        fontFamily: "'Segoe UI', system-ui, sans-serif",
      }}
    >
      <div style={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "flex-end",
        marginBottom: "1rem",
        borderBottom: "2px solid #e2e8f0",
        paddingBottom: "0.5rem"
      }}>
        <h2 style={{ margin: 0, fontSize: "1.2rem", fontWeight: 800, color: "#112240" }}>
          Analytical Profile
        </h2>
        <div style={{ display: "flex", gap: "2rem", fontSize: "0.8rem", fontWeight: 700, color: "#64748b", textTransform: "uppercase", letterSpacing: "0.05em" }}>
          <span style={{ width: "40px", textAlign: "right" }}>Raw</span>
          <span style={{ width: "40px", textAlign: "right" }}>%ile</span>
        </div>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: "2rem" }}>
        {GROUPS.map((group) => {
          // Filter out keys that don't exist in our percentiles data
          const validKeys = group.keys.filter(k => percentiles[k] !== undefined);
          if (validKeys.length === 0) return null;

          return (
            <div key={group.title}>
              <h3 style={{ margin: "0 0 1rem 0", fontSize: "0.9rem", fontWeight: 800, color: "#94a3b8", textTransform: "uppercase", letterSpacing: "0.05em" }}>
                {group.title}
              </h3>
              
              <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                {validKeys.map((key, i) => {
                  const perc = Math.max(0, Math.min(100, percentiles[key] || 0));
                  const raw = rawStats[key];
                  const barColor = getBarColor(theme, perc);
                  
                  return (
                    <div key={key} style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
                      
                      {/* Label */}
                      <div style={{ width: "140px", flexShrink: 0, textAlign: "right", fontSize: "0.95rem", fontWeight: 700, color: "#112240" }}>
                        {METRIC_LABELS[key] || key}
                      </div>

                      {/* Bar Track */}
                      <div style={{ flex: 1, height: "28px", position: "relative" }}>
                        {/* Background track (optional, keeping it clean by just having the active bar) */}
                        <div style={{ 
                          position: "absolute", left: 0, top: 0, bottom: 0, right: 0, 
                          borderRight: "1px solid #e2e8f0", borderLeft: "1px solid #e2e8f0" 
                        }} />
                        
                        {/* Grid lines (25, 50, 75) */}
                        {[25, 50, 75].map(tick => (
                          <div key={tick} style={{
                            position: "absolute", left: `${tick}%`, top: 0, bottom: 0, 
                            borderLeft: "1px dashed #cbd5e1", zIndex: 0
                          }} />
                        ))}

                        {/* Animated Bar */}
                        <motion.div 
                          initial={{ width: 0 }}
                          animate={{ width: `${perc}%` }}
                          transition={{ duration: 0.8, delay: i * 0.05, ease: "easeOut" }}
                          style={{
                            position: "absolute",
                            left: 0,
                            top: 0,
                            bottom: 0,
                            backgroundColor: barColor,
                            border: "1px solid #111", // The crisp black border requested
                            borderLeft: "none", // attach to left axis
                            borderTopRightRadius: "3px",
                            borderBottomRightRadius: "3px",
                            zIndex: 1,
                            boxShadow: "inset 0 1px 0 rgba(255,255,255,0.2)" // subtle top highlight
                          }}
                        />
                      </div>

                      {/* Raw Stat */}
                      <div style={{ width: "40px", flexShrink: 0, textAlign: "right", fontSize: "0.9rem", fontWeight: 600, color: "#64748b" }}>
                        {formatRaw(key, raw)}
                      </div>

                      {/* Percentile Number */}
                      <div style={{ width: "40px", flexShrink: 0, textAlign: "right", fontSize: "1.1rem", fontWeight: 900, color: "#112240" }}>
                        {Math.round(perc)}
                      </div>

                    </div>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>
      
      {/* X-Axis labels at bottom */}
      <div style={{ display: "flex", paddingLeft: "calc(140px + 1rem)", paddingRight: "calc(80px + 2rem)", marginTop: "0.5rem" }}>
         <div style={{ flex: 1, position: "relative", height: "20px" }}>
            {[0, 25, 50, 75, 100].map(tick => (
              <div key={tick} style={{
                position: "absolute", left: `${tick}%`, top: 0, 
                transform: "translateX(-50%)", fontSize: "0.75rem", fontWeight: 600, color: "#94a3b8"
              }}>
                {tick}
              </div>
            ))}
         </div>
      </div>
    </motion.div>
  );
};
