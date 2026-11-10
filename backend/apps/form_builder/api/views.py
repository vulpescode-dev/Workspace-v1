import csv

from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.text import slugify
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.api.permissions import FORMS
from apps.accounts.services.permissions import has_permission
from apps.form_builder.models import Answer
from apps.form_builder.selectors.forms import SCOPES, can_create, can_manage, filter_forms, form_with_questions, visible_forms
from apps.form_builder.selectors.results import form_results, results_table
from apps.form_builder.services.forms import create_form, delete_form, save_questions, update_form
from apps.form_builder.services.submissions import AnswerErrors, submit

from .serializers import FormCreateSerializer, FormDetailSerializer, FormEditSerializer, FormSerializer


def _as_drf_error(exc: DjangoValidationError) -> ValidationError:
    return ValidationError(exc.message_dict if hasattr(exc, "error_dict") else exc.messages)


def _get_form(request, form_uuid, *, with_questions=False):
    qs = visible_forms(request.user)
    return get_object_or_404(form_with_questions(qs) if with_questions else qs, uuid=form_uuid)


def _can_see_results(user, form) -> bool:
    """Resultados: quien creó el formulario, o quien tenga permiso de ver todos (formularios o respuestas)."""
    return can_manage(user, form) or any(
        has_permission(user, code) for code in ("forms.forms.view.all", "forms.submissions.view.all")
    )


def _ensure_manager(request, form) -> None:
    if not _can_see_results(request.user, form):
        raise PermissionDenied("Solo quien creó el formulario.")


def _ensure_can_export(request, form) -> None:
    """CSV: quien creó el formulario exporta lo suyo; lo ajeno, con resultados visibles y ``forms.submissions.export``."""
    if can_manage(request.user, form):
        return
    if not (_can_see_results(request.user, form) and has_permission(request.user, "forms.submissions.export")):
        raise PermissionDenied("No tienes permiso para exportar estas respuestas.")


def _detail(request, form_uuid) -> dict:
    form = _get_form(request, form_uuid, with_questions=True)
    context = {"request": request}
    if can_manage(request.user, form):
        context["answered_questions"] = set(Answer.objects.filter(question__form=form).values_list("question_id", flat=True))
    return FormDetailSerializer(form, context=context).data


class FormsMeView(APIView):
    """GET ``{"can_create"}``: si la persona puede crear formularios (para mostrar «Nuevo formulario»)."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"can_create": can_create(request.user)})


class FormListCreateView(generics.ListAPIView):
    """GET: formularios. ``?scope=pending`` (abiertos que no he respondido), ``?scope=mine`` (los míos, con
    borradores) o sin scope (todos los publicados). ``?q=`` busca en el título.
    POST ``{"title", "description"?}`` (``forms.forms.create``): crea un borrador."""

    serializer_class = FormSerializer
    permission_classes = [IsAuthenticated, FORMS]

    def get_queryset(self):
        scope = self.request.query_params.get("scope", "")
        if scope and scope not in SCOPES:
            raise ValidationError({"scope": f"Usa uno de: {', '.join(SCOPES)}."})
        return filter_forms(visible_forms(self.request.user), self.request.user, scope=scope,
                            query=self.request.query_params.get("q", "").strip()[:100])

    def post(self, request):
        data = FormCreateSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        try:
            form = create_form(owner=request.user, **data.validated_data)
        except DjangoValidationError as exc:
            raise _as_drf_error(exc) from exc
        return Response(_detail(request, form.uuid), status=status.HTTP_201_CREATED)


class FormDetailView(APIView):
    """GET: el formulario con sus preguntas (para responderlo o editarlo). PATCH (quien lo creó o
    ``forms.forms.update.all``): título, descripción, estado (``draft``/``open``/``closed``), ``opens_at``,
    ``closes_at``, ``one_submission_per_user``. DELETE (quien lo creó o ``forms.forms.delete.all``): borrado suave."""

    permission_classes = [IsAuthenticated, FORMS]

    def get(self, request, form_uuid):
        return Response(_detail(request, form_uuid))

    def patch(self, request, form_uuid):
        form = _get_form(request, form_uuid)
        data = FormEditSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        try:
            update_form(user=request.user, form=form, **data.validated_data)
        except DjangoValidationError as exc:
            raise _as_drf_error(exc) from exc
        return Response(_detail(request, form_uuid))

    def delete(self, request, form_uuid):
        delete_form(user=request.user, form=_get_form(request, form_uuid))
        return Response(status=status.HTTP_204_NO_CONTENT)


class FormQuestionsView(APIView):
    """PUT ``{"questions": [...]}`` (quien lo creó): guarda la lista completa de preguntas, en orden.
    Cada una: ``id`` (si ya existe), ``kind``, ``title``, ``description``, ``is_required`` y, según el tipo,
    ``options``/``rows`` (``[{"id"?, "text"}]``), ``has_other_option``, ``shuffle_options``, ``min_choices``,
    ``max_choices``, ``scale_min``, ``scale_max``, ``scale_min_label``, ``scale_max_label``."""

    permission_classes = [IsAuthenticated, FORMS]

    def put(self, request, form_uuid):
        form = _get_form(request, form_uuid)
        try:
            save_questions(user=request.user, form=form, questions=request.data.get("questions"))
        except DjangoValidationError as exc:
            raise _as_drf_error(exc) from exc
        return Response(_detail(request, form_uuid))


class FormSubmitView(APIView):
    """POST ``{"answers": [{"question", ...}]}``: responde el formulario. Errores por pregunta en
    ``{"answers": {"<id>": "mensaje"}}``; generales en ``form``."""

    permission_classes = [IsAuthenticated, FORMS]

    def post(self, request, form_uuid):
        form = _get_form(request, form_uuid, with_questions=True)
        try:
            submission = submit(user=request.user, form=form, answers=request.data.get("answers"))
        except AnswerErrors as exc:
            return Response({"detail": "Revisa las respuestas marcadas.", "answers": {str(k): v for k, v in exc.errors.items()}},
                            status=status.HTTP_400_BAD_REQUEST)
        except DjangoValidationError as exc:
            raise _as_drf_error(exc) from exc
        return Response({"id": submission.pk, "submitted_at": submission.submitted_at}, status=status.HTTP_201_CREATED)


class FormResultsView(APIView):
    """GET (quien lo creó, o con ``forms.forms.view.all`` / ``forms.submissions.view.all``): resumen por pregunta."""

    permission_classes = [IsAuthenticated, FORMS]

    def get(self, request, form_uuid):
        form = _get_form(request, form_uuid)
        _ensure_manager(request, form)
        return Response(form_results(form))


class FormResultsCsvView(APIView):
    """GET: todas las respuestas en CSV (UTF-8 con BOM para que Excel respete los acentos). Quien lo creó, siempre;
    otra persona, si ve sus resultados y tiene ``forms.submissions.export``."""

    permission_classes = [IsAuthenticated, FORMS]

    def get(self, request, form_uuid):
        form = _get_form(request, form_uuid)
        _ensure_can_export(request, form)
        headers, rows = results_table(form)
        response = HttpResponse(content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = f'attachment; filename="{slugify(form.title) or "formulario"}-respuestas.csv"'
        response["Cache-Control"] = "private, no-store"
        response.write("﻿")
        writer = csv.writer(response)
        writer.writerow(headers)
        # Una celda que empieza con = + - @ se abre como fórmula en Excel: se antepone un apóstrofo.
        writer.writerows([[f"'{cell}" if cell[:1] in ("=", "+", "-", "@") else cell for cell in row] for row in rows])
        return response
