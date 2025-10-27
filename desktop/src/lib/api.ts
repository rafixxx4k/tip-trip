// API Service Layer - Replace BASE_URL with your actual backend URL
const BASE_URL = 'http://localhost:3000/api/v1'; // TODO: Replace with your backend URL

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
  async createTrip(name: string, displayName: string): Promise<{ tripId: string; userId: string }> {
    // TODO: Implement actual API call
    // const response = await fetch(`${BASE_URL}/trips`, {
    //   method: 'POST',
    //   headers: { 'Content-Type': 'application/json' },
    //   body: JSON.stringify({ name, displayName })
    // });
    // return response.json();
    
    // Mock implementation
    const tripId = Math.random().toString(36).substring(2, 15);
    const userId = Math.random().toString(36).substring(2, 15);
    return { tripId, userId };
  },

  async joinTrip(tripId: string, displayName: string): Promise<{ userId: string; tripName: string }> {
    // TODO: Implement actual API call
    // const response = await fetch(`${BASE_URL}/trips/${tripId}/join`, {
    //   method: 'POST',
    //   headers: { 'Content-Type': 'application/json' },
    //   body: JSON.stringify({ displayName })
    // });
    // return response.json();
    
    // Mock implementation
    const userId = Math.random().toString(36).substring(2, 15);
    return { userId, tripName: 'Sample Trip' };
  },

  async getTrip(tripId: string): Promise<{ trip: Trip; users: User[] }> {
    // TODO: Implement actual API call
    // const response = await fetch(`${BASE_URL}/trips/${tripId}`);
    // return response.json();
    
    // Mock implementation
    return {
      trip: {
        id: tripId,
        name: 'Paris Adventure 2025',
        organizerUserId: 'user1',
        createdAt: new Date().toISOString()
      },
      users: [
        { id: 'user1', tripId, displayName: 'Alex' },
        { id: 'user2', tripId, displayName: 'Jordan' }
      ]
    };
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
