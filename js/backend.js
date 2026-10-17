$(function () {
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
                        throw new Error(data.error || 'Reservation could not be saved.');
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
            })
            .catch(function (error) {
                $('<div>', {
                    class: 'alert alert-danger',
                    role: 'alert',
                    text: error.message
                }).appendTo(feedback);
            })
            .finally(function () {
                submitButton.prop('disabled', false);
            });
    });
});