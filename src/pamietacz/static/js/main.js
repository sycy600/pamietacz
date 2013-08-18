$("#show_answer").click(function() {
    $("#answer").show();
    $(this).attr("disabled", "disabled");
    $(this).blur();
});

$(window).keypress(function(event) {
    if (event.which == "s".charCodeAt(0)) {
        $("#show_answer").click();
    }
    else if($("#show_answer").is(":disabled"))
    {
        if (["1".charCodeAt(0), "2".charCodeAt(0), "3".charCodeAt(0)].indexOf(event.which) != -1) {
            var option_button_name = "option_" + String.fromCharCode(event.which);
            $("#" + option_button_name).click();
        }
    }
});

$('input[id^="option_"]').click(function() {
    $(this).css("color", "red");
});