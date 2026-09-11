# Family Chicken Farm Tracker

Simple daily logbook for a small family chicken farm. Django + plain HTML/CSS.
Mobile-first, big readable numbers, fast entry.

## Run locally (SQLite, no setup)

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo   # optional sample data
python manage.py runserver
```

Open http://127.0.0.1:8000. Remove sample data later with
`python manage.py seed_demo --clear`.

## Use MySQL

```bash
# server side
CREATE DATABASE farmdb CHARACTER SET utf8mb4;
CREATE USER 'farm'@'localhost' IDENTIFIED BY 'secret';
GRANT ALL ON farmdb.* TO 'farm'@'localhost';

pip install -r requirements.txt
export DB_ENGINE=mysql DB_NAME=farmdb DB_USER=farm DB_PASSWORD=secret DB_HOST=localhost
python manage.py migrate
python manage.py runserver
```

Config values (env): `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`,
`FARM_CURRENCY` (default `GH₵`), `FEED_UNIT` (default `kg`), `TZ`.

## Deploying (read this)

SQLite is a single file on the server. It works for one device/computer
but does **not** persist on Netlify's static hosting. Options:

- Easiest: host the whole app on a small always-on server/VPS with MySQL
  (or SQLite + regular file backups via Download backup).
- Netlify frontend alone cannot run Django or hold the database. If you
  want Netlify, keep Django + MySQL on a backend host and point the
  domain at it.

Backups do not depend on the database file: use More → Download backup
(JSON of all records, plus per-table CSV).

## Rules the app follows

- Every event is entered once where it belongs. Bird count, egg stock,
  and net cash flow are always computed, never typed.
- A broiler sale fills one form and writes both the sale and the flock
  removal. Egg sales warn (but never block) when over stock.
- Home-eaten eggs are logged under More → Log home use and reduce stock.
- Feed bought = expense (category Feed). Daily feed use is optional.
- Health dates come only from you/vet. The app only counts due/overdue.
