import os
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.http import FileResponse, Http404, HttpResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse

from .models import ArchivoSubido
from .forms import PlanillaValidadoraForm
from .utils import validar_columnas_y_convertir
import pandas as pd
import io
from django.contrib import messages
from django.utils import timezone


def descargar_plantilla_excel(request):
    file_path = os.path.join(
        settings.BASE_DIR,
        "analyst",
        "static",
        "plantillas",
        "plantilla_validadora.xlsx",
    )
    if os.path.exists(file_path):
        return FileResponse(
            open(file_path, "rb"),
            as_attachment=True,
            filename="plantilla_validadora.xlsx",
        )
    else:
        raise Http404("El archivo no existe.")


def index(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    else:
        return redirect("login")


@login_required
def dashboard(request):
    return render(request, "analyst/dashboard.html")


@login_required
def subir_planilla_validadora(request):
    form = PlanillaValidadoraForm(request.POST or None, request.FILES or None)
    estado_subida = None
    detalles_validacion = []

    perfil = getattr(request.user, "perfilusuario", None)
    if not perfil or not perfil.region:
        estado_subida = "error"
        detalles_validacion.append(
            "No tiene una región asignada. No puede subir archivos."
        )
        return render(
            request,
            "analyst/subir_planilla_validadora.html",
            {
                "form": form,
                "estado_subida": estado_subida,
                "detalles_validacion": detalles_validacion,
            },
        )

    if request.method == "POST":
        if not request.FILES.get("archivo"):
            estado_subida = "error"
            detalles_validacion.append("Debe seleccionar un archivo para subir.")
        elif form.is_valid():
            archivo = form.cleaned_data.get("archivo")
            nombre_archivo = archivo.name.lower()

            if not nombre_archivo.endswith((".xls", ".xlsx", ".csv")):
                estado_subida = "error"
                detalles_validacion.append(
                    "Formato de archivo no permitido. Solo se permiten .xls, .xlsx o .csv."
                )
            else:
                valido, df_o_errores = validar_columnas_y_convertir(
                    archivo, "planilla_validadora"
                )

                if valido:
                    usuario = request.user
                    region = (
                        perfil.region.id
                        if hasattr(perfil.region, "id")
                        else perfil.region
                    )
                    anio = form.cleaned_data.get("anio")
                    mes = form.cleaned_data.get("mes")
                    proceso = "planilla_validadora"

                    existe = ArchivoSubido.objects.filter(
                        usuario=usuario,
                        region=region,
                        anio=anio,
                        mes=mes,
                        proceso=proceso,
                    ).exists()

                    if existe:
                        estado_subida = "error"
                        detalles_validacion.append(
                            "Ya existe un archivo para esta combinación. Debe eliminarlo primero desde la página de archivos subidos."
                        )
                    else:
                        # Guardar nuevo archivo
                        instancia = form.save(commit=False)
                        instancia.usuario = usuario
                        instancia.region = region
                        instancia.proceso = proceso
                        instancia.save()

                        estado_subida = "exito"
                        detalles_validacion.append(
                            f"Archivo {archivo.name} subido correctamente con {len(df_o_errores)} filas."
                        )

                        # Render con resumen y redirección
                        return render(
                            request,
                            "analyst/subir_planilla_validadora.html",
                            {
                                "form": PlanillaValidadoraForm(),
                                "estado_subida": estado_subida,
                                "detalles_validacion": detalles_validacion,
                                "redireccionar_url": reverse("listar_archivos_subidos"),
                                "redireccionar_segundos": 20,
                            },
                        )
                else:
                    estado_subida = "error"
                    detalles_validacion.extend(
                        df_o_errores or ["El archivo no tiene las columnas válidas."]
                    )
                    form.add_error(
                        "archivo",
                        "El archivo no tiene las columnas válidas, se recomienda descargar plantilla oficial",
                    )
        else:
            estado_subida = "error"
            detalles_validacion.append(
                "Hay errores en el formulario. Revise los campos ingresados."
            )

    return render(
        request,
        "analyst/subir_planilla_validadora.html",
        {
            "form": form,
            "estado_subida": estado_subida,
            "detalles_validacion": detalles_validacion,
        },
    )


@login_required
def listar_archivos_subidos(request):
    perfil = getattr(request.user, "perfilusuario", None)

    if not perfil or not perfil.region:
        detalles_validacion = ["No tiene una región asignada."]
        return render(
            request,
            "analyst/listar_archivos.html",
            {
                "detalles_validacion": detalles_validacion,
            },
        )

    archivos = ArchivoSubido.objects.filter(
        usuario=request.user,
        region=perfil.region.id if hasattr(perfil.region, "id") else perfil.region,
        proceso="planilla_validadora",
    ).order_by("-creado")

    return render(
        request,
        "analyst/listar_archivos.html",
        {
            "archivos": archivos,
        },
    )


@staff_member_required
def consolidar_archivos(request):
    mensaje = None
    regiones = ArchivoSubido.objects.values_list("region", flat=True).distinct()
    procesos = [p[0] for p in ArchivoSubido.PROCESOS]

    if request.method == "POST":
        anio = int(request.POST.get("anio"))
        mes = int(request.POST.get("mes"))
        region = int(request.POST.get("region"))
        proceso = request.POST.get("proceso")

        archivos = ArchivoSubido.objects.filter(
            anio=anio, mes=mes, region=region, proceso=proceso
        )

        if not archivos.exists():
            mensaje = "No se encontraron archivos para esos filtros."
            return render(
                request,
                "analyst/consolidar_admin.html",
                {
                    "mensaje": mensaje,
                    "regiones": regiones,
                    "procesos": procesos,
                },
            )

        dfs = []
        for archivo in archivos:
            try:
                df = pd.read_csv(archivo.archivo.path)
                dfs.append(df)
            except Exception as e:
                mensaje = f"Error leyendo archivo {archivo.archivo.name}: {e}"
                return render(
                    request,
                    "analyst/consolidar_admin.html",
                    {
                        "mensaje": mensaje,
                        "regiones": regiones,
                        "procesos": procesos,
                    },
                )

        df_consolidado = pd.concat(dfs, ignore_index=True)

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df_consolidado.to_excel(writer, index=False, sheet_name="Consolidado")
            writer.save()

        output.seek(0)
        filename = f"consolidado_{proceso}_{region}_{anio}_{mes}.xlsx"
        response = HttpResponse(
            output.read(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = f"attachment; filename={filename}"
        return response

    return render(
        request,
        "analyst/consolidar_admin.html",
        {
            "regiones": regiones,
            "procesos": procesos,
            "mensaje": mensaje,
        },
    )


@login_required
def eliminar_archivo_subido(request, archivo_id):
    archivo = get_object_or_404(ArchivoSubido, id=archivo_id, usuario=request.user)
    ahora = timezone.now()

    if archivo.anio != ahora.year or archivo.mes != ahora.month:
        messages.error(request, "Solo puede eliminar archivos del mes y año actual.")
        return redirect("listar_archivos_subidos")

    if request.method == "POST":
        # Borrar archivo físico
        if archivo.archivo:
            archivo.archivo.delete(save=False)
        archivo.delete()
        messages.success(request, "Archivo eliminado correctamente.")
        return redirect("listar_archivos_subidos")

    # Opcional: mostrar página de confirmación, o redirigir directamente
    return render(
        request, "analyst/confirmar_eliminar_archivo.html", {"archivo": archivo}
    )
