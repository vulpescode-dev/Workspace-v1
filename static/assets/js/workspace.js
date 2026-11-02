/* Workspace — comportamiento común (jQuery + componentes JS de Bootstrap: offcanvas, modal, toast).
   - [data-ws-soon="…"]  : acción aún no implementada → aviso "Próximamente" (nunca un éxito falso).
   - [data-ws-soon-submit="…"] : igual, pero al enviar un formulario.
   Inicio, Avisos y Buscar son páginas (antes Buscar era una vista de la portada con #buscar). */
(function ($) {
  "use strict";

  /* Aviso breve con el Toast de Bootstrap (#ws-toast en layouts/app.html). */
  function showSoon(message) {
    var $toast = $("#ws-toast");
    if (!$toast.length) { return; }
    $toast.find("[data-ws-toast-body]").text(message || "Próximamente.");
    window.bootstrap.Toast.getOrCreateInstance($toast[0], { delay: 2800 }).show();
  }

  window.Workspace = window.Workspace || {};
  window.Workspace.toast = showSoon;

  function csrfToken() {
    var match = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
    return match ? decodeURIComponent(match[1]) : "";
  }

  /* AJAX a la API con sesión + CSRF. Siempre resuelve { status, data } (también en 4xx/5xx; status 0 = sin conexión).
     Workspace.api(url) · Workspace.api(url, { method: "PUT", body: {...} })
     Archivos: Workspace.api(url, { method: "POST", formData: fd, onProgress: function (fraction) {} }) */
  window.Workspace.api = function (url, options) {
    options = options || {};
    var settings = { url: url, method: options.method || "GET", dataType: "json", headers: { "Accept": "application/json" } };
    if (options.method && options.method !== "GET") { settings.headers["X-CSRFToken"] = csrfToken(); }
    if (options.body) {
      settings.contentType = "application/json";
      settings.data = JSON.stringify(options.body);
    }
    if (options.formData) {
      settings.data = options.formData;
      settings.processData = false;
      settings.contentType = false;  // el navegador pone multipart/form-data con su boundary
      if (options.onProgress) {
        settings.xhr = function () {
          var xhr = $.ajaxSettings.xhr();
          xhr.upload.addEventListener("progress", function (event) {
            if (event.lengthComputable) { options.onProgress(event.loaded / event.total); }
          });
          return xhr;
        };
      }
    }
    return $.ajax(settings).then(
      function (data, textStatus, xhr) { return { status: xhr.status, data: data }; },
      function (xhr) { return $.Deferred().resolve({ status: xhr.status, data: xhr.responseJSON || null }); }
    );
  };

  /* ---- Imágenes → WebP (antes de subir) ---------------------------------
     Workspace.procesarAWebP(file, { maxSide: 2048, quality: 0.82 }) → Promise<File .webp>
     - Toda imagen se convierte a WebP en el navegador; si ya es WebP y no excede maxSide, se usa tal cual.
     - Respeta la orientación EXIF y, al redibujar, elimina los metadatos (p. ej. ubicación GPS de la foto).
     - Reduce a maxSide px por el lado mayor. El servidor solo valida (ver apps/core/uploads.py).
     Nativo (canvas / createImageBitmap): jQuery no tiene equivalente. */
  function loadBitmap(file) {
    if (window.createImageBitmap) {
      return window.createImageBitmap(file, { imageOrientation: "from-image" }).catch(function () { return loadImage(file); });
    }
    return loadImage(file);
  }

  function loadImage(file) {
    return new Promise(function (resolve, reject) {
      var url = URL.createObjectURL(file);
      var img = new Image();
      img.onload = function () { URL.revokeObjectURL(url); resolve(img); };
      img.onerror = function () { URL.revokeObjectURL(url); reject(new Error("No se pudo leer la imagen.")); };
      img.src = url;
    });
  }

  window.Workspace.procesarAWebP = function (file, options) {
    options = $.extend({ maxSide: 2048, quality: 0.82 }, options);
    if (!file || !/^image\//.test(file.type)) { return Promise.reject(new Error("El archivo no es una imagen.")); }
    return loadBitmap(file).then(function (source) {
      var width = source.width;
      var height = source.height;
      var scale = Math.min(1, options.maxSide / Math.max(width, height));
      if (file.type === "image/webp" && scale === 1) {
        if (source.close) { source.close(); }
        return file;
      }
      var canvas = document.createElement("canvas");
      canvas.width = Math.round(width * scale);
      canvas.height = Math.round(height * scale);
      var context = canvas.getContext("2d");
      context.imageSmoothingQuality = "high";
      context.drawImage(source, 0, 0, canvas.width, canvas.height);
      if (source.close) { source.close(); }
      return new Promise(function (resolve, reject) {
        canvas.toBlob(function (blob) {
          // Si el navegador no sabe codificar WebP, toBlob devuelve PNG: se rechaza en vez de subir otro formato.
          if (!blob || blob.type !== "image/webp") { reject(new Error("Tu navegador no puede convertir imágenes a WebP.")); return; }
          var name = (file.name || "imagen").replace(/\.[^.]+$/, "") + ".webp";
          resolve(new File([blob], name, { type: "image/webp", lastModified: Date.now() }));
        }, "image/webp", options.quality);
      });
    });
  };

  /* Perfil de una persona: /profile/?user_id=<id> (la base viene de <body data-profile-url>). */
  window.Workspace.profileUrl = function (userId) {
    return (document.body.getAttribute("data-profile-url") || "/profile/") + "?user_id=" + encodeURIComponent(userId);
  };

  /* Avatar (.ws-avatar): foto si la hay; si no, iniciales. La foto va como fondo para no cambiar el HTML. */
  window.Workspace.fillAvatar = function ($avatar, person) {
    if (person.avatar_url) {
      $avatar.addClass("has-image").css("background-image", "url(\"" + person.avatar_url + "\")").text("");
    } else {
      $avatar.removeClass("has-image").css("background-image", "").text(person.initials || "?");
    }
  };

  /* «x comentarios» en la tarjeta de un post (lo usan feed.js y comments.js). */
  window.Workspace.setCommentsCount = function ($post, count) {
    $post.data("comments-count", count)
      .find('[data-post-field="comments-count"]')
      .text(count === 1 ? "1 comentario" : count + " comentarios");
  };

  /* Confirmación para acciones destructivas (modal #ws-confirm-modal).
     Workspace.confirm({ title, text, accept }) → Promise<boolean>. Nunca window.confirm. */
  window.Workspace.confirm = function (options) {
    var $modal = $("#ws-confirm-modal");
    var modal = window.bootstrap.Modal.getOrCreateInstance($modal[0]);
    $modal.find("[data-confirm-title]").text(options.title || "¿Estás seguro?");
    $modal.find("[data-confirm-text]").text(options.text || "");
    $modal.find("[data-confirm-accept]").text(options.accept || "Eliminar");
    return new Promise(function (resolve) {
      var accepted = false;
      $modal.find("[data-confirm-accept]").off("click.confirm").on("click.confirm", function () {
        accepted = true;
        modal.hide();
      });
      $modal.one("hidden.bs.modal", function () {
        // Bootstrap quita "modal-open" del body al cerrar; si debajo sigue otro modal (comentarios), se restaura.
        if ($(".modal.show").length) { $("body").addClass("modal-open"); }
        resolve(accepted);
      });
      modal.show();
    });
  };

  /* Salida de un elemento (tarjeta, comentario): más rápida que la entrada y luego se quita del DOM. */
  window.Workspace.removeAnimated = function ($el) {
    if (window.Workspace.reducedMotion()) { $el.remove(); return; }
    // Se quitan las clases de entrada: su animación ganaría a la de salida y no habría "animationend".
    $el.removeClass("ws-post--new ws-comment--new ws-reaction--new").addClass("ws-leaving");
    var done = function () { $el.remove(); };
    $el.one("animationend", done);
    window.setTimeout(done, 400);   // respaldo por si el navegador no emite el evento
  };

  /* ¿El usuario pidió reducir el movimiento? (se consulta en cada uso por si cambia). */
  window.Workspace.reducedMotion = function () {
    return window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  };

  /* ---- Fechas (Day.js, vendorizado en static/assets/vendor/dayjs) -------
     Workspace.time.relative(iso) → "hace 5 minutos" (hasta 7 días) o "20 oct" / "20 oct 2025".
     Workspace.time.full(iso)     → "viernes, 24 de octubre de 2026 20:05 (GMT-6)" para el title.
     Las fechas llegan con desfase (ISO 8601) y se muestran en la zona horaria del navegador.
     Los <time data-ws-relative> se refrescan cada minuto sin volver a pedir datos. */
  var dayjs = window.dayjs;
  dayjs.extend(window.dayjs_plugin_relativeTime);
  dayjs.extend(window.dayjs_plugin_localizedFormat);
  dayjs.locale("es");

  // « (GMT-6)»: la zona del navegador, para que quede claro en qué hora se está viendo.
  function zoneLabel(iso) {
    try {
      var part = new Intl.DateTimeFormat("es-MX", { timeZoneName: "short" })
        .formatToParts(new Date(iso)).filter(function (p) { return p.type === "timeZoneName"; })[0];
      return part ? " (" + part.value + ")" : "";
    } catch (e) { return ""; }
  }

  window.Workspace.time = {
    relative: function (iso) {
      var date = dayjs(iso);
      var now = dayjs();
      if (now.diff(date, "day") < 7) { return date.fromNow(); }
      return date.format(date.year() === now.year() ? "D MMM" : "D MMM YYYY");
    },
    full: function (iso) { return dayjs(iso).format("LLLL") + zoneLabel(iso); },
    /* Corta, para listas como Avisos: hoy «10:24», ayer «Ayer», este año «19 oct», antes «19 oct 2025». */
    short: function (iso) {
      var date = dayjs(iso);
      var now = dayjs();
      if (date.isSame(now, "day")) { return date.format("HH:mm"); }
      if (date.isSame(now.subtract(1, "day"), "day")) { return "Ayer"; }
      return date.format(date.year() === now.year() ? "D MMM" : "D MMM YYYY");
    }
  };

  window.setInterval(function () {
    $("time[data-ws-relative]").each(function () {
      $(this).text(window.Workspace.time.relative($(this).attr("datetime")));
    });
  }, 60000);

  $(document)
    .on("click", "[data-ws-soon]", function (event) {
      event.preventDefault();
      showSoon($(this).attr("data-ws-soon"));
    })
    // «Volver»: regresa a la página anterior si venimos de Workspace; si no, sigue el href (Inicio).
    .on("click", "[data-ws-back]", function (event) {
      if (document.referrer.indexOf(window.location.origin) === 0 && window.history.length > 1) {
        event.preventDefault();
        window.history.back();
      }
    })
    .on("submit", "[data-ws-soon-submit]", function (event) {
      event.preventDefault();
      showSoon($(this).attr("data-ws-soon-submit"));
    });

  // Enlaces viejos a la portada con #avisos o #buscar: ahora son sus propias páginas.
  $(function () {
    var legacy = { avisos: "notifications", buscar: "search" }[window.location.hash.replace("#", "")];
    var $target = legacy ? $('.ws-bottom-nav [data-ws-nav="' + legacy + '"]') : $();
    if ($target.length && window.location.pathname === document.body.getAttribute("data-home-url")) {
      window.location.replace($target.attr("href"));
    }
  });
})(jQuery);
