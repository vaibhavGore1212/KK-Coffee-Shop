# Coffee Shop Flask Backend

## Run locally

From the project root, install the dependency and start Flask:

```powershell
python -m pip install -r requirements.txt
python backend/app.py
```

Open `http://127.0.0.1:5000`. Flask serves the existing HTML pages and their local assets. SQLite creates its database at `backend/data/coffee_shop.sqlite3` automatically. Set `COFFEE_SHOP_DATABASE` to use a different database file.

## API

- `POST /api/contact` saves a contact form message. JSON fields: `name`, `email`, `subject`, `message`.
- `POST /api/reservations` requires a logged-in account and saves the account's name/email with `date`, `time`, and `guests` from the form.
- `GET /api/menu` returns the current menu names and prices.
- `POST /api/auth/register` creates an account with `name`, `email`, `phone`, and `password`.
- `POST /api/auth/login` starts a session with `email` and `password`; `GET /api/auth/me` returns the current account; `POST /api/auth/logout` ends the session.
- `POST /api/orders` requires a logged-in account. JSON fields: `delivery_address`, `items` (array of `{ "name": "Espresso", "quantity": 2 }`), and optional `special_instructions`. Customer name, email, and phone are loaded from the account.
- `GET /api/health` checks that the API is running.

On `menu.html`, select **Add to Order** below an item. The item is added to the browser's cart and checkout opens. Select **Add More Items** to return to the menu and add coffee or snacks; the existing cart stays saved in that browser. Checkout requires login; new customers can create an account on `login.html`. The checkout uses the account's name, email, and phone, while the customer enters a delivery address. Flask validates every item against its menu catalog, calculates the combined total, saves the order, and returns a reference number. Set `FLASK_SECRET_KEY` in the environment to keep sessions stable across server restarts; use a strong private value in any deployed environment. Online payment is not part of this version.

## Tests

Run the backend tests from the project root:

```powershell
python -m unittest discover -s tests
```