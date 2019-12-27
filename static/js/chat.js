/*jslint browser: true*/
/*global $, jQuery, alert*/

$(function () {

    "use strict";

    $('.chat-left-inner > .chatonline').slimScroll({
        height: '100%',
        position: 'right',
        size: "5px",
        color: '#dcdcdc'

    });
    $('.chat-list').slimScroll({
        position: 'right'
        , size: "5px"
        , height: '100%'
        , color: '#dcdcdc'
     });
    
    var cht = function () {
            var topOffset = 445;
            var height = ((window.innerHeight > 0) ? window.innerHeight : this.screen.height) - 1;
            height = height - topOffset;
            $(".chat-list").css("height", (height) + "px");
    };
    $(window).ready(cht);
    $(window).on("resize", cht);
    
    

    // this is for the left-aside-fix in content area with scroll
    var chtin = function () {
            var topOffset = 270;
            var height = ((window.innerHeight > 0) ? window.innerHeight : this.screen.height) - 1;
            height = height - topOffset;
            $(".chat-left-inner").css("height", (height) + "px");
    };
    $(window).ready(chtin);
    $(window).on("resize", chtin);
    
    


    $(".open-panel").on("click", function () {
        $(".chat-left-aside").toggleClass("open-pnl");
        $(".open-panel i").toggleClass("ti-angle-left");
    });

});
