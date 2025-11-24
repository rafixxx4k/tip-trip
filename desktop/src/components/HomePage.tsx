import { useState, useEffect } from 'react';
import { Plus, LogIn, Calendar, Trash2 } from 'lucide-react';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from './ui/dialog';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { storage, StoredTrip, getStoredUser } from '../lib/storage';
import { api } from '../lib/api';

interface HomePageProps {
  onNavigateToTrip: (tripId: string) => void;
}

export function HomePage({ onNavigateToTrip }: HomePageProps) {
  const [trips, setTrips] = useState<StoredTrip[]>([]);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showJoinDialog, setShowJoinDialog] = useState(false);
  const [createName, setCreateName] = useState('');
  const [createDescription, setCreateDescription] = useState('');
  const [createDateStart, setCreateDateStart] = useState('');
  const [createDateEnd, setCreateDateEnd] = useState('');
  const [createWeekdays, setCreateWeekdays] = useState<number[]>([]);
  const [displayName, setDisplayName] = useState('');
  const [joinTripId, setJoinTripId] = useState('');
  const [joinDisplayName, setJoinDisplayName] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    setTrips(storage.getTrips());
  }, []);

  const handleCreateTrip = async () => {
    if (!createName.trim() || !displayName.trim()) return;
    
    setIsLoading(true);
    try {
      const { tripId, tripName } = await api.createTrip(createName, displayName, createDescription);
      // If user provided date edges or weekdays, update the trip to set them
      try {
        if (createDateStart && createDateEnd) {
          const updates: any = { date_start: createDateStart, date_end: createDateEnd };
          if (createWeekdays && createWeekdays.length > 0) updates.allowed_weekdays = createWeekdays;
          await api.updateTrip(tripId, '', updates);
        }
      } catch (err) {
        console.warn('Failed to set trip dates after creation', err);
      }
      const storedUser = getStoredUser();
      const userId = storedUser ? String(storedUser.id) : '';
      
      const newTrip: StoredTrip = {
        tripId,
        tripName: tripName || createName,
        userId: userId ?? '',
        displayName,
        joinedAt: new Date().toISOString()
      };
      
      storage.addTrip(newTrip);
      setTrips(storage.getTrips());
      setShowCreateDialog(false);
      setCreateName('');
      setCreateDescription('');
      setDisplayName('');
      onNavigateToTrip(tripId);
    } catch (error) {
      console.error('Failed to create trip:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleJoinTrip = async () => {
    if (!joinTripId.trim() || !joinDisplayName.trim()) return;
    
    setIsLoading(true);
    try {
      const { userId, tripName } = await api.joinTrip(joinTripId, joinDisplayName);
      
      const newTrip: StoredTrip = {
        tripId: joinTripId,
        tripName,
        userId,
        displayName: joinDisplayName,
        joinedAt: new Date().toISOString()
      };
      
      storage.addTrip(newTrip);
      setTrips(storage.getTrips());
      setShowJoinDialog(false);
      setJoinTripId('');
      setJoinDisplayName('');
      onNavigateToTrip(joinTripId);
    } catch (error) {
      console.error('Failed to join trip:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRemoveTrip = (tripId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (confirm('Remove this trip from your list?')) {
      storage.removeTrip(tripId);
      setTrips(storage.getTrips());
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-6">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-12">
          <h1 className="text-5xl mb-4">Trip Planner</h1>
          <p className="text-gray-600">Collaborate with friends to plan the perfect trip</p>
        </div>

        <div className="grid md:grid-cols-2 gap-6 mb-12">
          <Card className="cursor-pointer hover:shadow-lg transition-shadow" onClick={() => setShowCreateDialog(true)}>
            <CardHeader>
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-full bg-blue-100 flex items-center justify-center">
                  <Plus className="w-6 h-6 text-blue-600" />
                </div>
                <div>
                  <CardTitle>Create New Trip</CardTitle>
                  <CardDescription>Start planning a new adventure</CardDescription>
                </div>
              </div>
            </CardHeader>
          </Card>

          <Card className="cursor-pointer hover:shadow-lg transition-shadow" onClick={() => setShowJoinDialog(true)}>
            <CardHeader>
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-full bg-green-100 flex items-center justify-center">
                  <LogIn className="w-6 h-6 text-green-600" />
                </div>
                <div>
                  <CardTitle>Join Existing Trip</CardTitle>
                  <CardDescription>Enter a trip ID to collaborate</CardDescription>
                </div>
              </div>
            </CardHeader>
          </Card>
        </div>

        <div>
          <h2 className="text-2xl mb-6">Your Trips</h2>
          {trips.length === 0 ? (
            <Card>
              <CardContent className="py-12 text-center text-gray-500">
                <Calendar className="w-12 h-12 mx-auto mb-4 opacity-50" />
                <p>No trips yet. Create or join a trip to get started!</p>
              </CardContent>
            </Card>
          ) : (
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
              {trips.map((trip) => (
                <Card 
                  key={trip.tripId} 
                  className="cursor-pointer hover:shadow-lg transition-shadow"
                  onClick={() => onNavigateToTrip(trip.tripId)}
                >
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <CardTitle>{trip.tripName}</CardTitle>
                        <CardDescription>Joined as {trip.displayName}</CardDescription>
                        <p className="text-xs text-gray-400 mt-2">
                          ID: {trip.tripId.substring(0, 8)}...
                        </p>
                      </div>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={(e) => handleRemoveTrip(trip.tripId, e)}
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </CardHeader>
                </Card>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Create Trip Dialog */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create New Trip</DialogTitle>
            <DialogDescription>
              Enter a name for your trip and your display name
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div>
              <Label htmlFor="tripName">Trip Name</Label>
              <Input
                id="tripName"
                placeholder="e.g., Paris 2026"
                value={createName}
                onChange={(e) => setCreateName(e.target.value)}
              />
            </div>
            <div>
              <Label htmlFor="tripDescription">Description</Label>
              <Input
                id="tripDescription"
                placeholder="Short trip description"
                value={createDescription}
                onChange={(e) => setCreateDescription(e.target.value)}
              />
            </div>
            <div>
              <Label htmlFor="displayName">Your Name</Label>
              <Input
                id="displayName"
                placeholder="e.g., Alex"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="dateStart">Start Date (optional)</Label>
                <Input id="dateStart" type="date" value={createDateStart} onChange={e => setCreateDateStart(e.target.value)} />
              </div>
              <div>
                <Label htmlFor="dateEnd">End Date (optional)</Label>
                <Input id="dateEnd" type="date" value={createDateEnd} onChange={e => setCreateDateEnd(e.target.value)} />
              </div>
            </div>

            <div>
              <Label>Allowed Weekdays (optional)</Label>
              <div className="flex flex-wrap gap-2 mt-2">
                {['Sun','Mon','Tue','Wed','Thu','Fri','Sat'].map((d, idx) => {
                  const selected = createWeekdays.includes(idx);
                  return (
                    <button
                      key={d}
                      type="button"
                      onClick={() => setCreateWeekdays(prev => prev.includes(idx) ? prev.filter(x => x !== idx) : [...prev, idx])}
                      className={`px-2 py-1 rounded border ${selected ? 'bg-blue-600 text-white' : 'bg-white'}`}
                    >
                      {d}
                    </button>
                  );
                })}
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCreateDialog(false)}>
              Cancel
            </Button>
            <Button onClick={handleCreateTrip} disabled={isLoading || !createName.trim() || !displayName.trim()}>
              {isLoading ? 'Creating...' : 'Create Trip'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Join Trip Dialog */}
      <Dialog open={showJoinDialog} onOpenChange={setShowJoinDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Join Existing Trip</DialogTitle>
            <DialogDescription>
              Enter the trip ID shared with you and your display name
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div>
              <Label htmlFor="tripId">Trip ID</Label>
              <Input
                id="tripId"
                placeholder="Enter trip ID"
                value={joinTripId}
                onChange={(e) => setJoinTripId(e.target.value)}
              />
            </div>
            <div>
              <Label htmlFor="joinDisplayName">Your Name</Label>
              <Input
                id="joinDisplayName"
                placeholder="e.g., Jordan"
                value={joinDisplayName}
                onChange={(e) => setJoinDisplayName(e.target.value)}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowJoinDialog(false)}>
              Cancel
            </Button>
            <Button onClick={handleJoinTrip} disabled={isLoading || !joinTripId.trim() || !joinDisplayName.trim()}>
              {isLoading ? 'Joining...' : 'Join Trip'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
