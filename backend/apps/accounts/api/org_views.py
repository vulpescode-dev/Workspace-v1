from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.api.permissions import DEPARTMENTS, ORG_CHART
from apps.accounts.selectors.chart import DEFAULT_DEPTH, MAX_DEPTH, org_chart
from apps.accounts.selectors.departments import active_departments

from .org_serializers import ChartNodeSerializer, DepartmentSerializer


class DepartmentListView(generics.ListAPIView):
    """GET: departamentos activos por nombre (para filtros y formularios). Sin paginar: son pocos.
    Las personas de un departamento: ``/api/accounts/users/?department=<id>``."""

    serializer_class = DepartmentSerializer
    permission_classes = [IsAuthenticated, DEPARTMENTS]
    pagination_class = None

    def get_queryset(self):
        return active_departments(self.request.user)


class DepartmentDetailView(APIView):
    """GET: un departamento activo (404 si no existe o está desactivado)."""

    permission_classes = [IsAuthenticated, DEPARTMENTS]

    def get(self, request, pk):
        department = get_object_or_404(active_departments(request.user), pk=pk)
        return Response(DepartmentSerializer(department).data)


def _int_param(params, name: str, default: int | None = None, *, low: int = 1, high: int | None = None):
    value = params.get(name, "")
    if value == "":
        return default
    if not value.isdigit() or int(value) < low:
        raise ValidationError({name: "Debe ser un número entero positivo."})
    return min(int(value), high) if high else int(value)


class OrgChartView(APIView):
    """GET: organigrama por jefe directo.

    ``?root=<id de persona>``: solo desde esa persona (404 si no existe o está inactiva).
    ``?depth=<n>``: niveles a incluir (3 por omisión, máx. 10); ``reports_count`` dice cuántas
    personas tiene a cargo cada nodo aunque no vengan en ``children``.
    """

    permission_classes = [IsAuthenticated, ORG_CHART]

    def get(self, request):
        params = request.query_params
        root = _int_param(params, "root")
        depth = _int_param(params, "depth", DEFAULT_DEPTH, high=MAX_DEPTH)
        chart = org_chart(request.user, root_id=root, depth=depth)
        if chart is None:
            raise Http404
        return Response({
            "depth": depth,
            "unassigned_count": chart.unassigned_count,
            "roots": ChartNodeSerializer(chart.roots, many=True).data,
        })
