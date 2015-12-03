$(function () {

  // A global error handler
  $(document).ajaxError(function (event, jqxhr, settings, thrownError) {
    console.log("request failed");
    console.log(jqxhr.responseJSON);
  });

  updateStatus();
  setInterval(updateStatus, 5000);

  // add click listens for the three toggle switches
  $("#btn-aircon").click(function () {
    toggleSwitch("aircon")
  });
  $("#btn-humidifier").click(function () {
    toggleSwitch("humidifier")
  });
  $("#btn-auto").click(function () {
    toggleSwitch("auto")
  });

  function toggleSwitch(item) {
    $btn = $("#btn-" + item);
    current = $btn.hasClass("btn-primary");
    if (current == true) {
      $.post("/switch", {item: item, operation: "off"}, function () {
        $btn.removeClass("btn-primary");
      });
    } else {
      $.post("/switch", {item: item, operation: "on"}, function () {
        $btn.addClass("btn-primary");
      });
    }
  }

  function updateStatus() {
    $.getJSON('/status', function (data) {
      if (data.humidifier == 0) {
        $("#btn-humidifier").removeClass("btn-primary");
      } else {
        $("#btn-humidifier").addClass("btn-primary");
      }
      if (data.aircon == 0) {
        $("#btn-aircon").removeClass("btn-primary");
      } else {
        $("#btn-aircon").addClass("btn-primary");
      }
      if (data.auto_mode == 0) {
        $("#btn-auto").removeClass("btn-primary");
      } else {
        $("#btn-auto").addClass("btn-primary");
      }

      if (data.temp != null) {
        $("#temp").html(data.temp);
        $("#humidity").html(data.humidity);
      }
    });
  }

});
