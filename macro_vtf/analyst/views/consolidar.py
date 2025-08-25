import io
import pandas as pd

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render
from django.db.models import Q

from analyst.forms import ConsolidarForm, SemestreAnteriorForm
from analyst.models import ArchivoSubido, Region
from analyst.views.helpers import calcular_homologacion


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
                form.data["region"] = region_obj.id
            else:
                form.add_error("region", "No se encontró región asociada al usuario.")

        if form.is_valid():
            anio = int(form.cleaned_data["anio"])
            mes = int(form.cleaned_data["mes"]) - 1  # mes anterior
            region = form.cleaned_data["region"]

            if mes <= 6:
                # Semestre anterior: julio a diciembre del año anterior
                semestre_anio_anterior = anio - 1
                meses_semestre_anterior = list(range(7, 13))  # 7 a 12

                # Semestre actual: enero hasta el mes actual del año actual
                semestre_anio_actual = anio
                meses_semestre_actual = list(range(1, mes + 1))  # 1 hasta mes actual

                archivos = ArchivoSubido.objects.filter(
                    Q(anio=semestre_anio_anterior, mes__in=meses_semestre_anterior)
                    | Q(anio=semestre_anio_actual, mes__in=meses_semestre_actual),
                    proceso="planilla_validadora",
                    region=region.id,
                )

                meses_esperados = {
                    (semestre_anio_anterior, m) for m in meses_semestre_anterior
                } | {(semestre_anio_actual, m) for m in meses_semestre_actual}

                anio_referencia = anio  # Para nombre del archivo

            else:
                semestre_anio = anio
                meses_semestre = list(range(1, mes + 1))  # Enero a Junio

                archivos = ArchivoSubido.objects.filter(
                    anio=semestre_anio,
                    mes__in=meses_semestre,
                    proceso="planilla_validadora",
                    region=region.id,
                )

                meses_esperados = {(semestre_anio, m) for m in meses_semestre}
                anio_referencia = semestre_anio

            # Verificar meses faltantes
            meses_cargados = set(archivos.values_list("anio", "mes"))
            meses_faltantes = meses_esperados - meses_cargados

            if meses_faltantes:
                faltantes_str = ", ".join(
                    f"{m[1]}/{m[0]}" for m in sorted(meses_faltantes)
                )
                mensaje = f"No se puede realizar el cálculo ya que no tiene los meses solicitados: {faltantes_str}."
                return render(
                    request,
                    "analyst/consolidar_semestre.html",
                    {"form": form, "mensaje": mensaje},
                )

            # Consolidar archivos en un DataFrame
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

            df_consolidado = calcular_homologacion(df_consolidado, anio, mes)

            # Exportar a Excel
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                df_consolidado.to_excel(writer, index=False, sheet_name="Consolidado")

            output.seek(0)
            filename = f"calculo_homologacion_region_{region.id}_{anio_referencia}_semestre.xlsx"
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
