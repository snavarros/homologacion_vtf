from datetime import date
import os
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.http import FileResponse, Http404, HttpResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.core.files.base import ContentFile

from .planilla_validadora import PlanillaValidadora

from .models import ArchivoSubido, Region
from .forms import (
    ConsolidarForm,
    ParametroRemuneracionalForm,
    PlanillaValidadoraForm,
    SemestreAnteriorForm,
)

import pandas as pd
import io
from django.contrib import messages
from django.utils import timezone


def validar_columnas_y_convertir(archivo, tipo):
    validador = PlanillaValidadora(tipo)
    df = validador.cargar_archivo(archivo)

    if isinstance(df, str):
        return False, [df]  # error de carga

    valido, errores = validador.validar(df)
    if not valido:
        return False, errores

    return True, df


def validar_perfil(perfil):
    if not perfil or not perfil.region:
        return False, ["No tiene una región asignada. No puede subir archivos."]
    return True, []


def validar_archivo(nombre_archivo):
    if not nombre_archivo.endswith((".xls", ".xlsx", ".csv")):
        return False, [
            "Formato de archivo no permitido. Solo se permiten .xls, .xlsx o .csv."
        ]
    return True, []


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


@staff_member_required
def consolidar_archivos(request):
    mensaje = None

    regiones_ids = ArchivoSubido.objects.values_list("region", flat=True).distinct()
    regiones = Region.objects.filter(id__in=regiones_ids)

    if request.method == "POST":
        form = ConsolidarForm(request.POST, regiones=regiones)
        if form.is_valid():
            anio = int(form.cleaned_data["anio"])
            mes_inicio = int(form.cleaned_data["mes_inicio"])
            mes_termino = int(form.cleaned_data["mes_termino"])
            region = form.cleaned_data["region"].id
            proceso = form.cleaned_data["proceso"]

            if mes_termino < mes_inicio:
                mensaje = "El mes término no puede ser menor que el mes inicio."
                return render(
                    request,
                    "analyst/consolidar_admin.html",
                    {"form": form, "mensaje": mensaje},
                )

            archivos = ArchivoSubido.objects.filter(
                anio=anio,
                region=region,
                proceso=proceso,
                mes__gte=mes_inicio,
                mes__lte=mes_termino,
            )

            if not archivos.exists():
                mensaje = "No se encontraron archivos para esos filtros."
            else:
                dfs = []
                for archivo in archivos:
                    try:
                        df = pd.read_csv(archivo.archivo.path)
                        dfs.append(df)
                    except Exception as e:
                        mensaje = f"Error leyendo archivo {archivo.archivo.name}: {e}"
                        break

                if mensaje:
                    return render(
                        request,
                        "analyst/consolidar_admin.html",
                        {"form": form, "mensaje": mensaje},
                    )

                df_consolidado = pd.concat(dfs, ignore_index=True)

                output = io.BytesIO()
                with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                    df_consolidado.to_excel(
                        writer, index=False, sheet_name="Consolidado"
                    )

                output.seek(0)
                filename = f"consolidado_{proceso}_{region}_{anio}_{mes_inicio:02d}_{mes_termino:02d}.xlsx"
                response = HttpResponse(
                    output.read(),
                    content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
                response["Content-Disposition"] = f"attachment; filename={filename}"
                return response
        else:
            mensaje = "Formulario inválido, revise los datos."
    else:
        form = ConsolidarForm(regiones=regiones)

    return render(
        request,
        "analyst/consolidar_admin.html",
        {
            "form": form,
            "mensaje": mensaje,
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


@login_required
def consolidar_semestre_anterior(request):
    mensaje = None
    user = request.user

    if request.method == "POST":
        form = SemestreAnteriorForm(request.user, request.POST)

        # Forzar región para usuarios normales antes de validar
        if not user.is_superuser:
            if hasattr(user, "perfilusuario") and user.perfilusuario.region:
                region_obj = user.perfilusuario.region
                form.data = form.data.copy()  # Make it mutable
                form.data["region"] = region_obj.id  # Reasignamos en el form
            else:
                form.add_error("region", "No se encontró región asociada al usuario.")

        if form.is_valid():
            anio = int(form.cleaned_data["anio"])
            mes = int(form.cleaned_data["mes"])
            region = form.cleaned_data["region"]

            # Determinar semestre anterior
            if mes <= 6:
                semestre_anio = anio - 1
                meses_semestre = list(range(7, 13))  # Julio a Diciembre año anterior
            else:
                semestre_anio = anio
                meses_semestre = list(range(1, 7))  # Enero a Junio mismo año

            archivos = ArchivoSubido.objects.filter(
                anio=semestre_anio,
                mes__in=meses_semestre,
                proceso="planilla_validadora",
                region=region.id,
            )

            meses_cargados = set(archivos.values_list("mes", flat=True))
            meses_faltantes = set(meses_semestre) - meses_cargados

            if meses_faltantes:
                meses_faltantes_str = ", ".join(str(m) for m in sorted(meses_faltantes))
                mensaje = f"No se puede realizar el cálculo ya que no tiene los meses solicitados: {meses_faltantes_str} del año {semestre_anio}."
                return render(
                    request,
                    "analyst/consolidar_semestre.html",
                    {"form": form, "mensaje": mensaje},
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
                        "analyst/consolidar_semestre.html",
                        {"form": form, "mensaje": mensaje},
                    )

            df_consolidado = pd.concat(dfs, ignore_index=True)

            output = io.BytesIO()
            with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                df_consolidado.to_excel(writer, index=False, sheet_name="Consolidado")

            output.seek(0)
            filename = f"consolidado_planilla_validadora_{region.id}_{semestre_anio}_semestre.xlsx"
            response = HttpResponse(
                output.read(),
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
            response["Content-Disposition"] = f"attachment; filename={filename}"
            return response
    else:
        form = SemestreAnteriorForm(request.user)

    return render(
        request, "analyst/consolidar_semestre.html", {"form": form, "mensaje": mensaje}
    )


@staff_member_required
def subir_parametro_remuneracional(request):
    from .models import ParametroRemuneracional

    mensaje = None

    if request.method == "POST":
        form = ParametroRemuneracionalForm(request.POST, request.FILES)
        if form.is_valid():
            anio = int(form.cleaned_data["anio"])
            archivo = form.cleaned_data["archivo"]

            # Validaciones como antes...

            # Verificar existencia previa
            existente = ParametroRemuneracional.objects.filter(anio=anio).first()
            if existente:
                mensaje = f"Ya existe un archivo para el año {anio}. Debe eliminarlo antes de subir uno nuevo."
                return render(
                    request,
                    "analyst/subir_parametro_remuneracional.html",
                    {"form": form, "mensaje": mensaje},
                )

            # Guardar usando modelo
            nuevo = ParametroRemuneracional.objects.create(
                anio=anio,
                archivo=archivo,
                usuario=request.user,
            )
            nuevo.save()

            messages.success(request, f"Archivo para año {anio} subido correctamente.")
            form = ParametroRemuneracionalForm()
    else:
        form = ParametroRemuneracionalForm()

    return render(
        request,
        "analyst/subir_parametro_remuneracional.html",
        {"form": form, "mensaje": mensaje},
    )
