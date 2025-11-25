# Plex Library Multiselect - Implementation Plan

**Branch:** `feature/plex-library-multiselect`  
**Created:** November 25, 2025  
**Complexity:** Medium (6/10)  
**Estimated Time:** 4-6 hours

## Executive Summary

This implementation adds support for selecting multiple Plex libraries (both movie and series) instead of just one. Currently, users with multiple libraries of the same type (e.g., "Movies", "4K Movies", "Kids Movies") can only select one library, forcing them to choose which content gets subtitle support from Bazarr.

### Current Limitation
Users can only select a single library per type:
- Movie Library: Single selection
- Series Library: Single selection

### Proposed Solution
Allow multiple library selection per type:
- Movie Libraries: Multi-select dropdown
- Series Libraries: Multi-select dropdown

---

## Deep Analysis

### 1. Current Architecture

#### 1.1 Frontend Components
- **Location:** `/workspaces/bazarr/frontend/src/pages/Settings/Plex/LibrarySelector.tsx`
- **Current Implementation:**
  - Uses Mantine's `Select` component (single selection)
  - Type: `BaseInput<string>` (single string value)
  - Setting keys: `settings-plex-movie_library`, `settings-plex-series_library`
  - Value format: String (library name)

#### 1.2 Backend Configuration
- **Location:** `/workspaces/bazarr/bazarr/app/config.py`
- **Current Validators:**
  ```python
  Validator('plex.movie_library', must_exist=True, default='', is_type_of=str)
  Validator('plex.series_library', must_exist=True, default='', is_type_of=str)
  ```
- **Storage Format:** YAML file at `config/config.yaml`
- **Current Values:** Single string per library type

#### 1.3 Plex Operations
- **Location:** `/workspaces/bazarr/bazarr/plex/operations.py`
- **Functions Affected:**
  1. `plex_set_movie_added_date_now()` - Line 98
  2. `plex_set_episode_added_date_now()` - Line 113
  3. `plex_update_library()` - Lines 129-130
  4. `plex_refresh_item()` - Lines 149-150

- **Current Logic:**
  ```python
  library = plex.library.section(settings.plex.movie_library)
  ```
  - Calls PlexAPI's `library.section()` with single library name
  - Expects exactly one library to work with

#### 1.4 Subtitle Processing
- **Location:** `/workspaces/bazarr/bazarr/subtitles/processing.py`
- **Integration Points:**
  - Line 153: `if settings.plex.update_series_library is True:`
  - Line 168: `if settings.plex.update_movie_library is True:`
  - Calls `plex_refresh_item()` for specific items
  - Falls back to `plex_update_library()` if refresh fails

#### 1.5 TypeScript Type Definitions
- **Location:** `/workspaces/bazarr/frontend/src/types/settings.d.ts`
- **Current Types:**
  ```typescript
  interface Plex {
    movie_library?: string;
    series_library?: string;
    // ... other fields
  }
  ```

---

## 2. Implementation Plan

### Phase 1: Backend Configuration Changes

#### 2.1 Update Config Validators
**File:** `/workspaces/bazarr/bazarr/app/config.py`
**Lines:** 247-248

**Changes:**
```python
# OLD:
Validator('plex.movie_library', must_exist=True, default='', is_type_of=str),
Validator('plex.series_library', must_exist=True, default='', is_type_of=str),

# NEW:
Validator('plex.movie_library', must_exist=True, default=[], is_type_of=list),
Validator('plex.series_library', must_exist=True, default=[], is_type_of=list),
```

**Impact:**
- Allows array storage in YAML config
- Maintains backward compatibility with migration (see Phase 2)

---

#### 2.2 Create Migration Function
**File:** `/workspaces/bazarr/bazarr/app/config.py`
**New Function:** `migrate_plex_library_to_list()`

**Purpose:**
Convert existing single-string library values to list format for backward compatibility.

**Implementation:**
```python
def migrate_plex_library_to_list():
    """
    Migrate old single-string Plex library settings to new list format.
    Called during app initialization.
    """
    changed = False
    
    # Migrate movie library
    if isinstance(settings.plex.movie_library, str):
        old_value = settings.plex.movie_library
        if old_value:  # Only migrate if not empty
            settings.plex.movie_library = [old_value]
            logging.info(f"Migrated plex.movie_library from string to list: {old_value}")
            changed = True
        else:
            settings.plex.movie_library = []
            changed = True
    
    # Migrate series library
    if isinstance(settings.plex.series_library, str):
        old_value = settings.plex.series_library
        if old_value:  # Only migrate if not empty
            settings.plex.series_library = [old_value]
            logging.info(f"Migrated plex.series_library from string to list: {old_value}")
            changed = True
        else:
            settings.plex.series_library = []
            changed = True
    
    if changed:
        write_config()
        logging.debug("Plex library migration completed successfully")
```

**Integration Point:**
Add to `/workspaces/bazarr/bazarr/init.py` after line 173:
```python
# Migrate Plex library settings
migrate_plex_library_to_list()
```

---

#### 2.3 Update Plex Operations
**File:** `/workspaces/bazarr/bazarr/plex/operations.py`

**Strategy:**
Loop through all configured libraries to find the item, since we don't know which library contains which content.

##### 2.3.1 Update `plex_set_movie_added_date_now()`
**Current (Line 88-102):**
```python
def plex_set_movie_added_date_now(movie_metadata) -> None:
    try:
        plex = get_plex_server()
        library = plex.library.section(settings.plex.movie_library)
        video = library.getGuid(guid=movie_metadata.imdbId)
        update_added_date(video, datetime.now().strftime(DATETIME_FORMAT))
    except Exception as e:
        logger.error(f"Error in plex_set_movie_added_date_now: {e}")
```

**New Implementation:**
```python
def plex_set_movie_added_date_now(movie_metadata) -> None:
    """
    Update the added date of a movie in Plex to the current datetime.
    Searches across all configured movie libraries.

    :param movie_metadata: Metadata object containing the movie's IMDb ID.
    """
    try:
        plex = get_plex_server()
        movie_libraries = settings.plex.movie_library
        
        # Ensure we have a list
        if not isinstance(movie_libraries, list):
            movie_libraries = [movie_libraries] if movie_libraries else []
        
        if not movie_libraries:
            logger.debug("No movie libraries configured in Plex settings")
            return
        
        # Search through all configured movie libraries
        for library_name in movie_libraries:
            if not library_name:  # Skip empty strings
                continue
                
            try:
                library = plex.library.section(library_name)
                video = library.getGuid(guid=movie_metadata.imdbId)
                update_added_date(video, datetime.now().strftime(DATETIME_FORMAT))
                logger.info(f"Updated added date for movie in library '{library_name}'")
                return  # Success - no need to check other libraries
            except Exception as lib_error:
                # Movie not found in this library, try next one
                logger.debug(f"Movie not found in library '{library_name}': {lib_error}")
                continue
        
        # If we get here, movie wasn't found in any library
        logger.warning(f"Movie with IMDB ID {movie_metadata.imdbId} not found in any configured Plex movie library")
        
    except Exception as e:
        logger.error(f"Error in plex_set_movie_added_date_now: {e}")
```

##### 2.3.2 Update `plex_set_episode_added_date_now()`
**Current (Line 105-118):**
```python
def plex_set_episode_added_date_now(episode_metadata) -> None:
    try:
        plex = get_plex_server()
        library = plex.library.section(settings.plex.series_library)
        show = library.getGuid(episode_metadata.imdbId)
        episode = show.episode(season=episode_metadata.season, episode=episode_metadata.episode)
        update_added_date(episode, datetime.now().strftime(DATETIME_FORMAT))
    except Exception as e:
        logger.error(f"Error in plex_set_episode_added_date_now: {e}")
```

**New Implementation:**
```python
def plex_set_episode_added_date_now(episode_metadata) -> None:
    """
    Update the added date of a TV episode in Plex to the current datetime.
    Searches across all configured series libraries.

    :param episode_metadata: Metadata object containing the episode's IMDb ID, season, and episode number.
    """
    try:
        plex = get_plex_server()
        series_libraries = settings.plex.series_library
        
        # Ensure we have a list
        if not isinstance(series_libraries, list):
            series_libraries = [series_libraries] if series_libraries else []
        
        if not series_libraries:
            logger.debug("No series libraries configured in Plex settings")
            return
        
        # Search through all configured series libraries
        for library_name in series_libraries:
            if not library_name:  # Skip empty strings
                continue
                
            try:
                library = plex.library.section(library_name)
                show = library.getGuid(episode_metadata.imdbId)
                episode = show.episode(season=episode_metadata.season, episode=episode_metadata.episode)
                update_added_date(episode, datetime.now().strftime(DATETIME_FORMAT))
                logger.info(f"Updated added date for episode in library '{library_name}'")
                return  # Success - no need to check other libraries
            except Exception as lib_error:
                # Show not found in this library, try next one
                logger.debug(f"Show not found in library '{library_name}': {lib_error}")
                continue
        
        # If we get here, show wasn't found in any library
        logger.warning(f"Show with IMDB ID {episode_metadata.imdbId} not found in any configured Plex series library")
        
    except Exception as e:
        logger.error(f"Error in plex_set_episode_added_date_now: {e}")
```

##### 2.3.3 Update `plex_update_library()`
**Current (Line 121-134):**
```python
def plex_update_library(is_movie_library: bool) -> None:
    try:
        plex = get_plex_server()
        library_name = settings.plex.movie_library if is_movie_library else settings.plex.series_library
        library = plex.library.section(library_name)
        library.update()
        logger.info(f"Triggered update for library: {library_name}")
    except Exception as e:
        logger.error(f"Error in plex_update_library: {e}")
```

**New Implementation:**
```python
def plex_update_library(is_movie_library: bool) -> None:
    """
    Trigger a library update for the specified library type.
    Updates all configured libraries of the given type.

    :param is_movie_library: True for movie library, False for series library.
    """
    try:
        plex = get_plex_server()
        library_names = settings.plex.movie_library if is_movie_library else settings.plex.series_library
        
        # Ensure we have a list
        if not isinstance(library_names, list):
            library_names = [library_names] if library_names else []
        
        if not library_names:
            library_type = "movie" if is_movie_library else "series"
            logger.debug(f"No {library_type} libraries configured in Plex settings")
            return
        
        # Update all configured libraries
        updated_count = 0
        for library_name in library_names:
            if not library_name:  # Skip empty strings
                continue
                
            try:
                library = plex.library.section(library_name)
                library.update()
                logger.info(f"Triggered update for library: {library_name}")
                updated_count += 1
            except Exception as lib_error:
                logger.error(f"Failed to update library '{library_name}': {lib_error}")
                continue
        
        if updated_count > 0:
            logger.info(f"Successfully triggered update for {updated_count} libraries")
        else:
            logger.warning("Failed to update any Plex libraries")
            
    except Exception as e:
        logger.error(f"Error in plex_update_library: {e}")
```

##### 2.3.4 Update `plex_refresh_item()`
**Current (Line 137-167):**
```python
def plex_refresh_item(imdb_id: str, is_movie: bool, season: int = None, episode: int = None) -> None:
    try:
        plex = get_plex_server()
        library_name = settings.plex.movie_library if is_movie else settings.plex.series_library
        library = plex.library.section(library_name)
        
        if is_movie:
            item = library.getGuid(f"imdb://{imdb_id}")
            item.refresh()
            logger.info(f"Refreshed movie: {item.title} (IMDB: {imdb_id})")
        else:
            show = library.getGuid(f"imdb://{imdb_id}")
            episode_item = show.episode(season=season, episode=episode)
            episode_item.refresh()
            logger.info(f"Refreshed episode: {show.title} S{season:02d}E{episode:02d} (IMDB: {imdb_id})")
            
    except Exception as e:
        logger.warning(f"Failed to refresh specific item (IMDB: {imdb_id}), falling back to library update: {e}")
        plex_update_library(is_movie)
```

**New Implementation:**
```python
def plex_refresh_item(imdb_id: str, is_movie: bool, season: int = None, episode: int = None) -> None:
    """
    Refresh a specific item in Plex instead of scanning the entire library.
    This is much more efficient than a full library scan when subtitles are added.
    Searches across all configured libraries of the appropriate type.

    :param imdb_id: IMDB ID of the content
    :param is_movie: True for movie, False for TV episode
    :param season: Season number for TV episodes
    :param episode: Episode number for TV episodes
    """
    try:
        plex = get_plex_server()
        library_names = settings.plex.movie_library if is_movie else settings.plex.series_library
        
        # Ensure we have a list
        if not isinstance(library_names, list):
            library_names = [library_names] if library_names else []
        
        if not library_names:
            library_type = "movie" if is_movie else "series"
            logger.debug(f"No {library_type} libraries configured in Plex settings")
            return
        
        # Search through all configured libraries
        for library_name in library_names:
            if not library_name:  # Skip empty strings
                continue
                
            try:
                library = plex.library.section(library_name)
                
                if is_movie:
                    # Refresh specific movie
                    item = library.getGuid(f"imdb://{imdb_id}")
                    item.refresh()
                    logger.info(f"Refreshed movie in '{library_name}': {item.title} (IMDB: {imdb_id})")
                    return  # Success - no need to check other libraries
                else:
                    # Refresh specific episode
                    show = library.getGuid(f"imdb://{imdb_id}")
                    episode_item = show.episode(season=season, episode=episode)
                    episode_item.refresh()
                    logger.info(f"Refreshed episode in '{library_name}': {show.title} S{season:02d}E{episode:02d} (IMDB: {imdb_id})")
                    return  # Success - no need to check other libraries
                    
            except Exception as lib_error:
                # Item not found in this library, try next one
                logger.debug(f"Item not found in library '{library_name}': {lib_error}")
                continue
        
        # If we get here, item wasn't found in any library - fall back to full update
        logger.warning(f"Item (IMDB: {imdb_id}) not found in any configured library, falling back to library update")
        plex_update_library(is_movie)
            
    except Exception as e:
        logger.warning(f"Failed to refresh specific item (IMDB: {imdb_id}), falling back to library update: {e}")
        # Fallback to full library update if specific refresh fails
        plex_update_library(is_movie)
```

---

### Phase 2: Frontend Changes

#### 2.4 Update TypeScript Type Definitions
**File:** `/workspaces/bazarr/frontend/src/types/settings.d.ts`
**Lines:** 206-207

**Changes:**
```typescript
// OLD:
interface Plex {
  movie_library?: string;
  series_library?: string;
  // ... other fields
}

// NEW:
interface Plex {
  movie_library?: string[];
  series_library?: string[];
  // ... other fields
}
```

---

#### 2.5 Update LibrarySelector Component
**File:** `/workspaces/bazarr/frontend/src/pages/Settings/Plex/LibrarySelector.tsx`

**Key Changes:**

1. **Import MultiSelect instead of Select:**
```typescript
import { Alert, MultiSelect, Stack, Text } from "@mantine/core";
```

2. **Update Props Type:**
```typescript
export type LibrarySelectorProps = BaseInput<string[]> & {
  label: string;
  libraryType: "movie" | "show";
  placeholder?: string;
  description?: string;
};
```

3. **Update Component Logic:**
```typescript
const LibrarySelector: FunctionComponent<LibrarySelectorProps> = (props) => {
  const { libraryType, placeholder, description, label, ...baseProps } = props;
  const { value, update, rest } = useBaseInput(baseProps);

  // ... authentication and data fetching logic remains the same ...

  // Filter libraries by type
  const filtered = libraries.filter((library) => library.type === libraryType);

  const selectData = filtered.map((library) => ({
    value: library.title,
    label: `${library.title} (${library.count} items)`,
  }));

  // ... error states remain the same ...

  return (
    <div className={styles.librarySelector}>
      <MultiSelect
        {...rest}
        label={label}
        placeholder={placeholder || `Select ${libraryType} libraries...`}
        data={selectData}
        description={description}
        value={value || []}
        onChange={(newValue) => {
          // MultiSelect always returns an array
          update(newValue);
        }}
        searchable
        clearable
        className={styles.selectField}
      />
    </div>
  );
};
```

**Full Updated Component:**
```typescript
import { FunctionComponent } from "react";
import { Alert, MultiSelect, Stack, Text } from "@mantine/core";
import {
  usePlexAuthValidationQuery,
  usePlexLibrariesQuery,
} from "@/apis/hooks/plex";
import { BaseInput, useBaseInput } from "@/pages/Settings/utilities/hooks";
import styles from "@/pages/Settings/Plex/LibrarySelector.module.scss";

export type LibrarySelectorProps = BaseInput<string[]> & {
  label: string;
  libraryType: "movie" | "show";
  placeholder?: string;
  description?: string;
};

const LibrarySelector: FunctionComponent<LibrarySelectorProps> = (props) => {
  const { libraryType, placeholder, description, label, ...baseProps } = props;
  const { value, update, rest } = useBaseInput(baseProps);

  // Check if user is authenticated with OAuth
  const { data: authData } = usePlexAuthValidationQuery();
  const isAuthenticated = Boolean(
    authData?.valid && authData?.auth_method === "oauth",
  );

  // Fetch libraries if authenticated
  const {
    data: libraries = [],
    isLoading,
    error,
  } = usePlexLibrariesQuery({
    enabled: isAuthenticated,
  });

  // Filter libraries by type
  const filtered = libraries.filter((library) => library.type === libraryType);

  const selectData = filtered.map((library) => ({
    value: library.title,
    label: `${library.title} (${library.count} items)`,
  }));

  if (!isAuthenticated) {
    return (
      <Stack gap="xs" className={styles.librarySelector}>
        <Text fw={500} className={styles.labelText}>
          {label}
        </Text>
        <Alert color="brand" variant="light" className={styles.alertMessage}>
          Enable Plex OAuth above to automatically discover your libraries.
        </Alert>
      </Stack>
    );
  }

  if (isLoading) {
    return (
      <Stack gap="xs" className={styles.librarySelector}>
        <MultiSelect
          {...rest}
          label={label}
          placeholder="Loading libraries..."
          data={[]}
          disabled
          className={styles.loadingField}
        />
      </Stack>
    );
  }

  if (error) {
    return (
      <Stack gap="xs" className={styles.librarySelector}>
        <Alert color="red" variant="light" className={styles.alertMessage}>
          Failed to load libraries:{" "}
          {(error as Error)?.message || "Unknown error"}
        </Alert>
      </Stack>
    );
  }

  if (selectData.length === 0) {
    return (
      <Stack gap="xs" className={styles.librarySelector}>
        <Alert color="gray" variant="light" className={styles.alertMessage}>
          No {libraryType} libraries found on your Plex server.
        </Alert>
      </Stack>
    );
  }

  return (
    <div className={styles.librarySelector}>
      <MultiSelect
        {...rest}
        label={label}
        placeholder={placeholder || `Select ${libraryType} libraries...`}
        data={selectData}
        description={description}
        value={value || []}
        onChange={(newValue) => {
          update(newValue);
        }}
        searchable
        clearable
        className={styles.selectField}
      />
    </div>
  );
};

export default LibrarySelector;
```

---

### Phase 3: Testing Plan

#### 3.1 Unit Tests (Backend)

**Test File:** `tests/test_plex_operations.py` (create if doesn't exist)

**Test Cases:**
1. **Migration Tests:**
   - Test string-to-list migration for movie library
   - Test string-to-list migration for series library
   - Test empty string migration
   - Test already-list values (no migration needed)

2. **Plex Operations Tests:**
   - Test `plex_set_movie_added_date_now()` with multiple libraries
   - Test `plex_set_episode_added_date_now()` with multiple libraries
   - Test `plex_update_library()` with multiple libraries
   - Test `plex_refresh_item()` with multiple libraries
   - Test fallback behavior when item not in any library
   - Test behavior with empty library list

#### 3.2 Integration Tests

**Test Scenarios:**
1. **New Installation:**
   - Fresh config with empty lists
   - Add single library via UI
   - Add multiple libraries via UI

2. **Migration from Old Version:**
   - Config with single string value
   - Verify migration to list on startup
   - Verify UI shows migrated value correctly

3. **Multiple Libraries:**
   - Configure 2-3 movie libraries
   - Configure 2-3 series libraries
   - Download subtitles for content in different libraries
   - Verify Plex operations work correctly

#### 3.3 Manual Testing Checklist

- [ ] Fresh installation - UI allows selecting multiple libraries
- [ ] Migration - Single library converts to array on upgrade
- [ ] UI displays selected libraries correctly
- [ ] Can add/remove libraries from selection
- [ ] Subtitle download triggers correct Plex refresh
- [ ] Item found in first library - subsequent libraries not checked
- [ ] Item found in second/third library - all libraries checked
- [ ] Item not found in any library - graceful error handling
- [ ] Settings persist after restart
- [ ] YAML config file format is correct

---

### Phase 4: Documentation Updates

#### 4.1 User-Facing Documentation
**Location:** Wiki or README

**Content:**
- Explain multiselect feature
- Show screenshots of new UI
- Explain how Bazarr searches across libraries
- Performance considerations (more libraries = more API calls)

#### 4.2 Developer Documentation
**Location:** Code comments

**Content:**
- Document migration function
- Document search strategy in operations
- Document fallback behavior

---

## Implementation Order

**CRITICAL:** Before making ANY edits, use `manage_todo_list` tool to create task tracking for all steps below.

### Step 1: Backend Foundation (1-2 hours)
1. **Read whole file:** `/workspaces/bazarr/bazarr/app/config.py` (entire file, not just lines 247-248)
2. Update config validators in `config.py`
3. Create and integrate migration function
4. **Read whole file:** `/workspaces/bazarr/bazarr/init.py` (entire file, not just line 173)
5. Integrate migration call in `init.py`
6. Test migration with existing config

### Step 2: Backend Operations (1.5-2 hours)
1. **Read whole file:** `/workspaces/bazarr/bazarr/plex/operations.py` (entire file, not specific line ranges)
2. Update `plex_set_movie_added_date_now()`
3. Update `plex_set_episode_added_date_now()`
4. Update `plex_update_library()`
5. Update `plex_refresh_item()`
6. Add comprehensive logging
7. Test with mock Plex server

### Step 3: Frontend Implementation (1-1.5 hours)
1. **Read whole file:** `/workspaces/bazarr/frontend/src/types/settings.d.ts` (entire file, not just lines 206-207)
2. Update TypeScript types
3. **Read whole file:** `/workspaces/bazarr/frontend/src/pages/Settings/Plex/LibrarySelector.tsx` (entire file)
4. Update LibrarySelector component (MultiSelect, type changes)
5. Test UI interactions
6. Verify data flow to backend

### Step 4: Testing & Refinement (1-1.5 hours)
1. Manual testing with real Plex server
2. Test migration scenarios
3. Test edge cases (empty lists, single library, many libraries)
4. Performance testing with multiple libraries
5. **Mark all TODOs as completed** using `manage_todo_list`

---

## Potential Issues & Solutions

### Issue 1: Performance Impact
**Problem:** Searching through multiple libraries for each operation could be slow.

**Solutions:**
- Libraries are searched sequentially; operation stops at first match
- Refresh operations are already more efficient than full library scans
- Most users will have 2-3 libraries max, not a significant impact

### Issue 2: Configuration Complexity
**Problem:** Users might not understand which libraries to select.

**Solutions:**
- Clear UI labels and descriptions
- Placeholder text: "Select one or more libraries..."
- Help text: "Select all libraries where you want Bazarr to manage subtitles"

### Issue 3: Migration Edge Cases
**Problem:** Unexpected config formats from manual edits.

**Solutions:**
- Defensive type checking: `isinstance(value, list)`
- Handle None, empty string, and malformed values
- Log migration actions for debugging

### Issue 4: Backward Compatibility
**Problem:** Old API clients or scripts expecting string values.

**Solutions:**
- Migration handles conversion automatically
- Backend always normalizes to list internally
- Frontend uses BaseInput which handles type properly

---

## Rollback Plan

If issues arise after deployment:

1. **Quick Fix:** Revert frontend to single Select
   - Changes only in `LibrarySelector.tsx`
   - Users can still only select one, but lists work

2. **Full Rollback:**
   - Revert all changes
   - Create reverse migration (list → first item or empty string)
   - Config validator back to `is_type_of=str`

---

## Success Criteria

✅ **Functional Requirements:**
- Users can select multiple movie libraries
- Users can select multiple series libraries
- Subtitle operations work across all selected libraries
- Settings persist correctly
- Migration from old format works seamlessly

✅ **Performance Requirements:**
- No significant slowdown in subtitle operations
- UI remains responsive with multiple selections
- Plex API calls are efficient (stop at first match)

✅ **Quality Requirements:**
- No regression in existing single-library functionality
- Comprehensive error handling and logging
- Clean, maintainable code
- Type-safe frontend implementation

---

## Files Modified Summary

### Backend (Python)
1. `/workspaces/bazarr/bazarr/app/config.py` - Validators + Migration
2. `/workspaces/bazarr/bazarr/plex/operations.py` - All 4 functions
3. `/workspaces/bazarr/bazarr/init.py` - Migration call

### Frontend (TypeScript/TSX)
1. `/workspaces/bazarr/frontend/src/types/settings.d.ts` - Type definitions
2. `/workspaces/bazarr/frontend/src/pages/Settings/Plex/LibrarySelector.tsx` - Component update

### Total Files: 5

---

## Dependencies

### Required:
- Mantine UI `MultiSelect` component (already in project)
- PlexAPI library (already in project)
- Existing BaseInput hook system (already in project)

### No New Dependencies Required ✅

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|------------|---------|------------|
| Migration fails for some users | Low | High | Extensive testing, defensive coding, rollback plan |
| Performance degradation | Low | Medium | Sequential search, stop at first match |
| UI/UX confusion | Medium | Low | Clear labels, help text, placeholder |
| Plex API rate limiting | Low | Low | Already an issue with single library |
| Config corruption | Very Low | High | Atomic writes, backup on migration |

---

## Timeline

**Total Estimated Time:** 4-6 hours

- **Day 1 (2-3 hours):** Backend implementation + migration
- **Day 2 (1-2 hours):** Frontend implementation
- **Day 3 (1 hour):** Testing + refinement
- **Day 4:** Documentation + deployment prep

---

## Coding Standards Compliance

This implementation adheres to the project's coding standards:

1. ✅ **Rule 1 (Super Clean Code):** All implementations use idiomatic patterns, proper typing, comprehensive error handling
2. ✅ **Rule 2 (Cleanup Code):** No dead code, unused imports, or commented code
3. ✅ **Rule 3 (Read Whole Files):** Implementation order specifies reading ENTIRE files before any edits
4. ✅ **Rule 4 (No New useEffect/useCallback):** Uses existing `useBaseInput` hook (grandfathered), creates no NEW hook violations
5. ✅ **Rule 5 (Ask Then Do):** This plan created and presented before implementation
6. ✅ **Rule 6 (TODO Tracking):** Implementation order requires `manage_todo_list` tool usage from start to finish

**Note on Rule 4:** The `useBaseInput` hook (from `frontend/src/pages/Settings/utilities/hooks.ts`) uses `useCallback`, `useMemo`, and `useRef`. This is existing infrastructure used throughout all Settings pages. We will use this existing hook but will NOT create any new `useEffect` or `useCallback` hooks in our implementation.

---

## Conclusion

This implementation is well-scoped and achievable with moderate complexity. The main challenges are:

1. Ensuring robust migration from string to list format
2. Implementing efficient multi-library search in operations
3. Maintaining backward compatibility

The solution provides significant value to users with multiple Plex libraries while maintaining clean architecture and minimal performance impact.

**Recommendation:** Proceed with implementation. The benefits outweigh the complexity, and the risk is low with proper testing and migration handling.
