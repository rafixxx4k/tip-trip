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
  status: 'available' | 'unavailable' | 'maybe';
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

    // Normalize trip
    const trip: Trip = {
      id: tripData.hash_id ?? tripId,
      name: tripData.title ?? tripData.name ?? '',
      organizerUserId: String(tripData.owner_id ?? ''),
      createdAt: tripData.created_at ?? new Date().toISOString(),
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
    // TODO: Implement actual API call
    // const response = await fetch(`${BASE_URL}/trips/${tripId}`, {
    //   method: 'PUT',
    //   headers: { 'Content-Type': 'application/json' },
    //   body: JSON.stringify({ userId, ...updates })
    // });
    // return response.json();
    
    return { status: 'success' };
  },

  // Scheduling (Calendar)
  async submitAvailability(
    tripId: string,
    userId: string,
    dates: Array<{ date: string; status: 'available' | 'unavailable' | 'maybe' }>
  ): Promise<{ status: string }> {
    // TODO: Implement actual API call
    // const response = await fetch(`${BASE_URL}/trips/${tripId}/availability`, {
    //   method: 'POST',
    //   headers: { 'Content-Type': 'application/json' },
    //   body: JSON.stringify({ userId, dates })
    // });
    // return response.json();
    
    return { status: 'success' };
  },

  async getCalendar(tripId: string): Promise<{
    dates: string[];
    users: User[];
    availability: Record<string, Record<string, 'available' | 'unavailable' | 'maybe' | null>>;
  }> {
    // TODO: Implement actual API call
    // const response = await fetch(`${BASE_URL}/trips/${tripId}/calendar`);
    // return response.json();
    
    // Mock implementation
    const dates = ['2025-11-01', '2025-11-02', '2025-11-03', '2025-11-04', '2025-11-05'];
    const users = [
      { id: 'user1', tripId, displayName: 'Alex' },
      { id: 'user2', tripId, displayName: 'Jordan' }
    ];
    const availability: Record<string, Record<string, 'available' | 'unavailable' | 'maybe' | null>> = {
      'user1': {
        '2025-11-01': 'available',
        '2025-11-02': 'available',
        '2025-11-03': 'maybe',
      },
      'user2': {
        '2025-11-01': 'available',
        '2025-11-04': 'unavailable',
      }
    };
    return { dates, users, availability };
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
    // TODO: Implement actual API call
    // const response = await fetch(`${BASE_URL}/trips/${tripId}/expenses`, {
    //   method: 'POST',
    //   headers: { 'Content-Type': 'application/json' },
    //   body: JSON.stringify({ userId, amount, description, currency, debtors })
    // });
    // return response.json();
    
    const expenseId = Math.random().toString(36).substring(2, 15);
    return { expenseId };
  },

  async getExpenses(tripId: string): Promise<Expense[]> {
    // TODO: Implement actual API call
    // const response = await fetch(`${BASE_URL}/trips/${tripId}/expenses`);
    // return response.json();
    
    // Mock implementation
    return [
      {
        id: 'exp1',
        tripId,
        payerId: 'user1',
        amount: 120,
        currency: 'USD',
        description: 'Hotel booking',
        isSplitEqually: true,
        debtors: [
          { userId: 'user1', shareType: 'equal', value: 60 },
          { userId: 'user2', shareType: 'equal', value: 60 }
        ]
      },
      {
        id: 'exp2',
        tripId,
        payerId: 'user2',
        amount: 45,
        currency: 'USD',
        description: 'Dinner',
        isSplitEqually: true,
        debtors: [
          { userId: 'user1', shareType: 'equal', value: 22.5 },
          { userId: 'user2', shareType: 'equal', value: 22.5 }
        ]
      }
    ];
  },

  async getSettlements(tripId: string): Promise<{ balances: Settlement[] }> {
    // TODO: Implement actual API call
    // const response = await fetch(`${BASE_URL}/trips/${tripId}/settlements`);
    // return response.json();
    
    // Mock implementation
    return {
      balances: [
        { fromUser: 'user2', toUser: 'user1', amount: 37.5, currency: 'USD' }
      ]
    };
  },

  // AI Chat Agent
  async sendChatMessage(tripId: string, userId: string, message: string): Promise<{ response: string }> {
    // TODO: Implement actual API call
    // const response = await fetch(`${BASE_URL}/trips/${tripId}/chat`, {
    //   method: 'POST',
    //   headers: { 'Content-Type': 'application/json' },
    //   body: JSON.stringify({ userId, message })
    // });
    // return response.json();
    
    // Mock implementation
    await new Promise(resolve => setTimeout(resolve, 1000));
    return {
      response: `I'm your AI travel assistant! You asked: "${message}". Once connected to the backend, I'll provide personalized recommendations for your trip.`
    };
  }
};
