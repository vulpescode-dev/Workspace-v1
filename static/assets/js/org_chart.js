/* Workspace — organigrama (/people/org/).

   - Pide /api/org/chart/?depth=10 (árbol por jefe directo) y lo aplana a filas { id, parentId } para
     d3-org-chart. Si hay varias cabezas, cuelgan de un nodo «Workspace» para que haya una sola raíz.
   - Tarjetas con la misma jerarquía que Personas: foto, nombre (enlace al perfil) › cargo › departamento.
   - Buscar (con sugerencias del <datalist>) abre la rama, centra y resalta a la persona.
   - Movimiento: el árbol aparece ya armado (sin animación de entrada); 250 ms al abrir/cerrar ramas;
     nada con «reducir movimiento». */
(function ($) {
  "use strict";

  var NODE_WIDTH = 248;
  var NODE_HEIGHT = 92;
  var COMPANY_ID = "company";
  var chart = null;
  var people = {};   // nombre en minúsculas → id de nodo (para el buscador)

  function escapeHtml(text) {
    return $("<div>").text(text == null ? "" : String(text)).html();
  }

  function flatten(roots) {
    var rows = [];
    var parentOfRoots = null;
    if (roots.length > 1) {
      rows.push({ id: COMPANY_ID, parentId: null, isCompany: true, reports: roots.length });
      parentOfRoots = COMPANY_ID;
    }
    function walk(node, parentId) {
      rows.push({ id: String(node.id), parentId: parentId, person: node, reports: node.reports_count });
      $.each(node.children, function (_, child) { walk(child, String(node.id)); });
    }
    $.each(roots, function (_, root) { walk(root, parentOfRoots); });
    return rows;
  }

  function avatarHtml(person) {
    var style = person.avatar_url ? " style=\"background-image:url('" + encodeURI(person.avatar_url) + "')\"" : "";
    var cls = "ws-avatar ws-org-node__avatar rounded-circle d-inline-flex align-items-center justify-content-center fw-bold bg-primary-subtle text-primary" +
      (person.avatar_url ? " has-image" : "");
    return "<span class=\"" + cls + "\"" + style + " aria-hidden=\"true\">" + (person.avatar_url ? "" : escapeHtml(person.initials)) + "</span>";
  }

  function nodeHtml(d) {
    var row = d.data;
    var highlighted = row._highlighted || row._upToTheRootHighlighted ? " is-highlighted" : "";
    if (row.isCompany) {
      return "<div class=\"ws-org-node ws-org-node--company" + highlighted + "\" style=\"width:" + d.width + "px;height:" + d.height + "px\">" +
        "<span class=\"ws-org-node__logo\" aria-hidden=\"true\"><i class=\"bx bx-buildings\"></i></span>" +
        "<div class=\"ws-org-node__text\"><div class=\"ws-org-node__name\">Workspace</div>" +
        "<div class=\"ws-org-node__title\">Toda la empresa</div></div></div>";
    }
    var person = row.person;
    var dept = person.department ? "<span class=\"ws-org-node__dept\">" + escapeHtml(person.department.name) + "</span>" : "";
    return "<div class=\"ws-org-node" + highlighted + "\" style=\"width:" + d.width + "px;height:" + d.height + "px\">" +
      avatarHtml(person) +
      "<div class=\"ws-org-node__text\">" +
        "<a class=\"ws-org-node__name\" href=\"" + escapeHtml(window.Workspace.profileUrl(person.id)) + "\" title=\"" + escapeHtml(person.name) + "\">" + escapeHtml(person.name) + "</a>" +
        "<div class=\"ws-org-node__title\" title=\"" + escapeHtml(person.job_title) + "\">" + escapeHtml(person.job_title || "Sin cargo") + "</div>" +
        dept +
      "</div></div>";
  }

  function buttonHtml(params) {
    var node = params.node;
    var icon = node.children ? "bx-chevron-up" : "bx-chevron-down";
    return "<div class=\"ws-org-toggle\"><i class=\"bx " + icon + "\" aria-hidden=\"true\"></i>" + node.data._directSubordinates + "</div>";
  }

  function setState($root, name) {
    $root.find("[data-org-state]").each(function () {
      $(this).prop("hidden", $(this).attr("data-org-state") !== name);
    });
    $root.find("[data-org-canvas]").toggleClass("is-ready", name === "ready");
    $root.find("[data-org-toolbar]").prop("hidden", name !== "ready");
  }

  function renderCount($root, rows, unassigned) {
    var total = $.grep(rows, function (row) { return !row.isCompany; }).length;
    $root.find("[data-org-count]").text(total === 1 ? "1 persona en el organigrama" : total.toLocaleString("es-MX") + " personas en el organigrama");
    $root.find("[data-org-unassigned]")
      .text(unassigned === 1 ? "1 persona todavía no tiene jefe directo ni personas a cargo." :
        unassigned + " personas todavía no tienen jefe directo ni personas a cargo.")
      .prop("hidden", !unassigned);
  }

  function fillSearch($root, rows) {
    var $list = $root.find("[data-org-people]").empty();
    $.each(rows, function (_, row) {
      if (row.isCompany) { return; }
      people[row.person.name.toLowerCase()] = row.id;
      $list.append($("<option>").attr("value", row.person.name));
    });
  }

  function findPerson(query) {
    query = $.trim(query).toLowerCase();
    if (!query) { return null; }
    if (people[query]) { return people[query]; }
    var found = null;
    $.each(people, function (name, id) {
      if (name.indexOf(query) !== -1) { found = id; return false; }
    });
    return found;
  }

  function draw($root, rows) {
    var reduced = window.Workspace.reducedMotion();
    chart = new d3.OrgChart()
      .container($root.find("[data-org-canvas]").get(0))
      .data(rows)
      .nodeId(function (row) { return row.id; })
      .parentNodeId(function (row) { return row.parentId; })
      .nodeWidth(function () { return NODE_WIDTH; })
      .nodeHeight(function () { return NODE_HEIGHT; })
      // Sin modo compacto: en 3.1.1 «fit» no cuenta el acomodo compacto y deja tarjetas fuera del cuadro.
      .compact(false)
      .childrenMargin(function () { return 56; })
      .siblingsMargin(function () { return 20; })
      .neighbourMargin(function () { return 24; })
      .initialExpandLevel(2)
      .initialZoom(0.85)
      .duration(0)   // el primer dibujo aparece ya armado; la animación es solo para abrir/cerrar ramas
      .svgHeight($root.find("[data-org-canvas]").height())
      .nodeContent(nodeHtml)
      .buttonContent(buttonHtml)
      // El resaltado lo pinta .ws-org-node.is-highlighted; sin el marco rosa que trae la librería.
      .nodeUpdate(function () { d3.select(this).select(".node-rect").attr("stroke", "none"); })
      .linkUpdate(function (d) {
        var on = d.data._upToTheRootHighlighted;
        d3.select(this).attr("stroke", on ? "var(--bs-primary)" : "var(--bs-border-color)").attr("stroke-width", on ? 2 : 1.25);
        if (on) { d3.select(this).raise(); }
      })
      .render();
    frame($root);
    chart.duration(reduced ? 0 : 250);
  }

  /* Primer encuadre: todo si se puede leer (escala ≥ MIN_READABLE_SCALE); si no, centrado a tamaño
     legible para moverse arrastrando. «Ajustar» siempre muestra todo. */
  var MIN_READABLE_SCALE = 0.7;
  function frame($root) {
    var nodes = chart.getChartState().root.descendants();
    var xs = $.map(nodes, function (node) { return node.x; });
    var treeWidth = Math.max.apply(null, xs) - Math.min.apply(null, xs) + NODE_WIDTH + 100;
    var scale = $root.find("[data-org-canvas]").width() / treeWidth;
    if (scale >= MIN_READABLE_SCALE) { chart.fit(); return; }
    // A escala fija: la cabeza centrada a lo ancho y arriba (debajo de la barra de controles).
    var state = chart.getChartState();
    var top = 64 / state.lastTransform.k;
    chart.zoomTreeBounds({
      params: { animate: false, scale: false },
      x0: -NODE_WIDTH / 2, x1: NODE_WIDTH / 2, y0: -top, y1: state.svgHeight / state.lastTransform.k - top,
    });
  }

  function focusPerson(id) {
    if (!chart || !id) { return false; }
    chart.clearHighlighting();
    chart.setUpToTheRootHighlighted(id).setCentered(id).render();
    return true;
  }

  $(function () {
    var $root = $("[data-org-chart]");
    if (!$root.length || !window.d3 || !d3.OrgChart) { return; }

    window.Workspace.api($root.attr("data-org-chart-url")).then(function (res) {
      if (res.status !== 200 || !res.data) { setState($root, "error"); return; }
      var rows = flatten(res.data.roots);
      renderCount($root, rows, res.data.unassigned_count);
      if (!res.data.roots.length) { setState($root, "empty"); return; }
      setState($root, "ready");
      fillSearch($root, rows);
      draw($root, rows);
    });

    $root.on("click", "[data-org-action]", function () {
      if (!chart) { return; }
      var action = $(this).attr("data-org-action");
      if (action === "fit") { chart.fit(); }
      if (action === "expand") { chart.expandAll().fit(); }
      if (action === "collapse") { chart.clearHighlighting(); chart.collapseAll().fit(); }
      if (action === "zoom-in") { chart.zoomIn(); }
      if (action === "zoom-out") { chart.zoomOut(); }
    });

    var $input = $root.find("#ws-org-q");
    $root.find("[data-org-search]").on("submit", function (event) {
      event.preventDefault();
      var found = focusPerson(findPerson($input.val()));
      $input.toggleClass("is-invalid", !found && $.trim($input.val()) !== "");
      if (found) { $input.trigger("blur"); }   // en el teléfono cierra el teclado
    });
    // Elegir una sugerencia del <datalist> no envía el formulario: se busca al coincidir exacto.
    $input.on("input", function () {
      $input.removeClass("is-invalid");
      var id = people[$.trim($input.val()).toLowerCase()];
      if (id) { focusPerson(id); }
      if (!$.trim($input.val()) && chart) { chart.clearHighlighting(); }
    });

    // El lienzo cambia de alto con la ventana (teléfono girado, barra del navegador).
    var resizeTimer = null;
    $(window).on("resize", function () {
      window.clearTimeout(resizeTimer);
      resizeTimer = window.setTimeout(function () {
        if (chart) { chart.svgHeight($root.find("[data-org-canvas]").height()).render(); }
      }, 200);
    });
  });
})(jQuery);
