(function (factory) {
    if (typeof define === 'function' && define.amd) {
        define(['jquery'], factory);
    } else {
        factory(jQuery);
    }
}(function ($) {
    var uarr = String.fromCharCode(0x25b6),
        darr = String.fromCharCode(0x25bc);

    $('a.stackTrace').on('click', function() {
        var arrow = $(this).children('.toggleArrow');
        arrow.html(arrow.html() == uarr ? darr : uarr);
        $(this).closest('tr').next(':first').toggle();
        return false;
    });
}));
