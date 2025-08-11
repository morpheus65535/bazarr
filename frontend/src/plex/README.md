# Plex Module

This module contains all Plex-related functionality for the Bazarr frontend, providing OAuth authentication and server management capabilities using React Query for efficient API state management.

## Structure

```
plex/
├── index.ts                      # Main exports
├── constants/
│   └── auth.ts                   # Authentication constants and types
├── utilities/
│   └── errors.ts                 # Error handling utilities
├── queries/
│   └── plex.ts                   # React Query hooks for API calls
├── hooks/
│   ├── usePlexOAuth.ts           # OAuth authentication hook (React Query)
│   └── usePlexServers.ts         # Server + connection management hook
└── components/
    ├── PlexSettings.tsx          # Main Plex settings component
    └── PlexSettings.module.scss  # Component styles
```

## Features

- ✅ **React Query Integration**: All API calls use React Query for caching, error handling, and state management
- ✅ **Proper Error Handling**: Structured error handling with typed error responses
- ✅ **OAuth Authentication**: Secure Plex OAuth flow with proper token management
- ✅ **Server Management**: Automatic server discovery and connection testing
- ✅ **Type Safety**: Full TypeScript support with proper typing throughout
- ✅ **Mantine Components**: Uses Mantine UI components following design system
- ✅ **CSS Modules**: Styled with CSS modules for scoped styling

## Usage

### Importing Components

```typescript
import { PlexSettings } from "@/plex";
```

### Importing Hooks

```typescript
import { usePlexOAuth, usePlexServers } from "@/plex";
```

### Importing React Query Hooks

```typescript
import {
  usePlexAuthValidationQuery,
  usePlexServersQuery,
  usePlexPinMutation,
  usePlexLogoutMutation,
} from "@/plex";
```

### Importing Constants

```typescript
import { PLEX_AUTH_CONFIG, PLEX_ERROR_CODES } from "@/plex";
```

### Importing Utilities

```typescript
import { parseAxiosError, getErrorMessage } from "@/plex";
```

## Architecture

This module follows the established Bazarr frontend patterns:

1. **API Layer**: Uses the centralized Bazarr API client (`/apis/raw/plex.ts`)
2. **Query Layer**: React Query hooks for efficient API state management (`/queries/plex.ts`)
3. **Hook Layer**: Business logic hooks that combine queries and local state (`/hooks/*`)
4. **Component Layer**: UI components that consume the hooks (`/components/*`)

This architecture provides:

- Centralized error handling
- Automatic query caching and invalidation
- Type-safe API interactions
- Separation of concerns
- Easy testing and maintenance

## Features

- **OAuth Authentication**: Secure Plex.tv OAuth flow with PIN-based authentication
- **Server Discovery**: Automatic detection and testing of available Plex servers
- **Connection Management**: Smart connection selection with latency testing
- **Error Handling**: Structured error handling with user-friendly messages
- **State Management**: Proper state management with React reducers
- **Form Integration**: Seamless integration with Bazarr's settings forms
- **Theming**: Full dark/light mode support

## Components

### PlexSettings

Main component for Plex configuration, providing:

- OAuth authentication flow
- Server selection interface
- Connection testing and status display
- Manual configuration fallback

## Hooks

### usePlexOAuth

OAuth authentication hook built on React Query that provides:

- PIN-based authentication flow
- Polling for authentication completion
- Authentication state management
- Error handling with timeout support
- Window management for OAuth popup

### usePlexServers

Server management hook that handles:

- Server discovery and listing
- Connection testing with latency measurement
- Best connection selection algorithm
- Server selection and caching
- Throttled server fetching

Server selection now handled internally in the settings component with simple React state (lighter weight than previous reducer pattern).

## Form Integration

The Plex components integrate seamlessly with Bazarr's form system through:

- **Query Invalidation**: Uses React Query client to invalidate system queries when authentication changes
- **Form Reset**: Automatically resets forms after successful OAuth operations using Promise microtasks
- **Async Handling**: Proper async/await patterns in authentication and server selection flows

## Constants

### PLEX_AUTH_CONFIG

Configuration constants for OAuth flow:

- Polling intervals and timeouts
- Window configuration for OAuth popup
- Connection timeouts

### PLEX_ERROR_CODES

Standardized error codes for consistent error handling:

- `PIN_EXPIRED`: Authentication PIN has expired
- `AUTH_TIMEOUT`: Authentication timed out
- `CONNECTION_ERROR`: Network connection issues
- `INVALID_TOKEN`: Invalid authentication token
- `SERVER_NOT_FOUND`: Plex server not found
- `UNAUTHORIZED`: Unauthorized access

## Error Handling

The module provides structured error handling with:

- **Type-safe error objects**: All errors use the `PlexError` interface
- **User-friendly error messages**: Localized error messages for common scenarios
- **Retry capability indicators**: Errors include information about whether they're retryable
- **Consistent error parsing**: Centralized `parseAxiosError` function for API responses
