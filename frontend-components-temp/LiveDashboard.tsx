import React, { useState, useEffect } from 'react';
import './LiveDashboard.css';

// API Base URL - will be replaced with actual API Gateway URL
const API_BASE_URL = process.env.REACT_APP_API_URL || 'https://d4pstbgzu1.execute-api.us-east-1.amazonaws.com/development';

interface FootballEvent {
  event_id: string;
  event_type: string;
  match_id: string;
  timestamp: string;
  team_id: string;
  player_id: string;
  location?: { x: number; y: number };
  metadata?: {
    minute?: number;
    assist_by?: string;
    goal_type?: string;
    home_team?: string;
    away_team?: string;
    score?: string;
  };
}

interface Match {
  match_id: string;
  home_team: string;
  away_team: string;
  score: string;
  status: 'live' | 'scheduled' | 'finished';
  events: FootballEvent[];
}

const LiveDashboard: React.FC = () => {
  const [matches, setMatches] = useState<Match[]>([]);
  const [latestEvents, setLatestEvents] = useState<FootballEvent[]>([]);
  const [systemHealth, setSystemHealth] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch system health
  useEffect(() => {
    const fetchHealth = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/health`);
        const data = await response.json();
        setSystemHealth(data);
      } catch (err) {
        console.error('Health check failed:', err);
      }
    };

    fetchHealth();
    const interval = setInterval(fetchHealth, 30000); // Every 30 seconds

    return () => clearInterval(interval);
  }, []);

  // Simulated live updates (in production, this would use WebSocket)
  useEffect(() => {
    const fetchLiveData = async () => {
      try {
        setLoading(true);

        // Fetch metrics/events from API
        const response = await fetch(`${API_BASE_URL}/metrics`);
        const data = await response.json();

        // For demo: create a sample match
        const sampleMatch: Match = {
          match_id: 'npfl_2024_demo_' + Date.now(),
          home_team: 'Enyimba FC',
          away_team: 'Kano Pillars',
          score: '2-1',
          status: 'live',
          events: []
        };

        setMatches([sampleMatch]);
        setLoading(false);
      } catch (err) {
        setError('Failed to fetch live data');
        setLoading(false);
      }
    };

    fetchLiveData();

    // Refresh every 5 seconds for demo purposes
    const interval = setInterval(fetchLiveData, 5000);

    return () => clearInterval(interval);
  }, []);

  // Simulate live events
  useEffect(() => {
    const eventTypes = ['goal', 'pass', 'shot', 'tackle', 'foul'];
    const players = ['Victor Mbaoma', 'Alex Iwobi', 'Ahmed Musa', 'Junior Ajayi'];

    const generateEvent = (): FootballEvent => {
      const eventType = eventTypes[Math.floor(Math.random() * eventTypes.length)];
      const player = players[Math.floor(Math.random() * players.length)];

      return {
        event_id: `event_${Date.now()}_${Math.random()}`,
        event_type: eventType,
        match_id: 'npfl_2024_demo',
        timestamp: new Date().toISOString(),
        team_id: Math.random() > 0.5 ? 'enyimba_fc' : 'kano_pillars',
        player_id: player.toLowerCase().replace(/ /g, '_'),
        location: { x: Math.floor(Math.random() * 100), y: Math.floor(Math.random() * 100) },
        metadata: {
          minute: Math.floor(Math.random() * 90) + 1,
          home_team: 'Enyimba FC',
          away_team: 'Kano Pillars',
          score: '2-1'
        }
      };
    };

    const interval = setInterval(() => {
      const newEvent = generateEvent();
      setLatestEvents(prev => [newEvent, ...prev].slice(0, 20)); // Keep last 20 events
    }, 8000); // New event every 8 seconds

    return () => clearInterval(interval);
  }, []);

  const getEventIcon = (eventType: string) => {
    const icons: Record<string, string> = {
      goal: '⚽',
      pass: '🔄',
      shot: '🎯',
      tackle: '🛡️',
      foul: '⚠️',
      card: '🟨'
    };
    return icons[eventType] || '📊';
  };

  const getEventColor = (eventType: string) => {
    const colors: Record<string, string> = {
      goal: '#10b981', // green
      pass: '#3b82f6', // blue
      shot: '#f59e0b', // orange
      tackle: '#6366f1', // indigo
      foul: '#ef4444', // red
      card: '#eab308' // yellow
    };
    return colors[eventType] || '#6b7280';
  };

  if (loading && matches.length === 0) {
    return (
      <div className="dashboard">
        <div className="loading">
          <div className="spinner"></div>
          <p>Loading live matches...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="dashboard">
        <div className="error">
          <h2>⚠️ Error</h2>
          <p>{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard">
      {/* Header */}
      <header className="dashboard-header">
        <div className="container">
          <h1>⚽ NPFL Live Analytics</h1>
          <p className="subtitle">Nigerian Professional Football League • Real-time Match Data</p>
          {systemHealth && (
            <div className="health-status">
              <span className={`status-badge ${systemHealth.status === 'healthy' ? 'healthy' : 'unhealthy'}`}>
                {systemHealth.status === 'healthy' ? '✓ System Online' : '⚠ System Issue'}
              </span>
              <span className="latency">~50ms latency</span>
            </div>
          )}
        </div>
      </header>

      <div className="container">
        {/* Live Matches Section */}
        <section className="matches-section">
          <h2 className="section-title">
            <span className="live-indicator"></span>
            Live Matches
          </h2>

          {matches.length === 0 ? (
            <div className="no-matches">
              <p>No live matches currently</p>
              <small>Run demo script: <code>python3 scripts/demo_npfl_match.py</code></small>
            </div>
          ) : (
            <div className="matches-grid">
              {matches.map((match) => (
                <div key={match.match_id} className="match-card">
                  <div className="match-status">
                    <span className="live-badge">● LIVE</span>
                    <span className="match-time">45:00</span>
                  </div>

                  <div className="match-teams">
                    <div className="team">
                      <span className="team-name">{match.home_team}</span>
                      <span className="team-score">{match.score.split('-')[0]}</span>
                    </div>

                    <div className="vs-divider">vs</div>

                    <div className="team">
                      <span className="team-score">{match.score.split('-')[1]}</span>
                      <span className="team-name">{match.away_team}</span>
                    </div>
                  </div>

                  <div className="match-stats">
                    <div className="stat">
                      <span className="stat-label">Events</span>
                      <span className="stat-value">{latestEvents.length}</span>
                    </div>
                    <div className="stat">
                      <span className="stat-label">Goals</span>
                      <span className="stat-value">{latestEvents.filter(e => e.event_type === 'goal').length}</span>
                    </div>
                    <div className="stat">
                      <span className="stat-label">Shots</span>
                      <span className="stat-value">{latestEvents.filter(e => e.event_type === 'shot').length}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>

        {/* Live Events Feed */}
        <section className="events-section">
          <h2 className="section-title">Live Events Feed</h2>

          <div className="events-feed">
            {latestEvents.length === 0 ? (
              <div className="no-events">
                <p>Waiting for live events...</p>
              </div>
            ) : (
              latestEvents.map((event) => (
                <div
                  key={event.event_id}
                  className="event-item"
                  style={{ borderLeftColor: getEventColor(event.event_type) }}
                >
                  <div className="event-icon" style={{ backgroundColor: getEventColor(event.event_type) }}>
                    {getEventIcon(event.event_type)}
                  </div>

                  <div className="event-details">
                    <div className="event-header">
                      <span className="event-type">{event.event_type.toUpperCase()}</span>
                      <span className="event-minute">{event.metadata?.minute}'</span>
                    </div>

                    <div className="event-description">
                      <span className="player-name">{event.player_id.replace(/_/g, ' ')}</span>
                      {event.event_type === 'goal' && event.metadata?.assist_by && (
                        <span className="assist"> • Assist: {event.metadata.assist_by}</span>
                      )}
                    </div>

                    <div className="event-time">
                      {new Date(event.timestamp).toLocaleTimeString()}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </section>

        {/* System Stats */}
        <section className="stats-section">
          <h2 className="section-title">System Performance</h2>

          <div className="stats-grid">
            <div className="stat-card">
              <div className="stat-icon">⚡</div>
              <div className="stat-info">
                <div className="stat-value">~50ms</div>
                <div className="stat-label">Processing Latency</div>
              </div>
            </div>

            <div className="stat-card">
              <div className="stat-icon">📊</div>
              <div className="stat-info">
                <div className="stat-value">{latestEvents.length}</div>
                <div className="stat-label">Events Processed</div>
              </div>
            </div>

            <div className="stat-card">
              <div className="stat-icon">✓</div>
              <div className="stat-info">
                <div className="stat-value">100%</div>
                <div className="stat-label">Success Rate</div>
              </div>
            </div>

            <div className="stat-card">
              <div className="stat-icon">💰</div>
              <div className="stat-info">
                <div className="stat-value">$13/mo</div>
                <div className="stat-label">Operating Cost</div>
              </div>
            </div>
          </div>
        </section>
      </div>

      {/* Footer */}
      <footer className="dashboard-footer">
        <div className="container">
          <p>⚽ Football Analytics Serverless System • MSc Computing Research Project</p>
          <p>Adebayo Oyeleye • Sheffield Hallam University • 2024</p>
        </div>
      </footer>
    </div>
  );
};

export default LiveDashboard;
