/* Workspace — Avisos (/notifications/): notificaciones de todo el sistema.

   - Lista paginada (25) desde /api/notifications/; «Ver anteriores» trae la siguiente página.
   - Cada aviso trae su título, descripción, ícono, color, fecha y enlace (lo decide quien lo
     crea: social, documentos, sistema…).
   - Tres estados, uno visible a la vez: loading (skeleton), empty (centrado) y ready (lista).
   - Si tiene enlace, toda la tarjeta lleva a él. Las no leídas llevan un punto azul.
   Etapa actual: solo mostrar (sin marcar leídas ni contador). */
(function ($) {
  "use strict";

  var api = window.Workspace.api;
  var COLORS = ["primary", "secondary", "success", "danger", "warning", "info"];
  var $root, $list, $more;
  var state = { next: null };

  function setState(name) {
    $root.find("[data-notifications-state]").each(function () {
      $(this).prop("hidden", $(this).attr("data-notifications-state") !== name);
    });
  }

  function render(n) {
    // Nativo: <template>.content solo existe en el DOM, jQuery no lo clona bien.
    var $item = $(document.getElementById("ws-notification-template").content.firstElementChild.cloneNode(true));
    var color = COLORS.indexOf(n.color) > -1 ? n.color : "primary";
    var icon = /^bx[sl]?-[\w-]+$/.test(n.icon) ? n.icon : "bx-bell";   // solo clases de Boxicons
    $item.attr("data-id", n.id).toggleClass("is-unread", !n.is_read);

    var $card = $item.find("[data-notification-card]");
    // Solo rutas internas ("/algo"): nunca enlaces externos ni "javascript:".
    if (n.url && n.url.charAt(0) === "/" && n.url.charAt(1) !== "/") {
      // Con enlace: la tarjeta completa es el enlace.
      var $link = $('<a class="ws-notification__card-link"></a>').attr("href", n.url);
      $card.wrap($link);
    }

    $item.find("[data-notification-tile]").addClass("bg-" + color + "-subtle text-" + color + "-emphasis")
      .find("i").addClass(icon);

    $item.find("[data-notification-title]").text(n.title);
    $item.find("[data-notification-body]").text(n.body).prop("hidden", !n.body);
    $item.find("[data-notification-time]")
      .text(window.Workspace.time.short(n.created_at))
      .attr({ datetime: n.created_at, title: window.Workspace.time.full(n.created_at) });
    return $item;
  }

  function load(url) {
    $more.prop("hidden", true);
    api(url).then(function (res) {
      if (res.status !== 200 || !res.data) {
        if (!$list.children().length) { setState("error"); }
        return;
      }
      $.each(res.data.results, function (_, n) { $list.append(render(n)); });
      state.next = res.data.next;
      $more.prop("hidden", !state.next);
      setState($list.children().length ? "ready" : "empty");
    });
  }

  $(function () {
    $root = $("[data-notifications]");
    if (!$root.length) { return; }
    $list = $root.find("[data-notification-list]");
    $more = $root.find("[data-notifications-more]");
    $root.on("click", "[data-notifications-next]", function () { if (state.next) { load(state.next); } });
    load($root.attr("data-notifications-url"));
  });
})(jQuery);
