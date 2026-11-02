/* Workspace — botón Seguir / Siguiendo, compartido (perfil, listas de seguidores, directorio).

   Marcado: <button data-follow-btn data-user-id="5" aria-pressed="false"><i …></i><span data-follow-label>Seguir</span></button>
   - Optimista: cambia al instante y se corrige con la respuesta del servidor.
   - Al terminar dispara en document el evento "ws:follow" con { userId, stats } para que cada página
     actualice sus contadores (stats = followers_count, following_count, is_following, follows_me).
   API: Workspace.follow.setButton($btn, following)
   data-follow-variant="soft": «Seguir» con fondo azul claro (para listas donde el botón se repite). */
(function ($) {
  "use strict";

  var api = window.Workspace.api;

  function followUrl(userId) {
    // <body data-follow-url="/api/social/follows/0/">
    return document.body.getAttribute("data-follow-url").replace(/0\/$/, userId + "/");
  }

  function setButton($btn, following) {
    var soft = $btn.attr("data-follow-variant") === "soft";
    $btn.attr("aria-pressed", following ? "true" : "false")
      .toggleClass(soft ? "ws-btn-soft" : "btn-primary", !following).toggleClass("btn-light border", following)
      .find("[data-follow-label]").text(following ? "Siguiendo" : "Seguir");
    $btn.find("i").attr("class", "bx fs-5 " + (following ? "bx-user-check" : "bx-user-plus"));
  }

  function toggle($btn) {
    if ($btn.data("busy")) { return; }
    var userId = Number($btn.attr("data-user-id"));
    var following = $btn.attr("aria-pressed") === "true";
    $btn.data("busy", true);
    setButton($btn, !following);
    api(followUrl(userId), { method: following ? "DELETE" : "PUT" }).then(function (res) {
      if (res.status === 200 && res.data) {
        setButton($btn, res.data.is_following);
        $(document).trigger("ws:follow", [{ userId: userId, stats: res.data }]);
      } else {
        setButton($btn, following);
        window.Workspace.toast(res.status === 0 ? "Sin conexión. Inténtalo de nuevo." : "No se pudo actualizar.");
      }
    }).always(function () { $btn.removeData("busy"); });
  }

  $(document).on("click", "[data-follow-btn]", function () { toggle($(this)); });

  window.Workspace.follow = { setButton: setButton };
})(jQuery);
