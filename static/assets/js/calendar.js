/* Workspace — calendario (/calendar/). FullCalendar (vendor/fullcalendar) con nuestra barra de Bootstrap.

   - Vistas: Mes (dayGridMonth), Semana (timeGridWeek) y Agenda (listMonth). En el teléfono abre en Agenda.
   - ‹ Hoy › mueven el periodo; el título lo da FullCalendar en español («octubre de 2026») con mayúscula inicial.
   - Cambiar de vista o de periodo no se anima: se usa a cada rato.
   - Aún no hay fechas del sistema: events está vacío (la página lo avisa). Cuando haya API, aquí va
     events: "/api/…" (FullCalendar pide start/end del periodo visible). */
(function ($) {
  "use strict";

  function capitalize(text) { return text ? text.charAt(0).toUpperCase() + text.slice(1) : text; }

  $(function () {
    var el = document.getElementById("ws-calendar");
    if (!el || !window.FullCalendar) { return; }
    var $title = $("[data-calendar-title]");
    var $views = $("[data-calendar-view]");
    var phone = window.matchMedia("(max-width: 575.98px)").matches;

    function markView(type) {
      $views.each(function () {
        var active = $(this).attr("data-calendar-view") === type;
        $(this).toggleClass("ws-btn-soft", active).toggleClass("btn-light border", !active)
          .attr("aria-pressed", active ? "true" : "false");
      });
    }

    var calendar = new window.FullCalendar.Calendar(el, {
      locale: "es",
      headerToolbar: false,                 // la barra es nuestra (Bootstrap)
      initialView: phone ? "listMonth" : "dayGridMonth",
      height: "auto",
      fixedWeekCount: false,
      dayMaxEvents: 3,
      nowIndicator: true,
      allDaySlot: true,
      slotMinTime: "07:00:00",
      slotMaxTime: "21:00:00",
      noEventsContent: "No hay fechas en este periodo.",
      events: [],
      datesSet: function (info) {
        $title.text(capitalize(info.view.title));
        markView(info.view.type);
      }
    });
    calendar.render();

    $("[data-calendar-nav]").on("click", function () {
      var action = $(this).attr("data-calendar-nav");
      if (action === "prev") { calendar.prev(); } else if (action === "next") { calendar.next(); } else { calendar.today(); }
    });
    $views.on("click", function () { calendar.changeView($(this).attr("data-calendar-view")); });
  });
})(jQuery);
