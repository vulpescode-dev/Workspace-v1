/* Workspace — comentarios de publicaciones (modal #ws-comments-modal).

   - «Comentar» abre el modal con el campo enfocado; «x comentarios» lo abre para leer.
   - Hilos de un nivel: comentario raíz + respuestas. «Responder» en una respuesta responde al mismo hilo.
   - Mis comentarios: «Editar» (en línea) y «Eliminar» (con confirmación; borrado suave en el servidor).
     Un comentario raíz eliminado con respuestas queda como «Comentario eliminado».
   - Cada comentario es anfitrión de reacciones (reactions.js): «Reaccionar» abre el mismo selector.
   - Enviar: botón o Ctrl/Cmd + Enter. El contador de la tarjeta usa el valor que devuelve el servidor. */
(function ($) {
  "use strict";

  var api = window.Workspace.api;
  var $modal, $list, $form, $text, $submit, $more, $banner;
  var state = { $post: null, url: null, next: null, focus: false, replyTo: null };

  function cloneTemplate(id) {
    // Nativo: <template>.content solo existe en el DOM, jQuery no lo clona bien.
    return $(document.getElementById(id).content.firstElementChild.cloneNode(true));
  }

  function commentUrl(id, suffix) {
    return $modal.attr("data-comment-url").replace(/0\/$/, id + "/") + (suffix || "");
  }

  function markDeleted($item) {
    $item.addClass("is-deleted").removeData("comment");
    own($item, "[data-comment-author]").text("").removeAttr("href");
    own($item, "[data-comment-profile]").removeAttr("href");
    own($item, "[data-comment-body]").text("Comentario eliminado");
    own($item, "[data-comment-initials]").removeClass("has-image").css("background-image", "").html('<i class="bx bx-trash"></i>');
  }

  /* Elementos de un comentario que no pertenecen a sus respuestas (anidadas dentro). */
  function own($item, selector) {
    return $item.find(selector).filter(function () { return $(this).closest(".ws-comment").is($item); });
  }

  function renderComment(comment) {
    var $item = cloneTemplate("ws-comment-template").attr({
      "data-comment-id": comment.id,
      "data-reaction-url": commentUrl(comment.id, "reaction/")
    });
    if (comment.is_deleted) {
      markDeleted($item);
    } else {
      $item.data("comment", comment);
      var profileUrl = window.Workspace.profileUrl(comment.author.id);
      window.Workspace.fillAvatar(own($item, "[data-comment-initials]"), comment.author);
      own($item, "[data-comment-profile]").attr("href", profileUrl);
      own($item, "[data-comment-author]").text(comment.author.name).attr("href", profileUrl);
      own($item, "[data-comment-body]").text(comment.body);
      own($item, "[data-comment-time]")
        .text(window.Workspace.time.relative(comment.created_at))
        .attr({ datetime: comment.created_at, title: window.Workspace.time.full(comment.created_at) });
      own($item, "[data-comment-edited]").prop("hidden", !comment.edited_at);
      own($item, "[data-comment-edit], [data-comment-delete]").prop("hidden", !comment.is_mine);
      window.Workspace.reactions.render($item, comment.reactions);
    }
    var $replies = own($item, "[data-comment-replies]");
    $.each(comment.replies || [], function (_, reply) { $replies.append(renderComment(reply)); });
    return $item;
  }

  function setState(name) {
    $modal.find("[data-comments-state]").each(function () {
      $(this).prop("hidden", $(this).attr("data-comments-state") !== name);
    });
  }

  function syncEmpty() {
    setState($list.children(":not(.ws-leaving)").length ? "ready" : "empty");
  }

  function load(url) {
    $more.prop("hidden", true);
    $.when(api(url), window.Workspace.reactions.ready).then(function (res) {
      if (res.status !== 200 || !res.data) { setState("error"); return; }
      $.each(res.data.results, function (_, comment) { $list.append(renderComment(comment)); });
      state.next = res.data.next;
      $more.prop("hidden", !state.next);
      syncEmpty();
      highlightRequested();
    });
  }

  /* ?comment=<id> (desde una notificación): lleva a ese comentario y lo resalta un momento. */
  function highlightRequested() {
    var $detail = $("[data-highlight-comment]");
    if (!$detail.length) { return; }
    var $item = $list.find('.ws-comment[data-comment-id="' + $detail.attr("data-highlight-comment") + '"]');
    if (!$item.length) { return; }
    $detail.removeAttr("data-highlight-comment");
    window.setTimeout(function () {
      $item[0].scrollIntoView({ block: "center", behavior: window.Workspace.reducedMotion() ? "auto" : "smooth" });
      $item.addClass("ws-comment--highlight");
    }, 250);
  }

  function autosize() {
    $text.css("height", "auto").css("height", Math.min($text[0].scrollHeight, 160) + "px");
  }

  function syncSubmit() {
    $submit.prop("disabled", $form.hasClass("is-sending") || !$.trim($text.val()));
  }

  function setReplyTo(target) {
    state.replyTo = target;
    $banner.prop("hidden", !target);
    $banner.find("[data-reply-name]").text(target ? target.name : "");
    $text.attr("placeholder", target ? "Escribe una respuesta…" : "Escribe un comentario…");
  }

  function open($post, focus) {
    state.$post = $post;
    state.url = $post.attr("data-post-url") + "comments/";
    state.focus = focus;
    $list.empty();
    $text.val("");
    setReplyTo(null);
    autosize();
    syncSubmit();
    setState("loading");
    window.bootstrap.Modal.getOrCreateInstance($modal[0]).show();
    load(state.url);
  }

  function send() {
    var body = $.trim($text.val());
    if (!body || $form.hasClass("is-sending")) { return; }
    var payload = { body: body };
    if (state.replyTo) { payload.parent = state.replyTo.rootId; }
    $form.addClass("is-sending");
    syncSubmit();
    api(state.url, { method: "POST", body: payload }).then(function (res) {
      if (res.status === 201 && res.data) {
        var $item = renderComment(res.data).addClass("ws-comment--new");
        var $root = res.data.parent ? $list.find('.ws-comment[data-comment-id="' + res.data.parent + '"]') : $();
        if ($root.length) { own($root, "[data-comment-replies]").append($item); } else { $list.append($item); }
        syncEmpty();
        $item[0].scrollIntoView({ block: "nearest", behavior: window.Workspace.reducedMotion() ? "auto" : "smooth" });
        window.Workspace.setCommentsCount(state.$post, res.data.comments_count);
        $text.val("");
        setReplyTo(null);
        autosize();
      } else if (res.status === 400 && res.data) {
        window.Workspace.toast([].concat(res.data.body || res.data.parent || "Revisa el comentario.").join(" "));
      } else if (res.status === 0) {
        window.Workspace.toast("Sin conexión. Inténtalo de nuevo.");
      } else {
        window.Workspace.toast("No se pudo enviar el comentario.");
      }
    }).always(function () {
      $form.removeClass("is-sending");
      syncSubmit();
      $text.trigger("focus");
    });
  }

  /* ---- Editar / eliminar mis comentarios ------------------------------ */
  function closeEdit($item) {
    own($item, "[data-comment-edit-form]").prop("hidden", true);
    own($item, ".ws-comment__bubble").prop("hidden", false);
  }

  function startEdit($item) {
    var comment = $item.data("comment");
    own($item, ".ws-comment__bubble").prop("hidden", true);
    own($item, "[data-comment-edit-form]").prop("hidden", false).find("textarea").val(comment.body).trigger("focus");
  }

  function saveEdit($item, $editForm) {
    var $button = $editForm.find("[type=submit]").prop("disabled", true);
    var id = $item.attr("data-comment-id");
    api(commentUrl(id), { method: "PATCH", body: { body: $editForm.find("textarea").val() } }).then(function (res) {
      if (res.status === 200 && res.data) {
        $item.data("comment", res.data);
        own($item, "[data-comment-body]").text(res.data.body);
        own($item, "[data-comment-edited]").prop("hidden", false);
        closeEdit($item);
      } else if (res.status === 400 && res.data && res.data.body) {
        window.Workspace.toast([].concat(res.data.body).join(" "));
      } else {
        window.Workspace.toast(res.status === 0 ? "Sin conexión. Inténtalo de nuevo." : "No se pudo guardar el cambio.");
      }
    }).always(function () { $button.prop("disabled", false); });
  }

  function remove($item) {
    window.Workspace.confirm({
      title: "¿Eliminar comentario?",
      text: "Dejará de verse para todos.",
      accept: "Eliminar"
    }).then(function (accepted) {
      if (!accepted) { return; }
      api(commentUrl($item.attr("data-comment-id")), { method: "DELETE" }).then(function (res) {
        if (res.status !== 200 || !res.data) {
          window.Workspace.toast(res.status === 0 ? "Sin conexión. Inténtalo de nuevo." : "No se pudo eliminar el comentario.");
          return;
        }
        window.Workspace.setCommentsCount(state.$post, res.data.comments_count);
        if (res.data.keep_placeholder) {
          markDeleted($item);
        } else {
          window.Workspace.removeAnimated($item);
          window.setTimeout(syncEmpty, 200);
        }
      });
    });
  }

  $(function () {
    $modal = $("#ws-comments-modal");
    if (!$modal.length) { return; }
    $list = $modal.find("[data-comments-list]");
    $form = $modal.find("[data-comments-form]");
    $text = $form.find("textarea");
    $submit = $form.find("[data-comments-submit]");
    $more = $modal.find("[data-comments-more]");
    $banner = $modal.find("[data-reply-banner]");

    $(document).on("click", "[data-comments-open]", function () {
      open($(this).closest("[data-post-id]"), $(this).is("[data-comments-focus]"));
    });
    $modal
      .on("shown.bs.modal", function () { if (state.focus) { $text.trigger("focus"); } })
      .on("click", "[data-comments-next]", function () { if (state.next) { load(state.next); } })
      .on("click", "[data-comment-reply]", function () {
        var $item = $(this).closest(".ws-comment");
        var $root = $item.parent().closest(".ws-comment");   // si es respuesta, el hilo es su raíz
        var comment = $item.data("comment");
        setReplyTo({ rootId: ($root.length ? $root : $item).attr("data-comment-id"), name: comment ? comment.author.name : "" });
        $text.trigger("focus");
      })
      .on("click", "[data-reply-cancel]", function () { setReplyTo(null); $text.trigger("focus"); })
      .on("click", "[data-comment-edit]", function () { startEdit($(this).closest(".ws-comment")); })
      .on("click", "[data-comment-edit-cancel]", function () { closeEdit($(this).closest(".ws-comment")); })
      .on("submit", "[data-comment-edit-form]", function (event) {
        event.preventDefault();
        saveEdit($(this).closest(".ws-comment"), $(this));
      })
      .on("click", "[data-comment-delete]", function () { remove($(this).closest(".ws-comment")); });

    $text
      .on("input", function () { autosize(); syncSubmit(); })
      // Ctrl/Cmd + Enter envía; Enter solo hace salto de línea (en el teléfono no hay otra forma).
      .on("keydown", function (event) {
        if (event.key === "Enter" && (event.ctrlKey || event.metaKey)) { event.preventDefault(); send(); }
        if (event.key === "Escape" && state.replyTo) { event.stopPropagation(); setReplyTo(null); }
      });
    $form.on("submit", function (event) { event.preventDefault(); send(); });
  });
})(jQuery);
