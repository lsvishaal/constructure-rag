# 🏗️ Constructure RAG - Frontend

> Next.js 15 chat interface for construction document intelligence

Modern React application with Framer Motion animations, JWT authentication, and real-time RAG chat functionality.

---

## Quick Start

```bash
# Install dependencies
npm install

# Start development server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

**Login Credentials:**
```
Email:    testingcheckuser1234@gmail.com
Password: constructure2024
```

---

## Tech Stack

| Technology | Version | Purpose |
|------------|---------|---------|
| Next.js | 15 | App Router, Server Components |
| React | 19 | UI framework |
| TypeScript | 5.x | Type safety |
| Tailwind CSS | 3.x | Styling |
| Framer Motion | 11.x | Animations |
| shadcn/ui | Latest | UI components |
| Zustand | 5.x | State management |
| Axios | 1.x | HTTP client |

---

## Features

### Authentication
- JWT-based authentication with secure token storage
- Persistent login sessions with Zustand persist
- Protected routes with automatic redirects
- OAuth2-compatible login flow

### Chat Interface
- Real-time message streaming
- Source citations with page references
- Multi-mode support:
  - **Q&A Mode** - Natural language answers
  - **Extraction Mode** - Structured data output
  - **Sources Only** - Raw document chunks
- Message history with session persistence
- Typing indicators with animated loading

### Document Management
- PDF upload with progress feedback
- Document stats display
- Clear documents functionality

### UI/UX
- Dark/light mode toggle
- Responsive design (mobile-first)
- Framer Motion animations:
  - Fade-in entrance animations
  - Staggered list animations
  - Interactive hover/tap feedback
  - Smooth mode transitions
- Glass morphism design elements
- Gradient accents and glow effects

---

## Project Structure

```
frontend/
├── app/                          # Next.js App Router
│   ├── layout.tsx               # Root layout (fonts, theme)
│   ├── page.tsx                 # Home redirect
│   ├── login/
│   │   └── page.tsx             # Login page
│   ├── chat/
│   │   └── page.tsx             # Main chat interface
│   └── api/                     # API route proxies
│       ├── auth/
│       ├── chat/
│       ├── documents/
│       └── health/
│
├── components/
│   ├── chat/                    # Chat components
│   │   ├── ChatContainer.tsx
│   │   ├── ChatInput.tsx
│   │   ├── ChatMessage.tsx
│   │   ├── LoadingIndicator.tsx
│   │   └── SourceCitation.tsx
│   ├── extraction/              # Data display
│   │   ├── DoorScheduleTable.tsx
│   │   └── WageTable.tsx
│   ├── layout/
│   │   └── Header.tsx
│   ├── animations/              # Animation wrappers
│   │   ├── FadeIn.tsx
│   │   └── StaggerContainer.tsx
│   └── ui/                      # shadcn/ui components
│       ├── button.tsx
│       ├── input.tsx
│       ├── card.tsx
│       ├── dialog.tsx
│       └── ...
│
├── lib/
│   ├── api-client.ts            # Axios instance + interceptors
│   ├── constants.ts             # API endpoints
│   ├── animations.ts            # Framer Motion variants
│   ├── utils.ts                 # Utility functions
│   └── hooks/
│       ├── useAuth.ts           # Authentication state (Zustand)
│       ├── useChat.ts           # Chat state management
│       ├── useDocuments.ts      # Document operations
│       └── useTheme.ts          # Dark mode toggle
│
├── types/
│   ├── api.ts                   # API response types
│   ├── chat.ts                  # Chat domain types
│   └── extraction.ts            # Extraction schemas
│
└── styles/
    └── globals.css              # Tailwind + custom CSS
```

---

## Configuration

### Environment Variables

Create `.env.local`:

```env
# Backend API URL
NEXT_PUBLIC_API_URL=http://localhost:8000

# (Optional) For production
NEXT_PUBLIC_API_URL=https://your-backend-url.com
```

---

## Authentication Flow

```
Login Page
    │
    ▼
POST /api/v1/auth/login (OAuth2 form)
    │
    ▼
JWT Token Stored (Zustand persist)
    │
    ▼
GET /api/v1/auth/me (verify token)
    │
    ▼
Redirect to /chat
```

### Token Management
- Tokens stored in localStorage via Zustand persist
- Automatic token refresh on app load
- Axios interceptors add `Authorization` header
- 401 responses trigger logout

---

## Chat Flow

```
User Input
    │
    ▼
POST /api/v1/chat
{
  "query": "...",
  "mode": "qa|extraction|sources_only",
  "top_k": 5
}
    │
    ▼
Response
{
  "answer": "...",
  "sources": [
    {
      "filename": "...",
      "page": 1,
      "content": "...",
      "score": 0.85
    }
  ],
  "mode": "qa"
}
```

---

## Animation System

Using Framer Motion with consistent timing:

| Animation Type | Duration | Easing |
|----------------|----------|--------|
| Fast (feedback) | 150-200ms | ease-out |
| Medium (transitions) | 300-400ms | ease-in-out |
| Slow (hero) | 500-800ms | ease-out |

### Animation Variants

```typescript
// lib/animations.ts
export const SPRING = {
  snappy: { type: "spring", stiffness: 400, damping: 30 },
  gentle: { type: "spring", stiffness: 200, damping: 25 },
};

export const TIMING = {
  fast: 0.15,
  medium: 0.3,
  slow: 0.5,
};
```

---

## Component Patterns

### Protected Routes
```tsx
useEffect(() => {
  if (hasHydrated && !isCheckingAuth && !isAuthenticated) {
    router.push("/login");
  }
}, [isAuthenticated, isCheckingAuth, router, hasHydrated]);
```

### API Calls with Auth
```typescript
const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL,
});

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem("auth-token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
```

### Chat State (Zustand)
```typescript
const useChatStore = create((set) => ({
  messages: [],
  isLoading: false,
  mode: "qa",
  sendMessage: async (query) => { ... },
  clearMessages: () => set({ messages: [] }),
  setMode: (mode) => set({ mode }),
}));
```

---

## Development

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Run production build
npm start

# Lint code
npm run lint

# Type check
npx tsc --noEmit
```

---

## Styling

### Tailwind Classes
- `glass` - Glass morphism effect
- `text-gradient` - Gradient text
- `bg-mesh` - Mesh gradient background

### Color Scheme
```css
:root {
  --color-primary: #3B82F6;      /* Blue */
  --color-accent: #8B5CF6;       /* Purple */
  --color-success: #10B981;      /* Emerald */
  --color-error: #EF4444;        /* Red */
}
```

### Dark Mode
- Uses Tailwind `dark:` prefix
- Theme stored in Zustand with persist
- Respects `prefers-color-scheme`

---

## Key Dependencies

```json
{
  "dependencies": {
    "next": "^15.0.0",
    "react": "^19.0.0",
    "framer-motion": "^11.0.0",
    "zustand": "^5.0.0",
    "axios": "^1.6.0",
    "@radix-ui/react-*": "shadcn/ui components",
    "lucide-react": "icons",
    "sonner": "toast notifications",
    "clsx": "class merging",
    "tailwind-merge": "tailwind class merging"
  }
}
```

---

## Performance Optimizations

- Server Components where possible
- Dynamic imports for heavy components
- Optimistic UI updates
- Request deduplication via Zustand
- Lazy loading of animations
- `prefers-reduced-motion` support

---

## Accessibility

- Semantic HTML elements
- ARIA labels on interactive elements
- Keyboard navigation support
- Focus ring styling
- Color contrast compliance (WCAG AA)
- Reduced motion support

---

## Watermark

`CONSTRUCTURE_RAG_VISHAAL_LS_2025`

---

*Built for Constructure AI Technical Assignment | December 2025*
