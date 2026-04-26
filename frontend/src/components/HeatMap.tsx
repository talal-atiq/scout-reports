import React, { useMemo } from 'react';

type HeatMapProps = {
  grid: number[][]; // 5 rows x 6 columns
};

// Deterministic random generator so dots don't jump on re-renders
function mulberry32(a: number) {
  return function() {
    var t = a += 0x6D2B79F5;
    t = Math.imul(t ^ t >>> 15, t | 1);
    t ^= t + Math.imul(t ^ t >>> 7, t | 61);
    return ((t ^ t >>> 14) >>> 0) / 4294967296;
  }
}

const HeatMap: React.FC<HeatMapProps> = ({ grid }) => {
  // Find max value to scale opacities relative to the peak zone
  let maxVal = 0;
  for (let r = 0; r < 5; r++) {
    for (let c = 0; c < 6; c++) {
      if (grid[r] && grid[r][c] > maxVal) {
        maxVal = grid[r][c];
      }
    }
  }

  if (maxVal === 0) maxVal = 1;

  // Exact colors from the user's reference image
  const PITCH_BG = "#4E9C35"; // Vibrant green
  const LINE_COLOR = "#FFFFFF"; // Pure white lines

  // Pre-calculate the scattered dots so they don't regenerate constantly
  const heatmapDots = useMemo(() => {
    const rand = mulberry32(9999);
    const elements: React.ReactNode[] = [];
    
    grid.forEach((row, rIdx) => {
      row.forEach((val, cIdx) => {
        const v = val / maxVal;
        if (v < 0.05) return;

        const cellW = 105 / 6;
        const cellH = 68 / 5;
        const cx = (cIdx + 0.5) * cellW;
        const cy = (rIdx + 0.5) * cellH;

        // Base solid core to ensure continuous mass in high-density areas
        const coreR = v * 14;
        let coreColor = "#E4DE2A"; // Yellow
        if (v > 0.65) coreColor = "#D23028"; // Red
        else if (v > 0.35) coreColor = "#E87D1E"; // Orange
        
        elements.push(
          <circle key={`core-${rIdx}-${cIdx}`} cx={cx} cy={cy} r={coreR} fill={coreColor} opacity={0.9} />
        );

        // Scatter tiny dots around the cell
        const numDots = Math.floor(v * 40); 
        for (let i = 0; i < numDots; i++) {
          // Normal distribution-ish scattering
          const r1 = rand();
          const r2 = rand();
          const radius = Math.sqrt(-2.0 * Math.log(r1)) * Math.cos(2.0 * Math.PI * r2);
          const r3 = rand();
          const r4 = rand();
          const radius2 = Math.sqrt(-2.0 * Math.log(r3)) * Math.cos(2.0 * Math.PI * r4);

          const ox = radius * (cellW * 0.6);
          const oy = radius2 * (cellH * 0.6);
          
          const dotCx = cx + ox;
          const dotCy = cy + oy;
          const dotR = 1.5 + rand() * 3.5; // Random size

          // Determine color based on original cell intensity + distance from center
          const dist = Math.sqrt(ox*ox + oy*oy);
          const maxDist = cellW;
          let dotV = v * (1 - (dist / maxDist) * 0.5);
          
          let dotColor = "#E4DE2A"; // Yellow
          if (dotV > 0.6) dotColor = "#D23028"; // Red
          else if (dotV > 0.3) dotColor = "#E87D1E"; // Orange

          elements.push(
            <circle key={`dot-${rIdx}-${cIdx}-${i}`} cx={dotCx} cy={dotCy} r={dotR} fill={dotColor} opacity={0.8} />
          );
        }
      });
    });
    return elements;
  }, [grid, maxVal]);

  return (
    <div style={{
      width: "100%",
      maxWidth: "750px",
      margin: "0 auto",
    }}>
      <svg
        viewBox="-5 -15 115 88" // Perfect bounds to include arrow
        style={{
          width: "100%",
          height: "auto",
          display: "block",
          borderRadius: "8px",
        }}
      >
        <defs>
          {/* Heavy blur to fuse the scattered dots together into a thermal look */}
          <filter id="scatter-blur" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="2.5" />
          </filter>
        </defs>

        {/* 1. Base Pitch Background */}
        <rect x="-5" y="-15" width="115" height="88" fill={PITCH_BG} rx="3" />

        {/* 2. Attack Direction Arrow */}
        <g transform="translate(42, -8)">
          <line x1="0" y1="0" x2="20" y2="0" stroke={LINE_COLOR} strokeWidth="0.8" />
          <polygon points="20,-2 24,0 20,2" fill={LINE_COLOR} />
        </g>

        {/* 3. The Heatmap Blobs */}
        <clipPath id="pitch-clip">
          <rect x="0" y="0" width="105" height="68" />
        </clipPath>

        {/* Render dots with blur to create the textured heat effect */}
        <g clipPath="url(#pitch-clip)">
          <g filter="url(#scatter-blur)">
            {heatmapDots}
          </g>
        </g>

        {/* 4. Pitch Lines (Rendered ON TOP of heat for absolute professional crispness) */}
        <g stroke={LINE_COLOR} strokeWidth="0.3" fill="none" opacity="0.9">
          {/* Outline */}
          <rect x="0" y="0" width="105" height="68" />
          
          {/* Center line */}
          <line x1="52.5" y1="0" x2="52.5" y2="68" />
          
          {/* Center circle */}
          <circle cx="52.5" cy="34" r="9.15" />
          <circle cx="52.5" cy="34" r="0.6" fill={LINE_COLOR} stroke="none" />
          
          {/* Left Penalty Area */}
          <rect x="0" y="13.84" width="16.5" height="40.32" />
          {/* Left Goal Area */}
          <rect x="0" y="24.84" width="5.5" height="18.32" />
          {/* Left Penalty Spot */}
          <circle cx="11" cy="34" r="0.6" fill={LINE_COLOR} stroke="none" />
          {/* Left Penalty Arc */}
          <path d="M 16.5 26.85 A 9.15 9.15 0 0 0 16.5 41.15" />
          
          {/* Right Penalty Area */}
          <rect x="88.5" y="13.84" width="16.5" height="40.32" />
          {/* Right Goal Area */}
          <rect x="99.5" y="24.84" width="5.5" height="18.32" />
          {/* Right Penalty Spot */}
          <circle cx="94" cy="34" r="0.6" fill={LINE_COLOR} stroke="none" />
          {/* Right Penalty Arc */}
          <path d="M 88.5 26.85 A 9.15 9.15 0 0 1 88.5 41.15" />
        </g>
      </svg>
    </div>
  );
};

export default HeatMap;
