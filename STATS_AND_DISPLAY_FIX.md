# Stats Bar & Action Display Fix ✅

## Problems Identified

1. **Stats Bar showing zeros** - Stats endpoint wasn't counting actions correctly
2. **"Unknown Agent" in Action Feed** - Agent names not being included in broadcasts
3. **"Type: UNKNOWN"** - Action types not accessible at top level

## Fixes Applied

### 1. Enhanced Stats Endpoint
**File:** `app/main.py` - `/api/stats` endpoint

**Changes:**
- Uses `approval_manager.get_all_pending_actions()` for accurate pending count
- Better field checking for execution types
- Handles multiple possible field names:
  - `execution_type == "AUTONOMOUS"` OR `status == "EXECUTED"` with `execution_type == "AUTONOMOUS"`
  - `execution_type == "APPROVED"` OR `status == "APPROVED"` OR `approved_by` is not None
  - `execution_type == "REJECTED"` OR `status == "REJECTED"` OR `rejected_by` is not None
- Error handling with fallback values
- Logging for debugging

**Before:**
```python
stats = {
    "total_actions": len(history),
    "autonomous_actions": sum(1 for a in history if a.get("execution_type") == "AUTONOMOUS"),
    ...
}
```

**After:**
```python
pending = approval_manager.get_all_pending_actions()
stats = {
    "total_actions": len(history),
    "autonomous_actions": sum(
        1 for a in history 
        if a.get("execution_type") == "AUTONOMOUS" or 
           (a.get("status") == "EXECUTED" and a.get("execution_type") == "AUTONOMOUS")
    ),
    "pending_actions": len(pending),  # More reliable
    ...
}
```

### 2. Fixed Monitoring Service Redis Serialization
**File:** `app/core/monitoring.py` - `broadcast_action()` method

**Changes:**
- Ensures agent name is always present (defaults to "Unknown Agent")
- Copies action type to top level for easier access
- Properly serializes complex objects (dicts, lists) to JSON strings for Redis
- Deserializes when reading from Redis
- Keeps original structure in memory for WebSocket broadcasts

**Key improvements:**
```python
# Ensure agent name is present
if "agent" not in action_data:
    action_data["agent"] = "Unknown Agent"

# Ensure action type is accessible at top level
if "action" in action_data and isinstance(action_data["action"], dict):
    if "type" in action_data["action"] and "type" not in action_data:
        action_data["type"] = action_data["action"]["type"]

# Serialize for Redis
redis_data = {}
for key, value in action_data.items():
    if isinstance(value, (dict, list)):
        redis_data[key] = json.dumps(value, default=str)
    else:
        redis_data[key] = str(value) if value is not None else ""
```

### 3. Enhanced Action History Retrieval
**File:** `app/core/monitoring.py` - `get_recent_history()` method

**Changes:**
- Deserializes JSON strings when reading from Redis
- Handles both serialized and non-serialized data
- Returns proper list structure

### 4. Updated Frontend ActionCard Component
**File:** `frontend/src/components/ActionCard.jsx`

**Changes:**
- Handles both nested and flat data structures
- Extracts agent name from multiple possible locations
- Extracts action type from multiple possible locations
- Better fallback handling

**Before:**
```javascript
const actionData = action.action || {};
const agent = action.agent || 'Unknown Agent';
const actionType = actionData.type || 'UNKNOWN';
```

**After:**
```javascript
const actionData = action.action || action.action_data || {};
const agent = action.agent || 'Unknown Agent';
const actionType = action.type || actionData.type || 'UNKNOWN';
```

## Testing

### 1. Test Stats Endpoint
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/stats" | ConvertTo-Json
```

**Expected:**
```json
{
  "total_actions": 4,
  "autonomous_actions": 1,
  "approved_actions": 1,
  "pending_actions": 1,
  "rejected_actions": 2,
  "kill_switch_active": false
}
```

### 2. Test Action History
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/monitoring/history?limit=10" | ConvertTo-Json
```

**Expected:** Actions with agent names and types at top level

### 3. Test Frontend
- Open dashboard: http://localhost:5173
- Stats bar should show correct counts
- Action feed should show agent names (not "Unknown Agent")
- Action types should display correctly (not "UNKNOWN")

## Expected Behavior

✅ **Stats Bar:**
- Shows accurate counts for all action types
- Updates in real-time
- Pending count matches actual pending approvals

✅ **Action Feed:**
- Shows agent names: "Quartermaster", "Watchtower", "Press Secretary"
- Shows action types: "PURCHASE_ORDER", "PATIENT_ADVISORY", etc.
- Displays all action details correctly

✅ **Redis Storage:**
- No more tuple serialization errors
- Complex objects properly serialized
- Data retrievable and deserialized correctly

## Data Flow

```
1. Agent creates action → propose_and_execute()
2. Execution record includes agent name and action type
3. broadcast_action() ensures agent/type at top level
4. Serialized for Redis storage
5. Deserialized when retrieved
6. Frontend displays with correct agent names and types
```

## Notes

- The monitoring service now handles both Redis and in-memory storage gracefully
- All broadcasts include agent names (defaults to "Unknown Agent" if missing)
- Action types are accessible at both nested and top level
- Stats calculation is more robust with multiple field checks

