import { useMemo } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, ResponsiveContainer, Tooltip } from 'recharts';
import type { TransferMarketData } from '../api/client';

interface MarketValueChartProps {
  data: TransferMarketData;
  theme: 'blue' | 'orange' | 'red' | 'green' | 'purple';
  age?: number | string;
}

export function MarketValueChart({ data, theme, age }: MarketValueChartProps) {
  const chartData = useMemo(() => {
    if (!data.mv_history) return [];
    
    return Object.entries(data.mv_history)
      .sort(([yearA], [yearB]) => parseInt(yearA) - parseInt(yearB))
      .map(([year, value]) => ({
        year,
        value,
      }));
  }, [data]);

  const smartText = useMemo(() => {
    if (chartData.length < 2) return "Insufficient historical data to determine market value trends.";
    
    const playerName = data.player || "The player";
    const startVal = chartData[0].value;
    const endVal = chartData[chartData.length - 1].value;
    const maxVal = Math.max(...chartData.map(d => d.value));
    const parsedAge = typeof age === 'string' ? parseInt(age, 10) : (age || 25);
    
    const diff = endVal - startVal;
    const isDropping = endVal < maxVal && (maxVal - endVal) > maxVal * 0.15; // 15% drop from peak
    
    if (isDropping) {
      if (parsedAge > 29) {
        return `At ${parsedAge} years of age, ${playerName}'s market valuation has naturally entered its sunset phase, currently sitting at €${endVal}m. From a recruitment perspective, this represents a pivot from 'asset growth' to 'operational utility.' While the €${maxVal}m peak is now in the rearview, the current valuation reflects a player whose worth is measured in leadership and immediate tactical impact rather than future resale potential. Clubs investing in ${playerName} are paying for guaranteed output and veteran stability, as the standard age-related depreciation curve is now fully in effect.`;
      } else {
        return `${playerName}'s market value has undergone a significant correction, sliding to €${endVal}m from a previous high of €${maxVal}m. This downtrend is a critical scouting signal that warrants deeper investigation into variables such as recurring injury patterns, tactical misalignment, or approaching contract expiry. For potential suitors, this valuation dip may represent a strategic 'buy low' opportunity, provided the underlying performance metrics still align with elite output, as current market sentiment appears to be temporarily cooling on their immediate trajectory.`;
      }
    } else if (diff > 0) {
      if (parsedAge <= 23) {
        return `At just ${parsedAge} years old, ${playerName} is currently one of the most explosive assets in the global market. Their valuation is on a steep, compounding upward trajectory, growing from an initial €${startVal}m to a current €${endVal}m. This curve indicates a rare combination of high immediate floor and an uncapped developmental ceiling. From an investment standpoint, the window for an affordable acquisition is rapidly closing; the trend suggests they are outperforming expected economic growth, making them a high-priority target for organizations seeking a cornerstone profile with significant resale upside.`;
      } else {
        return `Currently entering their peak performance window at ${parsedAge}, ${playerName} has solidified a formidable market position at €${endVal}m. Unlike speculative growth seen in younger profiles, this trajectory is backed by sustained, high-level consistency across multiple competitive cycles. The steady climb reflects professional maturity and a 'low-risk' scouting profile. At €${endVal}m, ${playerName} is viewed as a definitive starter at the Champions League level, with their valuation likely to remain at this elite plateau as they maximize their prime athletic years.`;
      }
    } else {
      return `${playerName} has reached an established market equilibrium, with their valuation holding steady at €${endVal}m. In scouting terms, this plateau indicates a 'known quantity' whose performance has been fully priced in by the global market. While there is less speculative upside compared to younger assets, the stability of this curve offers a high degree of recruitment security. The consistency of their valuation over recent cycles suggests a player who provides predictable, reliable output, making them a safe tactical inclusion for teams prioritizing squad stability.`;
    }
  }, [chartData, data.player, age]);

  if (chartData.length === 0) {
    return null;
  }

  const themeColors: Record<string, string> = {
    blue: '#2563eb', 
    orange: '#ea580c', 
    red: '#dc2626', 
    green: '#16a34a', 
    purple: '#8b5cf6',
  };
  
  const barColor = themeColors[theme] || themeColors.blue;

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div style={{ backgroundColor: '#fff', padding: '8px 12px', border: '1px solid #e2e8f0', borderRadius: '4px', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}>
          <p style={{ margin: 0, fontWeight: 'bold', color: '#1e293b' }}>{label}</p>
          <p style={{ margin: 0, color: barColor, fontWeight: 600 }}>
            €{payload[0].value.toFixed(1)}m
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <div style={{ display: 'flex', width: '100%', padding: '24px 0', marginTop: '16px', borderTop: '1px solid #e2e8f0', borderBottom: '1px solid #e2e8f0', alignItems: 'center' }}>
      <div style={{ paddingLeft: '16px', paddingRight: '24px', minWidth: '150px' }}>
        <h2 style={{ margin: 0, fontSize: '28px', fontWeight: 600, color: '#64748b', lineHeight: 1.1 }}>Market</h2>
        <h2 style={{ margin: 0, fontSize: '28px', fontWeight: 600, color: '#64748b', lineHeight: 1.1 }}>Value</h2>
        <h2 style={{ margin: 0, fontSize: '28px', fontWeight: 600, color: '#64748b', lineHeight: 1.1 }}>Growth</h2>
      </div>
      
      <div style={{ height: 300, flex: 1.2 }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={chartData}
            margin={{ top: 20, right: 20, left: 20, bottom: 20 }}
            barCategoryGap="2%"
          >
            <CartesianGrid strokeDasharray="0" vertical={false} stroke="#e2e8f0" />
            <XAxis 
              dataKey="year" 
              axisLine={false} 
              tickLine={false} 
              tick={{ fill: '#64748b', fontSize: 12, fontWeight: 600 }} 
              dy={10}
            />
            <YAxis 
              orientation="right" 
              axisLine={false} 
              tickLine={false} 
              tickFormatter={(value) => `€${value}m`}
              tick={{ fill: '#64748b', fontSize: 14 }}
              dx={10}
            />
            <Tooltip content={<CustomTooltip />} cursor={{ fill: '#f8fafc' }} />
            <Bar 
              dataKey="value" 
              fill={barColor}
              radius={[50, 50, 0, 0]}
              maxBarSize={24}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div style={{ paddingLeft: '32px', paddingRight: '16px', minWidth: '400px', flex: 1.5 }}>
        <div style={{ 
          borderLeft: `5px solid ${barColor}`, 
          paddingLeft: '16px',
          color: '#64748b',
          fontSize: '14px',
          lineHeight: '1.6',
          fontFamily: 'system-ui, -apple-system, sans-serif'
        }}>
          {smartText}
        </div>
      </div>
    </div>
  );
}
