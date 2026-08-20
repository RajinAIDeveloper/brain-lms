# Local demo accounts

Run this command after migrations:

```powershell
& 'C:\Users\user\AppData\Local\Programs\Python\Python310\python.exe' manage.py seed_demo
```

All four demo users use the password `BrainGymMVP!2026`:

| Role | Email | Seeded relationships |
| --- | --- | --- |
| Admin | `admin@braingym.local` | Staff/superuser; full admin access |
| Teacher | `teacher@braingym.local` | Assigned to Level 2 · Batch A |
| Student | `student@braingym.local` | Enrolled in Level 2 · Batch A; current level L2 |
| Parent | `parent@braingym.local` | Linked to the demo student |

These credentials are for local validation only. Change them before any shared or production deployment.
