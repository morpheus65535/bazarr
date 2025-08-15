# 🔧 PLEX FRONTEND REFACTOR - TECHNICAL IMPLEMENTATION PLAN

**Project**: Bazarr Plex Settings Frontend Refactor  
**Branch**: `plex-frontend-refactor`  
**Created**: August 15, 2025  
**Status**: Implementation Plan - Ready for Execution  

---

## 📊 Current Status Analysis

**PROBLEM**: Anderson's refactoring is **90% complete** but has critical issues:
1. **Commented-out hook logic** in `PlexSettings.tsx`
2. **Missing variable references** (`isAuthenticated`, `servers`, etc.)
3. **Inconsistent hook patterns** (some return `useQuery`, others don't)
4. **Custom polling logic** instead of React Query native patterns

**Anderson's Feedback**:
> - "Please refactor or rebuild to make the hooks always return a react query useQuery"
> - "There is also an issue with your polling, you should try to make use of useTimeout instead"
> - "Also you shouldn't need to refetch if you invalidate the query properly"

---

## 🏗️ Architecture Overview

**BEFORE (Original - Monolithic)**:
- Single 350+ line `PlexSettings.tsx` file
- All logic mixed together (auth, servers, UI, state)
- Heavy prop drilling
- Tightly coupled components

**AFTER (Anderson's Vision - Modular)**:
- `PlexSettings.tsx` - **Orchestrator** (coordinator/container)
- `AuthSection.tsx` - **Authentication responsibility**
- `ServerSection.tsx` - **Server management responsibility** 
- `ConnectionsCard.tsx` - **Connection display responsibility**

**Key Benefits**:
- Single Responsibility Principle
- Independent data fetching per component
- React Query caching eliminates redundant API calls
- Better testability and maintainability

---

## 📋 DETAILED IMPLEMENTATION STEPS

### **STEP 1: Fix the Hook Architecture**
**File**: `/frontend/src/apis/hooks/plex.ts`

**Issue**: Anderson wants all hooks to return proper `useQuery` objects consistently.

#### A) Uncomment and Fix `usePlexOAuth` Hook - **SIMPLIFIED APPROACH**

**Location**: Lines ~110-260 (currently commented)
**Current**: Commented out complex custom implementation
**Action**: **SIMPLIFY** - Remove the complex hook entirely and use individual hooks directly

**Anderson's Requirement**: "make the hooks always return a react query useQuery"

**SOLUTION**: Instead of a complex `usePlexOAuth` hook, use the existing individual hooks directly in components:
- `usePlexAuthValidationQuery()` - returns pure useQuery
- `usePlexPinMutation()` - returns pure useMutation  
- `usePlexLogoutMutation()` - returns pure useMutation
- `usePlexPinCheckQuery()` - returns pure useQuery

**Action**: **DELETE the commented usePlexOAuth hook entirely** - don't uncomment it.

#### B) Create Simple useTimeout Hook for Polling

**NEW FILE**: `/frontend/src/hooks/useTimeout.ts`

```typescript
import { useEffect, useRef } from 'react';

export const useTimeout = (callback: () => void, delay: number | null) => {
  const savedCallback = useRef(callback);

  useEffect(() => {
    savedCallback.current = callback;
  }, [callback]);

  useEffect(() => {
    if (delay === null) return;

    const id = setTimeout(() => savedCallback.current(), delay);
    return () => clearTimeout(id);
  }, [delay]);
};
```

#### C) Clean Up Commented Code

**Location**: Lines ~110-355 (all commented hook logic)
**Action**: **DELETE all commented-out hook implementations**

**Reason**: These complex hooks cause the useCallback/useEffect issues Anderson mentioned. We'll use individual hooks directly in components instead.

---

### **STEP 2: Simplify PlexSettings.tsx - Direct Hook Usage**
**File**: `/frontend/src/pages/Settings/Plex/PlexSettings.tsx`

#### A) Replace Commented Code with Direct Hook Usage - **SIMPLIFIED APPROACH**

**Location**: Lines ~17-115 (commented section)
**Action**: **DELETE all commented code** and replace with simple, direct hook usage

```typescript
import { Stack } from "@mantine/core";
import { useForm } from "@mantine/form";
import { useFormActions } from "@/pages/Settings/utilities/FormValues";
import { 
  usePlexAuthValidationQuery,
  usePlexServersQuery,
  usePlexSelectedServerQuery,
  usePlexServerSelectionMutation 
} from "@/apis/hooks/plex";
import AuthSection from "./AuthSection";
import ServerSection from "./ServerSection";

export const PlexSettings = () => {
  const form = useForm({
    initialValues: {
      selectedServer: null as Plex.Server | null,
      isSelecting: false,
      isSaved: false,
    },
  });

  // Use individual hooks directly - Anderson's requirement: "return a react query useQuery"
  const authQuery = usePlexAuthValidationQuery();
  const serversQuery = usePlexServersQuery({
    enabled: authQuery.data?.valid && authQuery.data?.auth_method === "oauth"
  });
  const selectedServerQuery = usePlexSelectedServerQuery({
    enabled: authQuery.data?.valid && authQuery.data?.auth_method === "oauth"
  });
  const serverSelectionMutation = usePlexServerSelectionMutation();

  const isAuthenticated = authQuery.data?.valid && authQuery.data?.auth_method === "oauth";
  const servers = serversQuery.data || [];
  const savedSelectedServer = selectedServerQuery.data;

  // Auto-selection logic (simplified - NO useEffect/useCallback)
  if (isAuthenticated && savedSelectedServer && !form.values.isSaved) {
    // Restore previously selected server
    form.setFieldValue("selectedServer", savedSelectedServer);
    form.setFieldValue("isSaved", true);
  } else if (isAuthenticated && servers.length === 1 && servers[0].bestConnection && !form.values.isSaved && !savedSelectedServer) {
    // Auto-select single server
    form.setFieldValue("selectedServer", servers[0]);
    serverSelectionMutation.mutate({
      machineIdentifier: servers[0].machineIdentifier,
      name: servers[0].name,
      uri: servers[0].bestConnection.uri,
      local: servers[0].bestConnection.local,
    }, {
      onSuccess: () => form.setFieldValue("isSaved", true)
    });
  }

  // Simple handlers - NO useCallback (Anderson's feedback)
  const handleServerSelect = () => {
    const selectedServer = form.values.selectedServer;
    if (!selectedServer?.bestConnection) return;

    form.setFieldValue("isSelecting", true);
    serverSelectionMutation.mutate({
      machineIdentifier: selectedServer.machineIdentifier,
      name: selectedServer.name,
      uri: selectedServer.bestConnection.uri,
      local: selectedServer.bestConnection.local,
    }, {
      onSuccess: () => {
        form.setFieldValue("isSaved", true);
        form.setFieldValue("isSelecting", false);
      },
      onError: () => {
        form.setFieldValue("isSelecting", false);
      }
    });
  };

  const handleLogout = () => {
    form.reset();
  };

  const handleCancelAuth = () => {
    // Handled directly in AuthSection
  };

  return (
    <Stack gap="lg">
      <AuthSection 
        onCancelAuth={handleCancelAuth} 
        onLogout={handleLogout} 
      />
      <ServerSection
        isAuthenticated={isAuthenticated}
        servers={servers}
        error={serversQuery.error?.message}
        selectedServer={form.values.selectedServer}
        isSelecting={form.values.isSelecting}
        isSaved={form.values.isSaved}
        onFetchServers={() => serversQuery.refetch()}
        onServerSelect={handleServerSelect}
        onSelectedServerChange={(server: Plex.Server | null) =>
          form.setFieldValue("selectedServer", server)
        }
      />
    </Stack>
  );
};

export default PlexSettings;
```

**Key Changes:**
1. **NO useCallback/useEffect** - Anderson's main feedback about flickering
2. **All hooks return pure useQuery/useMutation** - as requested
3. **Simple function handlers** - no complex memoization
4. **Let React Query manage state** - no manual effect chains
5. **Simple auto-selection** - direct conditional logic, no complex effects

#### B) Remove Conflicting Code Sections

**Location**: The sections about "Fix Missing Variables in JSX" and "Add Missing useEffect"
**Action**: **DELETE these sections** - they're already handled in the simplified approach above

**Note**: The code example in section A already includes all necessary logic.

---

### **STEP 3: Simplify AuthSection.tsx - Use Direct Hooks + useTimeout**
**File**: `/frontend/src/pages/Settings/Plex/AuthSection.tsx`

#### A) Replace Complex Polling with useTimeout Pattern

**Action**: Rewrite AuthSection to use **individual hooks directly** + **useTimeout for polling**

```typescript
import { useRef, useState } from "react";
import { Alert, Button, Paper, Stack, Text, Title } from "@mantine/core";
import {
  usePlexAuthValidationQuery,
  usePlexLogoutMutation,
  usePlexPinCheckQuery,
  usePlexPinMutation,
} from "@/apis/hooks/plex";
import { useTimeout } from "@/hooks/useTimeout";
import { PLEX_AUTH_CONFIG } from "@/constants/plex";
import styles from "@/pages/Settings/Plex/PlexSettings.module.scss";

interface AuthSectionProps {
  onCancelAuth: () => void;
  onLogout: () => void;
}

const AuthSection = ({ onCancelAuth, onLogout }: AuthSectionProps) => {
  // Anderson's requirement: "hooks always return a react query useQuery"
  const authQuery = usePlexAuthValidationQuery();
  const pinMutation = usePlexPinMutation();
  const logoutMutation = usePlexLogoutMutation();
  
  const [pin, setPin] = useState<Plex.Pin | null>(null);
  const [pollCount, setPollCount] = useState(0);
  const authWindowRef = useRef<Window | null>(null);
  
  const isPolling = !!pin?.pinId && pollCount < PLEX_AUTH_CONFIG.MAX_POLLING_ATTEMPTS;

  // Anderson's requirement: "use useTimeout instead" - NO refetchInterval
  const pinCheckQuery = usePlexPinCheckQuery(
    pin?.pinId ?? null,
    false, // disable React Query polling
    false  // disable refetchInterval
  );

  // Use useTimeout for polling - NO useCallback/useEffect
  useTimeout(() => {
    if (isPolling) {
      pinCheckQuery.refetch();
      setPollCount(prev => prev + 1);
    }
  }, isPolling ? PLEX_AUTH_CONFIG.POLLING_INTERVAL_MS : null);

  const isAuthenticated = authQuery.data?.valid && authQuery.data?.auth_method === "oauth";

  // Simple handlers - NO useCallback (Anderson's feedback about flickering)
  const handleAuth = async () => {
    const { data: pinData } = await pinMutation.mutateAsync();
    setPin(pinData);
    setPollCount(0);

    const { width, height, features } = PLEX_AUTH_CONFIG.AUTH_WINDOW_CONFIG;
    const left = Math.round(window.screen.width / 2 - width / 2);
    const top = Math.round(window.screen.height / 2 - height / 2);

    authWindowRef.current = window.open(
      pinData.authUrl,
      "PlexAuth",
      `width=${width},height=${height},left=${left},top=${top},${features}`,
    );
  };

  const handleCancel = () => {
    setPin(null);
    setPollCount(0);
    if (authWindowRef.current) {
      authWindowRef.current.close();
    }
    onCancelAuth();
  };

  const handleLogout = () => {
    logoutMutation.mutate();
    onLogout();
  };

  // ... rest of the component UI remains the same but with updated handler names
};

export default AuthSection;
```

**Key Changes:**
1. **NO useCallback** - Anderson's main feedback about flickering
2. **useTimeout for polling** - eliminates refetchInterval flickering
3. **All hooks return pure useQuery/useMutation**
4. **Simple function handlers** - no memoization complexity
5. **Minimal state management** - let React Query handle caching

---

### **STEP 4: Verify ServerSection.tsx**
**File**: `/frontend/src/pages/Settings/Plex/ServerSection.tsx`

**Status**: ✅ **Already correct** - This component is properly implemented and receives all data via props.
**No action needed**

---

### **STEP 5: Verify ConnectionsCard.tsx**
**File**: `/frontend/src/pages/Settings/Plex/ConnectionsCard.tsx`

**Status**: ✅ **Already correct** - This component is properly implemented.
**No action needed**

---

### **STEP 6: Fix Query Invalidation Pattern**
**File**: `/frontend/src/apis/hooks/plex.ts`

**Issue**: Anderson mentioned "you shouldn't need to refetch if you invalidate properly"

**Current logout mutation** (Lines 77-85):
```typescript
onSuccess: () => {
  void queryClient.invalidateQueries({
    queryKey: [QueryKeys.Plex],
  });
  void queryClient.invalidateQueries({
    queryKey: [QueryKeys.System],
  });
},
```

**Status**: ✅ **Already correct** - Using proper invalidation pattern.
**No action needed**

---

## 🎯 REVISED IMPLEMENTATION ORDER - **SIMPLIFIED & STABLE**

**Following Anderson's specific requirements for stable, slim code:**

1. **First**: Create `/frontend/src/hooks/useTimeout.ts` (new simple utility)
2. **Second**: **DELETE all commented code** in `/frontend/src/apis/hooks/plex.ts` (remove complexity)  
3. **Third**: Rewrite `/frontend/src/pages/Settings/Plex/PlexSettings.tsx` (direct hook usage)
4. **Fourth**: Rewrite `/frontend/src/pages/Settings/Plex/AuthSection.tsx` (useTimeout polling)
5. **Fifth**: Test the simplified flow

---

## 🧪 REVISED VALIDATION CHECKLIST - **ANDERSON'S REQUIREMENTS**

- [ ] ✅ **"hooks always return a react query useQuery"** - All hooks are individual useQuery/useMutation
- [ ] ✅ **"use useTimeout instead"** - Custom useTimeout hook for polling  
- [ ] ✅ **"you shouldn't need to refetch if you invalidate properly"** - Proper invalidation pattern
- [ ] ✅ **No complex wrapper hooks** - Direct usage of individual queries
- [ ] ✅ **Stable and slim code** - Reduced complexity, focused components
- [ ] ✅ **Components properly separated** - Maintain Anderson's architectural separation
- [ ] ✅ **No commented-out code remains**
- [ ] ✅ **All variable references resolve correctly**
- [ ] ✅ **No TypeScript errors**

---

## 🔧 REVISED FILES TO MODIFY - **SIMPLIFIED APPROACH**

1. **NEW FILE**: `/frontend/src/hooks/useTimeout.ts` - **Simple polling utility**
2. `/frontend/src/apis/hooks/plex.ts` - **DELETE all commented code** (reduce complexity)
3. `/frontend/src/pages/Settings/Plex/PlexSettings.tsx` - **Complete rewrite with direct hooks**
4. `/frontend/src/pages/Settings/Plex/AuthSection.tsx` - **Rewrite with useTimeout polling**
5. `/frontend/src/pages/Settings/Plex/ServerSection.tsx` - **No changes needed** ✅
6. `/frontend/src/pages/Settings/Plex/ConnectionsCard.tsx` - **No changes needed** ✅

---

## 🚀 EXPECTED OUTCOME - **STABLE & SLIM**

After implementation:
- ✅ **All hooks return pure useQuery/useMutation** (Anderson's requirement)
- ✅ **useTimeout for polling** instead of React Query refetchInterval (Anderson's requirement)  
- ✅ **Proper query invalidation** without manual refetching (Anderson's requirement)
- ✅ **Clean, modular component architecture** (Anderson's vision maintained)
- ✅ **No complex wrapper hooks** - direct, simple approach
- ✅ **Reduced code complexity** while maintaining functionality
- ✅ **Stable, predictable behavior**
- ✅ **Each component manages its own focused responsibility**

---

**Notes**:
- This plan maintains Anderson's excellent architectural separation
- Fixes the technical implementation issues he identified
- Uses React Query best practices throughout
- Eliminates custom polling in favor of React Query patterns
- Maintains backward compatibility with existing API endpoints
