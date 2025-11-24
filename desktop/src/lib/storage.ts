export type StoredUser = {
  id: number;
  user_id: string;
  token: string;
  // name?: string | null;
  created_at: string;
};

const USER_KEY = "tiptrip_user";

export function getStoredUser(): StoredUser | null {
  const raw = localStorage.getItem(USER_KEY);
  return raw ? (JSON.parse(raw) as StoredUser) : null;
}

export function setStoredUser(user: StoredUser) {
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function clearStoredUser() {
  localStorage.removeItem(USER_KEY);
}
// Local storage utilities for managing trip data client-side

export interface StoredTrip {
  tripId: string;
  tripName: string;
  userId: string;
  displayName: string;
  joinedAt: string;
  // optional persisted metadata
  date_start?: string | null;
  date_end?: string | null;
  allowed_weekdays?: number[] | null;
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
  ,
  
  // Update arbitrary trip metadata (name, displayName, dates)
  updateTripMeta(tripId: string, updates: Partial<StoredTrip>): void {
    const trips = this.getTrips();
    const trip = trips.find(t => t.tripId === tripId);
    if (trip) {
      if (updates.tripName !== undefined) trip.tripName = updates.tripName;
      if (updates.displayName !== undefined) trip.displayName = updates.displayName;
      if (updates.date_start !== undefined) trip.date_start = updates.date_start ?? null;
      if (updates.date_end !== undefined) trip.date_end = updates.date_end ?? null;
      if (updates.allowed_weekdays !== undefined) trip.allowed_weekdays = updates.allowed_weekdays ?? null;
      localStorage.setItem(STORAGE_KEY, JSON.stringify(trips));
    }
  }
};
