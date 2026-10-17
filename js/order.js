$(function () {
    var cartKey = 'coffeeShopCart';
    var orderItems = $('#orderItems');
    var orderTotal = $('#orderTotal');
    var placeOrderButton = $('#placeOrderButton');
    var feedback = $('#orderFeedback');
    var menuPrices = {};
    var cart = readCart();

    function readCart() {
        try {
            var savedCart = JSON.parse(localStorage.getItem(cartKey) || '[]');
            return Array.isArray(savedCart) ? savedCart : [];
        } catch (_error) {
            return [];
        }
    }

    function saveCart() {
        localStorage.setItem(cartKey, JSON.stringify(cart));
    }

    function renderCart() {
        orderItems.empty();
        var total = 0;

        if (!cart.length) {
            orderItems.append($('<p>', {
                class: 'text-muted',
                text: 'Your order is empty. Add coffee or snacks from the menu.'
            }));
        }

        cart.forEach(function (item, index) {
            var price = menuPrices[item.name];
            if (!price) {
                return;
            }
            total += price * item.quantity;

            var row = $('<div>', { class: 'd-flex flex-wrap align-items-center border-bottom py-3' });
            var details = $('<div>', { class: 'flex-grow-1 mr-3 mb-2' });
            $('<strong>', { class: 'd-block', text: item.name }).appendTo(details);
            $('<span>', { class: 'text-muted', text: '₹' + price + ' each' }).appendTo(details);

            var quantity = $('<input>', {
                class: 'form-control mr-2 mb-2',
                type: 'number',
                min: 1,
                max: 99,
                value: item.quantity,
                'aria-label': 'Quantity for ' + item.name
            }).css('width', '88px').on('change', function () {
                var updatedQuantity = Number(this.value);
                if (!Number.isInteger(updatedQuantity) || updatedQuantity < 1 || updatedQuantity > 99) {
                    this.value = item.quantity;
                    return;
                }
                cart[index].quantity = updatedQuantity;
                saveCart();
                renderCart();
            });

            var removeButton = $('<button>', {
                class: 'btn btn-outline-danger mb-2',
                type: 'button',
                text: 'Remove',
                'aria-label': 'Remove ' + item.name + ' from order'
            }).on('click', function () {
                cart.splice(index, 1);
                saveCart();
                renderCart();
            });

            row.append(details, quantity, removeButton).appendTo(orderItems);
        });

        orderTotal.text('₹' + total);
        placeOrderButton.prop('disabled', cart.length === 0);
    }

    fetch('/api/menu')
        .then(function (response) {
            if (!response.ok) {
                throw new Error('The menu could not be loaded. Please refresh and try again.');
            }
            return response.json();
        })
        .then(function (data) {
            data.items.forEach(function (item) {
                menuPrices[item.name] = item.price_rupees;
            });
            cart = cart.filter(function (item) {
                return menuPrices[item.name]
                    && Number.isInteger(item.quantity)
                    && item.quantity >= 1
                    && item.quantity <= 99;
            });
            saveCart();
            renderCart();
        })
        .catch(function (error) {
            feedback.html($('<div>', { class: 'alert alert-danger', role: 'alert', text: error.message }));
        });

    $('#orderForm').on('submit', function (event) {
        event.preventDefault();
        feedback.empty();
        placeOrderButton.prop('disabled', true);

        var formValues = Object.fromEntries(new FormData(this).entries());
        var payload = {
            customer_name: formValues.customer_name,
            email: formValues.email,
            phone: formValues.phone,
            special_instructions: formValues.special_instructions,
            items: cart.map(function (item) {
                return { name: item.name, quantity: item.quantity };
            })
        };

        fetch('/api/orders', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        })
            .then(function (response) {
                return response.json().then(function (data) {
                    if (!response.ok) {
                        throw new Error(data.error || 'Your order could not be saved.');
                    }
                    return data;
                });
            })
            .then(function (data) {
                feedback.html($('<div>', {
                    class: 'alert alert-success',
                    role: 'status',
                    text: data.message + ' Reference: ' + data.order_id + '. Total: ₹' + data.total_rupees
                }));
                cart = [];
                saveCart();
                renderCart();
            })
            .catch(function (error) {
                feedback.html($('<div>', { class: 'alert alert-danger', role: 'alert', text: error.message }));
            })
            .finally(function () {
                placeOrderButton.prop('disabled', cart.length === 0);
            });
    });
});