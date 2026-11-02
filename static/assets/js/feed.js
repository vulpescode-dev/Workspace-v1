/* Workspace — feed de publicaciones consumido desde la API (/api/social/posts/).
   El HTML solo aporta el contenedor [data-ws-feed], los estados y <template id="ws-post-template">;
   los datos llegan siempre por JSON, igual que los consumirá un frontend separado.
   jQuery para eventos, AJAX y DOM; JS nativo solo para clonar el <template>. */
(function ($) {
  "use strict";

  function toast(message) {
    if (window.Workspace && window.Workspace.toast) { window.Workspace.toast(message); }
  }

  var api = window.Workspace.api;
  var MB = 1024 * 1024;
  var MAX_FILES = 10;                       // mismos límites que apps/core/uploads.py (el servidor decide)
  var VIDEO_TYPES = ["video/mp4", "video/quicktime", "video/webm"];
  var VIDEO_MAX = 100 * MB;
  var VISIBLE_MEDIA = 4;                    // en la tarjeta se ven hasta 4; el resto como "+N"
  var AUDIENCES = {
    company: { icon: "bx-globe", label: "Toda la empresa" },
    followers: { icon: "bx-group", label: "Solo seguidores" }
  };

  function renderAudience($post, audience) {
    var info = AUDIENCES[audience] || AUDIENCES.company;
    $post.find('[data-post-field="audience"]').attr("title", info.label)
      .find("i").attr("class", "bx " + info.icon).end()
      .find(".visually-hidden").text(info.label);
  }

  function cloneTemplate(id) {
    // Nativo: <template>.content solo existe en el DOM, jQuery no lo clona bien.
    return $(document.getElementById(id).content.firstElementChild.cloneNode(true));
  }

  /* Imágenes y videos del post: 1 a todo el ancho, 2 lado a lado, 3 = una grande + dos, 4+ = cuadrícula con "+N".
     Cada uno lleva data-media-index: tocar una foto (o el «+N») abre la galería del post (lightbox.js). */
  function renderMedia($media, attachments) {
    if (!attachments || !attachments.length) { return; }
    var shown = attachments.slice(0, VISIBLE_MEDIA);
    $media.addClass("ws-post-media--" + shown.length).prop("hidden", false);
    $.each(shown, function (index, item) {
      var $item;
      if (item.kind === "video") {
        $item = cloneTemplate("ws-media-video-template");
        $item.find("video").attr("src", item.url);
      } else {
        $item = cloneTemplate("ws-media-image-template");
        $item.find("img").attr({ src: item.url, width: item.width, height: item.height });
      }
      if (shown.length === 1 && item.width && item.height) {
        // Una sola imagen conserva su proporción (acotada en CSS para no ocupar toda la pantalla).
        $item.css("aspect-ratio", item.width + " / " + item.height);
      }
      var extra = attachments.length - VISIBLE_MEDIA;
      var hasMore = index === VISIBLE_MEDIA - 1 && extra > 0;
      $item.attr("data-media-index", index);
      if (item.kind !== "video" || hasMore) {
        $item.attr({
          role: "button", tabindex: 0,
          "aria-label": hasMore ? "Ver las " + attachments.length + " fotos y videos" : "Ver imagen " + (index + 1) + " de " + attachments.length
        });
      }
      if (hasMore) {
        $item.append($('<span class="ws-post-media__more" aria-hidden="true"></span>').text("+" + extra));
      }
      $media.append($item);
    });
  }

  /* Base de las URLs de cada post ("/api/social/posts/"). En el perfil el listado lleva ?author=,
     por eso la base va aparte en data-ws-posts-url. */
  function postsUrl() {
    var $root = $("[data-ws-feed]");
    return $root.attr("data-ws-posts-url") || $root.attr("data-ws-feed");
  }

  function renderPost(post) {
    var base = postsUrl() + post.id + "/";
    var $post = cloneTemplate("ws-post-template").attr({
      "data-post-id": post.id,
      "data-author-id": post.author.id,
      "data-post-url": base,
      "data-reaction-url": base + "reaction/",
      "data-reactions-url": base + "reactions/"
    });
    $post.data("post", post);
    $post.find("[data-post-menu]").prop("hidden", !post.is_mine);
    $post.find('[data-post-field="edited"]').prop("hidden", !post.edited_at);
    renderAudience($post, post.audience);
    // .text(): el contenido del usuario nunca se interpreta como HTML.
    // Los saltos de línea se respetan por CSS (white-space: pre-line), sin convertir a <br>.
    var profileUrl = window.Workspace.profileUrl(post.author.id);
    window.Workspace.fillAvatar($post.find('[data-post-field="initials"]'), post.author);
    $post.find('[data-post-field="profile-link"]').attr("href", profileUrl);
    $post.find('[data-post-field="author"]').text(post.author.name).attr("href", profileUrl);
    $post.find('[data-post-field="body"]').text(post.body).prop("hidden", !post.body);
    renderMedia($post.find("[data-post-media]"), post.attachments);
    window.Workspace.setCommentsCount($post, post.comments_count || 0);
    $post.find('[data-post-field="time"]')
      .text(window.Workspace.time.relative(post.created_at))
      .attr({ datetime: post.created_at, title: window.Workspace.time.full(post.created_at) });
    window.Workspace.reactions.render($post, post.reactions);
    return $post;
  }

  // ?page_size= (1–25) en la primera página; las siguientes lo conservan en «next».
  function withPageSize(url, size) {
    if (!size) { return url; }
    var parsed = new URL(url, window.location.origin);
    parsed.searchParams.set("page_size", size);
    return parsed.pathname + parsed.search;
  }

  /* Scroll infinito: 25 publicaciones por página (o las que indique data-ws-page-size). Un IntersectionObserver vigila el bloque
     [data-ws-feed-more] y pide la siguiente página cuando faltan ~600px para llegar a él.
     «Ver más» queda de respaldo (navegador sin IntersectionObserver o si falló una página). */
  function Feed($root) {
    var self = this;
    this.$root = $root;
    this.url = withPageSize($root.attr("data-ws-feed"), $root.attr("data-ws-page-size"));
    this.$list = $root.find("[data-ws-feed-list]");
    this.$more = $root.find("[data-ws-feed-more]");
    this.next = null;
    this.loading = false;
    this.seq = 0;          // «Recargar» invalida las respuestas que aún vienen en camino
    this.observer = "IntersectionObserver" in window
      ? new IntersectionObserver(function (entries) {
          if (entries[0].isIntersecting) { self.loadNext(); }
        }, { rootMargin: "600px 0px" })
      : null;
  }

  Feed.prototype.setState = function (state) {
    this.$root.find("[data-ws-feed-state]").each(function () {
      $(this).prop("hidden", $(this).attr("data-ws-feed-state") !== state);
    });
    this.$root.attr("aria-busy", state === "loading" ? "true" : "false");
  };

  // mode: "none" (no hay más), "auto" (vigilar el final), "button" (respaldo manual).
  Feed.prototype.setMore = function (mode) {
    var auto = mode === "auto" && !!this.observer;
    var el = this.$more[0];
    if (this.observer) { this.observer.unobserve(el); }
    this.$more.prop("hidden", mode === "none");
    this.$more.find("[data-ws-feed-more-spinner]").prop("hidden", !auto);
    this.$more.find("[data-ws-feed-next]").prop("hidden", auto);
    // observe() de nuevo avisa enseguida si el final ya está a la vista (páginas cortas).
    if (auto) { this.observer.observe(el); }
  };

  Feed.prototype.loadNext = function () {
    if (this.next && !this.loading) { this.load(this.next, true); }
  };

  Feed.prototype.load = function (url, append) {
    var self = this;
    var seq = ++self.seq;
    self.loading = true;
    if (!append) { self.$list.empty(); self.setState("loading"); self.setMore("none"); }
    function failed(state) {
      self.loading = false;
      if (append) { self.setMore("button"); } else { self.setState(state); }
    }
    // Las pastillas necesitan el catálogo de emojis: se piden en paralelo y se pinta cuando ambos llegan.
    return $.when(api(url || self.url), window.Workspace.reactions.ready).then(function (res) {
      if (seq !== self.seq) { return; }
      if (res.status === 401 || res.status === 403) { failed("auth"); return; }
      if (res.status !== 200 || !res.data) { failed("error"); return; }
      $.each(res.data.results, function (_, post) {
        // Si se publicó algo mientras tanto, la página siguiente puede repetir una que ya está.
        if (!self.$list.children('[data-post-id="' + post.id + '"]').length) { self.$list.append(renderPost(post)); }
      });
      self.loading = false;
      self.next = res.data.next;
      self.setState(self.$list.children().length ? "ready" : "empty");
      self.setMore(self.next ? "auto" : "none");
      // Página de una publicación con ?comments=1 (p. ej. desde una notificación): abre sus comentarios una vez.
      var $detail = self.$root.closest("[data-open-comments]");
      if ($detail.length && !append) {
        $detail.removeAttr("data-open-comments");
        self.$list.find("[data-comments-open]").not("[data-comments-focus]").first().trigger("click");
      }
    }, function () { if (seq === self.seq) { failed("error"); } });
  };

  /* Solo la publicación recién creada entra animada: el feed normal aparece sin animación
     porque se ve decenas de veces al día. */
  Feed.prototype.prepend = function (post) {
    var $post = renderPost(post).addClass("ws-post--new");
    this.$list.prepend($post);
    this.setState("ready");
    $post[0].scrollIntoView({ block: "nearest" });
  };

  function setupCreateForm(feed) {
    var $form = $("#ws-create-form");
    if (!$form.length) { return; }
    var $textarea = $form.find("textarea[name=body]");
    var $submit = $form.find("[data-ws-create-submit]");
    var $error = $("#ws-create-error");
    var $modal = $("#ws-create-modal");
    var $input = $form.find("[data-attach-input]");
    var $preview = $form.find("[data-attach-preview]");
    var $count = $form.find("[data-attach-count]");
    var $progress = $form.find("[data-upload-progress]");
    var items = [];   // { file, ready: Promise<File>, url, $tile }
    var $audience = $form.find("[data-audience-input]");

    // Audiencia elegida en el menú del modal: se guarda en el input oculto y se refleja en el botón.
    function syncAudience() {
      var info = AUDIENCES[$audience.val()] || AUDIENCES.company;
      $form.find("[data-audience-icon]").attr("class", "bx " + info.icon);
      $form.find("[data-audience-label]").text(info.label);
    }
    $form.on("click", "[data-audience-option]", function () {
      $audience.val($(this).attr("data-audience-option"));
      syncAudience();
    });

    function showError(message) {
      $error.text(message || "").prop("hidden", !message);
    }

    // PUBLICAR se habilita con texto o con al menos un archivo.
    function syncSubmit() {
      var empty = !$.trim($textarea.val()) && !items.length;
      $submit.prop("disabled", $form.hasClass("is-sending") || empty);
      $count.text(items.length ? items.length + " / " + MAX_FILES : "");
    }

    // El textarea crece con el contenido en lugar de mostrar barra de scroll.
    function autosize() {
      $textarea.css("height", "auto").css("height", $textarea[0].scrollHeight + "px");
    }

    function setProgress(fraction) {
      var percent = Math.round(fraction * 100);
      $progress.attr("aria-valuenow", percent).find(".progress-bar").css("width", percent + "%");
    }

    function removeItem(item) {
      if (item.url) { URL.revokeObjectURL(item.url); }
      item.$tile.remove();
      items = $.grep(items, function (other) { return other !== item; });
      syncSubmit();
    }

    function clearItems() {
      $.each(items.slice(), function (_, item) { removeItem(item); });
    }

    /* Agrega un archivo: las imágenes se convierten a WebP en segundo plano (la miniatura aparece al terminar). */
    function addFile(file) {
      var isImage = /^image\//.test(file.type);
      var isVideo = $.inArray(file.type, VIDEO_TYPES) !== -1;
      if (!isImage && !isVideo) { showError("«" + file.name + "» no es una imagen ni un video MP4, MOV o WebM."); return; }
      if (isVideo && file.size > VIDEO_MAX) { showError("«" + file.name + "» supera 100 MB."); return; }

      var item = { file: file, $tile: cloneTemplate("ws-attach-tile-template") };
      $preview.append(item.$tile);
      items.push(item);
      item.$tile.find("[data-attach-remove]").on("click", function () { removeItem(item); });

      item.ready = isImage ? window.Workspace.procesarAWebP(file) : Promise.resolve(file);
      item.ready.then(function (ready) {
        if ($.inArray(item, items) === -1) { return; }   // se quitó mientras se procesaba
        item.url = URL.createObjectURL(ready);
        if (isVideo) {
          item.$tile.find("video").attr("src", item.url).prop("hidden", false);
          item.$tile.find("[data-attach-video-badge]").prop("hidden", false);
        } else {
          item.$tile.find("img").attr("src", item.url).prop("hidden", false);
        }
        item.$tile.find("[data-attach-busy]").remove();
      }, function (error) {
        removeItem(item);
        showError("«" + file.name + "»: " + error.message);
      });
    }

    $input.on("change", function () {
      showError("");
      var files = Array.prototype.slice.call(this.files || []);
      var room = MAX_FILES - items.length;
      if (files.length > room) { showError("Máximo " + MAX_FILES + " archivos por publicación."); }
      $.each(files.slice(0, Math.max(room, 0)), function (_, file) { addFile(file); });
      this.value = "";   // permite volver a elegir el mismo archivo
      syncSubmit();
    });

    $textarea
      .on("input", function () { showError(""); syncSubmit(); autosize(); })
      // Ctrl/Cmd + Enter publica (atajo de teclado: sin animaciones extra).
      .on("keydown", function (event) {
        if (event.key === "Enter" && (event.ctrlKey || event.metaKey)) { $form.trigger("submit"); }
      });
    $modal
      .on("shown.bs.modal", function () { $textarea.trigger("focus"); })
      .on("hidden.bs.modal", function () { showError(""); });
    syncSubmit();

    function fail(message) {
      showError(message);
      $form.removeClass("is-sending");
      $progress.prop("hidden", true);
      syncSubmit();
    }

    $form.on("submit", function (event) {
      event.preventDefault();
      if ($form.hasClass("is-sending")) { return; }
      var body = $.trim($textarea.val());
      if (!body && !items.length) { showError("Escribe algo o agrega una foto o video."); $textarea.trigger("focus"); return; }
      showError("");
      $form.addClass("is-sending");
      syncSubmit();

      // Espera a que terminen las conversiones a WebP antes de armar el envío.
      Promise.all($.map(items, function (item) { return item.ready; })).then(function (files) {
        var formData = new FormData();
        formData.append("body", body);
        formData.append("audience", $audience.val());
        $.each(files, function (_, file) { formData.append("files", file, file.name); });
        if (files.length) { setProgress(0); $progress.prop("hidden", false); }

        api(feed.url, { method: "POST", formData: formData, onProgress: setProgress }).then(function (res) {
          if (res.status === 201) {
            $form[0].reset();
            syncAudience();   // la audiencia elegida se conserva para la siguiente publicación (reset() no toca inputs ocultos)
            clearItems();
            autosize();
            $form.removeClass("is-sending");
            $progress.prop("hidden", true);
            syncSubmit();
            // Se inserta cuando el modal ya se cerró, para que la entrada sea visible.
            $modal.one("hidden.bs.modal", function () { feed.prepend(res.data); });
            window.bootstrap.Modal.getOrCreateInstance($modal[0]).hide();
            toast("Publicación creada.");
          } else if (res.status === 400 && res.data) {
            fail([].concat(res.data.files || res.data.body || "Revisa la publicación.").join(" "));
          } else if (res.status === 413) {
            fail("Los archivos son demasiado grandes.");
          } else if (res.status === 401 || res.status === 403) {
            fail("Tu sesión expiró. Vuelve a iniciar sesión.");
          } else if (res.status === 0) {
            fail("Sin conexión. Inténtalo de nuevo.");
          } else {
            fail("No se pudo publicar. Inténtalo de nuevo.");
          }
        });
      }, function () {
        fail("Una imagen no se pudo procesar. Quítala e inténtalo de nuevo.");
      });
    });
  }

  /* ---- Editar / eliminar mi publicación (el menú solo aparece si is_mine) ---- */
  function setupPostOptions(feed) {
    function closeEdit($post) {
      $post.find("[data-post-edit-form]").prop("hidden", true);
      var body = $post.data("post").body;
      $post.find('[data-post-field="body"]').prop("hidden", !body);
    }

    $(document)
      .on("click", "[data-post-edit]", function () {
        var $post = $(this).closest("[data-post-id]");
        var $form = $post.find("[data-post-edit-form]");
        $post.find('[data-post-field="body"]').prop("hidden", true);
        $form.find("select[name=audience]").val($post.data("post").audience || "company");
        $form.prop("hidden", false).find("textarea").val($post.data("post").body).trigger("focus");
      })
      .on("click", "[data-post-edit-cancel]", function () {
        closeEdit($(this).closest("[data-post-id]"));
      })
      .on("submit", "[data-post-edit-form]", function (event) {
        event.preventDefault();
        var $form = $(this);
        var $post = $form.closest("[data-post-id]");
        var $button = $form.find("[type=submit]").prop("disabled", true);
        var payload = { body: $form.find("textarea").val(), audience: $form.find("select[name=audience]").val() };
        api($post.attr("data-post-url"), { method: "PATCH", body: payload }).then(function (res) {
          if (res.status === 200 && res.data) {
            $post.data("post", res.data);
            $post.find('[data-post-field="body"]').text(res.data.body);
            renderAudience($post, res.data.audience);
            $post.find('[data-post-field="edited"]').prop("hidden", false);
            closeEdit($post);
          } else if (res.status === 400 && res.data && res.data.body) {
            toast([].concat(res.data.body).join(" "));
          } else {
            toast(res.status === 0 ? "Sin conexión. Inténtalo de nuevo." : "No se pudo guardar el cambio.");
          }
        }).always(function () { $button.prop("disabled", false); });
      })
      .on("click", "[data-post-delete]", function () {
        var $post = $(this).closest("[data-post-id]");
        window.Workspace.confirm({
          title: "¿Eliminar publicación?",
          text: "Dejará de verse en el feed junto con sus comentarios y reacciones.",
          accept: "Eliminar"
        }).then(function (accepted) {
          if (!accepted) { return; }
          api($post.attr("data-post-url"), { method: "DELETE" }).then(function (res) {
            if (res.status === 204) {
              window.Workspace.removeAnimated($post);
              window.setTimeout(function () { if (!feed.$list.children(":not(.ws-leaving)").length) { feed.setState("empty"); } }, 200);
              toast("Publicación eliminada.");
            } else {
              toast(res.status === 0 ? "Sin conexión. Inténtalo de nuevo." : "No se pudo eliminar la publicación.");
            }
          });
        });
      });
  }

  $(function () {
    var $root = $("[data-ws-feed]");
    if (!$root.length) { return; }
    var feed = new Feed($root);
    feed.load();
    setupCreateForm(feed);
    setupPostOptions(feed);

    $(document)
      .on("click", "[data-ws-feed-reload]", function () { feed.load(); })
      .on("click", "[data-ws-feed-next]", function () { feed.loadNext(); });
  });
})(jQuery);
