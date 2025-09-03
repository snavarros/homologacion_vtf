import os
import io
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages

from analyst.forms import ParametroRemuneracionalForm
from analyst.models import ParametroRemuneracional
from django.core.files.base import ContentFile
import pandas as pd


@staff_member_required
def subir_parametro_remuneracional(request):
    mensaje = None

    if request.method == "POST":
        form = ParametroRemuneracionalForm(request.POST, request.FILES)
        if form.is_valid():
            anio = int(form.cleaned_data["anio"])
            archivo = form.cleaned_data["archivo"]

            # Verificar existencia previa
            existente = ParametroRemuneracional.objects.filter(anio=anio).first()
            if existente:
                mensaje = f"Ya existe un archivo para el año {anio}. Debe eliminarlo antes de subir uno nuevo."
                return render(
                    request,
                    "analyst/subir_parametro_remuneracional.html",
                    {"form": form, "mensaje": mensaje},
                )

            try:
                # Leer archivo en DataFrame
                df = pd.read_excel(archivo)  # o read_csv según corresponda
                total_filas_original = len(df)

                # Eliminar filas vacías
                df = df.dropna(how="all")
                filas_eliminadas = total_filas_original - len(df)

                # Resumen
                columnas = list(df.columns)
                resumen = f"Archivo tiene <strong>{len(df)} filas</strong> y <strong>{len(columnas)} columnas</strong>."
                if filas_eliminadas > 0:
                    resumen += f" Se eliminaron {filas_eliminadas} filas vacías."

                # Convertir a CSV
                buffer = io.StringIO()
                df.to_csv(buffer, index=False)
                buffer.seek(0)

                filename = (
                    f"parametro_remuneracional_{anio}_{request.user.username}.csv"
                )
                file_content = ContentFile(
                    buffer.getvalue().encode("utf-8"), name=filename
                )

                # Guardar en el modelo
                ParametroRemuneracional.objects.create(
                    anio=anio,
                    archivo=file_content,
                    usuario=request.user,
                )

                mensaje = f"Archivo para año {anio} subido correctamente.<br>{resumen}"
                messages.success(request, mensaje)

                # Reiniciar form
                form = ParametroRemuneracionalForm()

            except Exception as e:
                mensaje = f"Error procesando el archivo: {str(e)}"

    else:
        form = ParametroRemuneracionalForm()

    parametros = ParametroRemuneracional.objects.all().order_by("-anio")
    return render(
        request,
        "analyst/subir_parametro_remuneracional.html",
        {"form": form, "mensaje": mensaje, "parametros": parametros},
    )


@staff_member_required
def eliminar_parametro_remuneracional(request, pk):
    parametro = get_object_or_404(ParametroRemuneracional, pk=pk)

    # Elimina el archivo físico del disco
    if parametro.archivo:
        if os.path.isfile(parametro.archivo.path):
            os.remove(parametro.archivo.path)

    parametro.delete()
    messages.success(
        request, f"Archivo del año {parametro.anio} eliminado correctamente."
    )
    return redirect("subir_parametro_remuneracional")
