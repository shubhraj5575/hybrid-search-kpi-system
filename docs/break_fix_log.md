# Break/Fix Log

This document records intentionally induced errors, their symptoms, and recovery strategies.

---

## Scenario A: Semantic Index Dimension Mismatch

### Inject Error (2024-03-12 17:00)

**Change**: Modify vector index to use different embedding model after building

```bash
# Original index built with all-MiniLM-L6-v2 (384 dim)
# Change code to load with all-mpnet-base-v2 (768 dim)

# In backend/app/main.py startup_event:
vector_index = VectorIndex(model_name="all-mpnet-base-v2")  # Wrong model!
vector_index.load(metadata['vector_dir'])
```

### Expected Behavior
- Dimension mismatch: index has 384-dim vectors, model expects 768-dim
- Error at query time or index load time
- Either silent failure (wrong results) or crash

### Actual Observed Behavior

**Startup Error**:
```
ValueError: Dimension mismatch: index has dim=384, but model has dim=768
```

**Why**: The validation logic in `VectorIndex.load()` checks:
```python
if metadata['dimension'] != self.dimension:
    raise ValueError(f"Dimension mismatch...")
```

### Fix Implemented

**Prevention**: Index metadata includes:
```json
{
  "embedding_model": "all-MiniLM-L6-v2",
  "dimension": 384
}
```

**Validation on Load**:
```python
# In vector.py load() method
if metadata['model_name'] != self.model_name:
    raise ValueError(
        f"Model mismatch: index was built with {metadata['model_name']}, "
        f"but current model is {self.model_name}"
    )
```

**Automatic Recovery Option**: Could auto-rebuild index, but chose to fail fast with clear error

**User Action Required**: 
```bash
# If model changed, rebuild index:
python -m backend.app.index --input data/processed/docs.jsonl --model all-mpnet-base-v2
```

**Status**: ✅ Fixed - fails fast at startup with actionable error message

---

## Scenario B: Database Schema Migration Break

### Inject Error (2024-03-12 17:15)

**Change**: Add a NOT NULL column to QueryLog without migration

```python
# In backend/app/db/models.py, add new column:
class QueryLog(Base):
    # ... existing columns ...
    user_id = Column(String(50), nullable=False)  # NEW COLUMN, NOT NULL!
```

**Restart app without dropping old database**

### Expected Behavior
- Old database schema doesn't have user_id column
- INSERT queries will fail with missing column error
- API returns 500 errors
- Dashboard breaks, no query logging

### Actual Observed Behavior

**Error on Query Logging**:
```
sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) table query_logs has no column named user_id
```

**Symptoms**:
- Search API returns results but logging fails silently (caught by try/except)
- No new entries in query_logs table
- Dashboard KPIs show stale data

### Fix Implemented

**Option 1: Simple Migration (Implemented)**

Create migration script:
```python
# scripts/migrate_db.py
from backend.app.db.models import Base, Database
import os

def migrate_v1_to_v2():
    db_path = "data/metrics/app.db"
    
    # Backup existing database
    import shutil
    shutil.copy(db_path, f"{db_path}.backup")
    
    # Add new column with default value
    import sqlite3
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("ALTER TABLE query_logs ADD COLUMN user_id TEXT DEFAULT 'unknown'")
        conn.commit()
        print("✓ Migration complete")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e):
            print("✓ Column already exists")
        else:
            raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_v1_to_v2()
```

**Option 2: Alembic (Production)**
- For production, would use Alembic for versioned migrations
- Out of scope for this prototype

**Recovery Steps**:
```bash
# Run migration
python scripts/migrate_db.py

# Or, nuclear option: delete database (loses history)
rm data/metrics/app.db
./down.sh && ./up.sh  # Recreates with new schema
```

**Prevention**: 
- Add schema version to database
- Check version on startup
- Refuse to start if mismatch

**Status**: ✅ Fixed - migration script handles schema evolution

---

## Scenario C: Hybrid Scoring Division by Zero

### Inject Error (2024-03-12 17:30)

**Change**: Create query that triggers divide-by-zero in normalization

**Setup**: 
- Index with only 1 document
- Query that matches only that document
- All BM25 scores identical → max == min → divide by zero

```python
# In hybrid.py, REMOVE the protection:
def normalize_scores_minmax(self, scores):
    scores = np.array(scores)
    min_score = scores.min()
    max_score = scores.max()
    
    # BUG: No check for max_score == min_score!
    normalized = (scores - min_score) / (max_score - min_score)  # ZeroDivisionError!
    return normalized.tolist()
```

### Expected Behavior
- Query with all equal scores → divide by zero
- NaN or Inf in hybrid_score
- Incorrect ranking (NaNs sort unpredictably)
- API crashes or returns garbage

### Actual Observed Behavior

**Error Without Protection**:
```
RuntimeWarning: invalid value encountered in divide
```

**Result**: hybrid_score contains NaN values

**Evaluation Impact**:
```
# In eval.py
ndcg@10: nan
recall@10: 0.0  (no relevant docs retrieved due to NaN sorting)
```

### Fix Implemented

**Protection in normalize_scores_minmax**:
```python
def normalize_scores_minmax(self, scores):
    if not scores or len(scores) == 1:
        return [1.0] * len(scores)
    
    scores = np.array(scores)
    min_score = scores.min()
    max_score = scores.max()
    
    if max_score == min_score:
        # All scores equal - return uniform scores
        return [1.0] * len(scores)
    
    normalized = (scores - min_score) / (max_score - min_score)
    return normalized.tolist()
```

**Test Case**:
```python
def test_hybrid_zero_division_protection(hybrid_search):
    """Test normalization handles edge cases without crashing"""
    # Query unlikely to match anything well
    results = hybrid_search.search("xyzabc123", top_k=3, alpha=0.5)
    assert isinstance(results, list)
    # All results should have finite hybrid_score
    for r in results:
        assert not np.isnan(r['hybrid_score'])
        assert not np.isinf(r['hybrid_score'])
```

**Evaluation Recovery**:
- Before fix: nDCG = NaN, tests fail
- After fix: nDCG = 0.0 (correct - no relevant results), tests pass

**Status**: ✅ Fixed - graceful handling with sensible defaults

---

## Additional Robustness Improvements

### 1. Missing Index Files
**Symptom**: App crashes on startup if index files deleted
**Fix**: Check `metadata.json` exists, print helpful error
```python
if not metadata_path.exists():
    print("ERROR: No index metadata found. Run indexing first:")
    print("  python -m backend.app.index --input data/processed/docs.jsonl")
    return
```

### 2. Empty Query String
**Symptom**: Empty query returns all documents (useless)
**Fix**: Validate in API
```python
@app.post("/search")
async def search(request: SearchRequest):
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
```

### 3. Invalid Alpha Range
**Symptom**: alpha > 1.0 or alpha < 0.0 produces weird scores
**Fix**: Pydantic validation
```python
alpha: float = Field(0.5, ge=0.0, le=1.0, description="BM25 weight")
```

---

## Summary

| Scenario | Error Type | Detection | Recovery | Prevention |
|----------|-----------|-----------|----------|------------|
| A: Dimension Mismatch | Config | Startup validation | Rebuild index | Metadata checks |
| B: Schema Migration | Schema | Runtime error | Migration script | Version tracking |
| C: Division by Zero | Logic | Unit test | Edge case handling | Test coverage |

**Key Lessons**:
1. **Fail Fast**: Validation at startup > runtime errors
2. **Clear Messages**: Errors should tell user what to do
3. **Test Edge Cases**: Empty inputs, equal scores, missing data
4. **Graceful Degradation**: Return sensible defaults, not crashes

All scenarios are now handled with tests to prevent regression.
