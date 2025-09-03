from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def diccionario_planilla_validadora(request):
    return render(request, "analyst/diccionario_planilla_validadora.html")
