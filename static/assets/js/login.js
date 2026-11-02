/* Workspace — inicio de sesión (/accounts/login/).
   - Mostrar/ocultar contraseña sin perder el cursor.
   - Aviso de Bloq Mayús mientras se escribe la contraseña.
   - Al enviar: «Entrando…» y botón deshabilitado (evita doble envío). Si el navegador regresa
     a la página desde su caché (botón Atrás), el botón vuelve a su estado normal.
   - Emojis animados ([data-login-emoji], los Noto de las reacciones): primero se ve el SVG fijo; luego se
     carga lottie y cada uno se anima UNA vez, escalonado tras la entrada de su tarjetita. Al pasar el mouse
     por la tarjetita se repite. Sin bucles: distraerían al escribir. Con «reducir movimiento», nada se anima. */
(function ($) {
  "use strict";

  var LOTTIE_SRC = document.currentScript && document.currentScript.getAttribute("data-lottie-src");

  function animateEmojis() {
    var $emojis = $("[data-login-emoji]");
    if (!$emojis.length || !LOTTIE_SRC || window.matchMedia("(prefers-reduced-motion: reduce)").matches) { return; }
    $.ajax({ url: LOTTIE_SRC, dataType: "script", cache: true }).then(function () {
      $emojis.each(function (index) {
        var holder = this;
        var anim = window.lottie.loadAnimation({
          container: holder, renderer: "svg", loop: false, autoplay: false, path: holder.getAttribute("data-login-emoji")
        });
        anim.addEventListener("DOMLoaded", function () {
          $(holder).addClass("is-animated");            // el SVG de lottie toma el lugar del fijo (mismo tamaño)
          window.setTimeout(function () { anim.goToAndPlay(0, true); }, 450 + index * 180);
        });
        if (window.matchMedia("(hover: hover) and (pointer: fine)").matches) {
          $(holder).closest(".ws-auth-chip").on("mouseenter", function () { anim.goToAndPlay(0, true); });
        }
      });
    });
  }

  $(function () {
    var $form = $("[data-login-form]");
    if (!$form.length) { return; }
    var $password = $form.find("#id_password");
    var $submit = $form.find("[data-login-submit]");

    $form.on("click", "[data-password-toggle]", function () {
      var $btn = $(this);
      var show = $btn.attr("aria-pressed") !== "true";
      var input = $password[0];
      var start = input.selectionStart, end = input.selectionEnd;
      $password.attr("type", show ? "text" : "password");
      $btn.attr({ "aria-pressed": show ? "true" : "false", "aria-label": show ? "Ocultar contraseña" : "Mostrar contraseña" })
        .find("i").toggleClass("bx-show", !show).toggleClass("bx-hide", show);
      input.focus();
      try { input.setSelectionRange(start, end); } catch (e) { /* algunos navegadores no lo permiten */ }
    });

    $password.on("keydown keyup", function (event) {
      if (event.originalEvent && event.originalEvent.getModifierState) {
        $form.find("[data-caps-hint]").prop("hidden", !event.originalEvent.getModifierState("CapsLock"));
      }
    }).on("blur", function () { $form.find("[data-caps-hint]").prop("hidden", true); });

    // Al escribir de nuevo se quita el rojo del error anterior.
    $form.on("input", ".form-control", function () { $form.find(".is-invalid").removeClass("is-invalid"); });

    $form.on("submit", function (event) {
      if ($submit.hasClass("is-loading")) { event.preventDefault(); return; }
      $submit.addClass("is-loading").attr("aria-disabled", "true");
    });
    $(window).on("pageshow", function () { $submit.removeClass("is-loading").removeAttr("aria-disabled"); });

    animateEmojis();
  });
})(jQuery);
