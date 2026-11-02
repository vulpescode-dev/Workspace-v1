/* Workspace — página Buscar (/search/).

   - Filtros [data-ws-search-scope]: eligen dónde buscar y cambian el texto de ayuda. Sin animación
     (se usan a cada rato); solo el subrayado marca el elegido.
   - Enviar: con «Personas» abre el directorio con lo escrito (/people/?q=). La búsqueda general y la de
     documentos, avisos y formularios llega en una etapa posterior: avisa «Próximamente», nunca un
     resultado falso. */
(function ($) {
  "use strict";

  function soon(message) {
    var $toast = $("#ws-toast");
    $toast.find("[data-ws-toast-body]").text(message);
    window.bootstrap.Toast.getOrCreateInstance($toast[0], { delay: 2800 }).show();
  }

  $(function () {
    var $form = $("[data-ws-search]");
    if (!$form.length) { return; }
    var $input = $("#ws-search-input");

    $(document).on("click", "[data-ws-search-scope]", function () {
      var $scope = $(this);
      $("[data-ws-search-scope]").removeClass("is-active").attr("aria-pressed", "false");
      $scope.addClass("is-active").attr("aria-pressed", "true");
      $input.attr("placeholder", $scope.attr("data-placeholder")).trigger("focus");
    });

    $form.on("submit", function (event) {
      event.preventDefault();
      var q = $.trim($input.val());
      if (!q) { $input.trigger("focus"); return; }
      var $scope = $("[data-ws-search-scope].is-active");
      if ($scope.attr("data-ws-search-scope") === "people") {
        window.location.href = $form.attr("data-people-url") + "?q=" + encodeURIComponent(q);
        return;
      }
      soon($scope.attr("data-soon") || "La búsqueda en todo Workspace estará disponible próximamente.");
    });
  });
})(jQuery);
