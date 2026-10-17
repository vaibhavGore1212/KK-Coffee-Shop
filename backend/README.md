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
- `POST /api/reservations` saves a table reservation. JSON fields: `name`, `email`, `date`, `time`, `guests`.
- `GET /api/menu` returns the current menu names and prices.
- `POST /api/orders` saves an order. JSON fields: `customer_name`, `email`, optional `phone`, `items` (array of `{ "name": "Espresso", "quantity": 2 }`), and optional `special_instructions`.
- `GET /api/health` checks that the API is running.

On `menu.html`, select **Add to Order** below an item. The item is added to the browser's cart and checkout opens. Select **Add More Items** to return to the menu and add coffee or snacks; the existing cart stays saved in that browser. On checkout, change quantities or remove items, then enter customer details and select **Place Order**. Flask validates every item against its menu catalog, calculates the combined total, saves the order, and returns a reference number. Successful submissions return HTTP `201`; invalid requests return HTTP `400` with an `error` message. Online payment is not part of this version.

## Tests

Run the backend tests from the project root:

```powershell
python -m unittest discover -s tests
```