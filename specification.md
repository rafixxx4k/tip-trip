# Trip Planner Application (Backend) Specification

This document outlines the requirements, data models, and RESTful API endpoints for the core backend functionality of the collaborative trip planner application.

## 1. Core Requirements and Scope

### 1.1 Non-Authenticated Access (Room-Based)

* Users **do not** need to create accounts or log in.

* Access is granted via a unique, sharable **Room ID (Trip ID)**.

* A user is identified by a temporary `userId` (a UUID or hash) that is generated upon creation or joining a room and stored client-side.

### 1.2 Core Features

0. **starting page** a page with all joined trips button to create new trip and button to add one

1.  **Scheduling/Calendar:** Collaborative determination of optimal trip dates.

2.  **Expense Splitting:** Tracking, adding, and settling shared expenses.

3.  **AI Chat Agent:** Providing assistance and recommendations for trip planning.

---

## 2. Data Models (Database Schema)

We will use four primary collections/tables, linked by `tripId` and `userId`.

### 2.1 Trip (Room)

| **Field** | **Type** | **Description** |
| :--- | :--- | :--- |
| `id` | UUID/String | **Primary Key** (The shareable Room ID). |
| `name` | String | User-provided trip name (e.g., "Paris 2026"). |
| `organizerUserId` | String | The `userId` of the creator of the room. |
| `createdAt` | Timestamp | Creation date. |

### 2.2 User (Participant)

| **Field** | **Type** | **Description** |
| :--- | :--- | :--- |
| `id` | UUID/String | **Primary Key** (The unique identifier for the user session). |
| `tripId` | String | Foreign Key referencing `Trip.id`. |
| `displayName` | String | User-provided name (e.g., "Alex"). |
| `socketId` | String | (Optional for future real-time communication). |

### 2.3 Availability (Calendar Response Matrix)

This model represents a person's availability for a single day within the trip interval.

| **Field** | **Type** | **Description** |
| :--- | :--- | :--- |
| `id` | UUID/String | Primary Key. |
| `tripId` | String | Foreign Key referencing `Trip.id`. |
| `userId` | String | Foreign Key referencing `User.id`. |
| `date` | Date | The specific date being marked (YYYY-MM-DD). |
| `status` | String | **'available'** \| **'unavailable'** \| **'maybe'**. |

### 2.4 Expense

| **Field** | **Type** | **Description** |
| :--- | :--- | :--- |
| `id` | UUID/String | Primary Key. |
| `tripId` | String | Foreign Key referencing `Trip.id`. |
| `payerId` | String | Foreign Key referencing `User.id` (Who paid the initial amount). |
| `amount` | Number | Total amount of the expense. |
| `currency` | String | Currency code (e.g., USD, EUR). |
| `description` | String | Description of the expense (e.g., "Dinner at Joe's"). |
| `isSplitEqually` | Boolean | True if split equally among split members. |
| `debtors` | Array\<Object> | Details on who owes the money. |

#### Debtors Sub-Structure (within `Expense.debtors`)

This array defines how the expense is allocated.

| Field | Type | Description |
| :--- | :--- | :--- |
| `userId` | String | ID of the user who owes a share. |
| `shareType` | String | **'equal'** \| **'percent'** \| **'amount'**. |
| `value` | Number | The value of the share (e.g., 25 if percent, 50 if amount). |

---

## 3. REST API Endpoint Plan

All endpoints will be prefixed with `/api/v1`.

### 3.1 Trip & User Management

| **Method** | **Endpoint** | **Description** | **Request Body** | **Success Response** |
| :--- | :--- | :--- | :--- | :--- |
| `POST` | `/trips` | **Create a new room** (trip). | `name`, `displayName` | `{ tripId, userId }` |
| `POST` | `/trips/{tripId}/join` | **Join an existing room** (trip). | `displayName` | `{ userId, tripName, calendarInitialDates }` |
| `GET` | `/trips/{tripId}` | Get trip details and current members. | None | `{ trip: {...}, users: [...] }` |
| `PUT` | `/trips/{tripId}` | Update core trip details (e.g., name, date range). | `userId`, `name` (optional), `earliestDate` (optional), `latestDate` (optional), etc. | `{ status: 'success' }` |

### 3.2 Scheduling (When to Go)

| **Method** | **Endpoint** | **Description** | **Request Body** | **Success Response** |
| :--- | :--- | :--- | :--- | :--- |
| `POST` | `/trips/{tripId}/availability` | Submit or update user's availability. | `userId`, `dates`: `[{ date: 'YYYY-MM-DD', status: 'available' \| 'unavailable' \| 'maybe' }]` | `{ status: 'success' }` |
| `GET` | `/trips/{tripId}/calendar` | Get the full availability matrix. | None | **Calendar Grid Data (See Logic)** |

**Calendar Grid Data Logic:** The backend generates a list of all valid dates between `earliestDate` and `latestDate` that match `availableDaysOfWeek`. It then returns a matrix:

* **Rows:** Users in the trip.

* **Columns:** Each available date.

* **Cells:** The `status` for that `userId` on that `date`.

### 3.3 Expense Splitting

| **Method** | **Endpoint** | **Description** | **Request Body** | **Success Response** |
| :--- | :--- | :--- | :--- | :--- |
| `POST` | `/trips/{tripId}/expenses` | Record a new expense. | `userId` (payer), `amount`, `description`, `currency`, `debtors` (array) | `{ expenseId }` |
| `GET` | `/trips/{tripId}/expenses` | List all expenses for the trip. | None | `[Expense, Expense, ...]` |
| `GET` | `/trips/{tripId}/settlements` | Calculate and return current balances (who owes whom). | None | `{ balances: [{ fromUser: 'U1', toUser: 'U2', amount: 100, currency: 'USD' }, ...] }` |

**Settlement Logic:** This endpoint is the core of Feature 2. The backend must calculate the net balance for every user based on all recorded expenses, simplifying the settlement down to the minimum number of transactions required to clear all debts.

### 3.4 AI Chat Agent

| **Method** | **Endpoint** | **Description** | **Request Body** | **Success Response** |
| :--- | :--- | :--- | :--- | :--- |
| `POST` | `/trips/{tripId}/chat` | Send a message to the trip-planning AI agent. | `userId`, `message` | `{ response: 'AI text response' }` |

**AI Agent Integration:** This endpoint will call the Gemini API (`gemini-2.5-flash-preview-09-2025`) using the user's message as the query. The system instruction for the LLM will establish the persona (e.g., "You are a helpful, travel-savvy AI agent assisting with planning for the trip named \[Trip.name\].").

---

## 4. Technology Considerations

| **Component** | **Recommendation** | **Reason** |
| :--- | :--- | :--- |
| **Backend Language** | Node.js (Express), Python (Flask/Django) | Standard for modern REST APIs; strong ecosystem. |
| **Database** | MongoDB or Firestore | Highly flexible schema accommodates the dynamic nature of expense splitting and temporary user data. |
| **Real-time Comms** | WebSockets (via Socket.IO) | Recommended for real-time calendar updates and live chat (future expansion). |
| **AI Integration** | Google Gemini API | Directly integrates the requested AI functionality into the chat endpoint. |
