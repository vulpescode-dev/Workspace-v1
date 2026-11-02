/* Workspace — reacciones con emojis (Noto Animated Emoji).

   - Catálogo: /api/catalogs/emojis/ (una sola petición por página).
   - Pastillas 20px con SVG estático; el emoji elegido se anima UNA vez al reaccionar.
   - Selector (offcanvas inferior) con SVG 36px; se anima el emoji bajo el puntero o con foco.
   - lottie-web se descarga solo la primera vez que hace falta animar. Con «reducir movimiento», nada se anima.
   - Actualización optimista: la pastilla cambia al instante y se corrige con la respuesta del servidor.

   Funciona igual para posts y comentarios: cualquier elemento con [data-reaction-host] y
   data-reaction-url (PUT/DELETE de mi reacción) es un «anfitrión»; data-reactions-url (opcional)
   habilita «Ver todo». Los anfitriones pueden anidarse (respuestas dentro de un comentario):
   cada uno solo toca sus propias pastillas (ver own()).

   API pública (la usan feed.js y comments.js):  Workspace.reactions.ready  (promesa del catálogo)
                                                  Workspace.reactions.render($host, summary) */
(function ($) {
  "use strict";

  var script = document.currentScript;
  var LOTTIE_SRC = script.getAttribute("data-lottie-src");
  var EMOJIS_URL = script.getAttribute("data-emojis-url");
  var api = window.Workspace.api;
  var catalog = {};          // code → emoji
  var ordered = [];          // emojis activos en orden, para el selector
  var lottieLoading = null;  // promesa de carga de lottie-web
  var pickerHost = null;     // anfitrión al que se le está eligiendo emoji

  /* Elementos de $host que no pertenecen a un anfitrión anidado. */
  function own($host, selector) {
    return $host.find(selector).filter(function () { return $(this).closest("[data-reaction-host]").is($host); });
  }

  /* ---- Catálogo ------------------------------------------------------- */
  var ready = api(EMOJIS_URL).then(function (res) {
    if (res.status !== 200 || !res.data) { return; }
    $.each(res.data, function (_, emoji) {
      catalog[emoji.code] = emoji;
      if (emoji.is_active) { ordered.push(emoji); }
    });
  });

  /* ---- Animación (Lottie bajo demanda) --------------------------------- */
  function ensureLottie() {
    if (window.lottie) { return $.Deferred().resolve().promise(); }
    if (!lottieLoading) {
      lottieLoading = $.ajax({ url: LOTTIE_SRC, dataType: "script", cache: true });
    }
    return lottieLoading;
  }

  /* Anima una vez el emoji dentro de $holder (.ws-emoji con su <img>) y vuelve al SVG estático. */
  function playOnce($holder, code) {
    var emoji = catalog[code];
    if (!emoji || window.Workspace.reducedMotion() || $holder.hasClass("is-playing")) { return; }
    $holder.addClass("is-playing");
    ensureLottie().then(function () {
      var $stage = $('<span class="ws-emoji__stage" aria-hidden="true"></span>').appendTo($holder);
      var anim = window.lottie.loadAnimation({
        container: $stage[0], renderer: "svg", loop: false, autoplay: true, path: emoji.lottie_url
      });
      // El SVG estático se oculta solo cuando la animación ya pintó: sin parpadeo en blanco.
      anim.addEventListener("DOMLoaded", function () { $holder.addClass("is-animating"); });
      function done() {
        anim.destroy();
        $stage.remove();
        $holder.removeClass("is-playing is-animating");
      }
      anim.addEventListener("complete", done);
      anim.addEventListener("data_failed", done);
    }, function () { $holder.removeClass("is-playing"); });
  }

  /* ---- Pastillas ------------------------------------------------------ */
  function chipLabel(emoji, count, mine) {
    var name = emoji ? emoji.label : "Emoji";
    var people = count === 1 ? "1 persona" : count + " personas";
    return mine ? name + ": " + people + ". Quitar tu reacción" : name + ": " + people + ". Reaccionar con " + name;
  }

  function buildChip(reaction, mine) {
    var node = document.getElementById("ws-reaction-chip-template").content.firstElementChild.cloneNode(true);
    var emoji = catalog[reaction.emoji];
    var $chip = $(node).attr("data-emoji", reaction.emoji);
    var $img = $chip.find("img");
    if (emoji) {
      $img.attr({ src: emoji.svg_url, alt: "" });
    } else {
      $img.replaceWith(document.createTextNode("?"));
    }
    updateChip($chip, reaction.count, mine);
    return $chip;
  }

  function updateChip($chip, count, mine) {
    var emoji = catalog[$chip.attr("data-emoji")];
    $chip.find("[data-reaction-count]").text(count);
    $chip.toggleClass("is-mine", mine)
      .attr({ "aria-pressed": mine ? "true" : "false", "aria-label": chipLabel(emoji, count, mine), title: emoji ? emoji.label : "" });
  }

  /* Pinta el resumen sin rehacer las pastillas que no cambiaron (no se reinician animaciones ni saltan). */
  function render($host, summary, options) {
    options = options || {};
    $host.data("reactions", summary);
    var $chips = own($host, "[data-reaction-chips]");
    var counts = {};
    $.each(summary.reactions, function (_, r) { counts[r.emoji] = r.count; });

    $chips.children("[data-reaction-chip]").each(function () {
      var code = $(this).attr("data-emoji");
      if (!counts[code]) { $(this).remove(); } else { updateChip($(this), counts[code], summary.mine === code); }
    });
    $.each(summary.reactions, function (_, r) {
      if (!$chips.children('[data-emoji="' + r.emoji + '"]').length) {
        var $chip = buildChip(r, summary.mine === r.emoji);
        if (options.animate === r.emoji) { $chip.addClass("ws-reaction--new"); }
        $chips.append($chip);
      }
    });
    own($host, "[data-reactions-all]").prop("hidden", !summary.total);
    own($host, "[data-post-reactions]").toggleClass("has-reactions", summary.total > 0);
    if (options.animate) { playOnce($chips.children('[data-emoji="' + options.animate + '"]').find("[data-reaction-emoji]"), options.animate); }
  }

  /* ---- Reaccionar (optimista) ----------------------------------------- */
  function nextSummary(summary, code) {
    var reactions = $.map(summary.reactions, function (r) { return { emoji: r.emoji, count: r.count }; });
    function bump(target, delta) {
      var found = null;
      $.each(reactions, function (_, r) { if (r.emoji === target) { found = r; } });
      if (found) { found.count += delta; } else if (delta > 0) { reactions.push({ emoji: target, count: delta }); }
    }
    var removing = summary.mine === code;
    if (summary.mine) { bump(summary.mine, -1); }
    if (!removing) { bump(code, 1); }
    reactions = $.grep(reactions, function (r) { return r.count > 0; });
    var total = 0;
    $.each(reactions, function (_, r) { total += r.count; });
    return { reactions: reactions, total: total, mine: removing ? null : code };
  }

  function react($host, code) {
    if ($host.data("reacting")) { return; }
    var previous = $host.data("reactions");
    var optimistic = nextSummary(previous, code);
    var url = $host.attr("data-reaction-url");
    $host.data("reacting", true);
    render($host, optimistic, { animate: optimistic.mine === code ? code : null });

    var request = optimistic.mine ? api(url, { method: "PUT", body: { emoji: code } }) : api(url, { method: "DELETE" });
    request.then(function (res) {
      if (res.status === 200 && res.data) {
        render($host, res.data);
      } else {
        render($host, previous);
        window.Workspace.toast(res.status === 0 ? "Sin conexión. Inténtalo de nuevo." : "No se pudo guardar tu reacción.");
      }
    }).always(function () { $host.removeData("reacting"); });
  }

  /* ---- Selector -------------------------------------------------------- */
  function buildPicker() {
    var $grid = $("[data-emoji-grid]");
    if (!$grid.length || $grid.children().length) { return; }
    $.each(ordered, function (_, emoji) {
      $('<button type="button" class="btn ws-emoji-option"></button>')
        .attr({ "data-emoji": emoji.code, "aria-label": emoji.label, title: emoji.label })
        .append($('<span class="ws-emoji ws-emoji--36"></span>').append(
          $('<img width="36" height="36" alt="" loading="lazy" decoding="async">').attr("src", emoji.svg_url)
        ))
        .appendTo($grid);
    });
  }

  function openPicker($host) {
    pickerHost = $host;
    buildPicker();
    var mine = ($host.data("reactions") || {}).mine;
    $("[data-emoji-grid] .ws-emoji-option").each(function () {
      var selected = $(this).attr("data-emoji") === mine;
      $(this).toggleClass("is-selected", selected).attr("aria-pressed", selected ? "true" : "false");
    });
    window.bootstrap.Offcanvas.getOrCreateInstance(document.getElementById("ws-emoji-picker")).show();
  }

  /* ---- «Ver todo» ----------------------------------------------------- */
  var modalState = { next: null };

  function appendRows(results) {
    var template = document.getElementById("ws-reaction-row-template");
    var $list = $("[data-reactions-list]");
    $.each(results, function (_, item) {
      var $row = $(template.content.firstElementChild.cloneNode(true));
      var emoji = catalog[item.emoji];
      window.Workspace.fillAvatar($row.find("[data-row-initials]"), item.user);
      $row.find("[data-row-name]").text(item.user.name);
      if (emoji) { $row.find("[data-row-emoji] img").attr({ src: emoji.svg_url, alt: emoji.label }); }
      $list.append($row);
    });
  }

  function loadRows(url) {
    $("[data-reactions-loading]").prop("hidden", false);
    $("[data-reactions-more]").prop("hidden", true);
    api(url).then(function (res) {
      $("[data-reactions-loading]").prop("hidden", true);
      if (res.status !== 200 || !res.data) { window.Workspace.toast("No se pudieron cargar las reacciones."); return; }
      appendRows(res.data.results);
      modalState.next = res.data.next;
      $("[data-reactions-more]").prop("hidden", !modalState.next);
    });
  }

  function openAll($host) {
    var summary = $host.data("reactions") || { reactions: [] };
    var $summary = $("[data-reactions-summary]").empty();
    $.each(summary.reactions, function (_, r) {
      var emoji = catalog[r.emoji];
      $('<span class="badge rounded-pill text-bg-light border d-inline-flex align-items-center gap-1 fs-6 fw-semibold"></span>')
        .append(emoji ? $('<img width="20" height="20" alt="">').attr({ src: emoji.svg_url, alt: emoji.label }) : r.emoji)
        .append(document.createTextNode(String(r.count)))
        .appendTo($summary);
    });
    $("[data-reactions-list]").empty();
    window.bootstrap.Modal.getOrCreateInstance(document.getElementById("ws-reactions-modal")).show();
    loadRows($host.attr("data-reactions-url"));
  }

  /* ---- Eventos -------------------------------------------------------- */
  $(document)
    .on("click", "[data-reaction-chip]", function () {
      react($(this).closest("[data-reaction-host]"), $(this).attr("data-emoji"));
    })
    .on("click", "[data-reaction-add]", function () {
      var $host = $(this).closest("[data-reaction-host]");
      ready.then(function () { openPicker($host); });
    })
    .on("click", "[data-emoji-grid] .ws-emoji-option", function () {
      var code = $(this).attr("data-emoji");
      var $host = pickerHost;
      var offcanvas = document.getElementById("ws-emoji-picker");
      // Se reacciona al cerrarse el selector, para que la animación de la pastilla se vea.
      $(offcanvas).one("hidden.bs.offcanvas", function () {
        if ($host && ($host.data("reactions") || {}).mine !== code) { react($host, code); }
      });
      window.bootstrap.Offcanvas.getOrCreateInstance(offcanvas).hide();
    })
    .on("click", "[data-reactions-all]", function () {
      openAll($(this).closest("[data-reaction-host]"));
    })
    .on("click", "[data-reactions-next]", function () {
      if (modalState.next) { loadRows(modalState.next); }
    })
    // Vista previa animada en el selector: con puntero fino al pasar encima, o con el foco del teclado.
    .on("focus", "[data-emoji-grid] .ws-emoji-option", function () {
      playOnce($(this).find(".ws-emoji"), $(this).attr("data-emoji"));
    });

  if (window.matchMedia && window.matchMedia("(hover: hover) and (pointer: fine)").matches) {
    $(document).on("mouseenter", "[data-emoji-grid] .ws-emoji-option", function () {
      playOnce($(this).find(".ws-emoji"), $(this).attr("data-emoji"));
    });
  }

  window.Workspace.reactions = { ready: ready, render: render };
})(jQuery);
