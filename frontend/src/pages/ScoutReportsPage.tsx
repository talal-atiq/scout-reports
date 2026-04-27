import { useEffect, useMemo, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";

import {
  fetchScoutPlayerHeader,
  fetchScoutPlayerOptions,
  fetchSpatialProfile,
  fetchTransferMarketData,
  fetchTacticalTwins,
  fetchAiScoutReport,
  type ScoutPlayerHeader,
  type ScoutPlayerOption,
  type SpatialProfile,
  type TacticalTwinResponse,
  type TransferMarketData,
  type AiScoutReportResponse,
} from "../api/client";
import { PageShell } from "./PageShell";
import { PizzaChart } from "../components/PizzaChart";
import HeatMap from "../components/HeatMap";
import { ShotMap } from "../components/ShotMap";
import { ExpectedThreatMap } from "../components/ExpectedThreatMap";
import { PassNetworkMap } from "../components/PassNetworkMap";
import LeagueProjectionMap from '../components/LeagueProjectionMap';
import { MarketValueChart } from '../components/MarketValueChart';
import { PercentileBarChart } from "../components/PercentileBarChart";
import { ScatterPlotExplorer } from "../components/ScatterPlotExplorer";
import { AiAnnotation } from "../components/AiAnnotation";



export default function ScoutReportsPage() {
  const [season] = useState("25-26");
  const [players, setPlayers] = useState<ScoutPlayerOption[]>([]);
  const [selectedPlayer, setSelectedPlayer] = useState<{name: string, club: string | null} | null>(null);
  const [searchText, setSearchText] = useState("");
  const [theme, setTheme] = useState<"blue" | "orange" | "red" | "green" | "purple">("blue");
  const [header, setHeader] = useState<ScoutPlayerHeader | null>(null);
  const [spatialProfile, setSpatialProfile] = useState<SpatialProfile | null>(null);
  const [tmData, setTmData] = useState<TransferMarketData | null>(null);
  const [tacticalTwins, setTacticalTwins] = useState<TacticalTwinResponse | null>(null);
  const [aiReport, setAiReport] = useState<AiScoutReportResponse | null>(null);
  const [isAiLoading, setIsAiLoading] = useState(false);

  const [isLoadingPlayers, setIsLoadingPlayers] = useState(true);
  const [isLoadingHeader, setIsLoadingHeader] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [profileView, setProfileView] = useState<"visual" | "analytical">("visual");

  useEffect(() => {
    let active = true;
    const timeoutId = setTimeout(async () => {
      setIsLoadingPlayers(true);
      setErrorMessage(null);
      try {
        const options = await fetchScoutPlayerOptions(season, 30, searchText.trim() || undefined);
        if (!active) {
          return;
        }
        setPlayers(options);
      } catch {
        if (!active) {
          return;
        }
        setErrorMessage("Could not search players for scout reports.");
      } finally {
        if (active) {
          setIsLoadingPlayers(false);
        }
      }
    }, 250);

    return () => {
      active = false;
      clearTimeout(timeoutId);
    };
  }, [season, searchText]);

  useEffect(() => {
    let active = true;
    if (!selectedPlayer) {
      setHeader(null);
      setSpatialProfile(null);
      setTmData(null);
      setTacticalTwins(null);
      setAiReport(null);
      return;
    }

    async function loadPlayerHeader() {
      setIsLoadingHeader(true);
      setErrorMessage(null);
      setIsAiLoading(true);

      // Start AI generation asynchronously
      fetchAiScoutReport(selectedPlayer!.name, season)
        .then(res => { if (active) setAiReport(res); })
        .catch(e => console.error("AI report failed", e))
        .finally(() => { if (active) setIsAiLoading(false); });

      try {
        const payload = await fetchScoutPlayerHeader(selectedPlayer!.name, season, selectedPlayer!.club || undefined);
        const spatialPayload = await fetchSpatialProfile(selectedPlayer!.name, "2025/2026").catch(() => null);
        const tmPayload = await fetchTransferMarketData(selectedPlayer!.name).catch(() => null);
        const twinPayload = await fetchTacticalTwins(selectedPlayer!.name).catch(() => null);
        
        if (!active) {
          return;
        }
        setHeader(payload);
        setSpatialProfile(spatialPayload);
        setTmData(tmPayload);
        setTacticalTwins(twinPayload);
      } catch {
        if (!active) {
          return;
        }
        setHeader(null);
        setErrorMessage("Could not load player header data.");
      } finally {
        if (active) {
          setIsLoadingHeader(false);
        }
      }
    }

    loadPlayerHeader();
    return () => {
      active = false;
    };
  }, [selectedPlayer, season]);

  // confidenceLabel derived from header.confidence if needed in future

  const themeHex = useMemo(() => {
    switch (theme) {
      case "blue": return "#3b82f6";
      case "orange": return "#f59e0b";
      case "red": return "#ef4444";
      case "green": return "#10b981";
      case "purple": return "#8b5cf6";
      default: return "#3b82f6";
    }
  }, [theme]);

    return (
    <PageShell title="" description="">
      <div style={{ maxWidth: "1000px", margin: "0 auto", padding: "1rem" }}>
        
        {/* PREMIUM CENTERED HERO HEADER */}
        <div style={{ textAlign: 'center', marginBottom: '3rem', marginTop: '1rem', position: 'relative' }}>
          <h1 style={{ 
            fontSize: '3rem', 
            fontWeight: 800, 
            color: '#0f172a', 
            letterSpacing: '-0.025em',
            margin: '0 0 0.5rem 0'
          }}>
            Scout Reports
          </h1>
          <p style={{ 
            fontSize: '1.1rem', 
            color: '#64748b', 
            maxWidth: '600px', 
            margin: '0 auto',
            lineHeight: '1.6'
          }}>
            Identity and baseline output before advanced tactical visualizations.
          </p>
        </div>

        {/* CENTERED CONTROLS BAR */}
        <div style={{
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '2rem',
          backgroundColor: '#ffffff',
          padding: '1.5rem 2.5rem',
          borderRadius: '16px',
          boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.05), 0 8px 10px -6px rgba(0, 0, 0, 0.01)',
          border: '1px solid #e2e8f0',
          marginBottom: '3rem'
        }}>
          
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
            <span style={{ fontSize: '0.75rem', fontWeight: 700, letterSpacing: '0.05em', color: '#64748b', textTransform: 'uppercase', marginBottom: '0.5rem' }}>Season</span>
            <div style={{
              padding: '0.5rem 1.25rem',
              backgroundColor: `${themeHex}15`,
              color: themeHex,
              fontWeight: 700,
              borderRadius: '999px',
              border: `1px solid ${themeHex}30`,
              fontSize: '0.9rem'
            }}>
              {season}
            </div>
          </div>

          <div style={{ width: '1px', height: '40px', backgroundColor: '#e2e8f0' }}></div>

          <label style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start', position: 'relative', minWidth: '300px' }}>
            <span style={{ fontSize: '0.75rem', fontWeight: 700, letterSpacing: '0.05em', color: '#64748b', textTransform: 'uppercase', marginBottom: '0.5rem' }}>Search Player</span>
            <input
              type="text"
              placeholder="Type player name (e.g., Declan Rice)"
              value={searchText}
              onChange={(event) => setSearchText(event.target.value)}
              style={{
                width: '100%',
                padding: '0.75rem 1rem',
                borderRadius: '8px',
                border: '1px solid #cbd5e1',
                fontSize: '1rem',
                outline: 'none',
                transition: 'border-color 0.2s ease',
              }}
              onFocus={(e) => e.target.style.borderColor = themeHex}
              onBlur={(e) => e.target.style.borderColor = '#cbd5e1'}
            />
            {searchText && (
              <div className="scout-search-results" style={{
                position: 'absolute',
                top: '100%',
                left: 0,
                right: 0,
                marginTop: '0.5rem',
                backgroundColor: '#ffffff',
                border: '1px solid #e2e8f0',
                borderRadius: '8px',
                boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1)',
                zIndex: 50,
                maxHeight: '300px',
                overflowY: 'auto'
              }}>
                {isLoadingPlayers ? <p style={{ padding: '1rem', margin: 0, color: '#64748b' }}>Searching...</p> : null}
                {!isLoadingPlayers && players.length === 0 ? (
                  <p style={{ padding: '1rem', margin: 0, color: '#64748b' }}>No players found</p>
                ) : null}
                {players.map((player) => (
                  <button
                    key={`${player.player_name}-${player.club}`}
                    style={{
                      display: 'flex',
                      flexDirection: 'column',
                      width: '100%',
                      padding: '0.75rem 1rem',
                      border: 'none',
                      borderBottom: '1px solid #f1f5f9',
                      background: 'none',
                      textAlign: 'left',
                      cursor: 'pointer',
                      transition: 'background-color 0.1s ease',
                    }}
                    onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#f8fafc'}
                    onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                    type="button"
                    onClick={() => {
                      setSelectedPlayer({ name: player.player_name, club: player.club });
                      setSearchText(player.player_name);
                    }}
                  >
                    <strong style={{ color: '#0f172a', fontSize: '1rem' }}>{player.player_name}</strong>
                    <span style={{ color: '#64748b', fontSize: '0.85rem' }}>{player.club ?? "Unknown club"}</span>
                  </button>
                ))}
              </div>
            )}
          </label>

          <div style={{ width: '1px', height: '40px', backgroundColor: '#e2e8f0' }}></div>

          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
            <span style={{ fontSize: '0.75rem', fontWeight: 700, letterSpacing: '0.05em', color: '#64748b', textTransform: 'uppercase', marginBottom: '0.5rem' }}>Color Theme</span>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              {['blue', 'orange', 'red', 'green', 'purple'].map(color => (
                <button 
                  key={color}
                  className={`theme-btn ${color} ${theme === color ? 'active' : ''}`} 
                  onClick={() => setTheme(color as any)} 
                  aria-label={color}
                  style={{
                    width: '28px',
                    height: '28px',
                    borderRadius: '50%',
                    border: theme === color ? '2px solid #0f172a' : '2px solid transparent',
                    cursor: 'pointer',
                    transition: 'transform 0.1s ease',
                    transform: theme === color ? 'scale(1.15)' : 'scale(1)'
                  }}
                  onMouseEnter={(e) => e.currentTarget.style.transform = 'scale(1.15)'}
                  onMouseLeave={(e) => e.currentTarget.style.transform = theme === color ? 'scale(1.15)' : 'scale(1)'}
                ></button>
              ))}
            </div>
          </div>
        </div>

        <section id="scout-report-content" className={`scout-header-panel theme-${theme}`} style={{ paddingBottom: '2rem' }}>
          {errorMessage ? <p className="scout-error">{errorMessage}</p> : null}

        <article className="player-header-card">
          {isLoadingHeader ? (
            <p className="scout-loading">Loading player header...</p>
          ) : header ? (
            <>
              <div className="premium-header-container">
                {(() => {
                  const nameParts = header.player_name.split(' ');
                  const firstName = nameParts.length > 1 ? nameParts.slice(0, -1).join(' ') : '';
                  const lastName = nameParts.length > 1 ? nameParts[nameParts.length - 1] : header.player_name;
                  
                  let heightStr = "N/A";
                  if (header.height) {
                    const totalInches = Math.round(header.height / 2.54);
                    const feet = Math.floor(totalInches / 12);
                    const inches = totalInches % 12;
                    heightStr = `${feet}'${inches}`;
                  }

                  const prefFoot = header.preferred_foot?.toLowerCase() || "";
                  const isLeft = prefFoot.includes("left") || prefFoot.includes("both");
                  const isRight = prefFoot.includes("right") || prefFoot.includes("both");

                  return (
                    <div className="premium-header">
                      <div className="ph-left">
                        <div className="ph-first-name">{firstName}</div>
                        <div className="ph-last-name">{lastName}</div>
                        <div className="ph-club-row">
                          {header.nation_flag && <img src={header.nation_flag} alt="Nation" className="ph-flag" />}
                          <span className="ph-club-name">{header.club ?? "N/A"}</span>
                        </div>
                      </div>

                      <div className="ph-middle">
                        <div className="ph-stat">{header.position ?? "N/A"}</div>
                        <div className="ph-stat">{header.age ?? "N/A"}</div>
                        <div className="ph-stat">{heightStr}</div>
                        <div className="ph-feet">
                          <svg width="12" height="24" viewBox="0 0 12 24" fill={isLeft ? "#111" : "#d1d5db"} stroke="none">
                            <path d="M 9 2 C 4 2, 2 8, 2 14 C 2 19, 4 22, 6 22 C 8 22, 10 19, 10 14 C 10 8, 12 4, 9 2 Z"/>
                          </svg>
                          <svg width="12" height="24" viewBox="0 0 12 24" fill={isRight ? "#111" : "#d1d5db"} stroke="none">
                            <path d="M 3 2 C 8 2, 10 8, 10 14 C 10 19, 8 22, 6 22 C 4 22, 2 19, 2 14 C 2 8, 0 4, 3 2 Z"/>
                          </svg>
                        </div>
                      </div>

                      <div className="ph-right">
                        {header.player_picture ? (
                          <img src={header.player_picture} alt={lastName} className="ph-photo" />
                        ) : (
                          <div className="ph-photo-placeholder"></div>
                        )}
                      </div>
                    </div>
                  );
                })()}
                <hr className="scout-divider" />
              </div>
              <div className="player-header-meta">
                <div>
                  <span className="scout-label">Discipline</span>
                  <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.25rem' }}>
                    <div className="card-badge yellow-card" title="Yellow Cards">
                      <div className="card-icon"></div>
                      <strong>{header.yellow_cards ?? 0}</strong>
                    </div>
                    <div className="card-badge red-card" title="Red Cards">
                      <div className="card-icon"></div>
                      <strong>{header.red_cards ?? 0}</strong>
                    </div>
                  </div>
                </div>
                <div>
                  <span className="scout-label">Age</span>
                  <strong>{header.age ?? "N/A"}</strong>
                </div>
                <div>
                  <span className="scout-label">Height</span>
                  <strong>{header.height ? `${header.height} cm` : "N/A"}</strong>
                </div>

                <div>
                  <span className="scout-label">Role</span>
                  <strong>{spatialProfile?.sub_role || header?.position || "N/A"}</strong>
                </div>
                <div>
                  <span className="scout-label">Data Confidence</span>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <strong>{Math.round((spatialProfile?.confidence_score || 1) * 100)}%</strong>
                    <div style={{ 
                      width: '40px', 
                      height: '6px', 
                      background: '#eee', 
                      borderRadius: '3px',
                      overflow: 'hidden'
                    }}>
                      <div style={{ 
                        width: `${(spatialProfile?.confidence_score || 1) * 100}%`, 
                        height: '100%', 
                        background: (spatialProfile?.confidence_score || 1) > 0.7 ? '#35a849' : '#d72638' 
                      }} />
                    </div>
                  </div>
                </div>
              </div>

              <div className="player-header-stats">
                <div className="stat-box">
                  <span>Goals</span>
                  <strong>{header.goals_this_season ?? "N/A"}</strong>
                  <small>Understat 25-26</small>
                </div>
                <div className="stat-box">
                  <span>Assists</span>
                  <strong>{header.assists_this_season ?? "N/A"}</strong>
                  <small>Understat 25-26</small>
                </div>
                <div className="stat-box">
                  <span>xG</span>
                  <strong>
                    {typeof header.xg_this_season === "number" ? header.xg_this_season.toFixed(2) : "N/A"}
                  </strong>
                  <small>Understat 25-26</small>
                </div>
                <div className="stat-box">
                  <span>xA</span>
                  <strong>
                    {typeof header.xa_this_season === "number" ? header.xa_this_season.toFixed(2) : "N/A"}
                  </strong>
                  <small>Understat 25-26</small>
                </div>
                <div className="stat-box">
                  <span>Matches</span>
                  <strong>{header.matches_played}</strong>
                  <small>Sample size</small>
                </div>
              </div>
            </>
          ) : (
            <p className="scout-loading">Select a player to see header details.</p>
          )}
        </article>

        {header && (
          <AiAnnotation text={aiReport?.executive_summary || ""} theme={theme} loading={isAiLoading} />
        )}

        {tmData && (
          <MarketValueChart data={tmData} theme={theme} age={header?.age ?? undefined} />
        )}

        {spatialProfile && header && (
          <div className="mt-8" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {/* Profile Toggle & Charts */}
            <div style={{ width: "100%", maxWidth: "900px", margin: "0 auto 1.5rem auto" }}>
              <div id="profile-toggle-btns" style={{ display: "flex", justifyContent: "center", marginBottom: "1.5rem" }}>
                <div style={{ display: "flex", background: "#f8fafc", padding: "0.3rem", borderRadius: "999px", gap: "0.25rem", border: "1px solid #e2e8f0", boxShadow: "inset 0 2px 4px rgba(0,0,0,0.02)" }}>
                  <button
                    onClick={() => setProfileView("visual")}
                    style={{
                      padding: "0.5rem 1.75rem",
                      borderRadius: "999px",
                      border: "none",
                      fontSize: "0.85rem",
                      fontWeight: 700,
                      cursor: "pointer",
                      transition: "all 0.2s ease",
                      background: profileView === "visual" ? "#ffffff" : "transparent",
                      color: profileView === "visual" ? themeHex : "#64748b",
                      boxShadow: profileView === "visual" ? "0 2px 5px rgba(0,0,0,0.08), 0 1px 1px rgba(0,0,0,0.04)" : "none",
                    }}
                  >
                    Visual Profile
                  </button>
                  <button
                    onClick={() => setProfileView("analytical")}
                    style={{
                      padding: "0.5rem 1.75rem",
                      borderRadius: "999px",
                      border: "none",
                      fontSize: "0.85rem",
                      fontWeight: 700,
                      cursor: "pointer",
                      transition: "all 0.2s ease",
                      background: profileView === "analytical" ? "#ffffff" : "transparent",
                      color: profileView === "analytical" ? themeHex : "#64748b",
                      boxShadow: profileView === "analytical" ? "0 2px 5px rgba(0,0,0,0.08), 0 1px 1px rgba(0,0,0,0.04)" : "none",
                    }}
                  >
                    Analytical Profile
                  </button>
                </div>
              </div>

              <div style={{ width: "100%" }}>
                <AnimatePresence mode="wait">
                  {profileView === "visual" ? (
                    <motion.div
                      key="visual"
                      initial={{ opacity: 0, scale: 0.98 }}
                      animate={{ opacity: 1, scale: 1 }}
                      exit={{ opacity: 0, scale: 0.98 }}
                      transition={{ duration: 0.2 }}
                    >
                      <PizzaChart
                        percentiles={spatialProfile.percentiles_2526}
                        theme={theme}
                      />
                    </motion.div>
                  ) : (
                    <motion.div
                      key="analytical"
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -10 }}
                      transition={{ duration: 0.2 }}
                    >
                      <PercentileBarChart
                        percentiles={spatialProfile.percentiles_2526}
                        rawStats={spatialProfile.per_90}
                        theme={theme}
                      />
                    </motion.div>
                  )}
                </AnimatePresence>
                
                <AiAnnotation text={aiReport?.pizza_chart_analysis || ""} theme={theme} loading={isAiLoading} />
              </div>
            </div>
            
            {spatialProfile.touch_heatmap && (
              <div className="shot-map-container" style={{ marginTop: '0.5rem', marginBottom: '1.5rem', margin: '0.5rem auto 1.5rem auto' }}>
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', marginBottom: '2rem' }}>
                  <h1 className="shot-map-title">Touch Heatmap</h1>
                  <p className="shot-map-subtitle">All Touches • {season}</p>
                </div>
                <HeatMap
                  grid={spatialProfile.touch_heatmap.all}
                />
                <AiAnnotation text={aiReport?.heatmap_analysis || ""} theme={theme} loading={isAiLoading} />
              </div>
            )}

            <LeagueProjectionMap 
              playerName={header.player_name}
              season="2025/2026"
              theme={theme}
              aiAnalysis={aiReport?.skill_translation_analysis}
            />
            
            {spatialProfile.shot_zones && spatialProfile.shot_zones.length > 0 && (
              <div>
                <ShotMap 
                  playerName={header.player_name} 
                  shots={spatialProfile.shot_zones} 
                  season={season}
                />
              </div>
            )}

            {spatialProfile.xT_zones && spatialProfile.xT_zones.grid && (
              <div>
                <ExpectedThreatMap
                  playerName={header.player_name}
                  grid={spatialProfile.xT_zones.grid}
                  perTouchGrid={spatialProfile.xT_zones.xT_per_touch_grid}
                  touchDensity={spatialProfile.touch_heatmap?.all}
                  season={season}
                />
                <AiAnnotation text={aiReport?.expected_threat_analysis || ""} theme={theme} loading={isAiLoading} />
              </div>
            )}

            {spatialProfile.pass_vectors && spatialProfile.pass_vectors.length > 0 && (
              <div>
                <PassNetworkMap
                  playerName={header.player_name}
                  vectors={spatialProfile.pass_vectors}
                  clusterDistribution={spatialProfile.pass_cluster_distribution}
                  season={season}
                />
                <AiAnnotation text={aiReport?.passing_corridors_analysis || ""} theme={theme} loading={isAiLoading} />
              </div>
            )}
          </div>
        )}

        {header && (
          <div style={{ marginTop: '1.5rem', marginBottom: '2rem' }}>
            <ScatterPlotExplorer 
              theme={theme} 
              season="2025/2026" 
              targetPlayerName={header.player_name} 
            />
          </div>
        )}

        {header && aiReport && (aiReport.positive_development_factors?.length > 0 || aiReport.concerns_and_next_steps?.length > 0) && (
          <div style={{ marginTop: '3rem', marginBottom: '4rem', padding: '0 1rem' }}>
            <h2 style={{ fontSize: '1.5rem', fontWeight: 600, color: '#0f172a', marginBottom: '0.5rem' }}>Development and Next Steps</h2>
            <hr style={{ border: 'none', borderTop: '2px solid #e2e8f0', marginBottom: '2rem' }} />
            
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '4rem' }}>
              <div>
                <h3 style={{ fontSize: '1.25rem', fontWeight: 500, color: '#0f172a', marginBottom: '1.5rem' }}>Positive Development Factors</h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                  {aiReport.positive_development_factors?.map((factor, idx) => (
                    <div key={idx} style={{ paddingLeft: '1rem', borderLeft: '2px solid #000' }}>
                      <p style={{ margin: 0, fontSize: '0.95rem', color: '#475569', lineHeight: '1.5' }}>{factor}</p>
                    </div>
                  ))}
                </div>
              </div>
              
              <div>
                <h3 style={{ fontSize: '1.25rem', fontWeight: 500, color: '#0f172a', marginBottom: '1.5rem' }}>Concerns & Next Steps</h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                  {aiReport.concerns_and_next_steps?.map((concern, idx) => (
                    <div key={idx} style={{ paddingLeft: '1rem', borderLeft: '2px solid #000' }}>
                      <p style={{ margin: 0, fontSize: '0.95rem', color: '#475569', lineHeight: '1.5' }}>{concern}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {header && tacticalTwins && (
          <div>{/* Tactical Constellation — temporarily hidden */}</div>
        )}
      </section>
      </div>
    </PageShell>
  );
}
