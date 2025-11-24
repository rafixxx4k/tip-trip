import { useEffect, useState } from 'react';
import { HomePage } from './components/HomePage';
import { TripPage } from './components/TripPage';
import { ensureUser } from './lib/api';

export default function App() {
  const [currentView, setCurrentView] = useState<'home' | 'trip'>('home');
  const [selectedTripId, setSelectedTripId] = useState<string | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        await ensureUser();
      } catch (err) {
        console.error('ensureUser failed', err);
      } finally {
        if (mounted) setReady(true);
      }
    })();
    return () => {
      mounted = false;
    };
  }, []);

  const handleNavigateToTrip = (tripId: string) => {
    setSelectedTripId(tripId);
    setCurrentView('trip');
  };

  const handleBackToHome = () => {
    setCurrentView('home');
    setSelectedTripId(null);
  };

  if (!ready) return <div>Initializing...</div>;

  return (
    <>
      {currentView === 'home' && (
        <HomePage onNavigateToTrip={handleNavigateToTrip} />
      )}
      {currentView === 'trip' && selectedTripId && (
        <TripPage tripId={selectedTripId} onBack={handleBackToHome} />
      )}
    </>
  );
}
