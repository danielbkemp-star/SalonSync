# SalonSync Bug Report

## Critical (Blocking)
| ID | Description | Location | Status |
|----|-------------|----------|--------|
| C1 | User role not updated to Owner on salon creation (case-sensitive comparison) | app/api/salons.py:96 | Fixed |

## High Priority
| ID | Description | Location | Status |
|----|-------------|----------|--------|
| H1 | Sale model missing salon_id for multi-tenant support | app/models/sale.py | Fixed |
| H2 | SQLAlchemy JSON mutation not detected for tag removal | app/api/clients.py:500-507 | Fixed |
| H3 | SQLAlchemy JSON mutation not detected for formula addition | app/api/media.py:368-374 | Fixed |
| H4 | SQLAlchemy JSON mutation not detected for tag addition | app/api/clients.py:471-480 | Fixed |

## Medium Priority
| ID | Description | Location | Status |
|----|-------------|----------|--------|
| M1 | Test fixture uses wrong column name 'address' instead of 'address_line1' | tests/conftest.py:142 | Fixed |
| M2 | Test fixture uses wrong Staff columns (display_name, role, is_active) | tests/conftest.py:153-159 | Fixed |
| M3 | ClientCreate schema requires redundant salon_id in body when already in URL | app/schemas/client.py:50 | Fixed |
| M4 | ServiceCreate schema requires redundant salon_id in body when already in URL | app/schemas/service.py:30 | Fixed |

## Low Priority / Enhancements
| ID | Description | Location | Status |
|----|-------------|----------|--------|
| L1 | Pydantic deprecation warnings for class-based Config | app/app_settings.py:117, app/api/auth.py:60 | Backlog |
| L2 | SQLAlchemy deprecation warning for declarative_base() | app/database.py:33 | Backlog |
| L3 | ClientResponse missing referral_code field | app/schemas/client.py | Backlog |

## Fixed Bugs Log
| ID | Description | Fix Description | Files Modified |
|----|-------------|-----------------|----------------|
| C1 | User role not updated to Owner | Changed string comparison to enum comparison: `current_user.role == UserRole.CLIENT` | app/api/salons.py |
| H1 | Sale model missing salon_id | Added salon_id column with FK to salons.id, added relationship | app/models/sale.py, app/models/salon.py |
| H2 | Tag removal not persisting | Use list comprehension to create new list instead of in-place mutation | app/api/clients.py |
| H3 | Formula addition not persisting | Use list() constructor to create copy before mutation | app/api/media.py |
| H4 | Tag addition not persisting | Use list() constructor to create copy before mutation | app/api/clients.py |
| M1 | Test fixture wrong column name | Changed 'address' to 'address_line1' | tests/conftest.py |
| M2 | Test fixture wrong Staff fields | Changed display_name/role/is_active to title/status | tests/conftest.py |
| M3 | Redundant salon_id in ClientCreate | Removed required salon_id field (already in URL path) | app/schemas/client.py |
| M4 | Redundant salon_id in ServiceCreate | Removed required salon_id field (already in URL path) | app/schemas/service.py |

---

# SalonSync QA Summary

## Test Results
- Auth Tests: 13/13 passing
- Salon Tests: 12/12 passing
- Client Tests: 14/14 passing
- Integration Tests: 8/8 passing
- **Total Tests: 47/47 passing**

## Bugs Found & Fixed
- Critical: 1 found, 1 fixed
- High: 4 found, 4 fixed
- Medium: 4 found, 4 fixed
- Low/Backlog: 3 found, deferred

## Test Coverage Summary
- Authentication flow fully tested
- Salon CRUD fully tested
- Client CRUD fully tested
- Service CRUD tested via integration
- Stats endpoint tested
- Consent management tested
- Tag management tested
- Permissions/RBAC tested
- Full onboarding flow tested
- Data integrity tested

## Known Issues (Deferred)
- Pydantic V2 deprecation warnings (class-based Config) - cosmetic, won't affect functionality
- SQLAlchemy declarative_base() deprecation - cosmetic, won't affect functionality
- ClientResponse missing referral_code - minor feature gap

## Files Modified
1. `app/models/sale.py` - Added salon_id column
2. `app/models/salon.py` - Added sales relationship
3. `app/api/salons.py` - Fixed role comparison bug
4. `app/api/clients.py` - Fixed JSON mutation bugs for tags
5. `app/api/media.py` - Fixed JSON mutation bug for formulas
6. `app/schemas/client.py` - Removed redundant salon_id
7. `app/schemas/service.py` - Removed redundant salon_id
8. `tests/conftest.py` - Fixed test fixtures

## Ready for Deployment: Yes (with noted backlog items)
