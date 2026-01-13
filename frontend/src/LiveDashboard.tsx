import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import './LiveDashboard.css';

// API URLs
const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://d4pstbgzu1.execute-api.us-east-1.amazonaws.com/development';
const API_FOOTBALL_KEY = import.meta.env.VITE_API_FOOTBALL_KEY || '';
const API_FOOTBALL_URL = 'https://v3.football.api-sports.io';
const NPFL_LEAGUE_ID = 399; // Nigerian Professional Football League

// NPFL Teams data with API-Football IDs
const NPFL_TEAMS = [
  { id: 'enyimba', apiId: 2254, name: 'Enyimba FC', city: 'Aba', logo: '🦅' },
  { id: 'kano_pillars', apiId: 2247, name: 'Kano Pillars', city: 'Kano', logo: '🏛️' },
  { id: 'rivers_united', apiId: 2253, name: 'Rivers United', city: 'Port Harcourt', logo: '🌊' },
  { id: 'plateau_united', apiId: 2250, name: 'Plateau United', city: 'Jos', logo: '⛰️' },
  { id: 'rangers', apiId: 2252, name: 'Rangers Int.', city: 'Enugu', logo: '🦁' },
  { id: 'akwa_united', apiId: 2241, name: 'Akwa United', city: 'Uyo', logo: '⚡' },
  { id: 'sunshine', apiId: 2257, name: 'Sunshine Stars', city: 'Akure', logo: '☀️' },
  { id: 'kwara', apiId: 2249, name: 'Kwara United', city: 'Ilorin', logo: '🔵' },
  { id: 'abia', apiId: 2240, name: 'Abia Warriors', city: 'Umuahia', logo: '⚔️' },
  { id: 'lobi', apiId: 2255, name: 'Lobi Stars', city: 'Makurdi', logo: '⭐' },
];

interface Match {
  id: string;
  homeTeam: { name: string; logo: string; score: number };
  awayTeam: { name: string; logo: string; score: number };
  status: 'LIVE' | 'FT' | 'HT' | 'SCHEDULED' | '1H' | '2H' | 'ET' | 'P' | 'BT' | 'SUSP' | 'INT' | 'PST' | 'CANC' | 'ABD' | 'AWD' | 'WO' | 'NS';
  minute: string;
  venue: string;
  isLive?: boolean;
}

interface MatchEvent {
  id: string;
  type: 'goal' | 'yellow_card' | 'red_card' | 'shot' | 'pass' | 'tackle' | 'foul' | 'substitution';
  minute: string;
  player: string;
  team: string;
  detail: string;
  timestamp: Date;
  matchId: string;
}

// API-Football response types
interface APIFixture {
  fixture: {
    id: number;
    date: string;
    venue: { name: string; city: string };
    status: { short: string; elapsed: number | null };
  };
  league: { id: number; name: string };
  teams: {
    home: { id: number; name: string; logo: string };
    away: { id: number; name: string; logo: string };
  };
  goals: { home: number | null; away: number | null };
  events?: APIEvent[];
}

interface APIEvent {
  time: { elapsed: number };
  team: { name: string };
  player: { name: string };
  type: string;
  detail: string;
}

const LiveDashboard = () => {
  const [matches, setMatches] = useState<Match[]>([]);
  const [events, setEvents] = useState<MatchEvent[]>([]);
  const [systemHealth, setSystemHealth] = useState<{ status: string } | null>(null);
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());
  const [dataMode, setDataMode] = useState<'live' | 'demo'>('demo');
  const [apiError, setApiError] = useState<string | null>(null);

  // Get team emoji by name (fallback for API data)
  const getTeamEmoji = (teamName: string): string => {
    const team = NPFL_TEAMS.find(t =>
      teamName.toLowerCase().includes(t.name.split(' ')[0].toLowerCase()) ||
      t.name.toLowerCase().includes(teamName.split(' ')[0].toLowerCase())
    );
    return team?.logo || '⚽';
  };

  // Map API status to display status
  const mapStatus = (apiStatus: string): Match['status'] => {
    const statusMap: Record<string, Match['status']> = {
      '1H': 'LIVE', '2H': 'LIVE', 'HT': 'HT', 'ET': 'LIVE',
      'P': 'LIVE', 'BT': 'LIVE', 'SUSP': 'SUSP', 'INT': 'INT',
      'FT': 'FT', 'AET': 'FT', 'PEN': 'FT', 'PST': 'PST',
      'CANC': 'CANC', 'ABD': 'ABD', 'AWD': 'AWD', 'WO': 'WO',
      'NS': 'SCHEDULED', 'TBD': 'SCHEDULED'
    };
    return statusMap[apiStatus] || 'SCHEDULED';
  };

  // Check if status is live
  const isLiveStatus = (status: string): boolean => {
    return ['1H', '2H', 'HT', 'ET', 'P', 'BT', 'LIVE'].includes(status);
  };

  // Convert API fixture to Match
  const convertAPIFixture = (fixture: APIFixture): Match => {
    const status = mapStatus(fixture.fixture.status.short);
    const isLive = isLiveStatus(fixture.fixture.status.short);
    const elapsed = fixture.fixture.status.elapsed;

    return {
      id: fixture.fixture.id.toString(),
      homeTeam: {
        name: fixture.teams.home.name,
        logo: getTeamEmoji(fixture.teams.home.name),
        score: fixture.goals.home ?? 0
      },
      awayTeam: {
        name: fixture.teams.away.name,
        logo: getTeamEmoji(fixture.teams.away.name),
        score: fixture.goals.away ?? 0
      },
      status: isLive ? 'LIVE' : status,
      minute: isLive && elapsed ? `${elapsed}'` :
              status === 'HT' ? 'HT' :
              status === 'FT' ? 'FT' :
              new Date(fixture.fixture.date).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' }),
      venue: fixture.fixture.venue?.name || 'TBD',
      isLive
    };
  };

  // Convert API event to MatchEvent
  const convertAPIEvent = (event: APIEvent, fixtureId: string): MatchEvent => {
    const typeMap: Record<string, MatchEvent['type']> = {
      'Goal': 'goal', 'Card': event.detail?.includes('Yellow') ? 'yellow_card' : 'red_card',
      'subst': 'substitution', 'Var': 'goal'
    };

    return {
      id: `${fixtureId}_${event.time.elapsed}_${Math.random()}`,
      type: typeMap[event.type] || 'pass',
      minute: `${event.time.elapsed}'`,
      player: event.player?.name || 'Unknown',
      team: event.team?.name || 'Unknown',
      detail: event.detail || event.type,
      timestamp: new Date(),
      matchId: fixtureId
    };
  };

  // Dynamic demo matches data - changes based on date/time
  const getDemoMatches = (): Match[] => {
    const now = new Date();
    const dayOfYear = Math.floor((now.getTime() - new Date(now.getFullYear(), 0, 0).getTime()) / 86400000);
    const hour = now.getHours();
    const minute = now.getMinutes();

    // Rotate team matchups based on day
    const matchupSets = [
      // Set 0
      [
        { home: 0, away: 1, venue: 'Enyimba Stadium, Aba' },
        { home: 2, away: 3, venue: 'Adokiye Amiesimaka Stadium' },
        { home: 4, away: 5, venue: 'Nnamdi Azikiwe Stadium' },
        { home: 6, away: 9, venue: 'Akure Township Stadium' },
        { home: 7, away: 8, venue: 'Kwara Stadium, Ilorin' },
      ],
      // Set 1
      [
        { home: 1, away: 2, venue: 'Sani Abacha Stadium, Kano' },
        { home: 3, away: 4, venue: 'New Jos Stadium' },
        { home: 5, away: 6, venue: 'Godswill Akpabio Stadium' },
        { home: 8, away: 0, venue: 'Umuahia Township Stadium' },
        { home: 9, away: 7, venue: 'Aper Aku Stadium' },
      ],
      // Set 2
      [
        { home: 2, away: 0, venue: 'Adokiye Amiesimaka Stadium' },
        { home: 4, away: 1, venue: 'Nnamdi Azikiwe Stadium' },
        { home: 6, away: 3, venue: 'Akure Township Stadium' },
        { home: 7, away: 5, venue: 'Kwara Stadium, Ilorin' },
        { home: 9, away: 8, venue: 'Aper Aku Stadium' },
      ],
      // Set 3
      [
        { home: 3, away: 2, venue: 'New Jos Stadium' },
        { home: 5, away: 4, venue: 'Godswill Akpabio Stadium' },
        { home: 0, away: 6, venue: 'Enyimba Stadium, Aba' },
        { home: 8, away: 7, venue: 'Umuahia Township Stadium' },
        { home: 1, away: 9, venue: 'Sani Abacha Stadium, Kano' },
      ],
      // Set 4
      [
        { home: 4, away: 0, venue: 'Nnamdi Azikiwe Stadium' },
        { home: 6, away: 2, venue: 'Akure Township Stadium' },
        { home: 9, away: 3, venue: 'Aper Aku Stadium' },
        { home: 1, away: 8, venue: 'Sani Abacha Stadium, Kano' },
        { home: 5, away: 7, venue: 'Godswill Akpabio Stadium' },
      ],
      // Set 5
      [
        { home: 7, away: 0, venue: 'Kwara Stadium, Ilorin' },
        { home: 8, away: 2, venue: 'Umuahia Township Stadium' },
        { home: 1, away: 3, venue: 'Sani Abacha Stadium, Kano' },
        { home: 6, away: 4, venue: 'Akure Township Stadium' },
        { home: 9, away: 5, venue: 'Aper Aku Stadium' },
      ],
      // Set 6
      [
        { home: 0, away: 9, venue: 'Enyimba Stadium, Aba' },
        { home: 2, away: 5, venue: 'Adokiye Amiesimaka Stadium' },
        { home: 3, away: 7, venue: 'New Jos Stadium' },
        { home: 4, away: 8, venue: 'Nnamdi Azikiwe Stadium' },
        { home: 6, away: 1, venue: 'Akure Township Stadium' },
      ],
    ];

    const currentSet = matchupSets[dayOfYear % matchupSets.length];

    // Generate dynamic scores based on hour (changes throughout the day)
    const generateScore = (seed: number): number => {
      const combined = (hour * 60 + minute + seed * 17) % 100;
      if (combined < 30) return 0;
      if (combined < 55) return 1;
      if (combined < 75) return 2;
      if (combined < 90) return 3;
      return 4;
    };

    // Calculate match minute based on current time (cycles every 2 hours)
    const cycleMinutes = (hour * 60 + minute) % 120;
    const getMatchMinute = (offset: number): string => {
      const matchMin = (cycleMinutes + offset * 15) % 90;
      return `${matchMin + 1}'`;
    };

    // Determine match status based on time cycle
    const getStatus = (index: number): { status: Match['status']; minute: string } => {
      const phase = (cycleMinutes + index * 20) % 120;
      if (phase < 45) return { status: 'LIVE', minute: getMatchMinute(index) };
      if (phase < 50) return { status: 'HT', minute: 'HT' };
      if (phase < 95) return { status: 'LIVE', minute: `${45 + (phase - 50)}'` };
      if (phase < 105) return { status: 'FT', minute: 'FT' };
      return { status: 'SCHEDULED', minute: `${18 + index}:00` };
    };

    return currentSet.map((matchup, index) => {
      const homeTeam = NPFL_TEAMS[matchup.home];
      const awayTeam = NPFL_TEAMS[matchup.away];
      const statusInfo = getStatus(index);
      const isFinishedOrScheduled = statusInfo.status === 'FT' || statusInfo.status === 'SCHEDULED';

      return {
        id: `${dayOfYear}-${index + 1}`,
        homeTeam: {
          name: homeTeam.name,
          logo: homeTeam.logo,
          score: isFinishedOrScheduled && statusInfo.status === 'SCHEDULED' ? 0 : generateScore(index * 2)
        },
        awayTeam: {
          name: awayTeam.name,
          logo: awayTeam.logo,
          score: isFinishedOrScheduled && statusInfo.status === 'SCHEDULED' ? 0 : generateScore(index * 2 + 1)
        },
        status: statusInfo.status,
        minute: statusInfo.minute,
        venue: matchup.venue
      };
    });
  };

  // Fetch live matches from API-Football
  const fetchLiveMatches = useCallback(async () => {
    if (!API_FOOTBALL_KEY) {
      console.log('No API key configured, using demo mode');
      setDataMode('demo');
      setMatches(getDemoMatches());
      setLoading(false);
      return;
    }

    try {
      // Get today's date in YYYY-MM-DD format
      const today = new Date().toISOString().split('T')[0];

      // Fetch fixtures for NPFL league
      const response = await fetch(
        `${API_FOOTBALL_URL}/fixtures?league=${NPFL_LEAGUE_ID}&date=${today}`,
        {
          headers: {
            'x-rapidapi-key': API_FOOTBALL_KEY,
            'x-rapidapi-host': 'v3.football.api-sports.io'
          }
        }
      );

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }

      const data = await response.json();

      if (data.errors && Object.keys(data.errors).length > 0) {
        throw new Error(Object.values(data.errors).join(', '));
      }

      if (data.response && data.response.length > 0) {
        const apiMatches = data.response.map((fixture: APIFixture) => convertAPIFixture(fixture));
        setMatches(apiMatches);
        setDataMode('live');
        setApiError(null);

        // Fetch events for live matches
        const liveFixtures = data.response.filter((f: APIFixture) =>
          isLiveStatus(f.fixture.status.short)
        );

        if (liveFixtures.length > 0) {
          const allEvents: MatchEvent[] = [];
          for (const fixture of liveFixtures) {
            if (fixture.events) {
              fixture.events.forEach((event: APIEvent) => {
                allEvents.push(convertAPIEvent(event, fixture.fixture.id.toString()));
              });
            }
          }
          if (allEvents.length > 0) {
            setEvents(allEvents.sort((a, b) => parseInt(b.minute) - parseInt(a.minute)));
          }
        }
      } else {
        // No matches today, fall back to demo
        console.log('No NPFL matches today, using demo mode');
        setDataMode('demo');
        setMatches(getDemoMatches());
      }
    } catch (error) {
      console.error('Error fetching live data:', error);
      setApiError(error instanceof Error ? error.message : 'Failed to fetch live data');
      setDataMode('demo');
      setMatches(getDemoMatches());
    } finally {
      setLoading(false);
      setLastUpdate(new Date());
    }
  }, []);

  // Check system health
  useEffect(() => {
    const checkHealth = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/health`);
        const data = await response.json();
        setSystemHealth(data);
      } catch {
        setSystemHealth({ status: 'offline' });
      }
    };
    checkHealth();
    const interval = setInterval(checkHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  // Initialize matches - try API first, fall back to demo
  useEffect(() => {
    fetchLiveMatches();

    // Refresh live data every 60 seconds if in live mode
    const interval = setInterval(() => {
      if (dataMode === 'live') {
        fetchLiveMatches();
      }
    }, 60000);

    return () => clearInterval(interval);
  }, [fetchLiveMatches, dataMode]);

  // Generate demo events (only in demo mode) - uses current matches
  useEffect(() => {
    if (dataMode !== 'demo' || matches.length === 0) return;

    // Extended player list for more variety
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

    // Get teams currently playing from active matches
    const liveMatches = matches.filter(m => m.status === 'LIVE' || m.status === 'HT');
    if (liveMatches.length === 0) return;

    // Build team-to-matchId mapping from current matches
    const teamMatchMap: Record<string, string> = {};
    liveMatches.forEach(match => {
      teamMatchMap[match.homeTeam.name] = match.id;
      teamMatchMap[match.awayTeam.name] = match.id;
    });

    const activeTeams = Object.keys(teamMatchMap);
    const eventTypes: MatchEvent['type'][] = ['goal', 'shot', 'pass', 'tackle', 'yellow_card', 'foul'];

    const generateEvent = (): MatchEvent => {
      const type = eventTypes[Math.floor(Math.random() * eventTypes.length)];
      const team = activeTeams[Math.floor(Math.random() * activeTeams.length)];
      const teamPlayers = playersByTeam[team] || ['Unknown Player'];
      const player = teamPlayers[Math.floor(Math.random() * teamPlayers.length)];
      const minute = Math.floor(Math.random() * 90) + 1;

      const details: Record<string, string[]> = {
        goal: ['Goal! Bottom left corner', 'Goal! Header from close range', 'Goal! Long range strike', 'Goal! Penalty kick converted'],
        shot: ['Shot saved by goalkeeper', 'Shot goes wide', 'Shot blocked by defender', 'Shot hits the post'],
        pass: ['Key pass into the box', 'Through ball', 'Cross from the right', 'Long ball forward'],
        tackle: ['Clean tackle', 'Sliding tackle', 'Standing tackle won', 'Interception'],
        yellow_card: ['Yellow card for reckless challenge', 'Yellow card for time wasting', 'Yellow card for dissent'],
        foul: ['Foul in midfield', 'Free kick awarded', 'Foul near the box']
      };

      return {
        id: `event_${Date.now()}_${Math.random()}`,
        type,
        minute: `${minute}'`,
        player,
        team,
        detail: details[type][Math.floor(Math.random() * details[type].length)],
        timestamp: new Date(),
        matchId: teamMatchMap[team]
      };
    };

    // Initial events
    setEvents(Array.from({ length: 10 }, generateEvent).sort((a, b) =>
      parseInt(b.minute) - parseInt(a.minute)
    ));

    // Add new events every 5 seconds for more activity
    const interval = setInterval(() => {
      const newEvent = generateEvent();
      setEvents(prev => [newEvent, ...prev].slice(0, 20));
      setLastUpdate(new Date());
    }, 5000);

    return () => clearInterval(interval);
  }, [dataMode, matches]);

  // Update match minutes (only in demo mode)
  useEffect(() => {
    if (dataMode !== 'demo') return;

    const interval = setInterval(() => {
      setMatches(prev => prev.map(match => {
        if (match.status === 'LIVE') {
          const currentMinute = parseInt(match.minute) || 0;
          if (currentMinute < 90) {
            return { ...match, minute: `${currentMinute + 1}'` };
          }
        }
        return match;
      }));
    }, 60000);
    return () => clearInterval(interval);
  }, [dataMode]);

  const getEventIcon = (type: MatchEvent['type']) => {
    const icons: Record<string, string> = {
      goal: '⚽', yellow_card: '🟨', red_card: '🟥',
      shot: '🎯', pass: '👟', tackle: '🛡️', foul: '⚠️',
      substitution: '🔄'
    };
    return icons[type] || '📊';
  };

  const getStatusStyle = (status: Match['status']) => {
    const styles: Record<string, { bg: string; color: string }> = {
      LIVE: { bg: '#dc2626', color: '#fff' },
      HT: { bg: '#f59e0b', color: '#000' },
      FT: { bg: '#6b7280', color: '#fff' },
      SCHEDULED: { bg: '#3b82f6', color: '#fff' }
    };
    return styles[status] || styles.SCHEDULED;
  };

  if (loading) {
    return (
      <div className="loading-screen">
        <div className="spinner"></div>
        <h2>Loading NPFL Live Data...</h2>
      </div>
    );
  }

  const liveMatches = matches.filter(m => m.status === 'LIVE');
  const otherMatches = matches.filter(m => m.status !== 'LIVE');

  return (
    <div className="dashboard">
      {/* Header */}
      <header className="header">
        <div className="header-content">
          <div className="header-main">
            <h1>⚽ NPFL Live</h1>
            <span className="league-name">Nigerian Professional Football League</span>
          </div>
          <div className="header-info">
            <div className={`system-status ${systemHealth?.status === 'healthy' ? 'online' : ''}`}>
              <span className="status-dot"></span>
              {systemHealth?.status === 'healthy' ? 'Online' : 'Connecting...'}
            </div>
            <div className={`data-badge ${dataMode === 'live' ? 'live-badge' : 'demo-badge'}`}>
              {dataMode === 'live' ? 'LIVE DATA' : 'DEMO MODE'}
            </div>
            {apiError && (
              <div className="api-error" title={apiError}>
                API: Fallback
              </div>
            )}
            <div className="last-updated">
              Updated: {lastUpdate.toLocaleTimeString()}
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="main">
        {/* Matches Column */}
        <div className="matches-column">
          {/* Live Matches */}
          {liveMatches.length > 0 && (
            <section className="matches-section">
              <h2 className="section-title">
                <span className="live-dot"></span>
                Live Now
              </h2>
              <div className="matches-list">
                {liveMatches.map(match => (
                  <Link key={match.id} to={`/match/${match.id}`} className="match-card live clickable">
                    <div className="match-header">
                      <span className="match-status" style={{
                        backgroundColor: getStatusStyle(match.status).bg,
                        color: getStatusStyle(match.status).color
                      }}>
                        ● {match.minute}
                      </span>
                      <span className="match-venue">{match.venue}</span>
                    </div>
                    <div className="match-content">
                      <div className="team home">
                        <span className="team-logo">{match.homeTeam.logo}</span>
                        <span className="team-name">{match.homeTeam.name}</span>
                      </div>
                      <div className="score-box">
                        <span className="score">{match.homeTeam.score}</span>
                        <span className="separator">-</span>
                        <span className="score">{match.awayTeam.score}</span>
                      </div>
                      <div className="team away">
                        <span className="team-name">{match.awayTeam.name}</span>
                        <span className="team-logo">{match.awayTeam.logo}</span>
                      </div>
                    </div>
                  </Link>
                ))}
              </div>
            </section>
          )}

          {/* Other Matches */}
          <section className="matches-section">
            <h2 className="section-title">Today's Fixtures</h2>
            <div className="matches-list">
              {otherMatches.map(match => (
                <Link key={match.id} to={`/match/${match.id}`} className={`match-card ${match.status.toLowerCase()} clickable`}>
                  <div className="match-header">
                    <span className="match-status" style={{
                      backgroundColor: getStatusStyle(match.status).bg,
                      color: getStatusStyle(match.status).color
                    }}>
                      {match.status === 'SCHEDULED' ? match.minute : match.status}
                    </span>
                    <span className="match-venue">{match.venue}</span>
                  </div>
                  <div className="match-content">
                    <div className="team home">
                      <span className="team-logo">{match.homeTeam.logo}</span>
                      <span className="team-name">{match.homeTeam.name}</span>
                    </div>
                    <div className="score-box">
                      <span className="score">{match.status !== 'SCHEDULED' ? match.homeTeam.score : '-'}</span>
                      <span className="separator">-</span>
                      <span className="score">{match.status !== 'SCHEDULED' ? match.awayTeam.score : '-'}</span>
                    </div>
                    <div className="team away">
                      <span className="team-name">{match.awayTeam.name}</span>
                      <span className="team-logo">{match.awayTeam.logo}</span>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          </section>
        </div>

        {/* Sidebar */}
        <aside className="sidebar">
          {/* Live Events */}
          <div className="panel events-panel">
            <h3 className="panel-title">📢 Live Events</h3>
            <div className="events-list">
              {events.map(event => (
                <Link key={event.id} to={`/match/${event.matchId}`} className={`event-item ${event.type} clickable`}>
                  <span className="event-icon">{getEventIcon(event.type)}</span>
                  <div className="event-info">
                    <div className="event-top">
                      <span className="event-minute">{event.minute}</span>
                      <span className="event-player">{event.player}</span>
                    </div>
                    <div className="event-bottom">
                      <span className="event-team">{event.team}</span>
                      <span className="event-detail">{event.detail}</span>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          </div>

          {/* System Stats */}
          <div className="panel stats-panel">
            <h3 className="panel-title">📊 System Stats</h3>
            <div className="stats-grid">
              <div className="stat-box">
                <span className="stat-value">~50ms</span>
                <span className="stat-label">Latency</span>
              </div>
              <div className="stat-box">
                <span className="stat-value">100%</span>
                <span className="stat-label">Uptime</span>
              </div>
              <div className="stat-box">
                <span className="stat-value">{events.length}</span>
                <span className="stat-label">Events</span>
              </div>
              <div className="stat-box">
                <span className="stat-value">$13</span>
                <span className="stat-label">/month</span>
              </div>
            </div>
          </div>

          {/* Teams */}
          <div className="panel teams-panel">
            <h3 className="panel-title">🏆 NPFL Teams</h3>
            <div className="teams-grid">
              {NPFL_TEAMS.map(team => (
                <Link key={team.id} to={`/team/${team.id}`} className="team-item clickable">
                  <span className="team-emoji">{team.logo}</span>
                  <span className="team-short">{team.name.split(' ')[0]}</span>
                </Link>
              ))}
            </div>
          </div>
        </aside>
      </main>

      {/* Footer */}
      <footer className="footer">
        <p>⚽ Football Analytics • MSc Research Project • Sheffield Hallam University</p>
        <p>Adebayo Oyeleye © 2025 • Data: NPFL (League ID: 399)</p>
      </footer>
    </div>
  );
};

export default LiveDashboard;
