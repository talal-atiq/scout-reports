import { useEffect, useMemo, useState } from "react";

import {
  fetchScoutPlayerHeader,
  fetchScoutPlayerOptions,
  fetchSpatialProfile,
  type ScoutPlayerHeader,
  type ScoutPlayerOption,
  type SpatialProfile,
} from "../api/client";
import { PageShell } from "./PageShell";
import { PizzaChart } from "../components/PizzaChart";
import HeatMap from "../components/HeatMap";

export default function ScoutReportsPage() {
  const [season] = useState("25-26");
  const [players, setPlayers] = useState<ScoutPlayerOption[]>([]);
  const [selectedPlayer, setSelectedPlayer] = useState<{name: string, club: string | null} | null>(null);
  const [searchText, setSearchText] = useState("");
  const [theme, setTheme] = useState<"blue" | "orange" | "red" | "green">("blue");
  const [header, setHeader] = useState<ScoutPlayerHeader | null>(null);
  const [spatialProfile, setSpatialProfile] = useState<SpatialProfile | null>(null);
  const [isLoadingPlayers, setIsLoadingPlayers] = useState(true);
  const [isLoadingHeader, setIsLoadingHeader] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

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
      return;
    }

    async function loadPlayerHeader() {
      setIsLoadingHeader(true);
      setErrorMessage(null);
      try {
        const payload = await fetchScoutPlayerHeader(selectedPlayer!.name, season, selectedPlayer!.club || undefined);
        const spatialPayload = await fetchSpatialProfile(selectedPlayer!.name, "2025/2026").catch(() => null);
        
        if (!active) {
          return;
        }
        setHeader(payload);
        setSpatialProfile(spatialPayload);
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

  const confidenceLabel = useMemo(() => {
    if (!header) {
      return "N/A";
    }
    if (header.confidence === "high") {
      return "High Confidence";
    }
    if (header.confidence === "medium") {
      return "Medium Confidence";
    }
    return "Low Confidence";
  }, [header]);

  return (
    <PageShell
      title="Scout Reports"
      description="Player header (season 25-26): identity and baseline output before advanced visualizations."
    >
      <section className={`scout-header-panel theme-${theme}`}>
        <div className="scout-header-controls">
          <div>
            <span className="scout-label">Season</span>
            <div className="scout-season-chip">{season}</div>
          </div>
          <label className="scout-player-select-wrap">
            <span className="scout-label">Search Player</span>
            <input
              type="text"
              placeholder="Type player name (e.g., Erling Haaland)"
              value={searchText}
              onChange={(event) => setSearchText(event.target.value)}
            />
            <div className="scout-search-results">
              {isLoadingPlayers ? <p className="scout-loading">Searching...</p> : null}
              {!isLoadingPlayers && players.length === 0 ? (
                <p className="scout-loading">No players found</p>
              ) : null}
              {players.map((player) => (
                <button
                  key={`${player.player_name}-${player.club}`}
                  className="scout-search-item"
                  type="button"
                  onClick={() => {
                    setSelectedPlayer({ name: player.player_name, club: player.club });
                    setSearchText(player.player_name);
                  }}
                >
                  <strong>{player.player_name}</strong>
                  <span>{player.club ?? "Unknown club"}</span>
                </button>
              ))}
            </div>
          </label>
        </div>

        <div className="theme-selector-container">
          <span className="scout-label" style={{ marginBottom: "0.2rem", fontSize: "0.75rem" }}>Color Theme</span>
          <div className="theme-buttons">
            <button className={`theme-btn blue ${theme === 'blue' ? 'active' : ''}`} onClick={() => setTheme('blue')} aria-label="Blue"></button>
            <button className={`theme-btn orange ${theme === 'orange' ? 'active' : ''}`} onClick={() => setTheme('orange')} aria-label="Orange"></button>
            <button className={`theme-btn red ${theme === 'red' ? 'active' : ''}`} onClick={() => setTheme('red')} aria-label="Red"></button>
            <button className={`theme-btn green ${theme === 'green' ? 'active' : ''}`} onClick={() => setTheme('green')} aria-label="Green"></button>
          </div>
        </div>

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
                  <span className="scout-label">Value</span>
                  <strong style={{ color: "#2d7a46" }}>{header.market_value ?? "N/A"}</strong>
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

        {spatialProfile && header && (
          <div className="mt-8" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <PizzaChart
              percentiles={spatialProfile.percentiles_2526}
              theme={theme}
            />
            
            {spatialProfile.touch_heatmap && (
              <div style={{ marginTop: '0.5rem' }}>
                <h3 style={{ 
                  textAlign: 'center', 
                  marginBottom: '1rem', 
                  fontSize: '1.2rem', 
                  fontWeight: 700,
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em',
                  color: 'inherit',
                  fontFamily: 'inherit'
                }}>
                  All Touches Heatmap
                </h3>
                <HeatMap
                  grid={spatialProfile.touch_heatmap.all}
                />
              </div>
            )}
          </div>
        )}
      </section>
    </PageShell>
  );
}
