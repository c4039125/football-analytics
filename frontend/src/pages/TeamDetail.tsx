import { useParams, Link } from 'react-router-dom';
import './TeamDetail.css';

// NPFL Teams data with extended info
const NPFL_TEAMS = [
  {
    id: 'enyimba',
    apiId: 2254,
    name: 'Enyimba FC',
    city: 'Aba',
    logo: '🦅',
    stadium: 'Enyimba International Stadium',
    capacity: 16000,
    founded: 1976,
    coach: 'Finidi George',
    nickname: 'The Peoples Elephant',
    titles: 8,
    cafTitles: 2,
    colors: 'Blue and White'
  },
  {
    id: 'kano_pillars',
    apiId: 2247,
    name: 'Kano Pillars',
    city: 'Kano',
    logo: '🏛️',
    stadium: 'Sani Abacha Stadium',
    capacity: 25000,
    founded: 1990,
    coach: 'Salisu Yusuf',
    nickname: 'Sai Masu Gida',
    titles: 4,
    cafTitles: 0,
    colors: 'Gold and Red'
  },
  {
    id: 'rivers_united',
    apiId: 2253,
    name: 'Rivers United',
    city: 'Port Harcourt',
    logo: '🌊',
    stadium: 'Adokiye Amiesimaka Stadium',
    capacity: 30000,
    founded: 2016,
    coach: 'Stanley Eguma',
    nickname: 'Pride of Rivers',
    titles: 2,
    cafTitles: 0,
    colors: 'Blue and White'
  },
  {
    id: 'plateau_united',
    apiId: 2250,
    name: 'Plateau United',
    city: 'Jos',
    logo: '⛰️',
    stadium: 'New Jos Stadium',
    capacity: 10000,
    founded: 1975,
    coach: 'Fidelis Ilechukwu',
    nickname: 'Peace Boys',
    titles: 2,
    cafTitles: 0,
    colors: 'Green and White'
  },
  {
    id: 'rangers',
    apiId: 2252,
    name: 'Rangers International',
    city: 'Enugu',
    logo: '🦁',
    stadium: 'Nnamdi Azikiwe Stadium',
    capacity: 22000,
    founded: 1970,
    coach: 'Abdul Maikaba',
    nickname: 'The Flying Antelopes',
    titles: 7,
    cafTitles: 1,
    colors: 'Blue and White'
  },
  {
    id: 'akwa_united',
    apiId: 2241,
    name: 'Akwa United',
    city: 'Uyo',
    logo: '⚡',
    stadium: 'Godswill Akpabio Stadium',
    capacity: 30000,
    founded: 1996,
    coach: 'Kennedy Boboye',
    nickname: 'The Promise Keepers',
    titles: 1,
    cafTitles: 0,
    colors: 'Gold and Blue'
  },
  {
    id: 'sunshine',
    apiId: 2257,
    name: 'Sunshine Stars',
    city: 'Akure',
    logo: '☀️',
    stadium: 'Akure Township Stadium',
    capacity: 10000,
    founded: 2007,
    coach: 'Deji Ayeni',
    nickname: 'The Owena Whales',
    titles: 1,
    cafTitles: 0,
    colors: 'Yellow and Blue'
  },
  {
    id: 'kwara',
    apiId: 2249,
    name: 'Kwara United',
    city: 'Ilorin',
    logo: '🔵',
    stadium: 'Kwara Stadium Complex',
    capacity: 18000,
    founded: 2006,
    coach: 'Abdullahi Biffo',
    nickname: 'The Afonja Warriors',
    titles: 0,
    cafTitles: 0,
    colors: 'Blue and White'
  },
  {
    id: 'abia',
    apiId: 2240,
    name: 'Abia Warriors',
    city: 'Umuahia',
    logo: '⚔️',
    stadium: 'Umuahia Township Stadium',
    capacity: 10000,
    founded: 2008,
    coach: 'Imama Amapakabo',
    nickname: 'Umuahia Warriors',
    titles: 0,
    cafTitles: 0,
    colors: 'Green and White'
  },
  {
    id: 'lobi',
    apiId: 2255,
    name: 'Lobi Stars',
    city: 'Makurdi',
    logo: '⭐',
    stadium: 'Aper Aku Stadium',
    capacity: 15000,
    founded: 1968,
    coach: 'Eugene Agagbe',
    nickname: 'Pride of Benue',
    titles: 2,
    cafTitles: 0,
    colors: 'Orange and White'
  },
];

const TeamDetail = () => {
  const { teamId } = useParams<{ teamId: string }>();
  const team = NPFL_TEAMS.find(t => t.id === teamId) || NPFL_TEAMS[0];

  // Demo squad data
  const squad = [
    { number: 1, name: 'Goalkeeper', position: 'GK' },
    { number: 2, name: 'Right Back', position: 'DEF' },
    { number: 4, name: 'Centre Back', position: 'DEF' },
    { number: 5, name: 'Centre Back', position: 'DEF' },
    { number: 3, name: 'Left Back', position: 'DEF' },
    { number: 6, name: 'Defensive Mid', position: 'MID' },
    { number: 8, name: 'Central Mid', position: 'MID' },
    { number: 10, name: 'Attacking Mid', position: 'MID' },
    { number: 7, name: 'Right Winger', position: 'FWD' },
    { number: 9, name: 'Striker', position: 'FWD' },
    { number: 11, name: 'Left Winger', position: 'FWD' },
  ];

  // Demo recent results
  const recentResults = [
    { opponent: NPFL_TEAMS[1].name, result: 'W', score: '2-1', home: true },
    { opponent: NPFL_TEAMS[2].name, result: 'D', score: '1-1', home: false },
    { opponent: NPFL_TEAMS[3].name, result: 'W', score: '3-0', home: true },
    { opponent: NPFL_TEAMS[4].name, result: 'L', score: '0-2', home: false },
    { opponent: NPFL_TEAMS[5].name, result: 'W', score: '1-0', home: true },
  ];

  return (
    <div className="team-detail-page">
      {/* Back Navigation */}
      <div className="back-nav">
        <Link to="/" className="back-link">← Back to Matches</Link>
      </div>

      {/* Team Header */}
      <div className="team-header">
        <div className="team-header-content">
          <span className="team-logo-xl">{team.logo}</span>
          <div className="team-header-info">
            <h1>{team.name}</h1>
            <p className="team-nickname">"{team.nickname}"</p>
            <p className="team-location">📍 {team.city}, Nigeria</p>
          </div>
        </div>
      </div>

      {/* Team Content */}
      <div className="team-content">
        {/* Quick Stats */}
        <div className="quick-stats">
          <div className="quick-stat">
            <span className="stat-number">{team.titles}</span>
            <span className="stat-label">NPFL Titles</span>
          </div>
          <div className="quick-stat">
            <span className="stat-number">{team.cafTitles}</span>
            <span className="stat-label">CAF Titles</span>
          </div>
          <div className="quick-stat">
            <span className="stat-number">{team.founded}</span>
            <span className="stat-label">Founded</span>
          </div>
          <div className="quick-stat">
            <span className="stat-number">{team.capacity?.toLocaleString()}</span>
            <span className="stat-label">Stadium Capacity</span>
          </div>
        </div>

        <div className="team-grid">
          {/* Club Info */}
          <div className="info-panel">
            <h3>Club Information</h3>
            <div className="info-list">
              <div className="info-row">
                <span className="info-label">Full Name</span>
                <span className="info-value">{team.name}</span>
              </div>
              <div className="info-row">
                <span className="info-label">Nickname</span>
                <span className="info-value">{team.nickname}</span>
              </div>
              <div className="info-row">
                <span className="info-label">Founded</span>
                <span className="info-value">{team.founded}</span>
              </div>
              <div className="info-row">
                <span className="info-label">Stadium</span>
                <span className="info-value">{team.stadium}</span>
              </div>
              <div className="info-row">
                <span className="info-label">Capacity</span>
                <span className="info-value">{team.capacity?.toLocaleString()}</span>
              </div>
              <div className="info-row">
                <span className="info-label">Head Coach</span>
                <span className="info-value">{team.coach}</span>
              </div>
              <div className="info-row">
                <span className="info-label">Colors</span>
                <span className="info-value">{team.colors}</span>
              </div>
            </div>
          </div>

          {/* Recent Form */}
          <div className="form-panel">
            <h3>Recent Form</h3>
            <div className="form-badges">
              {recentResults.map((r, i) => (
                <span key={i} className={`form-badge ${r.result.toLowerCase()}`}>
                  {r.result}
                </span>
              ))}
            </div>
            <div className="recent-results">
              {recentResults.map((r, i) => (
                <div key={i} className="result-row">
                  <span className={`result-badge ${r.result.toLowerCase()}`}>{r.result}</span>
                  <span className="result-info">
                    {r.home ? 'vs' : '@'} {r.opponent}
                  </span>
                  <span className="result-score">{r.score}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Squad */}
          <div className="squad-panel">
            <h3>Squad</h3>
            <div className="squad-list">
              {squad.map((player, i) => (
                <div key={i} className="squad-row">
                  <span className="player-number">{player.number}</span>
                  <span className="player-name">{player.name}</span>
                  <span className={`player-position ${player.position.toLowerCase()}`}>
                    {player.position}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Other NPFL Teams */}
          <div className="other-teams-panel">
            <h3>Other NPFL Teams</h3>
            <div className="teams-list">
              {NPFL_TEAMS.filter(t => t.id !== teamId).map(t => (
                <Link key={t.id} to={`/team/${t.id}`} className="other-team-link">
                  <span className="other-team-logo">{t.logo}</span>
                  <span className="other-team-name">{t.name}</span>
                </Link>
              ))}
            </div>
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

export default TeamDetail;
