import { useState } from 'react';
import { HomePage } from './components/HomePage';
import { TripPage } from './components/TripPage';

export default function App() {
  const [currentView, setCurrentView] = useState<'home' | 'trip'>('home');
  const [selectedTripId, setSelectedTripId] = useState<string | null>(null);

  const handleNavigateToTrip = (tripId: string) => {
    setSelectedTripId(tripId);
    setCurrentView('trip');
  };

  const handleBackToHome = () => {
    setCurrentView('home');
    setSelectedTripId(null);
  };

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
