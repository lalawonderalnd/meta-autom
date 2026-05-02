# AccFarm Dashboard

Next.js 15 dashboard for managing the AccFarm Instagram account farm.

## Tech Stack

- Next.js 15 (App Router, React Server Components)
- TypeScript strict mode
- Tailwind CSS v4
- TanStack Table v8 + TanStack Virtual
- TanStack Query v5
- Supabase JS client v2 (REST + Realtime)
- Lucide icons
- Recharts

## Getting Started

### Prerequisites

- Node.js 20+
- Supabase project (see `../00_OVERVIEW.md`)
- Orchestrator running locally

### Installation

```bash
npm install
```

### Configuration

Copy `.env.example` to `.env.local` and fill in your values:

```bash
cp .env.example .env.local
```

Required variables:
- `NEXT_PUBLIC_SUPABASE_URL` - Your Supabase project URL
- `NEXT_PUBLIC_SUPABASE_ANON_KEY` - Supabase anon key
- `SUPABASE_SERVICE_ROLE_KEY` - Supabase service role key
- `ORCHESTRATOR_URL` - Local orchestrator URL (default: http://localhost:8000)
- `WS_SCRCPY_URL` - ws-scrcpy stream URL (default: http://localhost:8001)

### Development

```bash
npm run dev
```

Open http://localhost:3000

### Build

```bash
npm run build
npm run start
```

## Features

- **Accounts Table**: Virtualized table supporting 5,000+ rows with realtime updates
- **Status Pills**: Color-coded account status with glow animations
- **Warmup Bar**: Visual progress indicator for 7-day warmup curriculum
- **Bulk Actions**: Select multiple accounts and queue jobs
- **Realtime Updates**: Supabase Realtime keeps the UI in sync with database changes
- **Keyboard Navigation**: Cmd+K command palette (coming soon)

## Architecture

```
dashboard/
├── app/                      # Next.js App Router
│   ├── (app)/                # Authenticated app pages
│   │   ├── accounts/         # Accounts table and detail
│   │   ├── devices/          # Device fleet management
│   │   └── ...
│   └── api/                  # API routes (proxies to orchestrator)
├── components/               # React components
│   ├── shell/                # Sidebar, topbar layout
│   ├── accounts-table/       # Main accounts table
│   └── ui/                   # Primitive components
├── hooks/                    # Custom React hooks
│   └── use-realtime-table.ts # Supabase Realtime subscription
├── lib/                      # Utilities and types
│   ├── supabase/             # Supabase clients
│   ├── types.ts              # TypeScript types
│   └── utils.ts              # Helper functions
└── public/fonts/             # Self-hosted fonts
```

## Realtime Updates

The accounts table uses Supabase Realtime to receive live updates when accounts change state. To enable this, run the following SQL in your Supabase project:

```sql
ALTER PUBLICATION supabase_realtime ADD TABLE accounts, devices, jobs;
```

## Performance

- Initial load: Server-side fetch of first 200 rows
- Virtualization: Only renders visible rows (+5 overscan)
- Realtime patches: Updates individual rows without full re-render
- Target: 60fps scrolling with 10,000 rows

## Visual Design

- **Background**: Deep black (#07080a)
- **Surface**: Dark gray (#0e1014, #14171c)
- **Accents**: Cyan (ACTIVE), Magenta (WARMING), Amber (WARNING), Red (BANNED)
- **Typography**: JetBrains Mono (data), Manrope (body), Departure Mono (display)
- **Corners**: Sharp (max 2px radius)
- **Shadows**: None (borders only)
