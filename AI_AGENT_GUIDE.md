# AI Agent Anti-Hallucination Guide

## 🎯 Mandatory Prompt Prefix (Use for EVERY Task)

```
CRITICAL INSTRUCTIONS - READ FIRST:

You are an AI coding assistant helping a solo founder build a production SaaS.
Your outputs must be:
1. FULLY FUNCTIONAL (no placeholders, no "implement this later" comments)
2. COPY-PASTE READY (human should not need to edit your code)
3. TYPE-SAFE (TypeScript strict mode, Python type hints)
4. ERROR-HANDLED (try/catch, validation, meaningful error messages)
5. TESTED (include example test that proves it works)

BANNED PHRASES (never say these):
- "This is a basic example, expand as needed"
- "TODO: Implement this feature"
- "// Add error handling here"
- "You may want to consider..."
- "This should work, but might need adjustments"

VERIFICATION CHECKLIST (answer before generating code):
- [ ] Does this solve the EXACT task requirement?
- [ ] Can this code run without modifications?
- [ ] Are all edge cases handled?
- [ ] Is there a concrete example demonstrating it works?
- [ ] Would Apple ship this quality?

If you cannot provide FULLY WORKING CODE, say:
"I cannot complete this task without more information about [specific detail]."

Now, proceed with the task:
```

---

## ⚠️ Common AI Agent Mistakes

### Mistake #1: Incomplete Implementations
**Problem:** Returns code with `// TODO: Add validation`  
**Solution:** "COMPLETE THE ENTIRE FEATURE. No TODOs, no placeholders."

### Mistake #2: Wrong Technology Choices
**Problem:** Suggests `localStorage` (doesn't work in all contexts)  
**Solution:**
```
CONSTRAINTS:
- Frontend: Next.js 14 (App Router), NOT Claude artifacts
- Backend: FastAPI, NOT Flask or Django
- Database: PostgreSQL, NOT MySQL or MongoDB
- Use ONLY these libraries: [list from tech stack]

If you suggest something not listed, STOP and ask for approval.
```

### Mistake #3: Overcomplication
**Problem:** Creates 5-layer architecture for simple CRUD  
**Solution:**
```
SIMPLICITY FIRST:
- Solve THIS specific problem, not a general framework
- Fewer files is better
- Copy-paste OK if only 2 places
- No design patterns unless absolutely necessary
```

### Mistake #4: No Error Handling
**Problem:** Happy path only, crashes on bad input  
**Solution:**
```
ERROR HANDLING REQUIRED:
- Every API call wrapped in try/catch
- Every user input validated BEFORE processing
- Every database query handles "not found"
- Every function returns typed result or throws specific error

Show error handling explicitly. Don't say "add error handling here."
```

### Mistake #5: Type Safety Violations
**Problem:** Uses `any` everywhere  
**Solution:**
```
TYPE SAFETY RULES:
- Zero 'any' types (use 'unknown' if dynamic)
- All API responses have interfaces
- Optional fields checked before use
- Zod schemas for runtime validation

Paste your types/interfaces at the start.
```

### Mistake #6: Untested Code
**Problem:** Code without verification  
**Solution:**
```
MANDATORY TEST EXAMPLE:
After your code, provide:
1. Exact command to run: `python script.py` or `curl ...`
2. Expected output: Show actual JSON/text
3. How to verify: Check database, file system, UI

If you can't provide working example, code is incomplete.
```

### Mistake #7: Missing Dependencies
**Problem:** Imports libraries not installed  
**Solution:**
```
DEPENDENCY CHECK:
Before writing code, list all imports.
Verify each is in package.json/requirements.txt

If need new library:
1. Explain why
2. Check if existing libs can do it
3. Wait for approval

Current installed: [paste from package.json]
```

---

## 📋 Task-Specific Validation Templates

### Backend Tasks
```
After generating code, provide TEST VERIFICATION:

1. Example curl command
2. Expected output (exact JSON)
3. Database verification: SELECT ... FROM ...
4. Common errors and fixes

Example:
# Test:
curl -X POST http://localhost:8000/api/test \
  -H "Content-Type: application/json" \
  -d '{"key": "value"}'

# Expected:
{"status": "success", "data": {...}}

# Verify DB:
SELECT * FROM table_name WHERE id = 'xxx';

# Common error: "Connection refused"
# Fix: Check server running: uvicorn main:app
```

### Frontend Tasks
```
After generating code, provide UI VERIFICATION:

1. What should I see on screen?
2. What happens when I click [button]?
3. Loading state description
4. Error state description
5. Empty state description

Example:
# Visual verification:
- Blue "Submit" button
- On hover: scales up 2%, shows shadow
- On click: spinner, disables
- After 2s: success toast top-right
- Button re-enables

# Test:
1. Open http://localhost:3000/test-page
2. Click button
3. Network tab: no 404s
4. Console: no errors
```

### Database Tasks
```
After generating migration, provide DATABASE VERIFICATION:

1. Apply: alembic upgrade head
2. Verify: \d table_name
3. Sample INSERT
4. Rollback: alembic downgrade -1

Example:
# Apply:
alembic upgrade head

# Verify:
psql $DATABASE_URL -c "\d users"

# Test insert:
INSERT INTO users (email, name) VALUES ('test@example.com', 'Test');

# Error: "relation does not exist"
# Fix: Migration didn't apply, check alembic/versions/
```

---

## 🛠️ Daily AI Agent Prompt Template

```
CONTEXT:
I'm building [feature name] for API documentation platform.
Tech stack: Next.js 14, FastAPI, PostgreSQL.

EXACT TASK:
[Be extremely specific - include acceptance criteria]

CONSTRAINTS:
- Must work with existing models: [list]
- Follow error handling from previous tasks
- No new dependencies unless approved
- TypeScript strict mode (no 'any')

VERIFICATION:
Provide:
1. Exact command to test
2. Expected output
3. How to verify in database/UI

ANTI-HALLUCINATION RULES:
- No TODOs or placeholders
- Complete implementation only
- Include error handling explicitly
- Types defined upfront

Proceed:
```

---

## 🚨 Emergency: AI Keeps Making Same Mistake

### Step 1: Document the Mistake
Create file: `ai-agent-mistakes.md`

```markdown
## Mistake: Using localStorage in React artifacts

Wrong code:
```javascript
localStorage.setItem('key', 'value')
```

Correct code:
```javascript
const [data, setData] = useState()
```

Prevention prompt:
"NEVER use localStorage or sessionStorage. Use React state (useState)."
```

### Step 2: Prepend to ALL Future Prompts
```
KNOWN MISTAKES TO AVOID:
[Paste from ai-agent-mistakes.md]

If you're about to make any of these mistakes, STOP and use correct approach.
```

### Step 3: If Repeats 3+ Times
- Switch AI model
- Ask humans (Discord, Reddit, StackOverflow)
- Take a break, try fresh tomorrow

---

## 📚 Learning Resources (When Stuck)

### FastAPI
- Docs: https://fastapi.tiangolo.com/
- Ask: Reddit r/FastAPI

### Next.js
- Docs: https://nextjs.org/docs
- Ask: Next.js Discord

### Database
- SQLAlchemy: https://docs.sqlalchemy.org/
- Ask: StackOverflow (postgresql + sqlalchemy)

### Gemini AI
- Docs: https://ai.google.dev/docs
- Ask: r/PromptEngineering

---

## 📞 When to Ask for Help

**Ask humans when:**
1. Stuck >4 hours on same problem
2. Not sure if architecture is right
3. Production down >30 minutes
4. Considering major pivot
5. Feeling burnt out

**Don't ask:** "Is this the best way?" (endless debate)  
**Do ask:** "This error, how to fix?" (actionable)

---

**Remember:** AI agents are tools, not oracles. Always verify, always test, always think critically.
