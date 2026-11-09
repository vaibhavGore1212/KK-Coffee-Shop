$(function () {
    var reservationForm = $('#reservationForm');
    try {
        var savedDraft = JSON.parse(sessionStorage.getItem('coffeeShopReservationDraft') || '{}');
        reservationForm.find('[name="date"]').val(savedDraft.date || '');
        reservationForm.find('[name="time"]').val(savedDraft.time || '');
        reservationForm.find('[name="guests"]').val(savedDraft.guests || '');
        sessionStorage.removeItem('coffeeShopReservationDraft');
    } catch (_error) {
        sessionStorage.removeItem('coffeeShopReservationDraft');
    }

    $('#reservationForm').on('submit', function (event) {
        event.preventDefault();

        var form = this;
        var submitButton = $(form).find('button[type="submit"]');
        var feedback = $('#reservationFeedback');
        var formValues = Object.fromEntries(new FormData(form).entries());
        formValues.guests = Number(formValues.guests);
        submitButton.prop('disabled', true);
        feedback.empty();

        fetch('/api/reservations', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formValues)
        })
            .then(function (response) {
                return response.json().then(function (data) {
                    if (!response.ok) {
                        var error = new Error(data.error || 'Reservation could not be saved.');
                        error.status = response.status;
                        throw error;
                    }
                    return data;
                });
            })
            .then(function (data) {
                $('<div>', {
                    class: 'alert alert-success',
                    role: 'status',
                    text: data.message + ' Reference: ' + data.reservation_id
                }).appendTo(feedback);
                form.reset();
                sessionStorage.removeItem('coffeeShopReservationDraft');
            })
            .catch(function (error) {
                if (error.status === 401) {
                    var alertBox = $('<div>', {
                        class: 'alert alert-warning d-flex align-items-center justify-content-between',
                        role: 'alert'
                    });
                    $('<span>', { text: 'Please log in first to book a table.' }).appendTo(alertBox);
                    $('<button>', {
                        class: 'btn btn-warning ml-3',
                        type: 'button',
                        text: 'OK'
                    }).on('click', function () {
                        try {
                            sessionStorage.setItem('coffeeShopReservationDraft', JSON.stringify(formValues));
                        } catch (_error) {
                            // Continue to login even if session storage is unavailable.
                        }
                        window.location.href = 'login.html?next=reservation.html';
                    }).appendTo(alertBox);
                    alertBox.appendTo(feedback);
                    return;
                }

                $('<div>', { class: 'alert alert-danger', role: 'alert', text: error.message }).appendTo(feedback);
            })
            .finally(function () {
                submitButton.prop('disabled', false);
            });
    });
});