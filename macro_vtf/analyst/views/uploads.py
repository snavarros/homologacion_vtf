from datetime import date
import io


from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from django.core.files.base import ContentFile
from django.urls import reverse
from django.contrib import messages
from django.utils import timezone
from django.shortcuts import redirect

from analyst.forms import PlanillaValidadoraForm
from analyst.models import ArchivoSubido
from analyst.views.helpers import (
    validar_archivo,
    validar_columnas_y_convertir,
    validar_perfil,
)


@login_required
def subir_planilla_validadora(request):
    form = PlanillaValidadoraForm(request.POST or None, request.FILES or None)
    detalles_validacion = []

    perfil = getattr(request.user, "perfilusuario", None)
    perfil_valido, errores_perfil = validar_perfil(perfil)
    if not perfil_valido:
        return render(
            request,
            "analyst/subir_planilla_validadora.html",
            {
                "form": form,
                "estado_subida": "error",
                "detalles_validacion": errores_perfil,
            },
        )

    if request.method == "POST":
        if not request.FILES.get("archivo"):
            detalles_validacion.append("Debe seleccionar un archivo para subir.")
        elif form.is_valid():
            archivo = form.cleaned_data["archivo"]
            nombre_archivo = archivo.name.lower()

            archivo_valido, errores_archivo = validar_archivo(nombre_archivo)
            if not archivo_valido:
                detalles_validacion.extend(errores_archivo)
            else:
                valido, df_o_errores = validar_columnas_y_convertir(
                    archivo, "planilla_validadora"
                )
                if valido:
                    usuario = request.user
                    region = perfil.region.id
                    anio = form.cleaned_data["anio"]
                    mes = form.cleaned_data["mes"]
                    proceso = "planilla_validadora"

                    if ArchivoSubido.objects.filter(
                        usuario=usuario,
                        region=region,
                        anio=anio,
                        mes=mes,
                        proceso=proceso,
                    ).exists():
                        detalles_validacion.append(
                            "Ya existe un archivo para el mes y año seleccionado. "
                            "Si desea reemplazarlo debe eliminarlo en la sección Archivos Subidos."
                        )
                    else:
                        instancia = form.save(commit=False)
                        instancia.usuario = usuario
                        instancia.region = region
                        instancia.proceso = proceso

                        # Eliminar filas con valores vacíos (NaN)
                        total_filas_original = len(df_o_errores)
                        df_o_errores = df_o_errores.dropna(how="all")
                        filas_eliminadas = total_filas_original - len(df_o_errores)

                        # Calcular resumen
                        establecimientos_distintos = df_o_errores[
                            "CODIGO_ESTABLECIMIENTO"
                        ].nunique()
                        rut_distintos = df_o_errores["RUT"].nunique()
                        ruts_repetidos = df_o_errores["RUT"].value_counts()
                        cantidad_ruts_repetidos = (ruts_repetidos > 1).sum()

                        # Crear mensaje informativo
                        mensaje = (
                            f"Archivo <code>{archivo.name}</code> subido correctamente con "
                            f"<strong>{len(df_o_errores)} filas</strong>."
                        )
                        if filas_eliminadas > 0:
                            mensaje += f" Se eliminaron <strong>{filas_eliminadas}</strong> filas vacías."

                        mensaje += (
                            f"<br>Resumen del archivo:"
                            f"<ul>"
                            f"<li><strong>{establecimientos_distintos}</strong> establecimientos distintos</li>"
                            f"<li><strong>{rut_distintos}</strong> RUT distintos</li>"
                            f"<li><strong>{cantidad_ruts_repetidos}</strong> RUT repetidos</li>"
                            f"</ul>"
                        )

                        # Convertir el DataFrame a CSV
                        buffer = io.StringIO()
                        df_o_errores.to_csv(buffer, index=False)
                        buffer.seek(0)

                        # Crear un archivo ContentFile desde el buffer CSV
                        filename = f"{proceso}_{mes}_{anio}_{usuario.username}.csv"
                        file_content = ContentFile(
                            buffer.getvalue().encode("utf-8"), name=filename
                        )
                        instancia.archivo.save(filename, file_content, save=True)

                        return render(
                            request,
                            "analyst/subir_planilla_validadora.html",
                            {
                                "form": PlanillaValidadoraForm(),  # Reiniciar formulario
                                "estado_subida": "exito",
                                "detalles_validacion": [mensaje],
                                "redireccionar_url": reverse("listar_archivos_subidos"),
                                "redireccionar_segundos": 20,
                            },
                        )
                else:
                    detalles_validacion.extend(
                        df_o_errores or ["El archivo no tiene las columnas válidas."]
                    )
                    form.add_error(
                        "archivo",
                        "El archivo no tiene las columnas válidas. "
                        "Se recomienda descargar la plantilla oficial.",
                    )
        else:
            detalles_validacion.append(
                "Hay errores en el formulario. Revise los campos ingresados."
            )

        return render(
            request,
            "analyst/subir_planilla_validadora.html",
            {
                "form": form,
                "estado_subida": "error",
                "detalles_validacion": detalles_validacion,
            },
        )

    return render(
        request,
        "analyst/subir_planilla_validadora.html",
        {
            "form": form,
            "estado_subida": None,
            "detalles_validacion": [],
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

    hoy = date.today()
    year_now = str(hoy.year)  # ejemplo: "2025"
    month_now = f"{hoy.month:02d}"  # ejemplo: "07"

    return render(
        request,
        "analyst/listar_archivos.html",
        {
            "archivos": archivos,
            "year_now": year_now,
            "month_now": month_now,
        },
    )


@login_required
def eliminar_archivo_subido(request, archivo_id):
    archivo = get_object_or_404(ArchivoSubido, id=archivo_id)

    # Solo permite eliminar si:
    # - El usuario es el dueño del archivo Y está dentro del mes/año actual
    # - O si es superusuario (admin), sin restricciones
    if not request.user.is_superuser:
        if archivo.usuario != request.user:
            messages.error(request, "No tienes permiso para eliminar este archivo.")
            return redirect("listar_archivos_subidos")

        ahora = timezone.now()
        if archivo.anio != ahora.year or archivo.mes != ahora.month:
            messages.error(
                request, "Solo puede eliminar archivos del mes y año actual."
            )
            return redirect("listar_archivos_subidos")

    if request.method == "POST":
        # Borrar archivo físico
        if archivo.archivo:
            archivo.archivo.delete(save=False)
        archivo.delete()
        messages.success(request, "Archivo eliminado correctamente.")
        return redirect("listar_archivos_subidos")

    return render(
        request, "analyst/confirmar_eliminar_archivo.html", {"archivo": archivo}
    )
