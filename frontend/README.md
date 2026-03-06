# PostPilot AI - Frontend

React frontend application for PostPilot AI social media automation platform.

## Features

- User authentication (register, login, JWT tokens)
- Product management (upload, edit, delete with image preview)
- Campaign management (list, view details, schedule, cancel)
- Analytics dashboard with metrics and trends
- Instagram OAuth connection flow
- Protected routes with authentication
- Responsive design

## Tech Stack

- React 19
- React Router DOM for navigation
- Axios for HTTP requests
- Vite for build tooling

## Setup

1. Install dependencies:
```bash
npm install
```

2. Create `.env` file from example:
```bash
cp .env.example .env
```

3. Update `.env` with your API base URL:
```
VITE_API_BASE_URL=http://localhost:8000
```

4. Start development server:
```bash
npm run dev
```

The application will be available at `http://localhost:5173`

## Project Structure

```
src/
├── auth/              # Authentication context and hooks
│   ├── AuthContext.jsx
│   └── useAuth.js
├── components/        # Reusable components
│   ├── DashboardLayout.jsx
│   └── ProtectedRoute.jsx
├── pages/            # Page components
│   ├── Login.jsx
│   ├── Register.jsx
│   ├── Dashboard.jsx
│   ├── Products.jsx
│   ├── ProductForm.jsx
│   ├── Campaigns.jsx
│   ├── CampaignDetail.jsx
│   ├── Analytics.jsx
│   └── InstagramConnect.jsx
├── services/         # API client
│   └── api.js
├── App.jsx          # Main app with routing
├── main.jsx         # Entry point
└── index.css        # Global styles
```

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

## API Integration

The frontend communicates with the backend API at the URL specified in `VITE_API_BASE_URL`.

### Authentication Flow

1. User registers or logs in
2. Backend returns JWT access token (60 min) and refresh token (7 days)
3. Tokens stored in localStorage
4. Access token included in Authorization header for all requests
5. If access token expires (401), automatically refresh using refresh token
6. If refresh fails, redirect to login

### API Endpoints Used

- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/refresh` - Refresh access token
- `GET /api/v1/products` - List products
- `POST /api/v1/products` - Create product (multipart/form-data)
- `PUT /api/v1/products/:id` - Update product
- `DELETE /api/v1/products/:id` - Delete product
- `GET /api/v1/campaigns` - List campaigns
- `GET /api/v1/campaigns/:id` - Get campaign details
- `POST /api/v1/campaigns/:id/schedule` - Schedule campaign
- `POST /api/v1/campaigns/:id/cancel` - Cancel campaign
- `GET /api/v1/analytics` - Get analytics summary
- `GET /api/v1/instagram/authorize` - Get Instagram OAuth URL
- `GET /api/v1/instagram/callback` - Handle Instagram OAuth callback

## Environment Variables

- `VITE_API_BASE_URL` - Backend API base URL (default: http://localhost:8000)

## Requirements

- Node.js 18+
- npm or yarn
- Backend API running

## Notes

- All routes except `/login` and `/register` require authentication
- Images must be JPEG or PNG, max 10MB
- Campaign scheduling requires Instagram connection
- Analytics date range defaults to last 30 days
