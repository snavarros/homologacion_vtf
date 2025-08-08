import os

from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages

from analyst.forms import ParametroRemuneracionalForm
from analyst.models import ParametroRemuneracional


@staff_member_required
def subir_parametro_remuneracional(request):
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
