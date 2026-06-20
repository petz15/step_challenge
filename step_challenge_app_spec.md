# Step Challenge App - Build Guide for Claude Code

## Overview

**Problem:** Two users with Garmin watches want to compete in weekly and monthly step challenges, but Garmin's built-in challenge app cannot count custom activities (cycling, climbing, etc.) as "steps" or offer both weekly and monthly leaderboards simultaneously.

**Solution:** A lightweight web app where both users can log activities (steps, hiking, cycling, etc.), convert them to a standardized "step equivalent," and compete on daily/weekly/monthly leaderboards.

**Target Users:** 2 people (but scalable to more)  
**Tech Stack:** FastAPI backend, Next.js frontend, PostgreSQL, optional Garmin API integration  
**Timeline:** MVP in 1 sprint (6-8 hours)

---

## Core Requirements

### 1. Activity Input
- Users can log activities with:
  - **Activity type** (Walking, Hiking, Running, Cycling, Climbing Gym, Strength Training, etc.)
  - **Duration** (minutes) OR **Distance** (km)
  - **Date** (defaults to today)
  - **Manual step count** (optional, for direct Garmin sync or manual entry)
- Activities are submitted via a simple form or quick-add interface
- If possible use garmin to import other activities as well such as cycling, cycling indoor, swimming etc

### 2. Step Conversion Rules
**The heart of the app:** All activities convert to a "step equivalent" using configurable rules. -> find a baseline online

**Admin/Settings panel:** Allow users to customize these conversion ratios per activity type. -> only admins

### 3. Leaderboards & Competitions
Display three simultaneous leaderboards, all auto-updating:
- **Daily Leaderboard** (resets at midnight)
- **Weekly Leaderboard** (resets every Monday at 00:00)
- **Monthly Leaderboard** (resets on the 1st of each month at 00:00)

Each leaderboard shows:
- Rank
- User name
- Total step equivalents for the period
- Percentage of personal weekly/monthly goal (if goals are set)

### 4. User Management
- Simple login (email + password, or just two hardcoded accounts for now)
- User profile with:
  - Name
  - Optional weekly goal (steps/week)
  - Optional monthly goal (steps/month)
  - Activity preferences (which activity types to track)

### 5. Garmin Integration (Optional/Phase 2)
- Ability to import step data from Garmin Connect API (if available)
- Synced activities should be deduplicated (don't count same run twice)

---

## User Flows

### Flow 1: Log an Activity
```
User clicks "Log Activity"
→ Select Activity Type (dropdown)
→ Enter Duration or Distance
→ (Optional) Add notes
→ Click "Submit"
→ Activity saved to database
→ Leaderboards auto-refresh
```

### Flow 2: View Leaderboards
```
User opens app
→ Dashboard shows three leaderboards (daily/weekly/monthly)
→ Can click on self or opponent to see activity history for that period
```

### Flow 3: Adjust Conversion Rules
```
Admin goes to Settings
→ See current conversion rules for each activity type
→ Edit a ratio (e.g., "Hiking: change 1min = 50steps to 1min = 60steps")
→ Save
→ All activities recalculate retroactively
→ Leaderboards update
```

---

## Data Model

### Users Table
```
id (primary key)
email (unique)
password_hash
name (e.g., "Peter")
weekly_goal (integer, steps)
monthly_goal (integer, steps)
created_at
updated_at
```

### Activities Table
```
id (primary key)
user_id (foreign key → Users)
activity_type (enum: Walking, Hiking, Running, Cycling, Climbing, Strength, Manual Steps)
duration_minutes (nullable)
distance_km (nullable)
manual_steps (nullable, for direct input)
step_equivalent_calculated (integer, auto-computed based on conversion rules)
date (date, the day the activity occurred)
notes (text, optional)
source (enum: manual, garmin_api, csv_import)
created_at
updated_at
```

### Conversion Rules Table
```
id (primary key)
activity_type (string)
conversion_per_minute (float, steps per minute)
conversion_per_km (float, steps per km)
is_default (boolean)
user_id (nullable, if user wants personal overrides)
updated_at
```

### Leaderboard Cache (optional, for performance)
```
id (primary key)
user_id
period_type (enum: daily, weekly, monthly)
period_start_date
period_end_date
total_steps
rank (integer)
updated_at
```

---

## API Endpoints

### Authentication
```
POST /api/auth/login
  Body: { email, password }
  Returns: { access_token, user_id, name }

POST /api/auth/logout
  Returns: { success: true }

GET /api/auth/me
  Returns: { user_id, email, name, weekly_goal, monthly_goal }
```

### Activities
```
POST /api/activities
  Body: { activity_type, duration_minutes?, distance_km?, manual_steps?, date, notes? }
  Returns: { activity_id, step_equivalent_calculated }

GET /api/activities
  Query: ?start_date=2026-06-01&end_date=2026-06-30&user_id=?
  Returns: [ { activity_id, activity_type, duration_minutes, step_equivalent, date, notes } ]

DELETE /api/activities/{activity_id}
  Returns: { success: true }

PUT /api/activities/{activity_id}
  Body: { activity_type?, duration_minutes?, distance_km?, notes? }
  Returns: { activity_id, step_equivalent_calculated }
```

### Leaderboards
```
GET /api/leaderboards/daily?date=2026-06-20
  Returns: [ { rank, user_id, name, total_steps, goal?, goal_progress? } ]

GET /api/leaderboards/weekly?week_start=2026-06-16
  Returns: [ { rank, user_id, name, total_steps, goal?, goal_progress? } ]

GET /api/leaderboards/monthly?year=2026&month=6
  Returns: [ { rank, user_id, name, total_steps, goal?, goal_progress? } ]
```

### Conversion Rules
```
GET /api/settings/conversion-rules
  Returns: [ { activity_type, conversion_per_minute, conversion_per_km } ]

PUT /api/settings/conversion-rules/{activity_type}
  Body: { conversion_per_minute?, conversion_per_km? }
  Returns: { success: true, message: "All activities recalculated" }

GET /api/settings/user
  Returns: { user_id, name, weekly_goal, monthly_goal }

PUT /api/settings/user
  Body: { name?, weekly_goal?, monthly_goal? }
  Returns: { success: true }
```

### Admin/Debug (optional)
```
POST /api/admin/seed-data
  Populates test data for development
  Returns: { users: N, activities: M }
```

---

## Frontend (Next.js) Structure

### Pages
- `/` — Login/splash
- `/dashboard` — Main leaderboards (daily/weekly/monthly tabs)
- `/log` — Quick activity entry form
- `/history` — Activity history with filters
- `/settings` — User goals + conversion rules
- `/activity/[id]` — Individual activity detail/edit

### Key Components
- `<LeaderboardTable />` — Displays ranked list with goals progress
- `<ActivityForm />` — Submit new activity
- `<ConverterRuleEditor />` — Adjust conversion ratios
- `<StepChart />` — Optional: visualize trends (recharts)

### State Management
- Use Next.js `useContext` + `useState` for auth, or simple JWT in localStorage
- Fetch leaderboards on mount and auto-refresh every 30 seconds

---

## Conversion Logic (Backend)

When an activity is submitted or rules are changed:

```python
def calculate_step_equivalent(activity: Activity, conversion_rules: dict) -> int:
    rule = conversion_rules.get(activity.activity_type, {})
    
    if activity.manual_steps:
        return activity.manual_steps
    
    if activity.duration_minutes:
        steps = activity.duration_minutes * rule.get("conversion_per_minute", 0)
    elif activity.distance_km:
        steps = activity.distance_km * rule.get("conversion_per_km", 0)
    else:
        steps = 0
    
    return int(round(steps))
```

When conversion rules are updated, **recalculate all activities retroactively**:
```python
def update_conversion_rule(activity_type: str, new_per_minute: float):
    rule = conversion_rules.update(activity_type, new_per_minute)
    activities = db.query(Activity).filter(Activity.activity_type == activity_type)
    for activity in activities:
        activity.step_equivalent = calculate_step_equivalent(activity, {activity_type: rule})
    db.commit()
```

---



## Deployment

Set it all up to run on the local lan only for now with postgres as DB and docker as run environment. use a .env file for all env variables


---

## MVP Features (Required)
- ✅ User login (simple)
- ✅ Log activities with type + duration/distance
- ✅ Auto-convert activities to step equivalents
- ✅ Daily, weekly, monthly leaderboards
- ✅ Settings to adjust conversion rules -> find online if possible
- ✅ Activity history view

## Phase 2 (Nice-to-Have)
- Garmin API integration for auto-sync
- Apple Health integration for auto-sync
- Notifications when opponent logs activity
- Chart visualization of trends
- Mobile-responsive design polish
- Streak tracking (consecutive days)

---

## Notes for Claude Code

1. **Start with the backend first.** Get the FastAPI server and PostgreSQL schema working, populate test data, verify leaderboard calculations.

2. **Test conversion logic thoroughly.** This is the core logic—edge cases matter (what if user submits 0 minutes? what if rules change mid-week?).

3. **Keep auth simple for MVP.** Hardcode two users or use simple email/password. Don't over-engineer.

4. **Leaderboard recalculation should be fast.** If you have 100+ activities per user per month, you may want to cache leaderboards separately (see optional Leaderboard Cache table).

5. **Frontend can be minimal.** Three tabs for daily/weekly/monthly leaderboards, a form to log activity, a settings page. No fancy UI needed—clarity matters more.

6. **Database resets:** Easy way to reset for testing: `python manage.py seed_data --reset`

7. **Time zones:** For now, assume UTC or local Switzerland time (CET/CEST). Weekly starts Monday, monthly starts 1st.

8. **Resources** Use existing github repos or other online resources where ever possible

---

## Questions to Clarify Before Building

- Are there any other activity types beyond the defaults listed?
- Do you want weekly/monthly goals, or just leaderboards?
- Do you want to eventually pull Garmin API data, or is manual entry + optional CSV import enough for now?

