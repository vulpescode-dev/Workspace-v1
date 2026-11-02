/* Workspace — widgets de la columna 3 de Inicio (pantallas ≥ 1200px).

   Cada [data-widget] pide su API y pasa por tres estados: loading (skeleton) → empty o lista.
   Solo se piden si la columna se ve (en el teléfono no existe, no se gastan peticiones); si la
   ventana crece hasta mostrarla, se cargan en ese momento. Si una petición falla, el widget
   muestra su texto de vacío con un aviso, sin romper los demás. */
(function ($) {
  "use strict";

  var api = window.Workspace.api;
  var MONTHS = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"];
  var COLORS = ["primary", "secondary", "success", "danger", "warning", "info"];

  function clone(id) {
    // Nativo: <template>.content solo existe en el DOM, jQuery no lo clona bien.
    return $(document.getElementById(id).content.firstElementChild.cloneNode(true));
  }

  function avatar(person) {
    var $avatar = $('<span class="ws-avatar rounded-circle d-inline-flex align-items-center justify-content-center fw-bold bg-primary-subtle text-primary" aria-hidden="true"></span>');
    window.Workspace.fillAvatar($avatar, person);
    return $avatar;
  }

  var renderers = {
    birthdays: function (b) {
      var $item = clone("ws-widget-birthday-template");
      $item.find("[data-field=link]").attr("href", window.Workspace.profileUrl(b.id)).toggleClass("is-today", b.is_today);
      $item.find("[data-field=date]").html(b.is_today ? "¡Hoy!" : b.day + "<br>" + MONTHS[b.month - 1]);
      $item.find("[data-field=name]").text(b.name);
      $item.find("[data-field=detail]").text(
        b.is_today ? "Cumple años hoy 🎉" : (b.days_until === 1 ? "Mañana" : "En " + b.days_until + " días") + (b.job_title ? " · " + b.job_title : "")
      );
      $item.find("[data-field=avatar]").replaceWith(avatar(b));
      return $item;
    },
    suggestions: function (p) {
      var $item = clone("ws-widget-person-template");
      $item.find("[data-field=link]").attr("href", window.Workspace.profileUrl(p.id));
      $item.find("[data-field=avatar]").replaceWith(avatar(p));
      $item.find("[data-field=name]").text(p.name);
      $item.find("[data-field=detail]").text(p.job_title || "");
      $item.find("[data-follow-btn]").attr({ "data-user-id": p.id, "aria-label": "Seguir a " + p.name });
      return $item;
    },
    notifications: function (n) {
      var $item = clone("ws-widget-notice-template");
      var color = COLORS.indexOf(n.color) > -1 ? n.color : "primary";
      var icon = /^bx[sl]?-[\w-]+$/.test(n.icon) ? n.icon : "bx-bell";   // solo clases de Boxicons
      // Solo rutas internas ("/algo"); si no tiene enlace, lleva a la página de avisos.
      var url = n.url && n.url.charAt(0) === "/" && n.url.charAt(1) !== "/" ? n.url : $("[data-widget=notifications] a").first().attr("href");
      $item.find("[data-field=link]").attr("href", url);
      $item.find("[data-field=tile]").addClass("bg-" + color + "-subtle text-" + color + "-emphasis").find("i").addClass(icon);
      $item.find("[data-field=name]").text(n.title);
      $item.find("[data-field=time]").text(window.Workspace.time.short(n.created_at))
        .attr({ datetime: n.created_at, title: window.Workspace.time.full(n.created_at) });
      return $item;
    }
  };

  function setState($widget, state) {
    $widget.find("[data-widget-state]").each(function () {
      $(this).prop("hidden", $(this).attr("data-widget-state") !== state);
    });
    $widget.find("[data-widget-list]").prop("hidden", state !== "ready");
  }

  function load($widget) {
    var name = $widget.attr("data-widget");
    api($widget.attr("data-widget-url")).then(function (res) {
      var items = res.data && (Array.isArray(res.data) ? res.data : res.data.results);
      if (res.status !== 200 || !items) {
        $widget.find("[data-widget-state=empty]").text("No se pudo cargar. Recarga la página.");
        setState($widget, "empty");
        return;
      }
      var $list = $widget.find("[data-widget-list]").empty();
      $.each(items, function (_, item) { $list.append(renderers[name](item)); });
      setState($widget, items.length ? "ready" : "empty");
    });
  }

  $(function () {
    var $aside = $("[data-widgets]");
    if (!$aside.length) { return; }
    var loaded = false;
    function loadIfVisible() {
      if (loaded || !$aside.is(":visible")) { return; }
      loaded = true;
      $aside.find("[data-widget]").each(function () { load($(this)); });
      $(window).off("resize.widgets");
    }
    loadIfVisible();
    $(window).on("resize.widgets", loadIfVisible);
  });
})(jQuery);
