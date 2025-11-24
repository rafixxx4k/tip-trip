import { useState, useEffect } from "react";
import {
  ArrowLeft,
  Users,
  Share2,
  Copy,
  Check,
} from "lucide-react";
import { Button } from "./ui/button";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "./ui/tabs";
import { Card, CardContent } from "./ui/card";
import { CalendarView } from "./CalendarView";
import { ExpenseView } from "./ExpenseView";
import { ChatView } from "./ChatView";
import { getStoredUser } from "../lib/storage";
import { api, User } from "../lib/api";

interface TripPageProps {
  tripId: string;
  onBack: () => void;
}

export function TripPage({ tripId, onBack }: TripPageProps) {
  const [tripName, setTripName] = useState("");
  const [users, setUsers] = useState<User[]>([]);
  const [currentUserId, setCurrentUserId] = useState(getStoredUser()?.id.toString() ?? "");
  const [copied, setCopied] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadTripData();
  }, [tripId]);

  const loadTripData = async () => {
    try {
      // Get current user ID from storage
      // Load trip data from API
      const { trip, users: tripUsers } =
        await api.getTrip(tripId);
      setTripName(trip.name);
      setUsers(tripUsers);

    } catch (error) {
      console.error("Failed to load trip:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCopyTripId = () => {
    navigator.clipboard.writeText(tripId);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-gray-600">Loading trip...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="max-w-7xl mx-auto p-6">
        {/* Header */}
        <div className="mb-6">
          <Button
            variant="ghost"
            onClick={onBack}
            className="mb-4"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Trips
          </Button>

          <div className="flex items-start justify-between">
            <div>
              <div className="flex items-center gap-3 mb-2">
                <h1 className="text-4xl">{tripName}</h1>
                <div className="flex items-center gap-2 px-3 py-1 bg-white rounded-lg border border-gray-300">
                  <span className="text-sm text-gray-500">
                    ID:
                  </span>
                  <code className="text-sm">
                    {tripId.substring(0, 8)}...
                  </code>
                  <button
                    onClick={handleCopyTripId}
                    className="ml-1 hover:bg-gray-100 p-1 rounded"
                  >
                    {copied ? (
                      <Check className="w-3 h-3 text-green-600" />
                    ) : (
                      <Copy className="w-3 h-3 text-gray-500" />
                    )}
                  </button>
                </div>
              </div>
              <div className="flex items-center gap-4 text-gray-600">
                <div className="flex items-center gap-2">
                  <Users className="w-4 h-4" />
                  <span>
                    {users.length}{" "}
                    {users.length === 1
                      ? "participant"
                      : "participants"}
                  </span>
                </div>
              </div>
            </div>
            <Button
              variant="outline"
              onClick={handleCopyTripId}
            >
              {copied ? (
                <>
                  <Check className="w-4 h-4 mr-2" />
                  Copied!
                </>
              ) : (
                <>
                  <Share2 className="w-4 h-4 mr-2" />
                  Share Trip ID
                </>
              )}
            </Button>
          </div>
        </div>

        {/* Participants */}
        <Card className="mb-6">
          <CardContent className="p-4">
            <div className="flex items-center gap-3 flex-wrap">
              <span className="text-sm text-gray-600">
                Participants:
              </span>
              {users.map((user) => (
                <div
                  key={user.id}
                  className="flex items-center gap-2 px-3 py-1 bg-blue-50 rounded-full"
                >
                  <div className="w-6 h-6 rounded-full bg-blue-200 flex items-center justify-center text-xs">
                    {user.displayName[0].toUpperCase()}
                  </div>
                  <span className="text-sm">
                    {user.displayName}
                    {user.id === currentUserId && (
                      <span className="text-blue-600 ml-1">
                        (you)
                      </span>
                    )}
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Main Content Tabs */}
        <Tabs defaultValue="calendar" className="space-y-6">
          <TabsList className="grid w-full grid-cols-3 lg:w-[600px]">
            <TabsTrigger value="calendar">Schedule</TabsTrigger>
            <TabsTrigger value="expenses">Expenses</TabsTrigger>
            <TabsTrigger value="chat">AI Assistant</TabsTrigger>
          </TabsList>

          <TabsContent value="calendar">
            <CalendarView
              tripId={tripId}
              currentUserId={currentUserId}
            />
          </TabsContent>

          <TabsContent value="expenses">
            <ExpenseView
              tripId={tripId}
              currentUserId={currentUserId}
            />
          </TabsContent>

          <TabsContent value="chat">
            <ChatView
              tripId={tripId}
              currentUserId={currentUserId}
            />
          </TabsContent>
        </Tabs>

        {/* Trip ID Card */}
        <Card className="mt-6 bg-gray-50">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 mb-1">
                  Trip ID (share with others):
                </p>
                <code className="text-sm bg-white px-3 py-1 rounded border">
                  {tripId}
                </code>
              </div>
              <Button
                size="sm"
                variant="outline"
                onClick={handleCopyTripId}
              >
                <Copy className="w-4 h-4 mr-2" />
                Copy
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}