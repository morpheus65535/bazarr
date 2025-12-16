# Plex Unique Instance Identification - Complete Implementation Plan

**Date:** December 16, 2025  
**Author:** GitHub Copilot Analysis  
**Related Commit:** https://github.com/morpheus65535/bazarr/commit/70abad4f07faa5cb98dcc9478163239b61c33291  
**Last Updated:** December 16, 2025

---

## Executive Summary

This plan provides a **complete solution** for unique Plex instance identification in multi-Bazarr setups.

### What Already Exists (Leveraged)

| Component | Config Key | Status |
|-----------|------------|--------|
| Instance Name | `general.instance_name` | ✅ Already exists (commit 70abad4f) |
| Server Machine ID | `plex.server_machine_id` | ✅ Already stored when server selected |
| Library Names | `plex.movie_library`, `plex.series_library` | ✅ Already stored (titles only) |
| Library API returns `key` | PlexLibraries endpoint | ✅ Returns section ID, but not stored |

### What We Need to Add

| Phase | Change | Priority | Lines |
|-------|--------|----------|-------|
| **0** | Add `instance` param to webhook URL | CRITICAL | ~5 |
| **1** | Persistent client identifier for Plex | HIGH | ~15 |
| **2** | Store library IDs + webhook filtering | HIGH | ~60 |
| **3** | Frontend UI to show instance info | MEDIUM | ~40 |
| **4** | Enhanced logging | LOW | ~10 |

**Total: ~130 lines of code**

---

## The Problem

User has 4 Bazarr instances for different libraries on the same Plex server. Currently:
1. All webhooks look identical in Plex: `https://bazarr.local/api/webhooks/plex?apikey=xxx`
2. ALL instances process ALL webhook events (wasted processing)
3. All instances appear as "Bazarr" / "Bazarr Web" in Plex device list
4. No way to identify which Bazarr instance is which in the UI

---

## Phase 0: Instance-Identified Webhook URLs (CRITICAL)

**Goal**: Each webhook URL includes the instance name for easy identification.

### 0.1 Modify Webhook Creation

**File:** `bazarr/api/plex/oauth.py` (PlexWebhookCreate.post, ~line 859)

```python
# Add import at top
from urllib.parse import quote_plus

# In PlexWebhookCreate.post(), modify webhook URL creation:

# Get instance name for webhook identification
instance_name = settings.general.get('instance_name', 'Bazarr')
instance_param = quote_plus(instance_name)

if configured_base_url:
    webhook_url = f"{configured_base_url}/api/webhooks/plex?apikey={apikey}&instance={instance_param}"
    logger.info(f"Using configured base URL for webhook: {configured_base_url}/api/webhooks/plex (instance: {instance_name})")
else:
    scheme = 'https' if request.is_secure else 'http'
    host = request.host
    webhook_url = f"{scheme}://{host}/api/webhooks/plex?apikey={apikey}&instance={instance_param}"
    logger.info(f"Using request host for webhook: {scheme}://{host}/api/webhooks/plex (instance: {instance_name})")
```

**Result in Plex:**
```
https://bazarr1.local/api/webhooks/plex?apikey=xxx&instance=Bazarr-4K-Movies
https://bazarr2.local/api/webhooks/plex?apikey=xxx&instance=Bazarr-4K-TV
```

### 0.2 Files to Modify

| File | Change |
|------|--------|
| `bazarr/api/plex/oauth.py` | Add `instance` query parameter to webhook URL |

---

## Phase 1: Persistent Client Identifier & Device Name (HIGH)

**Goal**: Each Bazarr instance appears with a unique, persistent identity in Plex.

### 1.1 Add Config Validator

**File:** `bazarr/app/config.py` (after line ~262)

```python
Validator('plex.client_identifier', must_exist=True, default='', is_type_of=str),
```

### 1.2 Create Persistent Client ID Function

**File:** `bazarr/api/plex/oauth.py` (add new function near top)

```python
def get_or_create_client_identifier():
    """Get existing client identifier or create and persist a new one."""
    client_id = settings.plex.get('client_identifier', '')
    if not client_id:
        client_id = str(uuid.uuid4())
        settings.plex.client_identifier = client_id
        write_config()
        logger.info(f"Generated new persistent Plex client identifier: {client_id[:8]}...")
    return client_id
```

### 1.3 Use Instance Name + Version in Plex Headers

**File:** `bazarr/api/plex/oauth.py` (PlexPin.post, ~line 215-228)

```python
import os

def post(self):
    try:
        args = self.post_request_parser.parse_args()
        
        # Use persistent client identifier
        client_id = get_or_create_client_identifier()
        
        # Get instance name and version for device identification
        instance_name = settings.general.get('instance_name', 'Bazarr')
        bazarr_version = os.environ.get('BAZARR_VERSION', 'unknown')
        
        state_token = get_token_manager().generate_state_token()

        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'X-Plex-Product': 'Bazarr',
            'X-Plex-Version': bazarr_version,  # ← USE ACTUAL VERSION
            'X-Plex-Client-Identifier': client_id,
            'X-Plex-Platform': 'Web',
            'X-Plex-Platform-Version': '1.0',
            'X-Plex-Device': 'Bazarr',
            'X-Plex-Device-Name': instance_name  # ← USE INSTANCE NAME
        }
```

**Result in Plex devices:** Shows "Bazarr-4K-Movies" with version "1.4.5" instead of "1.0"

### 1.4 Update Auth URL

**File:** `bazarr/api/plex/oauth.py` (~line 253)

```python
# Include instance name in auth URL for Plex device display
from urllib.parse import quote_plus
instance_name_encoded = quote_plus(instance_name)

return {
    'data': {
        'pinId': pin_data['id'],
        'code': pin_data['code'],
        'clientId': client_id,
        'state': state_token,
        'authUrl': f"https://app.plex.tv/auth#?clientID={client_id}&code={pin_data['code']}&context[device][product]=Bazarr&context[device][deviceName]={instance_name_encoded}"
    }
}
```

### 1.5 Files to Modify

| File | Change |
|------|--------|
| `bazarr/app/config.py` | Add `plex.client_identifier` validator |
| `bazarr/api/plex/oauth.py` | Add `get_or_create_client_identifier()`, use in headers and auth URL |

---

## Phase 2: Library ID Storage & Webhook Filtering (HIGH)

**Goal**: Filter webhooks by server UUID AND library section ID (100% reliable).

### 2.1 Add Library ID Config Validators

**File:** `bazarr/app/config.py` (after line ~250)

```python
Validator('plex.movie_library_ids', must_exist=True, default=[], is_type_of=list),
Validator('plex.series_library_ids', must_exist=True, default=[], is_type_of=list),
```

### 2.2 Store Library IDs When Selected (Frontend Change)

**File:** `frontend/src/pages/Settings/Plex/LibrarySelector.tsx`

The frontend already has access to `library.key` (section ID) but only stores `library.title`. 
We add a parallel settings key to store IDs alongside names.

```tsx
// Add new prop for the IDs setting key
export type LibrarySelectorProps = BaseInput<string[]> & {
  label: string;
  libraryType: "movie" | "show";
  settingKeyIds: string;  // NEW: e.g., "settings-plex-movie_library_ids"
  description?: string;
};

// Inside component, get the IDs updater
const { value: idsValue, update: updateIds } = useBaseInput({ 
  settingKey: settingKeyIds 
});

// Modify the onChange to update BOTH settings simultaneously
const handleChange = (selectedTitles: string[]) => {
  update(selectedTitles);  // movie_library: ["4K Movies", "Movies"]
  
  // Also update the IDs array
  const selectedIds = filtered
    .filter(lib => selectedTitles.includes(lib.title))
    .map(lib => lib.key);
  updateIds(selectedIds);  // movie_library_ids: ["1", "3"]
};
```

**File:** `frontend/src/pages/Settings/Plex/index.tsx`

```tsx
// Add the IDs setting key prop
<LibrarySelector
  settingKey="settings-plex-movie_library"
  settingKeyIds="settings-plex-movie_library_ids"  // NEW
  label="Movie Libraries"
  libraryType="movie"
/>

<LibrarySelector
  settingKey="settings-plex-series_library"
  settingKeyIds="settings-plex-series_library_ids"  // NEW
  label="Series Libraries"
  libraryType="show"
/>
```

**Why this approach:**
- ✅ No new backend endpoint needed (removed `/plex/sync-library-ids`)
- ✅ IDs stored at selection time = always in sync
- ✅ Leverages existing `library.key` already returned by API
- ✅ Minimal code change (~15 lines)

### 2.3 Webhook Filtering with Server UUID + Library ID

**File:** `bazarr/api/webhooks/plex.py`

Add filtering methods and call them in `post()`:

```python
from app.config import settings

@api_ns_webhooks_plex.route('webhooks/plex')
class WebHooksPlex(Resource):
    post_request_parser = reqparse.RequestParser()
    post_request_parser.add_argument('payload', type=str, required=True, help='Webhook payload')

    @authenticate
    @api_ns_webhooks_plex.doc(parser=post_request_parser)
    def post(self):
        """Trigger subtitles search on play media event in Plex"""
        try:
            args = self.post_request_parser.parse_args()
            json_webhook = args.get('payload')
            
            if not json_webhook:
                logger.debug('PLEX WEBHOOK: No payload received')
                return "No payload found in request", 400
            
            parsed_json_webhook = json.loads(json_webhook)
            instance_name = settings.general.get('instance_name', 'Bazarr')
            
            # Validate event type
            if 'event' not in parsed_json_webhook:
                logger.debug(f'PLEX WEBHOOK [{instance_name}]: Invalid payload - missing "event" field')
                return "Invalid webhook payload - missing event field", 400
            
            event = parsed_json_webhook['event']
            
            if event not in ['media.play', 'playback.started']:
                logger.debug(f'PLEX WEBHOOK [{instance_name}]: Ignoring unhandled event "{event}"')
                return 'Unhandled event', 204
            
            # NEW: Filter by server UUID
            if not self._is_relevant_server(parsed_json_webhook):
                return 'Event from different Plex server, skipping', 204
            
            # NEW: Filter by library ID/name
            if not self._is_relevant_library(parsed_json_webhook):
                return 'Event for different library, skipping', 204
            
            # ... rest of existing processing (Metadata check, GUID extraction, etc.) ...
    
    def _is_relevant_server(self, payload):
        """Check if webhook is from our configured Plex server."""
        instance_name = settings.general.get('instance_name', 'Bazarr')
        
        server_uuid = payload.get('Server', {}).get('uuid', '')
        configured_server = settings.plex.get('server_machine_id', '')
        
        if not configured_server:
            # No server configured, process all (backward compatible)
            logger.debug(f'PLEX WEBHOOK [{instance_name}]: No server configured, processing all')
            return True
        
        if not server_uuid:
            # Can't determine server from payload, process anyway
            logger.debug(f'PLEX WEBHOOK [{instance_name}]: No server UUID in payload, processing')
            return True
        
        if server_uuid == configured_server:
            logger.debug(f'PLEX WEBHOOK [{instance_name}]: Server UUID matches ({server_uuid[:8]}...)')
            return True
        
        logger.debug(f'PLEX WEBHOOK [{instance_name}]: Server UUID mismatch '
                    f'(got {server_uuid[:8]}..., expected {configured_server[:8]}...), skipping')
        return False
    
    def _is_relevant_library(self, payload):
        """Check if webhook is for a library this instance manages."""
        instance_name = settings.general.get('instance_name', 'Bazarr')
        
        metadata = payload.get('Metadata', {})
        library_section_id = metadata.get('librarySectionID')
        library_section_title = metadata.get('librarySectionTitle', '')
        media_type = metadata.get('type', '')
        
        # Determine which library config to check
        if media_type == 'episode':
            configured_lib_ids = settings.plex.get('series_library_ids', [])
            configured_lib_names = settings.plex.get('series_library', [])
        else:
            configured_lib_ids = settings.plex.get('movie_library_ids', [])
            configured_lib_names = settings.plex.get('movie_library', [])
        
        # Normalize to lists
        if isinstance(configured_lib_ids, str):
            configured_lib_ids = [configured_lib_ids] if configured_lib_ids else []
        if isinstance(configured_lib_names, str):
            configured_lib_names = [configured_lib_names] if configured_lib_names else []
        
        # If no libraries configured, process all (backward compatible)
        if not configured_lib_ids and not configured_lib_names:
            logger.debug(f'PLEX WEBHOOK [{instance_name}]: No libraries configured, processing all')
            return True
        
        # Check by ID first (100% reliable)
        if configured_lib_ids and library_section_id:
            if str(library_section_id) in [str(lid) for lid in configured_lib_ids]:
                logger.debug(f'PLEX WEBHOOK [{instance_name}]: Library ID {library_section_id} matches')
                return True
        
        # Fallback to name matching
        if configured_lib_names and library_section_title:
            if library_section_title in configured_lib_names:
                logger.debug(f'PLEX WEBHOOK [{instance_name}]: Library name "{library_section_title}" matches')
                return True
        
        logger.debug(f'PLEX WEBHOOK [{instance_name}]: Library "{library_section_title}" '
                    f'(ID: {library_section_id}) not configured, skipping')
        return False
```

### 2.4 Files to Modify

| File | Change |
|------|--------|
| `bazarr/app/config.py` | Add `plex.movie_library_ids`, `plex.series_library_ids` validators |
| `frontend/src/pages/Settings/Plex/LibrarySelector.tsx` | Store library IDs alongside names |
| `frontend/src/pages/Settings/Plex/index.tsx` | Add `settingKeyIds` prop to LibrarySelector |
| `bazarr/api/webhooks/plex.py` | Add `_is_for_this_instance()` filtering method |

---

## Phase 3: Frontend UI to Show Instance Info (MEDIUM)

**Goal**: Users can see their Plex instance identifier in the Bazarr UI.

### 3.1 New Backend Endpoint

**File:** `bazarr/api/plex/oauth.py`

```python
@api_ns_plex.route('plex/instance-info')
class PlexInstanceInfo(Resource):
    def get(self):
        """Get instance identification information for Plex."""
        try:
            client_id = get_or_create_client_identifier()
            instance_name = settings.general.get('instance_name', 'Bazarr')
            server_machine_id = settings.plex.get('server_machine_id', '')
            
            return {
                'data': {
                    'client_identifier': client_id,
                    'client_identifier_short': f"{client_id[:8]}..." if client_id else '',
                    'instance_name': instance_name,
                    'server_machine_id': server_machine_id,
                    'server_machine_id_short': f"{server_machine_id[:8]}..." if server_machine_id else ''
                }
            }
        except Exception as e:
            logger.error(f"Failed to get instance info: {e}")
            return {'error': 'Failed to get instance info'}, 500
```

### 3.2 Frontend API Method

**File:** `frontend/src/apis/raw/plex.ts`

```typescript
async instanceInfo(): Promise<Plex.InstanceInfo> {
  const response = await this.get<DataWrapper<Plex.InstanceInfo>>("/instance-info");
  return response.data;
}
```

### 3.3 Frontend Hook

**File:** `frontend/src/apis/hooks/plex.ts`

```typescript
export const usePlexInstanceInfoQuery = () => {
  return useQuery({
    queryKey: [QueryKeys.Plex, "instanceInfo"],
    queryFn: () => api.plex.instanceInfo(),
    staleTime: 1000 * 60 * 30, // 30 minutes - rarely changes
  });
};
```

### 3.4 TypeScript Types

**File:** `frontend/src/types/api.d.ts` (inside `namespace Plex`)

```typescript
interface InstanceInfo {
  client_identifier: string;
  client_identifier_short: string;
  instance_name: string;
  server_machine_id: string;
  server_machine_id_short: string;
}
```

### 3.5 UI Component

**File:** `frontend/src/pages/Settings/Plex/ServerSection.tsx`

Add instance info display:

```tsx
import { usePlexInstanceInfoQuery } from "@/apis/hooks/plex";

// Inside component:
const { data: instanceInfo } = usePlexInstanceInfoQuery();

// In the render, after server name/badge:
{instanceInfo && (
  <Group gap="xs" mt="xs">
    <Text size="xs" c="dimmed">
      Instance: {instanceInfo.instance_name}
    </Text>
    <Text size="xs" c="dimmed">
      Client ID: {instanceInfo.client_identifier_short}
    </Text>
  </Group>
)}
```

### 3.6 Expected UI

```
┌─────────────────────────────────────────────────────────┐
│ Plex Servers                                            │
│                                                         │
│ qbit (Linux - v1.42.2.10156-f737b826c)  [CONNECTED]    │
│ Instance: Bazarr-4K-Movies | Client ID: a1b2c3d4...    │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 3.7 Files to Modify

| File | Change |
|------|--------|
| `bazarr/api/plex/oauth.py` | Add `/plex/instance-info` endpoint |
| `frontend/src/apis/raw/plex.ts` | Add `instanceInfo()` method |
| `frontend/src/apis/hooks/plex.ts` | Add `usePlexInstanceInfoQuery` hook |
| `frontend/src/types/api.d.ts` | Add `Plex.InstanceInfo` interface |
| `frontend/src/pages/Settings/Plex/ServerSection.tsx` | Display instance info |

---

## Phase 4: Enhanced Logging (LOW)

**Goal**: Clear logging for debugging multi-instance setups.

Already incorporated into Phase 2 filtering methods. Each log line includes `[instance_name]` prefix.

---

## Files Summary

| File | Phase | Changes |
|------|-------|---------|
| `bazarr/app/config.py` | 1, 2 | Add `plex.client_identifier`, `plex.movie_library_ids`, `plex.series_library_ids` validators |
| `bazarr/api/plex/oauth.py` | 0, 1, 3 | Add instance to webhook URL, `get_or_create_client_identifier()`, instance name + version in headers, `/plex/instance-info` endpoint |
| `bazarr/api/webhooks/plex.py` | 2 | Add `_is_for_this_instance()` filtering method |
| `frontend/src/pages/Settings/Plex/LibrarySelector.tsx` | 2 | Store library IDs alongside names |
| `frontend/src/pages/Settings/Plex/index.tsx` | 2 | Add `settingKeyIds` prop |
| `frontend/src/apis/raw/plex.ts` | 3 | Add `instanceInfo()` method |
| `frontend/src/apis/hooks/plex.ts` | 3 | Add `usePlexInstanceInfoQuery` hook |
| `frontend/src/types/api.d.ts` | 3 | Add `Plex.InstanceInfo` interface |
| `frontend/src/pages/Settings/Plex/ServerSection.tsx` | 3 | Display instance info |

---

## Migration & Compatibility

### For Existing Users

1. **Webhook URLs**: Re-create webhooks to get instance-identified URLs
2. **Client Identifier**: Generated automatically on first OAuth action
3. **Library IDs**: Re-select libraries in settings to populate IDs (or IDs default to empty = fallback to name matching)
4. **No Breaking Changes**: All changes are backward compatible with sensible defaults

### Re-authentication Note

> **After changing your Instance Name in General Settings:**
> 1. Re-authenticate with Plex to update how this instance appears in Plex devices
> 2. Delete old webhook and create a new one to get the instance-identified URL

### Backward Compatibility

- If no `client_identifier` → generates new one
- If no `library_ids` → falls back to name matching
- If no `server_machine_id` → processes all servers
- Old webhooks (without `instance` param) continue to work

---

## Testing Checklist

- [ ] Webhook URL includes `&instance=NAME`
- [ ] Instance name appears in Plex device list after OAuth
- [ ] Persistent client ID survives Bazarr restart
- [ ] Library IDs are synced when libraries are selected
- [ ] Webhook from wrong server → 204 response
- [ ] Webhook from wrong library (by ID) → 204 response
- [ ] Webhook from correct server + library → 200 response
- [ ] Instance info displayed in Plex settings UI
- [ ] Logs include instance name prefix

---

## Summary

This implementation provides **complete** unique Plex instance identification:

1. **Phase 0 (CRITICAL)**: Instance name in webhook URLs - users can identify webhooks
2. **Phase 1 (HIGH)**: Persistent client ID + instance name + Bazarr version in Plex headers
3. **Phase 2 (HIGH)**: Library ID storage + server/library webhook filtering (100% reliable)
4. **Phase 3 (MEDIUM)**: Frontend UI showing instance info
5. **Phase 4 (LOW)**: Enhanced logging with instance context

Total: ~130 lines of well-crafted, impactful code.
