/* Workspace — perfil (/profile/?user_id=<id>).

   - Pide el perfil a la API y lo pinta (antes se ve un esqueleto).
   - Pestañas Todo / Información / Seguidores / Fotos (lo que no está en «Todo» se carga la primera vez
     que se abre). En «Todo» (pantallas grandes) hay vista previa de fotos y un resumen de datos.
   - Seguir / Siguiendo (inmediato, sin solicitud), contadores y listas de seguidores y seguidos
     (la misma lista sirve en el modal de los contadores y en la pestaña «Seguidores»).
   - Mi perfil: cambiar foto (se convierte a WebP con Workspace.procesarAWebP y se muestra al instante
     mientras sube), quitarla, y editar la presentación. La portada es estática. Las publicaciones las
     pinta feed.js. */
(function ($) {
  "use strict";

  var api = window.Workspace.api;
  var AVATAR_SIZE = 512;
  var $root, profile = null;

  function field(name) { return $root.find('[data-profile-field="' + name + '"]'); }

  function row(name, value, setter) {
    var $row = $root.find('[data-profile-row="' + name + '"]');
    $row.prop("hidden", value === "" || value === null || value === undefined);
    if (setter) { setter($row.find("[data-value]")); } else { $row.find("[data-value]").text(value); }
  }

  function render(data) {
    profile = data;
    document.title = data.name + " · Workspace";
    $root.attr("aria-busy", "false");
    $root.find("[data-profile-identity]").removeClass("placeholder-glow");

    field("name").text(data.name);
    var headline = $.grep([data.job_title, data.department], Boolean).join(" · ");
    field("headline").text(headline).prop("hidden", !headline);

    window.Workspace.fillAvatar($root.find("[data-profile-avatar]"), data);

    field("bio").text(data.bio || (data.is_me ? "Aún no tienes presentación. Agrégala en «Editar perfil»." : "Sin presentación."))
      .toggleClass("text-body-secondary fst-italic", !data.bio);
    // Cumpleaños: solo día y mes (la API nunca manda el año). Se arma sobre el 2000 (bisiesto) para
    // que el 29 de febrero, o un día 31, no se recorran al mes siguiente.
    var birthday = data.birthday ? window.dayjs(new Date(2000, data.birthday.month - 1, data.birthday.day)).format("D [de] MMMM") : "";
    field("birthday").prop("hidden", !birthday).find("span").text(birthday);
    row("birthday", birthday);
    row("job_title", data.job_title);
    row("department", data.department);
    row("email", data.email, function ($a) { $a.text(data.email).attr("href", "mailto:" + data.email); });
    row("date_joined", window.dayjs(data.date_joined).format("D [de] MMMM [de] YYYY"));
    row("posts_count", String(data.posts_count));

    $root.find("[data-profile-email]").attr("href", "mailto:" + data.email).prop("hidden", !data.email);
    renderFollow(data.follow);
    $("[data-profile-remove=avatar]").prop("hidden", !data.avatar_url);
    loadPhotoPreview();
  }

  /* ---- Seguir (el botón lo maneja follow.js) ---------------------------- */
  var setFollowButton = function ($btn, following) { window.Workspace.follow.setButton($btn, following); };

  function renderFollow(stats) {
    if (!stats) { return; }
    $root.find('[data-stat="followers"]').text(stats.followers_count);
    $root.find('[data-stat-label="followers"]').text(stats.followers_count === 1 ? "seguidor" : "seguidores");
    $root.find('[data-stat="following"]').text(stats.following_count);
    $root.find("[data-profile-follows-me]").prop("hidden", !stats.follows_me);
    var $btn = $root.find("[data-follow-btn]").attr("data-user-id", profile.id);
    setFollowButton($btn, stats.is_following);
  }

  /* Contadores tras seguir/dejar de seguir: de esta persona, o mis «seguidos» si es mi perfil. */
  $(document).on("ws:follow", function (event, change) {
    if (!profile) { return; }
    if (change.userId === profile.id) {
      renderFollow(change.stats);
    } else if (profile.is_me) {
      var $count = $root.find('[data-stat="following"]');
      $count.text(Math.max(0, Number($count.text()) + (change.stats.is_following ? 1 : -1)));
    }
  });

  /* ---- Lista de seguidores / seguidos ----------------------------------- */
  // Una «caja» [data-people-box] tiene la lista, sus estados y «Ver más»: la del modal (contadores)
  // y la de la pestaña «Seguidores». Cada caja guarda su propia página siguiente.
  function emptyTextFor(kind) {
    var isFollowers = kind === "followers";
    if (profile.is_me) { return isFollowers ? "Todavía nadie te sigue." : "Todavía no sigues a nadie."; }
    return isFollowers ? "Todavía nadie sigue a esta persona." : "Todavía no sigue a nadie.";
  }

  function setPeopleState($box, name, emptyText) {
    $box.find("[data-people-state]").each(function () {
      $(this).prop("hidden", $(this).attr("data-people-state") !== name);
    });
    if (emptyText) { $box.find('[data-people-state="empty"]').text(emptyText); }
  }

  function loadPeople($box, url) {
    var $list = $box.find("[data-people-list]");
    var emptyText = $box.data("emptyText");
    var request = ($box.data("request") || 0) + 1;   // si se cambia de lista a medio cargar, gana la última
    $box.data("request", request);
    $box.find("[data-people-more]").prop("hidden", true);
    api(url).then(function (res) {
      if ($box.data("request") !== request) { return; }
      if (res.status !== 200 || !res.data) { setPeopleState($box, "empty", "No se pudo cargar la lista."); return; }
      var template = document.getElementById("ws-person-template");
      $.each(res.data.results, function (_, person) {
        var $row = $(template.content.firstElementChild.cloneNode(true));
        var href = window.Workspace.profileUrl(person.id);
        window.Workspace.fillAvatar($row.find("[data-person-avatar]"), person);
        $row.find("[data-person-link]").attr("href", href);
        $row.find("[data-person-name]").text(person.name).attr("href", href);
        $row.find("[data-person-job]").text(person.job_title || "");
        var $btn = $row.find("[data-follow-btn]").attr("data-user-id", person.id).prop("hidden", person.is_me);
        setFollowButton($btn, person.is_following);
        $list.append($row);
      });
      $box.data("next", res.data.next);
      $box.find("[data-people-more]").prop("hidden", !res.data.next);
      setPeopleState($box, $list.children().length ? "ready" : "empty", emptyText);
    });
  }

  function showPeople($box, kind) {
    $box.data("emptyText", emptyTextFor(kind)).find("[data-people-list]").empty();
    setPeopleState($box, "loading");
    loadPeople($box, $root.attr(kind === "followers" ? "data-followers-url" : "data-following-url"));
  }

  function openPeople(kind) {
    var $modal = $("#ws-people-modal");
    $modal.find("[data-people-title]").text(kind === "followers" ? "Seguidores" : "Seguidos");
    window.bootstrap.Modal.getOrCreateInstance($modal[0]).show();
    showPeople($modal.find("[data-people-box]"), kind);
  }

  // Pestaña «Seguidores»: interruptor Seguidores / Seguidos.
  function showPeopleTab(kind) {
    var $panel = $root.find('[data-profile-panel="people"]');
    $panel.find("[data-people-kind]").each(function () {
      var active = $(this).attr("data-people-kind") === kind;
      $(this).toggleClass("active", active).attr("aria-selected", active ? "true" : "false");
    });
    showPeople($panel.find("[data-people-box]"), kind);
  }

  function load() {
    api($root.attr("data-profile-url")).then(function (res) {
      if (res.status === 200 && res.data) { render(res.data); return; }
      $root.attr("aria-busy", "false");
      $root.find("[data-profile-error]").prop("hidden", false);
      $root.find("[data-profile-body]").prop("hidden", true);
      $root.find("[data-profile-identity]").removeClass("placeholder-glow").find(".placeholder").remove();
    });
  }

  /* Tras cambiar mi foto, las tarjetas de mis publicaciones ya pintadas también se actualizan. */
  function refreshMyAvatars() {
    $('.ws-post[data-author-id="' + profile.id + '"] [data-post-field="initials"]').each(function () {
      window.Workspace.fillAvatar($(this), profile);
    });
    // Mi avatar en «Compártenos tu día», en el modal de publicar, en el menú y en el encabezado (renderizados por el servidor).
    $(".ws-create .ws-avatar, #ws-create-modal .ws-avatar, #ws-menu .ws-avatar, .ws-header .ws-avatar").each(function () {
      if (this.tagName === "IMG") {
        if (profile.avatar_url) { $(this).attr("src", profile.avatar_url); }
      } else {
        window.Workspace.fillAvatar($(this), profile);
      }
    });
  }

  /* ---- Fotos ----------------------------------------------------------- */
  var photos = { loaded: false, next: null };

  function setPhotosState(name) {
    $root.find("[data-photos-state]").each(function () {
      $(this).prop("hidden", $(this).attr("data-photos-state") !== name);
    });
  }

  // Por ahora abre la imagen completa; el visor a pantalla completa está pendiente.
  function photoTile(photo) {
    return $('<a class="ws-photo-grid__item" target="_blank" rel="noopener"></a>')
      .attr({ href: photo.url, "aria-label": "Abrir foto" })
      .append($('<img alt="" loading="lazy" decoding="async">').attr("src", photo.url));
  }

  // «Todo» en pantallas grandes: las 9 fotos más recientes. En el teléfono esa columna no se ve: no se pide.
  function loadPhotoPreview() {
    var $preview = $root.find("[data-photos-preview]");
    // Se mira la columna, no la cuadrícula: vacía, la cuadrícula está oculta (:empty) y nunca cargaría.
    if (!$preview.length || !$preview.closest(".ws-profile-all__side").is(":visible") || $preview.data("loaded")) { return; }
    $preview.data("loaded", true);
    api($root.attr("data-photos-url") + "&page_size=9").then(function (res) {
      var items = res.status === 200 && res.data ? res.data.results : [];
      $.each(items, function (_, photo) { $preview.append(photoTile(photo)); });
      $root.find("[data-photos-preview-empty]").prop("hidden", items.length > 0);
    });
  }

  function loadPhotos(url) {
    var $grid = $root.find("[data-photos-grid]");
    var $more = $root.find("[data-photos-more]").prop("hidden", true);
    if (!$grid.children().length) { setPhotosState("loading"); }
    api(url).then(function (res) {
      if (res.status !== 200 || !res.data) { setPhotosState("error"); return; }
      $.each(res.data.results, function (_, photo) {
        photoTile(photo)
          .appendTo($grid);
      });
      photos.next = res.data.next;
      $more.prop("hidden", !photos.next);
      setPhotosState($grid.children().length ? "ready" : "empty");
    });
  }

  /* ---- Pestañas -------------------------------------------------------- */
  function showTab(name) {
    $root.attr("data-tab", name);
    if (name === "photos" && !photos.loaded) {
      photos.loaded = true;
      loadPhotos($root.attr("data-photos-url"));
    }
    if (name === "people" && !$root.data("peopleLoaded")) {
      $root.data("peopleLoaded", true);
      showPeopleTab("followers");
    }
    $root.find("[data-profile-tab-btn]").each(function () {
      var active = $(this).attr("data-profile-tab-btn") === name;
      $(this).toggleClass("active", active).attr("aria-selected", active ? "true" : "false");
    });
  }

  /* ---- Foto de perfil (mía) -------------------------------------------- */
  function uploadAvatar(file) {
    var $avatar = $root.find("[data-profile-avatar]");
    $avatar.addClass("is-uploading");
    window.Workspace.procesarAWebP(file, { maxSide: AVATAR_SIZE, quality: 0.85 }).then(function (webp) {
      // Vista previa inmediata: la foto nueva se ve mientras sube (se corrige si falla).
      var preview = URL.createObjectURL(webp);
      window.Workspace.fillAvatar($avatar, { avatar_url: preview });
      var formData = new FormData();
      formData.append("file", webp, webp.name);
      return api($root.attr("data-me-avatar-url"), { method: "POST", formData: formData }).then(function (res) {
        if (res.status === 200 && res.data) {
          render(res.data);
          refreshMyAvatars();
          window.Workspace.toast("Foto de perfil actualizada.");
        } else {
          render(profile);
          var detail = res.data && res.data.file ? [].concat(res.data.file).join(" ") : "";
          window.Workspace.toast(detail || (res.status === 0 ? "Sin conexión. Inténtalo de nuevo." : "No se pudo subir la foto."));
        }
        window.setTimeout(function () { URL.revokeObjectURL(preview); }, 1000);
      });
    }, function (error) {
      window.Workspace.toast(error.message);
    }).then(function () { $avatar.removeClass("is-uploading"); }, function () { $avatar.removeClass("is-uploading"); });
  }

  function removeAvatar() {
    api($root.attr("data-me-avatar-url"), { method: "DELETE" }).then(function (res) {
      if (res.status === 200 && res.data) {
        render(res.data);
        refreshMyAvatars();
      } else {
        window.Workspace.toast("No se pudo quitar la foto.");
      }
    });
  }

  /* ---- Editar presentación -------------------------------------------- */
  function setupEditModal() {
    var $modal = $("#ws-profile-edit-modal");
    if (!$modal.length) { return; }
    var $form = $modal.find("[data-profile-edit-form]");
    var $bio = $form.find("textarea[name=bio]");
    var $count = $form.find("[data-bio-count]");

    function syncCount() { $count.text($bio.val().length + " / 280"); }

    $root.on("click", "[data-profile-edit]", function () {
      $bio.val(profile ? profile.bio : "");
      syncCount();
      window.bootstrap.Modal.getOrCreateInstance($modal[0]).show();
    });
    $modal.on("shown.bs.modal", function () { $bio.trigger("focus"); });
    $bio.on("input", syncCount);
    $form.on("submit", function (event) {
      event.preventDefault();
      var $button = $form.find("[type=submit]").prop("disabled", true);
      api($root.attr("data-me-url"), { method: "PATCH", body: { bio: $bio.val() } }).then(function (res) {
        if (res.status === 200 && res.data) {
          render(res.data);
          window.bootstrap.Modal.getInstance($modal[0]).hide();
          window.Workspace.toast("Perfil actualizado.");
        } else {
          window.Workspace.toast(res.data && res.data.bio ? [].concat(res.data.bio).join(" ") : "No se pudo guardar.");
        }
      }).always(function () { $button.prop("disabled", false); });
    });
  }

  $(function () {
    $root = $("[data-profile]");
    if (!$root.length) { return; }
    load();
    setupEditModal();
    $(window).on("resize", function () { if (profile) { loadPhotoPreview(); } });

    var $file = $root.find("[data-profile-file]");
    $(document)
      .on("click", "[data-profile-tab-btn]", function () { showTab($(this).attr("data-profile-tab-btn")); })
      .on("click", "[data-photos-next]", function () { if (photos.next) { loadPhotos(photos.next); } })
      .on("click", "[data-people-open]", function () { if (profile) { openPeople($(this).attr("data-people-open")); } })
      .on("click", "[data-people-kind]", function () {
        if (profile && !$(this).hasClass("active")) { showPeopleTab($(this).attr("data-people-kind")); }
      })
      .on("click", "[data-people-next]", function () {
        var $box = $(this).closest("[data-people-box]");
        if ($box.data("next")) { loadPeople($box, $box.data("next")); }
      })
      // «Ver toda la información» / «Ver todas» (fotos): cambian de pestaña y suben a las pestañas si quedaron arriba.
      .on("click", "[data-profile-goto]", function () {
        showTab($(this).attr("data-profile-goto"));
        var tabs = $root.find(".ws-profile-tabs")[0];
        var header = document.querySelector(".ws-header");
        var top = tabs.getBoundingClientRect().top - (header ? header.offsetHeight : 0) - 12;
        if (top < 0) { window.scrollBy(0, top); }
      })
      .on("click", "[data-profile-pick]", function () { $file.trigger("click"); })
      .on("click", "[data-profile-remove]", removeAvatar);
    $file.on("change", function () {
      var file = this.files && this.files[0];
      this.value = "";
      if (file) { uploadAvatar(file); }
    });
  });
})(jQuery);
