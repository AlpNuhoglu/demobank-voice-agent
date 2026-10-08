# Data model

All data is synthetic. SQLite via SQLAlchemy 2.0.

## Conventions

- **Money:** `Decimal` TRY in code, integer kuruş in the DB (`amount_kurus`).
  Helpers in `app/money.py` convert and format (`1.250,50 TL`).
- **Time:** timezone-aware `Europe/Istanbul` datetimes. SQLite stores no
  offset, so `IstanbulDateTime` writes UTC and reads back Istanbul time.
- **Enums:** stored as English strings. Turkish wording belongs in the speech
  layer, not the data.

## Tables

### customers
| column | type | notes |
|---|---|---|
| id | int | PK |
| full_name | str | synthetic Turkish name |
| phone_number | str | unique, E.164 (`+905550000001`) |

### cards
| column | type | notes |
|---|---|---|
| id | int | PK |
| customer_id | int | FK customers |
| type | `debit` \| `credit` | |
| last4 | str(4) | the only card digits stored |
| status | `active` \| `blocked` \| `expired` | |
| expires_on | date | past for expired cards |
| blocked_at | datetime \| null | set when blocked |
| block_reason | `lost` \| `stolen` \| `other` \| null | |

### transactions
| column | type | notes |
|---|---|---|
| id | int | PK |
| card_id | int | FK cards |
| merchant | str | fictional merchant |
| amount_kurus | int | positive, kuruş |
| occurred_at | datetime | Istanbul time |
| category | str | e.g. `market`, `restoran`, `akaryakıt` |

## Seed data

`app/services/seed.py` builds 5 customers, 8 cards (one expired, one blocked
as `lost`) and 8–15 transactions per card over the last 30 days. The output
depends only on the reference time `now`. Each run drops and recreates all
tables.
