import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import LiveDashboard from './LiveDashboard';
import MatchDetail from './pages/MatchDetail';
import TeamDetail from './pages/TeamDetail';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<LiveDashboard />} />
        <Route path="/match/:matchId" element={<MatchDetail />} />
        <Route path="/team/:teamId" element={<TeamDetail />} />
      </Routes>
    </Router>
  );
}

export default App;
