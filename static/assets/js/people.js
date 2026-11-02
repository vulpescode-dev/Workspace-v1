/* Workspace — directorio de personas (/people/).

   - Pide /api/accounts/users/?search=&page= (25 por página) y pinta tarjetas; «Ver más» trae la siguiente.
   - Busca mientras escribes con una pausa de 300 ms; solo se pinta la respuesta de la última búsqueda
     (si una vieja llega tarde, se ignora). La búsqueda queda en la URL (?q=) para recargar o compartir.
   - Si la API dice que la página ya no existe (404 con total_pages), se deja de pedir más sin romper la lista.
   - El botón Seguir lo maneja follow.js. */
(function ($) {
  "use strict";

  var api = window.Workspace.api;
  var DEBOUNCE_MS = 300;
  var $root, $grid, $count, $more, $input;
  var state = { next: null, request: 0, timer: null };

  function setState(name) {
    $root.find("[data-people-state]").each(function () {
      $(this).prop("hidden", $(this).attr("data-people-state") !== name);
    });
    $grid.attr("aria-busy", name === "loading" ? "true" : "false");
  }

  function renderCount(count, query) {
    var people = count === 1 ? "1 persona" : count.toLocaleString("es-MX") + " personas";
    $count.text(query ? people + " para «" + query + "»" : people);
  }

  function renderCard(person) {
    // Nativo: <template>.content solo existe en el DOM, jQuery no lo clona bien.
    var $card = $(document.getElementById("ws-person-card-template").content.firstElementChild.cloneNode(true));
    var href = window.Workspace.profileUrl(person.id);
    window.Workspace.fillAvatar($card.find("[data-person-avatar]"), person);
    $card.find("[data-person-link]").attr({ href: href, "aria-label": "Ver perfil de " + person.name });
    // Nombre › cargo › área. Sin cargo se muestra el correo; title= deja leer lo que se recorta con «…».
    $card.find("[data-person-name]").text(person.name).attr("title", person.name);
    var title = person.job_title || person.email;
    $card.find("[data-person-title]").text(title).attr("title", title);
    $card.find("[data-person-dept]").text(person.department).attr("title", person.department).prop("hidden", !person.department);
    var $btn = $card.find("[data-follow-btn]").attr("data-user-id", person.id).prop("hidden", person.is_me);
    window.Workspace.follow.setButton($btn, person.is_following);
    $card.find("[data-person-me]").attr("href", href).prop("hidden", !person.is_me);
    return $card;
  }

  function query() { return $.trim($input.val()); }

  function load(url, append) {
    var request = ++state.request;
    if (!append) { $grid.empty(); setState("loading"); }
    $more.prop("hidden", true);
    api(url).then(function (res) {
      if (request !== state.request) { return; }   // llegó tarde: ya hay una búsqueda más nueva
      if (res.status === 404 && res.data && res.data.total_pages !== undefined) {
        // La página pedida ya no existe (p. ej. cambió el número de personas): no se piden más.
        state.next = null;
        setState($grid.children().length ? "ready" : "empty");
        return;
      }
      if (res.status !== 200 || !res.data) { setState("error"); return; }
      $.each(res.data.results, function (_, person) { $grid.append(renderCard(person)); });
      renderCount(res.data.count, query());
      state.next = res.data.next;
      $more.prop("hidden", !state.next);
      setState($grid.children().length ? "ready" : "empty");
    });
  }

  function search() {
    var q = query();
    var url = $root.attr("data-people-url") + (q ? "?search=" + encodeURIComponent(q) : "");
    if (window.history && window.history.replaceState) {
      window.history.replaceState(null, "", window.location.pathname + (q ? "?q=" + encodeURIComponent(q) : ""));
    }
    load(url, false);
  }

  $(function () {
    $root = $("[data-people]");
    if (!$root.length) { return; }
    $grid = $root.find("[data-people-grid]");
    $count = $root.find("[data-people-count]");
    $more = $root.find("[data-people-more]");
    $input = $root.find("#ws-people-q");

    $input.on("input", function () {
      window.clearTimeout(state.timer);
      state.timer = window.setTimeout(search, DEBOUNCE_MS);
    });
    $root.find("[data-people-search]").on("submit", function (event) {
      event.preventDefault();
      window.clearTimeout(state.timer);
      search();
      $input.trigger("blur");   // en el teléfono cierra el teclado al pulsar «Buscar»
    });
    $root.on("click", "[data-people-next]", function () { if (state.next) { load(state.next, true); } });

    search();
  });
})(jQuery);
