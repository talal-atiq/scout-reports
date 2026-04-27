import React, { useState, useEffect, useMemo } from 'react';
import { 
  ScatterChart, 
  Scatter, 
  XAxis, 
  YAxis, 
  ZAxis, 
  Tooltip, 
  ResponsiveContainer,
  CartesianGrid
} from 'recharts';
import { fetchLeagueProjection, LeagueProjectionResponse } from '../api/client';

interface Props {
  playerName: string;
  season?: string;
  theme?: string;
  aiAnalysis?: string;
}

const METRICS = [
  { label: 'Expected Threat (xT)', value: 'xT_p90' },
  { label: 'Progressive Actions', value: 'progressive_actions' },
  { label: 'Box Entries', value: 'box_entries' },
  { label: 'High Regains', value: 'high_regains' },
];

const LeagueProjectionMap: React.FC<Props> = ({ playerName, season = "2025/2026", theme = "blue", aiAnalysis }) => {
  const [metric, setMetric] = useState('xT_p90');
  const [peerFilter, setPeerFilter] = useState(false);
  const [data, setData] = useState<LeagueProjectionResponse | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        const res = await fetchLeagueProjection(playerName, season, metric, peerFilter);
        setData(res);
      } catch (err) {
        console.error("Failed to fetch league projection:", err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [playerName, season, metric, peerFilter]);

  const themeColors: Record<string, string> = {
    blue: '#2563eb', 
    orange: '#ea580c', 
    red: '#dc2626', 
    green: '#16a34a', 
    purple: '#8b5cf6',
  };
  const activeColor = themeColors[theme] || themeColors.blue;

  const CustomDot = (props: any) => {
    const { cx, cy, payload } = props;
    if (payload.is_target) {
      return (
        <g>
          <circle cx={cx} cy={cy} r={10} fill={activeColor} stroke="#111" strokeWidth={2.5} />
          <text x={cx} y={cy - 16} textAnchor="middle" fontSize="13" fontWeight="900" fill="#111">
            {payload.translated_z_score.toFixed(2)}
          </text>
        </g>
      );
    }
    return <circle cx={cx} cy={cy} r={4.5} fill="#94a3b8" fillOpacity={0.15} />;
  };

  const leagueNames = data?.leagues.map(l => l.league) || [];
  
  const combinedData = useMemo(() => {
    if (!data) return [];
    let all: any[] = [];
    data.leagues.forEach((l, idx) => {
      const xCenter = idx + 1;
      const pList = l.players.map(p => ({
          ...p,
          leagueName: l.league,
          x: p.is_target ? xCenter : xCenter + (Math.random() * 0.6 - 0.3),
      }));
      all = [...all, ...pList];
    });
    // Target players must be drawn last so they sit on top of the swarm
    return all.sort((a, b) => (a.is_target ? 1 : -1));
  }, [data]);

  return (
    <div className="league-projection-container">
      <div className="projection-header">
        <div className="projection-title-group">
          <h1 className="projection-title">Skill Translation Swarm</h1>
          <p className="projection-subtitle">
            Projected Z-Score of <strong>{data?.metric || 'Metric'}</strong> vs {data?.pos_group || 'Peers'} across Top 5 Leagues
          </p>
        </div>

        <div className="projection-controls">
          <div className="control-group">
            <label>Metric</label>
            <select value={metric} onChange={(e) => setMetric(e.target.value)} className="projection-select">
              {METRICS.map(m => <option key={m.value} value={m.value}>{m.label}</option>)}
            </select>
          </div>

          <div className="control-group">
            <label className="toggle-label">
              <input type="checkbox" checked={peerFilter} onChange={(e) => setPeerFilter(e.target.checked)} />
              Filter by "{data?.cluster_label || 'Style Cluster'}"
            </label>
          </div>
        </div>
      </div>

      <div className="projection-analysis-text">
        {data && data.leagues.length > 0 && (
          aiAnalysis ? (
            <div style={{ marginTop: '1rem', marginBottom: '1rem' }}>
              <p style={{ margin: 0 }}>{aiAnalysis}</p>
            </div>
          ) : (
            <p>
              Looking at possible next steps for {playerName}, joining a <strong>{data.leagues[0].league}</strong> club could be an 
              excellent move for him. His ability and strengths would translate well, placing him as a 
              <strong> {data.leagues[0].players.find(p => p.is_target)!.translated_z_score > 0.5 ? 'well above average' : 'solid'} </strong> 
              {data.pos_group}, capable of breaking into the top tier of the league.
            </p>
          )
        )}
      </div>

      {loading ? (
        <div className="projection-loading">Calculating league-wide distributions...</div>
      ) : (
        <div style={{ marginTop: '2rem', height: '450px', width: '100%', position: 'relative' }}>
          <ResponsiveContainer width="100%" height="100%">
            <ScatterChart margin={{ top: 40, right: 30, bottom: 30, left: 0 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
              <XAxis 
                type="number" 
                dataKey="x" 
                domain={[0.5, leagueNames.length + 0.5]} 
                ticks={Array.from({length: leagueNames.length}, (_, i) => i + 1)}
                tickFormatter={(tick) => leagueNames[tick - 1] || ''}
                tick={{ fontSize: 13, fontWeight: 'bold', fill: '#334155' }}
                axisLine={false}
                tickLine={false}
              />
              <YAxis 
                type="number" 
                dataKey="translated_z_score" 
                domain={[-3, 3]} 
                tick={{ fontSize: 12, fill: '#64748b' }} 
                axisLine={false}
                tickLine={false}
                width={50}
              />
              <ZAxis type="number" range={[0, 100]} />
              <Tooltip 
                cursor={{ strokeDasharray: '3 3', stroke: '#cbd5e1' }}
                content={({ active, payload }) => {
                  if (active && payload && payload.length) {
                    const d = payload[0].payload;
                    return (
                      <div className="custom-tooltip" style={{ backgroundColor: '#fff', padding: '10px', border: '1px solid #e2e8f0', borderRadius: '6px', boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)' }}>
                        <p style={{ margin: '0 0 4px 0', fontWeight: 'bold', color: '#0f172a' }}>{d.player_name}</p>
                        <p style={{ margin: '0 0 2px 0', fontSize: '13px', color: '#334155' }}><strong>Z-Score:</strong> {d.translated_z_score.toFixed(2)}</p>
                        <p style={{ margin: 0, fontSize: '11px', color: '#64748b' }}>League: {d.leagueName}</p>
                      </div>
                    );
                  }
                  return null;
                }}
              />
              <Scatter data={combinedData} shape={<CustomDot />} />
            </ScatterChart>
          </ResponsiveContainer>
        </div>
      )}

      <div className="projection-footer" style={{ marginTop: '1rem', borderTop: '1px solid #e2e8f0', paddingTop: '1rem' }}>
         * League weights are calculated based on Opta Power Rankings & UEFA Coefficients for the 25/26 season. 
         A translated Z-score of +1.0 means the player is in the top 15% of that specific league.
      </div>
    </div>
  );
};

export default LeagueProjectionMap;
