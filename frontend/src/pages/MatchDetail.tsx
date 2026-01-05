import { useParams, Link } from 'react-router-dom';
import { useState, useEffect, useMemo } from 'react';
import './MatchDetail.css';

// NPFL Teams data
const NPFL_TEAMS = [
  { id: 'enyimba', apiId: 2254, name: 'Enyimba FC', city: 'Aba', logo: '🦅', stadium: 'Enyimba International Stadium', founded: 1976, coach: 'Finidi George' },
  { id: 'kano_pillars', apiId: 2247, name: 'Kano Pillars', city: 'Kano', logo: '🏛️', stadium: 'Sani Abacha Stadium', founded: 1990, coach: 'Salisu Yusuf' },
  { id: 'rivers_united', apiId: 2253, name: 'Rivers United', city: 'Port Harcourt', logo: '🌊', stadium: 'Adokiye Amiesimaka Stadium', founded: 2016, coach: 'Stanley Eguma' },
  { id: 'plateau_united', apiId: 2250, name: 'Plateau United', city: 'Jos', logo: '⛰️', stadium: 'New Jos Stadium', founded: 1975, coach: 'Fidelis Ilechukwu' },
  { id: 'rangers', apiId: 2252, name: 'Rangers Int.', city: 'Enugu', logo: '🦁', stadium: 'Nnamdi Azikiwe Stadium', founded: 1970, coach: 'Abdul Maikaba' },
  { id: 'akwa_united', apiId: 2241, name: 'Akwa United', city: 'Uyo', logo: '⚡', stadium: 'Godswill Akpabio Stadium', founded: 1996, coach: 'Kennedy Boboye' },
  { id: 'sunshine', apiId: 2257, name: 'Sunshine Stars', city: 'Akure', logo: '☀️', stadium: 'Akure Township Stadium', founded: 2007, coach: 'Deji Ayeni' },
  { id: 'kwara', apiId: 2249, name: 'Kwara United', city: 'Ilorin', logo: '🔵', stadium: 'Kwara Stadium Complex', founded: 2006, coach: 'Abdullahi Biffo' },
  { id: 'abia', apiId: 2240, name: 'Abia Warriors', city: 'Umuahia', logo: '⚔️', stadium: 'Umuahia Township Stadium', founded: 2008, coach: 'Imama Amapakabo' },
  { id: 'lobi', apiId: 2255, name: 'Lobi Stars', city: 'Makurdi', logo: '⭐', stadium: 'Aper Aku Stadium', founded: 1968, coach: 'Eugene Agagbe' },
];

// Team-specific players for events
const playersByTeam: Record<string, string[]> = {
  'Enyimba FC': ['Victor Mbaoma', 'Austin Ogunye', 'Cyril Olisema', 'Tosin Omoyele'],
  'Kano Pillars': ['Ahmed Musa', 'Rabiu Ali', 'Nyima Nwagua', 'David Ebuka'],
  'Rivers United': ['Chisom Chikatara', 'Kazie Enyinnaya', 'Cletus Emotan', 'Fortune Omoniwari'],
  'Plateau United': ['Ifeanyi George', 'Jesse Akila', 'Ibrahim Buhari', 'Mustapha Ibrahim'],
  'Rangers Int.': ['Godwin Obaje', 'Chiamaka Madu', 'Christian Nnaji', 'Kenechukwu Agu'],
  'Akwa United': ['Ndifreke Effiong', 'Samuel Amadi', 'Seth Mayi', 'Ubong Friday'],
  'Sunshine Stars': ['Sadiq Umar', 'Fuad Ekelojuoti', 'Anthony Omaka', 'Sunday Adetunji'],
  'Kwara United': ['Jide Fatokun', 'Wasiu Jimoh', 'Michael Ohanu', 'Samad Kadiri'],
  'Abia Warriors': ['Paul Onuachu', 'Emeka Obioma', 'Henry Ocheme', 'Sunday Megwo'],
  'Lobi Stars': ['Moses Simon', 'Sikiru Alimi', 'Ossy Martins', 'Chinonso Okonkwo'],
};

// Rotating matchup sets (same as LiveDashboard)
const matchupSets = [
  [
    { home: 0, away: 1, venue: 'Enyimba Stadium, Aba' },
    { home: 2, away: 3, venue: 'Adokiye Amiesimaka Stadium' },
    { home: 4, away: 5, venue: 'Nnamdi Azikiwe Stadium' },
    { home: 6, away: 9, venue: 'Akure Township Stadium' },
    { home: 7, away: 8, venue: 'Kwara Stadium, Ilorin' },
  ],
  [
    { home: 1, away: 2, venue: 'Sani Abacha Stadium, Kano' },
    { home: 3, away: 4, venue: 'New Jos Stadium' },
    { home: 5, away: 6, venue: 'Godswill Akpabio Stadium' },
    { home: 8, away: 0, venue: 'Umuahia Township Stadium' },
    { home: 9, away: 7, venue: 'Aper Aku Stadium' },
  ],
  [
    { home: 2, away: 0, venue: 'Adokiye Amiesimaka Stadium' },
    { home: 4, away: 1, venue: 'Nnamdi Azikiwe Stadium' },
    { home: 6, away: 3, venue: 'Akure Township Stadium' },
    { home: 7, away: 5, venue: 'Kwara Stadium, Ilorin' },
    { home: 9, away: 8, venue: 'Aper Aku Stadium' },
  ],
  [
    { home: 3, away: 2, venue: 'New Jos Stadium' },
    { home: 5, away: 4, venue: 'Godswill Akpabio Stadium' },
    { home: 0, away: 6, venue: 'Enyimba Stadium, Aba' },
    { home: 8, away: 7, venue: 'Umuahia Township Stadium' },
    { home: 1, away: 9, venue: 'Sani Abacha Stadium, Kano' },
  ],
  [
    { home: 4, away: 0, venue: 'Nnamdi Azikiwe Stadium' },
    { home: 6, away: 2, venue: 'Akure Township Stadium' },
    { home: 9, away: 3, venue: 'Aper Aku Stadium' },
    { home: 1, away: 8, venue: 'Sani Abacha Stadium, Kano' },
    { home: 5, away: 7, venue: 'Godswill Akpabio Stadium' },
  ],
  [
    { home: 7, away: 0, venue: 'Kwara Stadium, Ilorin' },
    { home: 8, away: 2, venue: 'Umuahia Township Stadium' },
    { home: 1, away: 3, venue: 'Sani Abacha Stadium, Kano' },
    { home: 6, away: 4, venue: 'Akure Township Stadium' },
    { home: 9, away: 5, venue: 'Aper Aku Stadium' },
  ],
  [
    { home: 0, away: 9, venue: 'Enyimba Stadium, Aba' },
    { home: 2, away: 5, venue: 'Adokiye Amiesimaka Stadium' },
    { home: 3, away: 7, venue: 'New Jos Stadium' },
    { home: 4, away: 8, venue: 'Nnamdi Azikiwe Stadium' },
    { home: 6, away: 1, venue: 'Akure Township Stadium' },
  ],
];

// Function to get dynamic match data based on ID
const getMatchData = (matchId: string) => {
  const now = new Date();
  const hour = now.getHours();
  const minute = now.getMinutes();

  // Parse dynamic ID format: "dayOfYear-index" (e.g., "343-1")
  const parts = matchId.split('-');
  if (parts.length === 2) {
    const dayOfYear = parseInt(parts[0]);
    const index = parseInt(parts[1]) - 1; // Convert to 0-based index

    if (!isNaN(dayOfYear) && !isNaN(index) && index >= 0 && index < 5) {
      const currentSet = matchupSets[dayOfYear % matchupSets.length];
      const matchup = currentSet[index];

      // Generate dynamic scores based on hour
      const generateScore = (seed: number): number => {
        const combined = (hour * 60 + minute + seed * 17) % 100;
        if (combined < 30) return 0;
        if (combined < 55) return 1;
        if (combined < 75) return 2;
        if (combined < 90) return 3;
        return 4;
      };

      // Calculate match status based on time cycle
      const cycleMinutes = (hour * 60 + minute) % 120;
      const phase = (cycleMinutes + index * 20) % 120;

      let status: string;
      let matchMinute: string;

      if (phase < 45) {
        status = 'LIVE';
        matchMinute = `${(cycleMinutes + index * 15) % 90 + 1}'`;
      } else if (phase < 50) {
        status = 'HT';
        matchMinute = 'HT';
      } else if (phase < 95) {
        status = 'LIVE';
        matchMinute = `${45 + (phase - 50)}'`;
      } else if (phase < 105) {
        status = 'FT';
        matchMinute = 'FT';
      } else {
        status = 'SCHEDULED';
        matchMinute = `${18 + index}:00`;
      }

      const isScheduled = status === 'SCHEDULED';

      return {
        home: NPFL_TEAMS[matchup.home],
        away: NPFL_TEAMS[matchup.away],
        homeScore: isScheduled ? 0 : generateScore(index * 2),
        awayScore: isScheduled ? 0 : generateScore(index * 2 + 1),
        status,
        minute: matchMinute,
        venue: matchup.venue
      };
    }
  }

  // Fallback for old-style IDs (1-5) or invalid IDs
  const todayDayOfYear = Math.floor((now.getTime() - new Date(now.getFullYear(), 0, 0).getTime()) / 86400000);
  const fallbackIndex = Math.max(0, Math.min(4, parseInt(matchId) - 1 || 0));
  const currentSet = matchupSets[todayDayOfYear % matchupSets.length];
  const matchup = currentSet[fallbackIndex];

  return {
    home: NPFL_TEAMS[matchup.home],
    away: NPFL_TEAMS[matchup.away],
    homeScore: 2,
    awayScore: 1,
    status: 'LIVE',
    minute: "67'",
    venue: matchup.venue
  };
};

interface MatchEvent {
  id: string;
  type: 'goal' | 'yellow_card' | 'red_card' | 'shot' | 'substitution' | 'foul';
  minute: string;
  player: string;
  team: string;
  detail: string;
}

interface MatchStats {
  homeShots: number;
  awayShots: number;
  homeShotsOnTarget: number;
  awayShotsOnTarget: number;
  homePossession: number;
  awayPossession: number;
  homeCorners: number;
  awayCorners: number;
  homeFouls: number;
  awayFouls: number;
}

const MatchDetail = () => {
  const { matchId } = useParams<{ matchId: string }>();
  const [events, setEvents] = useState<MatchEvent[]>([]);
  const [stats, setStats] = useState<MatchStats | null>(null);

  // Memoize match data to prevent re-renders
  const match = useMemo(() => {
    return getMatchData(matchId || '1');
  }, [matchId]);

  // Generate demo events and stats once when matchId changes
  useEffect(() => {
    const homeName = match.home.name;
    const awayName = match.away.name;

    // Get team-specific players
    const homePlayers = playersByTeam[homeName] || ['Player 1', 'Player 2', 'Player 3', 'Player 4'];
    const awayPlayers = playersByTeam[awayName] || ['Player 1', 'Player 2', 'Player 3', 'Player 4'];

    const generateMatchEvents = (): MatchEvent[] => {
      if (match.status === 'SCHEDULED') return [];

      const generatedEvents: MatchEvent[] = [];
      const currentMinute = match.status === 'FT' || match.status === 'HT' ?
        (match.status === 'HT' ? 45 : 90) : parseInt(match.minute) || 45;

      // Generate goals for home team
      for (let i = 0; i < match.homeScore; i++) {
        const minute = Math.floor(Math.random() * currentMinute) + 1;
        generatedEvents.push({
          id: `goal_home_${i}`,
          type: 'goal',
          minute: `${minute}'`,
          player: homePlayers[Math.floor(Math.random() * homePlayers.length)],
          team: homeName,
          detail: ['Header', 'Penalty', 'Long range', 'Tap in'][Math.floor(Math.random() * 4)]
        });
      }

      // Generate goals for away team
      for (let i = 0; i < match.awayScore; i++) {
        const minute = Math.floor(Math.random() * currentMinute) + 1;
        generatedEvents.push({
          id: `goal_away_${i}`,
          type: 'goal',
          minute: `${minute}'`,
          player: awayPlayers[Math.floor(Math.random() * awayPlayers.length)],
          team: awayName,
          detail: ['Header', 'Penalty', 'Long range', 'Tap in'][Math.floor(Math.random() * 4)]
        });
      }

      // Add some cards
      if (currentMinute > 20) {
        generatedEvents.push({
          id: 'yellow_1',
          type: 'yellow_card',
          minute: `${Math.floor(Math.random() * currentMinute) + 1}'`,
          player: homePlayers[2],
          team: homeName,
          detail: 'Reckless challenge'
        });
      }

      return generatedEvents.sort((a, b) => parseInt(b.minute) - parseInt(a.minute));
    };

    // Generate stats once
    const homePoss = Math.floor(Math.random() * 30) + 40;
    const generatedStats: MatchStats = {
      homeShots: Math.floor(Math.random() * 10) + 5,
      awayShots: Math.floor(Math.random() * 10) + 3,
      homeShotsOnTarget: Math.floor(Math.random() * 5) + 2,
      awayShotsOnTarget: Math.floor(Math.random() * 5) + 1,
      homePossession: homePoss,
      awayPossession: 100 - homePoss,
      homeCorners: Math.floor(Math.random() * 8),
      awayCorners: Math.floor(Math.random() * 8),
      homeFouls: Math.floor(Math.random() * 15),
      awayFouls: Math.floor(Math.random() * 15)
    };

    setEvents(generateMatchEvents());
    setStats(generatedStats);
  }, [matchId, match.home.name, match.away.name, match.status, match.minute, match.homeScore, match.awayScore]);

  const getEventIcon = (type: MatchEvent['type']) => {
    const icons: Record<string, string> = {
      goal: '⚽',
      yellow_card: '🟨',
      red_card: '🟥',
      shot: '🎯',
      substitution: '🔄',
      foul: '⚠️'
    };
    return icons[type] || '📊';
  };

  return (
    <div className="match-detail-page">
      {/* Back Navigation */}
      <div className="back-nav">
        <Link to="/" className="back-link">← Back to Matches</Link>
      </div>

      {/* Match Header */}
      <div className="match-detail-header">
        <div className="match-status-bar">
          <span className={`match-badge ${match.status.toLowerCase()}`}>
            {match.status === 'LIVE' && <span className="live-pulse"></span>}
            {match.status === 'LIVE' ? `LIVE ${match.minute}` : match.status === 'FT' ? 'Full Time' : match.minute}
          </span>
          <span className="venue-info">📍 {match.venue}</span>
        </div>

        <div className="teams-display">
          <Link to={`/team/${match.home.id}`} className="team-block home">
            <span className="team-logo-large">{match.home.logo}</span>
            <span className="team-name-full">{match.home.name}</span>
            <span className="team-city">{match.home.city}</span>
          </Link>

          <div className="score-display">
            <span className="score-large">{match.homeScore}</span>
            <span className="score-divider">-</span>
            <span className="score-large">{match.awayScore}</span>
          </div>

          <Link to={`/team/${match.away.id}`} className="team-block away">
            <span className="team-logo-large">{match.away.logo}</span>
            <span className="team-name-full">{match.away.name}</span>
            <span className="team-city">{match.away.city}</span>
          </Link>
        </div>
      </div>

      {/* Match Content */}
      <div className="match-content-grid">
        {/* Match Events Timeline */}
        <div className="events-timeline">
          <h3>Match Events</h3>
          {events.length === 0 ? (
            <div className="no-events">
              {match.status === 'SCHEDULED' ? 'Match has not started yet' : 'No events recorded'}
            </div>
          ) : (
            <div className="timeline">
              {events.map(event => (
                <div key={event.id} className={`timeline-event ${event.type}`}>
                  <div className="event-time">{event.minute}</div>
                  <div className="event-icon">{getEventIcon(event.type)}</div>
                  <div className="event-details">
                    <span className="event-player">{event.player}</span>
                    <span className="event-team-name">{event.team}</span>
                    <span className="event-description">{event.detail}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Match Stats */}
        <div className="match-stats">
          <h3>Match Statistics</h3>
          {stats && (
            <div className="stats-list">
              <div className="stat-row">
                <span className="stat-home">{stats.homeShots}</span>
                <span className="stat-name">Shots</span>
                <span className="stat-away">{stats.awayShots}</span>
              </div>
              <div className="stat-row">
                <span className="stat-home">{stats.homeShotsOnTarget}</span>
                <span className="stat-name">Shots on Target</span>
                <span className="stat-away">{stats.awayShotsOnTarget}</span>
              </div>
              <div className="stat-row">
                <span className="stat-home">{stats.homePossession}%</span>
                <span className="stat-name">Possession</span>
                <span className="stat-away">{stats.awayPossession}%</span>
              </div>
              <div className="stat-row">
                <span className="stat-home">{stats.homeCorners}</span>
                <span className="stat-name">Corners</span>
                <span className="stat-away">{stats.awayCorners}</span>
              </div>
              <div className="stat-row">
                <span className="stat-home">{stats.homeFouls}</span>
                <span className="stat-name">Fouls</span>
                <span className="stat-away">{stats.awayFouls}</span>
              </div>
            </div>
          )}
        </div>

        {/* Team Info */}
        <div className="team-info-panel">
          <h3>Team Information</h3>
          <div className="team-info-grid">
            <Link to={`/team/${match.home.id}`} className="team-info-card">
              <span className="team-info-logo">{match.home.logo}</span>
              <div className="team-info-details">
                <span className="team-info-name">{match.home.name}</span>
                <span className="team-info-meta">Founded: {match.home.founded}</span>
                <span className="team-info-meta">Stadium: {match.home.stadium}</span>
              </div>
            </Link>
            <Link to={`/team/${match.away.id}`} className="team-info-card">
              <span className="team-info-logo">{match.away.logo}</span>
              <div className="team-info-details">
                <span className="team-info-name">{match.away.name}</span>
                <span className="team-info-meta">Founded: {match.away.founded}</span>
                <span className="team-info-meta">Stadium: {match.away.stadium}</span>
              </div>
            </Link>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="detail-footer">
        <p>⚽ Football Analytics • MSc Research Project • Sheffield Hallam University</p>
        <p>Adebayo Oyeleye © 2025</p>
      </footer>
    </div>
  );
};

export default MatchDetail;
