(function($) {
    "use strict";

    // search active code
    $("#search-btn, #closeBtn").on("click", function() {
        $("body").toggleClass("search-form-on");
    });
    // sticky active
    var $window = $(window);
    $window.on("scroll", function() {
        if ($window.scrollTop() > 0) {
            $("body").addClass("sticky");
        } else {
            $("body").removeClass("sticky");
        }

    });

})(jQuery);