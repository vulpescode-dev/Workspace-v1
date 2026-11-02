/* Workspace — lightbox de las publicaciones (PhotoSwipe 5, vendor/photoswipe, MIT).

   - Tocar una foto del post abre su galería a pantalla completa, solo con los medios de ESE post
     (si tiene 3, la galería tiene 3; incluye los que en la tarjeta quedan tras «+N»).
   - Movimiento (guía de Emil Kowalski): abre con zoom desde la miniatura que se tocó (no aparece de la
     nada en el centro), curva ease-out fuerte; cerrar es más rápido que abrir. Arrastrar hacia abajo
     cierra con inercia (un gesto rápido basta); deslizar cambia de foto; pellizcar o rueda acerca.
     Con «reducir movimiento»: solo fundido.
   - Teclado: Enter/Espacio sobre la foto la abre; ← → cambian; Esc cierra y el foco vuelve a la foto.
   - Los videos se reproducen en la tarjeta (sus controles nativos); en la galería aparecen en su lugar
     y se pausan al cambiar de diapositiva o al cerrar.
   API: Workspace.lightbox.open($post, index) */
(function ($) {
  "use strict";

  var EASE_OUT = "cubic-bezier(0.23, 1, 0.32, 1)";   // = --ws-ease-out
  var FALLBACK = { width: 1600, height: 1200 };       // por si un adjunto viejo no trae medidas
  var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
  var lightbox = null;

  function pauseVideos() {
    if (!lightbox || !lightbox.pswp) { return; }
    $(lightbox.pswp.element).find("video").each(function () { this.pause(); });
  }

  function getLightbox() {
    if (lightbox || !window.PhotoSwipeLightbox || !window.PhotoSwipe) { return lightbox; }
    var reduced = reduceMotion.matches;
    lightbox = new window.PhotoSwipeLightbox({
      pswpModule: window.PhotoSwipe,
      showHideAnimationType: reduced ? "fade" : "zoom",
      showAnimationDuration: reduced ? 150 : 260,
      hideAnimationDuration: reduced ? 120 : 200,
      easing: EASE_OUT,
      bgOpacity: 1,                 // sólido como Facebook; al arrastrar para cerrar se aclara solo
      wheelToZoom: true,
      closeTitle: "Cerrar (Esc)",
      zoomTitle: "Acercar",
      arrowPrevTitle: "Anterior",
      arrowNextTitle: "Siguiente",
      indexIndicatorSep: " de ",
      errorMsg: "No se pudo cargar la imagen."
    });
    lightbox.on("change", pauseVideos);
    lightbox.on("close", pauseVideos);
    lightbox.init();
    return lightbox;
  }

  /* Diapositivas a partir de los adjuntos del post. element = miniatura (para el zoom de entrada y salida). */
  function slides($post, attachments) {
    var $thumbs = $post.find("[data-media-index]");
    return $.map(attachments, function (item, index) {
      var thumb = $thumbs.filter('[data-media-index="' + index + '"]')[0];
      if (item.kind === "video") {
        // .attr(): la URL se escapa al armar el HTML del video.
        var video = $('<video controls playsinline preload="metadata"></video>').attr("src", item.url)[0].outerHTML;
        return { html: '<div class="ws-lightbox-video">' + video + "</div>" };
      }
      return {
        src: item.url,
        msrc: item.url,
        width: item.width || FALLBACK.width,
        height: item.height || FALLBACK.height,
        alt: "Imagen " + (index + 1) + " de " + attachments.length,
        element: thumb,
        thumbCropped: true          // la miniatura usa object-fit: cover
      };
    });
  }

  function open($post, index) {
    var post = $post.data("post");
    var box = getLightbox();
    if (!post || !post.attachments || !box) { return; }
    box.loadAndOpen(index, slides($post, post.attachments));
  }

  $(document)
    .on("click", "[data-media-index]", function (event) {
      if (event.target.tagName === "VIDEO") { return; }   // el video se controla en la tarjeta
      event.preventDefault();
      open($(this).closest("[data-post-id]"), Number($(this).attr("data-media-index")));
    })
    .on("keydown", "[data-media-index][role='button']", function (event) {
      if (event.key !== "Enter" && event.key !== " ") { return; }
      event.preventDefault();
      open($(this).closest("[data-post-id]"), Number($(this).attr("data-media-index")));
    });

  window.Workspace = window.Workspace || {};
  window.Workspace.lightbox = { open: open };
})(jQuery);
