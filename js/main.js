(function ($) {
    "use strict";
    
    // Dropdown on mouse hover
    $(document).ready(function () {
        function toggleNavbarMethod() {
            if ($(window).width() > 992) {
                $('.navbar .dropdown').on('mouseover', function () {
                    $('.dropdown-toggle', this).trigger('click');
                }).on('mouseout', function () {
                    $('.dropdown-toggle', this).trigger('click').blur();
                });
            } else {
                $('.navbar .dropdown').off('mouseover').off('mouseout');
            }
        }
        toggleNavbarMethod();
        $(window).resize(toggleNavbarMethod);
    });
    
    
    // Back to top button
    $(window).scroll(function () {
        if ($(this).scrollTop() > 100) {
            $('.back-to-top').fadeIn('slow');
        } else {
            $('.back-to-top').fadeOut('slow');
        }
    });
    $('.back-to-top').click(function () {
        $('html, body').animate({scrollTop: 0}, 1500, 'easeInOutExpo');
        return false;
    });

    // Add menu items to a cart that persists between the menu and checkout pages.
    $('#menuItems .row.align-items-center').each(function () {
        var itemName = $(this).find('h4').text().trim();
        $('<a>', {
            class: 'btn btn-primary btn-sm mt-2',
            href: '#',
            text: 'Add to Order',
            'data-order-item': itemName
        }).insertAfter($(this).find('p.m-0'));
    });

    $('#menuItems').on('click', '[data-order-item]', function (event) {
        event.preventDefault();
        var cartKey = 'coffeeShopCart';
        var cart = JSON.parse(localStorage.getItem(cartKey) || '[]');
        var itemName = $(this).attr('data-order-item');
        var cartItem = cart.find(function (item) {
            return item.name === itemName;
        });

        if (cartItem) {
            cartItem.quantity = Math.min(cartItem.quantity + 1, 99);
        } else {
            cart.push({ name: itemName, quantity: 1 });
        }

        localStorage.setItem(cartKey, JSON.stringify(cart));
        window.location.href = 'order.html';
    });
    

    // Date and time picker
    $('.date').datetimepicker({
        format: 'L'
    });
    $('.time').datetimepicker({
        format: 'LT'
    });


    // Testimonials carousel
    $(".testimonial-carousel").owlCarousel({
        autoplay: true,
        smartSpeed: 1500,
        margin: 30,
        dots: true,
        loop: true,
        center: true,
        responsive: {
            0:{
                items:1
            },
            576:{
                items:1
            },
            768:{
                items:2
            },
            992:{
                items:3
            }
        }
    });
    
})(jQuery);

