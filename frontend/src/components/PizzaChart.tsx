import React, { useMemo } from 'react';

// --- Configuration & Styling ---
const METRIC_COLORS: Record<string, string> = {
  // Attacking (Green)
  shots: "#35a849",
  big_chances: "#35a849",
  touches_in_box: "#35a849",
  box_entries: "#35a849",
  xT_p90: "#35a849",
  
  // Possession / Passing (Blue)
  key_passes: "#1d70b8",
  progressive_passes: "#1d70b8",
  through_balls: "#1d70b8",
  progressive_carries: "#1d70b8",
  dribbles: "#1d70b8",
  pass_completion_pct: "#1d70b8",
  crosses: "#1d70b8",
  turnovers_p90: "#1d70b8", // Handled as inverted metric
  
  // Defending (Red)
  tackles: "#d72638",
  interceptions: "#d72638",
  clearances: "#d72638",
  high_regains: "#d72638",
  tackle_win_pct: "#d72638",
  defensive_actions: "#d72638",
  aerial_duels_won: "#d72638",
};

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
  turnovers_p90: "Ball Security", 
  tackles: "Tackles",
  interceptions: "Interceptions",
  clearances: "Clearances",
  high_regains: "High Regains",
  tackle_win_pct: "Tackle Win %",
  defensive_actions: "Def. Actions",
  aerial_duels_won: "Aerials Won",
};

// Math Helpers
const polarToCartesian = (centerX: number, centerY: number, radius: number, angleInDegrees: number) => {
  const angleInRadians = ((angleInDegrees - 90) * Math.PI) / 180.0;
  return {
    x: centerX + radius * Math.cos(angleInRadians),
    y: centerY + radius * Math.sin(angleInRadians)
  };
};

const describeArc = (x: number, y: number, radius: number, startAngle: number, endAngle: number) => {
  const start = polarToCartesian(x, y, radius, endAngle);
  const end = polarToCartesian(x, y, radius, startAngle);
  const largeArcFlag = endAngle - startAngle <= 180 ? "0" : "1";
  
  // Create a wedge (pie slice)
  return [
    "M", x, y,
    "L", start.x, start.y,
    "A", radius, radius, 0, largeArcFlag, 0, end.x, end.y,
    "Z"
  ].join(" ");
};

interface PizzaChartProps {
  percentiles: Record<string, number>;
  theme?: "blue" | "orange" | "red" | "green";
}

export const PizzaChart: React.FC<PizzaChartProps> = ({
  percentiles,
  theme = "blue",
}) => {
  // Config
  const size = 660;
  const center = size / 2;
  const maxRadius = 240; // Inner chart radius
  const minRadius = 20;  // Leave a tiny gap in the center

  // Extract the metrics and values
  // We want to sort them so colors are grouped together
  const sortedMetrics = useMemo(() => {
    return Object.entries(percentiles)
      .filter(([k]) => METRIC_LABELS[k]) // Only keep known metrics
      .map(([k, v]) => ({
        key: k,
        label: METRIC_LABELS[k],
        value: v,
        color: METRIC_COLORS[k] || "#ccc"
      }))
      .sort((a, b) => {
        // Sort by color to group the Attack/Possession/Defense slices
        if (a.color === b.color) return a.label.localeCompare(b.label);
        return a.color.localeCompare(b.color);
      });
  }, [percentiles]);

  const numSlices = sortedMetrics.length;
  const anglePerSlice = 360 / numSlices;

  // Calculate averages for categories
  const categoryAverages = useMemo(() => {
    const sums = { defending: 0, possession: 0, attacking: 0 };
    const counts = { defending: 0, possession: 0, attacking: 0 };

    sortedMetrics.forEach(m => {
      if (m.color === "#d72638") {
        sums.defending += m.value;
        counts.defending++;
      } else if (m.color === "#1d70b8") {
        sums.possession += m.value;
        counts.possession++;
      } else if (m.color === "#35a849") {
        sums.attacking += m.value;
        counts.attacking++;
      }
    });

    return {
      defending: counts.defending > 0 ? Math.round(sums.defending / counts.defending) : 0,
      possession: counts.possession > 0 ? Math.round(sums.possession / counts.possession) : 0,
      attacking: counts.attacking > 0 ? Math.round(sums.attacking / counts.attacking) : 0,
    };
  }, [sortedMetrics]);

  // Background rings
  const rings = [20, 40, 60, 80, 100];

  const bgColors = {
    blue: "#f0f6ff",
    orange: "#fff4eb",
    red: "#fdf2f2",
    green: "#f0fdf4",
  };
  const bgColor = theme ? bgColors[theme] : "#fdf5e6";

  return (
    <div 
      style={{
        width: "100%",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        padding: "2rem",
        borderRadius: "12px",
        boxShadow: "0 10px 15px -3px rgba(0, 0, 0, 0.1)",
        border: "1px solid #e8dcc4",
        fontFamily: "sans-serif",
        backgroundColor: bgColor,
      }}
    >
      
      {/* Category Averages (Horizontal Layout) */}
      <div style={{
        width: "100%",
        maxWidth: "700px",
        display: "flex",
        flexDirection: "row",
        justifyContent: "space-between",
        alignItems: "center",
        marginBottom: "0.5rem",
        marginTop: "1rem",
        marginLeft: "auto",
        marginRight: "auto",
      }}>
        
        {/* Defending */}
        <div style={{ display: "flex", flexDirection: "row", alignItems: "center", gap: "0.75rem" }}>
          <span style={{ fontSize: "19px", fontWeight: 500, letterSpacing: "0.025em", color: "#111" }}>Defending Average</span>
          <div style={{
            display: "flex", alignItems: "center", justifyContent: "center",
            width: "46px", height: "36px", backgroundColor: "#d72638", color: "white",
            fontWeight: 600, fontSize: "18px", borderRadius: "3px", boxShadow: "0 1px 2px 0 rgba(0, 0, 0, 0.05)"
          }}>
            {categoryAverages.defending}
          </div>
        </div>

        {/* Possession */}
        <div style={{ display: "flex", flexDirection: "row", alignItems: "center", gap: "0.75rem" }}>
          <span style={{ fontSize: "19px", fontWeight: 500, letterSpacing: "0.025em", color: "#111" }}>Possession Average</span>
          <div style={{
            display: "flex", alignItems: "center", justifyContent: "center",
            width: "46px", height: "36px", backgroundColor: "#1d70b8", color: "white",
            fontWeight: 600, fontSize: "18px", borderRadius: "3px", boxShadow: "0 1px 2px 0 rgba(0, 0, 0, 0.05)"
          }}>
            {categoryAverages.possession}
          </div>
        </div>

        {/* Attacking */}
        <div style={{ display: "flex", flexDirection: "row", alignItems: "center", gap: "0.75rem" }}>
          <span style={{ fontSize: "19px", fontWeight: 500, letterSpacing: "0.025em", color: "#111" }}>Attacking Average</span>
          <div style={{
            display: "flex", alignItems: "center", justifyContent: "center",
            width: "46px", height: "36px", backgroundColor: "#35a849", color: "white",
            fontWeight: 600, fontSize: "18px", borderRadius: "3px", boxShadow: "0 1px 2px 0 rgba(0, 0, 0, 0.05)"
          }}>
            {categoryAverages.attacking}
          </div>
        </div>

      </div>

      {/* --- SVG CHART --- */}
      <svg
        width="100%"
        height="100%"
        viewBox={`0 0 ${size} ${size}`}
        style={{ maxWidth: "800px", overflow: "visible" }}
      >
        {/* Concentric Grid Rings */}
        {rings.map((ringValue) => {
          const radius = minRadius + (ringValue / 100) * (maxRadius - minRadius);
          return (
            <circle
              key={`ring-${ringValue}`}
              cx={center}
              cy={center}
              r={radius}
              fill="none"
              stroke="#cbd5e1"
              strokeWidth="1.5"
              strokeDasharray={ringValue === 100 ? "none" : "5,5"}
            />
          );
        })}

        {/* Wedges */}
        {sortedMetrics.map((metric, i) => {
          const startAngle = i * anglePerSlice;
          const endAngle = (i + 1) * anglePerSlice;
          
          // Radius based on percentile (Sanitize value)
          const safeValue = (typeof metric.value === 'number' && isFinite(metric.value)) ? metric.value : 0;
          const radius = minRadius + (Math.max(5, safeValue) / 100) * (maxRadius - minRadius);
          
          if (!isFinite(radius)) return null;

          const pathData = describeArc(center, center, radius, startAngle, endAngle);

          return (
            <path
              key={`wedge-${metric.key}`}
              d={pathData}
              fill={metric.color}
              stroke="#111"
              strokeWidth="2"
              className="hover:opacity-90 transition-opacity duration-200 cursor-pointer"
            />
          );
        })}

        {/* Outer Value Badges & Labels */}
        {sortedMetrics.map((metric, i) => {
          const startAngle = i * anglePerSlice;
          const endAngle = (i + 1) * anglePerSlice;
          const midAngle = startAngle + anglePerSlice / 2;
          
          // Outer edge of the drawn wedge for the badge
          const radius = minRadius + (Math.max(5, metric.value) / 100) * (maxRadius - minRadius);
          const badgePos = polarToCartesian(center, center, radius, midAngle);
          
          // Label position pushed further out
          const labelPos = polarToCartesian(center, center, maxRadius + 40, midAngle);
          
          // Adjust label text anchor based on angle
          let textAnchor = "middle";
          if (midAngle > 20 && midAngle < 160) textAnchor = "start";
          if (midAngle > 200 && midAngle < 340) textAnchor = "end";

          return (
            <g key={`overlay-${metric.key}`}>
              {/* Value Badge */}
              <rect
                x={badgePos.x - 14}
                y={badgePos.y - 10}
                width="28"
                height="20"
                fill="white"
                stroke="#111"
                strokeWidth="1.5"
                rx="3"
              />
              <text
                x={badgePos.x}
                y={badgePos.y + 4}
                textAnchor="middle"
                fontSize="12"
                fontWeight="bold"
                fill="#111"
                style={{ pointerEvents: 'none' }}
              >
                {Math.round(metric.value)}
              </text>

              {/* Metric Label */}
              <text
                x={labelPos.x}
                y={labelPos.y}
                textAnchor={textAnchor}
                fontSize="13"
                fontWeight="600"
                fill="#222"
              >
                {metric.label}
              </text>
            </g>
          );
        })}
        
        {/* Center Cover */}
        <circle cx={center} cy={center} r={minRadius} fill={bgColor} stroke="#111" strokeWidth="2" />
      </svg>
    </div>
  );
};
