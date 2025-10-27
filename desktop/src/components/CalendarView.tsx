import { useState, useEffect } from 'react';
import { Calendar, Check, X, HelpCircle } from 'lucide-react';
import { Button } from './ui/button';
import { Card } from './ui/card';
import { api, User } from '../lib/api';

interface CalendarViewProps {
  tripId: string;
  currentUserId: string;
}

type AvailabilityStatus = 'available' | 'unavailable' | 'maybe' | null;

export function CalendarView({ tripId, currentUserId }: CalendarViewProps) {
  const [dates, setDates] = useState<string[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [availability, setAvailability] = useState<Record<string, Record<string, AvailabilityStatus>>>({});
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    loadCalendar();
  }, [tripId]);

  const loadCalendar = async () => {
    try {
      const data = await api.getCalendar(tripId);
      setDates(data.dates);
      setUsers(data.users);
      setAvailability(data.availability);
    } catch (error) {
      console.error('Failed to load calendar:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const toggleAvailability = async (date: string, currentStatus: AvailabilityStatus) => {
    const statusOrder: AvailabilityStatus[] = [null, 'available', 'maybe', 'unavailable'];
    const currentIndex = statusOrder.indexOf(currentStatus);
    const newStatus = statusOrder[(currentIndex + 1) % statusOrder.length];

    // Update local state
    setAvailability(prev => ({
      ...prev,
      [currentUserId]: {
        ...prev[currentUserId],
        [date]: newStatus
      }
    }));

    // Save to backend
    try {
      if (newStatus) {
        await api.submitAvailability(tripId, currentUserId, [{ date, status: newStatus }]);
      }
    } catch (error) {
      console.error('Failed to save availability:', error);
    }
  };

  const getStatusIcon = (status: AvailabilityStatus) => {
    switch (status) {
      case 'available':
        return <Check className="w-4 h-4 text-green-600" />;
      case 'unavailable':
        return <X className="w-4 h-4 text-red-600" />;
      case 'maybe':
        return <HelpCircle className="w-4 h-4 text-yellow-600" />;
      default:
        return null;
    }
  };

  const getStatusColor = (status: AvailabilityStatus) => {
    switch (status) {
      case 'available':
        return 'bg-green-100 hover:bg-green-200 border-green-300';
      case 'unavailable':
        return 'bg-red-100 hover:bg-red-200 border-red-300';
      case 'maybe':
        return 'bg-yellow-100 hover:bg-yellow-200 border-yellow-300';
      default:
        return 'bg-gray-50 hover:bg-gray-100 border-gray-200';
    }
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return {
      day: date.toLocaleDateString('en-US', { weekday: 'short' }),
      date: date.getDate(),
      month: date.toLocaleDateString('en-US', { month: 'short' })
    };
  };

  const getAvailabilityCount = (date: string) => {
    let available = 0;
    let unavailable = 0;
    let maybe = 0;

    users.forEach(user => {
      const status = availability[user.id]?.[date];
      if (status === 'available') available++;
      else if (status === 'unavailable') unavailable++;
      else if (status === 'maybe') maybe++;
    });

    return { available, unavailable, maybe };
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <Calendar className="w-12 h-12 mx-auto mb-4 animate-pulse text-gray-400" />
          <p className="text-gray-500">Loading calendar...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl">When to Go</h2>
          <p className="text-gray-600">Mark your availability for each date</p>
        </div>
        <div className="flex items-center gap-4 text-sm">
          <div className="flex items-center gap-2">
            <Check className="w-4 h-4 text-green-600" />
            <span>Available</span>
          </div>
          <div className="flex items-center gap-2">
            <HelpCircle className="w-4 h-4 text-yellow-600" />
            <span>Maybe</span>
          </div>
          <div className="flex items-center gap-2">
            <X className="w-4 h-4 text-red-600" />
            <span>Unavailable</span>
          </div>
        </div>
      </div>

      <Card className="overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b bg-gray-50">
                <th className="px-4 py-3 text-left sticky left-0 bg-gray-50 z-10">Name</th>
                {dates.map(date => {
                  const { day, date: d, month } = formatDate(date);
                  const counts = getAvailabilityCount(date);
                  return (
                    <th key={date} className="px-4 py-3 text-center min-w-[120px]">
                      <div className="text-xs text-gray-500">{day}</div>
                      <div>{month} {d}</div>
                      <div className="text-xs text-gray-500 mt-1">
                        {counts.available > 0 && <span className="text-green-600">{counts.available}✓ </span>}
                        {counts.maybe > 0 && <span className="text-yellow-600">{counts.maybe}? </span>}
                        {counts.unavailable > 0 && <span className="text-red-600">{counts.unavailable}✗</span>}
                      </div>
                    </th>
                  );
                })}
              </tr>
            </thead>
            <tbody>
              {users.map(user => (
                <tr key={user.id} className="border-b">
                  <td className="px-4 py-3 sticky left-0 bg-white z-10">
                    <div className="flex items-center gap-2">
                      <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center text-sm">
                        {user.displayName[0].toUpperCase()}
                      </div>
                      <span>{user.displayName}</span>
                      {user.id === currentUserId && (
                        <span className="text-xs text-blue-600">(you)</span>
                      )}
                    </div>
                  </td>
                  {dates.map(date => {
                    const status = availability[user.id]?.[date] || null;
                    const isCurrentUser = user.id === currentUserId;
                    return (
                      <td key={date} className="p-2 text-center">
                        {isCurrentUser ? (
                          <button
                            onClick={() => toggleAvailability(date, status)}
                            className={`w-full h-12 rounded-lg border-2 transition-colors flex items-center justify-center cursor-pointer ${getStatusColor(status)}`}
                            type="button"
                          >
                            {getStatusIcon(status)}
                          </button>
                        ) : (
                          <div className={`w-full h-12 rounded-lg border-2 flex items-center justify-center ${getStatusColor(status)}`}>
                            {getStatusIcon(status)}
                          </div>
                        )}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <p className="text-sm text-blue-800">
          💡 <strong>Tip:</strong> Click on the cells in your row to cycle through: Not set → Available → Maybe → Unavailable
        </p>
      </div>
    </div>
  );
}
