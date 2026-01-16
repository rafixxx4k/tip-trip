import { getStoredUser, setStoredUser, storage } from "./storage";

type CreatedUser = {
  id: number;
  user_id: string;
  token: string;
  name?: string | null;
  created_at: string;
};

const BASE = (import.meta as any).env.VITE_API_BASE ?? "http://localhost:8000/api/v1";

export async function createUser(): Promise<CreatedUser> {
  const res = await fetch(`${BASE}/users`, {
    method: "POST",
  });
  if (!res.ok) throw new Error(`create user failed: ${res.status}`);
  const data = await res.json();
  setStoredUser(data);
  return data;
}

export async function ensureUser(): Promise<CreatedUser> {
  const existing = getStoredUser();
  if (existing) return existing;

  return await createUser();
}

export function authHeaders(): Record<string, string> {
  const u = getStoredUser();
  return u ? { "X-User-Hash": u.token } : {};
}

export async function authFetch(input: RequestInfo, init: RequestInit = {}) {
  const headers = { ...(init.headers || {}), ...authHeaders() } as Record<string, string>;
  return fetch(input, { ...init, headers });
}

// Types
export interface Trip {
  id: string;
  name: string;
  organizerUserId: string;
  createdAt: string;
  date_start?: string | null;
  date_end?: string | null;
  allowed_weekdays?: number[] | null;
}

export interface User {
  id: string;
  tripId: string;
  displayName: string;
}

export interface Availability {
  id: string;
  tripId: string;
  userId: string;
  date: string;
  status: 'available' | 'unavailable' | 'maybe' | 'unset';
}

export interface Debtor {
  userId: string;
  shareType: 'equal' | 'percent' | 'amount';
  value: number;
}

export interface Expense {
  id: string;
  tripId: string;
  payerId: string;
  amount: number;
  currency: string;
  description: string;
  isSplitEqually: boolean;
  debtors: Debtor[];
}

export interface Settlement {
  fromUser: string;
  toUser: string;
  amount: number;
  currency: string;
}

// API Functions
export const api = {
  // Trip & User Management
  async createTrip(title: string, user_name: string, description?: string): Promise<{ tripId: string; tripName: string }> {
    // Call backend to create a trip. Backend expects { title, user_name, description }.
    const body: any = { title };
    if (user_name) body.user_name = user_name;
    if (description) body.description = description;

    const res = await authFetch(`${BASE}/trips`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    if (!res.ok) throw new Error(`createTrip failed: ${res.status}`);
    const data = await res.json();
    return { tripId: data.hash_id, tripName: data.title };
  },

  async joinTrip(tripId: string, displayName: string): Promise<{ userId: string; tripName: string }> {
    // Join a trip by creating a membership for the current user.
    const stored = getStoredUser();
    if (!stored) throw new Error('no stored user');

    const payload = { user_hash: stored.token, user_name: displayName };
    const res = await authFetch(`${BASE}/trips/${tripId}/members`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const text = await res.text();
      throw new Error(`joinTrip failed: ${res.status} ${text}`);
    }
    const data = await res.json();
    // data contains membership; return userId and try to fetch trip name
    const tripRes = await authFetch(`${BASE}/trips/${tripId}`);
    const tripData = tripRes.ok ? await tripRes.json() : { title: tripId };
    return { userId: data.user_id ?? stored.id, tripName: tripData.title ?? tripData.hash_id ?? tripId };
  },

  async getTrip(tripId: string): Promise<{ trip: Trip; users: User[] }> {
    // Fetch trip details and members from backend
    const tripRes = await authFetch(`${BASE}/trips/${tripId}`);
    if (!tripRes.ok) {
      const txt = await tripRes.text();
      throw new Error(`getTrip failed: ${tripRes.status} ${txt}`);
    }
    const tripData = await tripRes.json();

    // Normalize trip (include date fields returned by backend)
    const trip: Trip = {
      id: tripData.hash_id ?? tripId,
      name: tripData.title ?? tripData.name ?? '',
      organizerUserId: String(tripData.owner_id ?? ''),
      createdAt: tripData.created_at ?? new Date().toISOString(),
      date_start: tripData.date_start ?? null,
      date_end: tripData.date_end ?? null,
      allowed_weekdays: tripData.allowed_weekdays ?? null,
    };

    // Fetch members
    const membersRes = await authFetch(`${BASE}/trips/${tripId}/members`);
    let users: User[] = [];
    if (membersRes.ok) {
      const members = await membersRes.json();
      users = members.map((m: any) => ({
        id: String(m.user_id),
        tripId: trip.id,
        displayName: m.user_name,
      }));
    }

    // Persist trip into storage (for the current user) if we have a stored user
    const me = getStoredUser();
    if (me) {
      const myMembership = users.find(u => u.id === String(me.id));
      const displayName = myMembership ? myMembership.displayName : '';
      try {
        storage.addTrip({
          tripId: trip.id,
          tripName: trip.name,
          userId: String(me.id),
          displayName,
          joinedAt: new Date().toISOString(),
        });
      } catch (e) {
        // storage operations are best-effort
        console.warn('saving trip to storage failed', e);
      }
    }

    return { trip, users };
  },

  async updateTrip(tripId: string, userId: string, updates: Partial<Trip>): Promise<{ status: string }> {
    const body = { ...updates } as any;
    const res = await authFetch(`${BASE}/trips/${tripId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    if (!res.ok) {
      const txt = await res.text();
      throw new Error(`updateTrip failed: ${res.status} ${txt}`);
    }
    const data = await res.json();
    return { status: 'success' };
  },

  // Scheduling (Calendar)
  async submitAvailability(
    tripId: string,
    userId: string,
    dates: Array<{ date: string; status: 'available' | 'unavailable' | 'maybe' | 'unset' }>
  ): Promise<{ status: string }> {
    const payload = { updates: dates.map(d => ({ date: d.date, status: d.status })) };
    const res = await authFetch(`${BASE}/trips/${tripId}/availability`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const txt = await res.text();
      throw new Error(`submitAvailability failed: ${res.status} ${txt}`);
    }
    return { status: 'success' };
  },

  async getCalendar(tripId: string): Promise<{
    dates: string[];
    users: User[];
    availability: Record<string, Record<string, 'available' | 'unavailable' | 'maybe' | null>>;
  }> {
    const res = await authFetch(`${BASE}/trips/${tripId}/calendar`);
    if (!res.ok) {
      const txt = await res.text();
      throw new Error(`getCalendar failed: ${res.status} ${txt}`);
    }
    const data = await res.json();
    const users: User[] = (data.users || []).map((u: any) => ({ id: String(u.id), tripId, displayName: u.displayName }));
    return { dates: data.dates || [], users, availability: data.availability || {} };
  },

  // Expense Splitting
  async createExpense(
    tripId: string,
    userId: string,
    amount: number,
    description: string,
    currency: string,
    debtors: Debtor[]
  ): Promise<{ expenseId: string }> {
    const response = await authFetch(`${BASE}/trips/${tripId}/expenses`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ amount, description, currency, debtors })
    });
    if (!response.ok) {
      const txt = await response.text();
      throw new Error(`createExpense failed: ${response.status} ${txt}`);
    }
    const data = await response.json();
    return { expenseId: data.id };
  },

  async getExpenses(tripId: string): Promise<Expense[]> {
    const response = await authFetch(`${BASE}/trips/${tripId}/expenses`);
    if (!response.ok) {
      const txt = await response.text();
      throw new Error(`getExpenses failed: ${response.status} ${txt}`);
    }
    return await response.json();
  },

  async getSettlements(tripId: string): Promise<{ balances: Settlement[] }> {
    const response = await authFetch(`${BASE}/trips/${tripId}/settlements`);
    if (!response.ok) {
      const txt = await response.text();
      throw new Error(`getSettlements failed: ${response.status} ${txt}`);
    }
    return await response.json();
  },

  // AI Chat Agent
  async sendChatMessage(tripId: string, userId: string, message: string): Promise<{ response: string }> {
    const res = await authFetch(`${BASE}/trips/${tripId}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message })
    });
    if (!res.ok) {
      const txt = await res.text();
      throw new Error(`sendChatMessage failed: ${res.status} ${txt}`);
    }
    return await res.json();
  }
};
