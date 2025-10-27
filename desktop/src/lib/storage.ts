// Local storage utilities for managing trip data client-side

export interface StoredTrip {
  tripId: string;
  tripName: string;
  userId: string;
  displayName: string;
  joinedAt: string;
}

const STORAGE_KEY = 'tripPlanner_trips';

export const storage = {
  // Get all trips the user has joined
  getTrips(): StoredTrip[] {
    if (typeof window === 'undefined') return [];
    const data = localStorage.getItem(STORAGE_KEY);
    return data ? JSON.parse(data) : [];
  },

  // Add a new trip
  addTrip(trip: StoredTrip): void {
    const trips = this.getTrips();
    const existing = trips.find(t => t.tripId === trip.tripId);
    if (!existing) {
      trips.push(trip);
      localStorage.setItem(STORAGE_KEY, JSON.stringify(trips));
    }
  },

  // Get a specific trip
  getTrip(tripId: string): StoredTrip | undefined {
    return this.getTrips().find(t => t.tripId === tripId);
  },

  // Remove a trip
  removeTrip(tripId: string): void {
    const trips = this.getTrips().filter(t => t.tripId !== tripId);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(trips));
  },

  // Update trip name
  updateTripName(tripId: string, tripName: string): void {
    const trips = this.getTrips();
    const trip = trips.find(t => t.tripId === tripId);
    if (trip) {
      trip.tripName = tripName;
      localStorage.setItem(STORAGE_KEY, JSON.stringify(trips));
    }
  }
};
