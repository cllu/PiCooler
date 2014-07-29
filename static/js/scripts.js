$(function() {

  updateStatus();
  setInterval(updateStatus, 5000);

  $("#btn-aircon").click(function() {toggleSwitch("aircon")});
  $("#btn-humidifier").click(function() {toggleSwitch("humidifier")});
  $("#btn-auto").click(function() {toggleSwitch("auto")});
  
  function toggleSwitch(item) {
     $btn = $("#btn-" + item);
     current = $btn.hasClass("btn-primary");
     if (current == true) {
       $.post("/switch", {item: item, operation:"off"}, function(data) {
         if (data.status == "succeed") {
           $btn.removeClass("btn-primary");
         } else {
           console.log("failed", data.error);
         }
      });
    } else {
        $.post("/switch", {item: item, operation:"on"}, function(data) {
         if (data.status == "succeed") {
           $btn.addClass("btn-primary");
         } else {
           console.log("failed", data.error);
         }
      });
   
    } 
  }
  
  function updateStatus() {
    $.getJSON('/status', function(data) {
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
