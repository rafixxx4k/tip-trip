import { useState, useEffect } from 'react';
import { DollarSign, Plus, Users, ArrowRight } from 'lucide-react';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from './ui/dialog';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Checkbox } from './ui/checkbox';
import { api, Expense, User, Settlement, Debtor } from '../lib/api';

interface ExpenseViewProps {
  tripId: string;
  currentUserId: string;
}

export function ExpenseView({ tripId, currentUserId }: ExpenseViewProps) {
  const [expenses, setExpenses] = useState<Expense[]>([]);
  const [settlements, setSettlements] = useState<Settlement[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showAddDialog, setShowAddDialog] = useState(false);
  
  // Form state
  const [description, setDescription] = useState('');
  const [amount, setAmount] = useState('');
  const [currency, setCurrency] = useState('USD');
  const [selectedDebtors, setSelectedDebtors] = useState<Set<string>>(new Set());
  const [isSplitEqually, setIsSplitEqually] = useState(true);

  useEffect(() => {
    loadData();
  }, [tripId]);

  const loadData = async () => {
    try {
      const [expensesData, settlementsData, tripData] = await Promise.all([
        api.getExpenses(tripId),
        api.getSettlements(tripId),
        api.getTrip(tripId)
      ]);
      
      setExpenses(expensesData);
      setSettlements(settlementsData.balances);
      setUsers(tripData.users);
      
      // Initialize debtors to all users except current user
      const otherUsers = tripData.users.filter(u => u.id !== currentUserId).map(u => u.id);
      setSelectedDebtors(new Set([currentUserId, ...otherUsers]));
    } catch (error) {
      console.error('Failed to load expenses:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleAddExpense = async () => {
    if (!description.trim() || !amount || parseFloat(amount) <= 0 || selectedDebtors.size === 0) return;

    const totalAmount = parseFloat(amount);
    const debtors: Debtor[] = Array.from(selectedDebtors).map(userId => ({
      userId,
      shareType: 'equal',
      value: totalAmount / selectedDebtors.size
    }));

    try {
      await api.createExpense(tripId, currentUserId, totalAmount, description, currency, debtors);
      await loadData();
      setShowAddDialog(false);
      resetForm();
    } catch (error) {
      console.error('Failed to add expense:', error);
    }
  };

  const resetForm = () => {
    setDescription('');
    setAmount('');
    setCurrency('USD');
    const otherUsers = users.filter(u => u.id !== currentUserId).map(u => u.id);
    setSelectedDebtors(new Set([currentUserId, ...otherUsers]));
    setIsSplitEqually(true);
  };

  const toggleDebtor = (userId: string) => {
    const newSet = new Set(selectedDebtors);
    if (newSet.has(userId)) {
      newSet.delete(userId);
    } else {
      newSet.add(userId);
    }
    setSelectedDebtors(newSet);
  };

  const getUserName = (userId: string) => {
    const user = users.find(u => u.id === userId);
    return user ? user.displayName : 'Unknown';
  };

  const getTotalPaid = (userId: string) => {
    return expenses
      .filter(e => e.payerId === userId)
      .reduce((sum, e) => sum + e.amount, 0);
  };

  const getTotalOwed = (userId: string) => {
    return expenses.reduce((sum, expense) => {
      const debtor = expense.debtors.find(d => d.userId === userId);
      if (debtor && expense.payerId !== userId) {
        return sum + debtor.value;
      }
      return sum;
    }, 0);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <DollarSign className="w-12 h-12 mx-auto mb-4 animate-pulse text-gray-400" />
          <p className="text-gray-500">Loading expenses...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl">Expenses</h2>
          <p className="text-gray-600">Track and split trip costs</p>
        </div>
        <Button onClick={() => setShowAddDialog(true)}>
          <Plus className="w-4 h-4 mr-2" />
          Add Expense
        </Button>
      </div>

      {/* Settlements */}
      {settlements.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Settlements</CardTitle>
            <CardDescription>Who owes whom</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {settlements.map((settlement, idx) => (
              <div key={idx} className="flex items-center justify-between p-3 bg-yellow-50 rounded-lg border border-yellow-200">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-full bg-yellow-100 flex items-center justify-center text-sm">
                    {getUserName(settlement.fromUser)[0].toUpperCase()}
                  </div>
                  <span>{getUserName(settlement.fromUser)}</span>
                  <ArrowRight className="w-4 h-4 text-gray-400" />
                  <div className="w-8 h-8 rounded-full bg-green-100 flex items-center justify-center text-sm">
                    {getUserName(settlement.toUser)[0].toUpperCase()}
                  </div>
                  <span>{getUserName(settlement.toUser)}</span>
                </div>
                <div className="text-lg">
                  {settlement.amount.toFixed(2)} {settlement.currency}
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {/* Summary */}
      <div className="grid md:grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <CardTitle>Total Expenses</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl">
              {expenses.reduce((sum, e) => sum + e.amount, 0).toFixed(2)} {expenses[0]?.currency || 'USD'}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Your Balance</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl">
              {(getTotalPaid(currentUserId) - getTotalOwed(currentUserId)).toFixed(2)} {expenses[0]?.currency || 'USD'}
            </div>
            <p className="text-sm text-gray-500 mt-1">
              Paid: {getTotalPaid(currentUserId).toFixed(2)} | Owe: {getTotalOwed(currentUserId).toFixed(2)}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Expense List */}
      <Card>
        <CardHeader>
          <CardTitle>All Expenses</CardTitle>
        </CardHeader>
        <CardContent>
          {expenses.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <DollarSign className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p>No expenses yet. Add your first expense to get started!</p>
            </div>
          ) : (
            <div className="space-y-3">
              {expenses.map((expense) => (
                <div key={expense.id} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span>{expense.description}</span>
                    </div>
                    <div className="text-sm text-gray-500">
                      Paid by {getUserName(expense.payerId)}
                      {' • '}
                      Split among {expense.debtors.length} {expense.debtors.length === 1 ? 'person' : 'people'}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-lg">
                      {expense.amount.toFixed(2)} {expense.currency}
                    </div>
                    <div className="text-sm text-gray-500">
                      {expense.debtors.find(d => d.userId === currentUserId) && (
                        <span>
                          Your share: {expense.debtors.find(d => d.userId === currentUserId)?.value.toFixed(2)}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Add Expense Dialog */}
      <Dialog open={showAddDialog} onOpenChange={setShowAddDialog}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Add Expense</DialogTitle>
            <DialogDescription>Record a new shared expense</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div>
              <Label htmlFor="description">Description</Label>
              <Input
                id="description"
                placeholder="e.g., Hotel booking"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="amount">Amount</Label>
                <Input
                  id="amount"
                  type="number"
                  step="0.01"
                  placeholder="0.00"
                  value={amount}
                  onChange={(e) => setAmount(e.target.value)}
                />
              </div>
              <div>
                <Label htmlFor="currency">Currency</Label>
                <Select value={currency} onValueChange={setCurrency}>
                  <SelectTrigger id="currency">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="USD">USD</SelectItem>
                    <SelectItem value="EUR">EUR</SelectItem>
                    <SelectItem value="GBP">GBP</SelectItem>
                    <SelectItem value="JPY">JPY</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div>
              <Label className="mb-2 block">Split Between</Label>
              <div className="space-y-2 border rounded-lg p-3">
                {users.map(user => (
                  <div key={user.id} className="flex items-center gap-2">
                    <Checkbox
                      id={`debtor-${user.id}`}
                      checked={selectedDebtors.has(user.id)}
                      onCheckedChange={() => toggleDebtor(user.id)}
                    />
                    <Label htmlFor={`debtor-${user.id}`} className="cursor-pointer">
                      {user.displayName} {user.id === currentUserId && '(you)'}
                    </Label>
                  </div>
                ))}
              </div>
              {selectedDebtors.size > 0 && amount && (
                <p className="text-sm text-gray-500 mt-2">
                  Each person pays: {(parseFloat(amount) / selectedDebtors.size).toFixed(2)} {currency}
                </p>
              )}
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowAddDialog(false)}>
              Cancel
            </Button>
            <Button 
              onClick={handleAddExpense} 
              disabled={!description.trim() || !amount || parseFloat(amount) <= 0 || selectedDebtors.size === 0}
            >
              Add Expense
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
