import datetime
from django import forms

from .models import ArchivoSubido


class PlanillaValidadoraForm(forms.ModelForm):
    MESES_CHOICES = [
        (1, "Enero"),
        (2, "Febrero"),
        (3, "Marzo"),
        (4, "Abril"),
        (5, "Mayo"),
        (6, "Junio"),
        (7, "Julio"),
        (8, "Agosto"),
        (9, "Septiembre"),
        (10, "Octubre"),
        (11, "Noviembre"),
        (12, "Diciembre"),
    ]

    mes = forms.ChoiceField(choices=MESES_CHOICES)

    class Meta:
        model = ArchivoSubido
        fields = ["anio", "mes", "archivo"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Año y mes actuales
        ahora = datetime.date.today()
        anio_actual = ahora.year
        mes_actual = ahora.month

        # Sólo asignar initial si no hay datos POST (no sobreescribir en edición o envío)
        if not self.data:
            self.fields["anio"].initial = anio_actual
            self.fields["mes"].initial = mes_actual

        # Agregar clases Tailwind a widgets
        self.fields["anio"].widget.attrs.update(
            {
                "class": "w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            }
        )
        self.fields["mes"].widget.attrs.update(
            {
                "class": "w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            }
        )
        self.fields["archivo"].widget.attrs.update(
            {
                "class": "block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-blue-100 file:text-blue-700 hover:file:bg-blue-200 cursor-pointer border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            }
        )


class ConsolidarForm(forms.Form):
    anio = forms.IntegerField(label="Año", min_value=2000, max_value=2100)
    mes = forms.ChoiceField(label="Mes", choices=[(str(i), i) for i in range(1, 13)])
    region = forms.ModelChoiceField(
        label="Región",
        queryset=None,  # Aquí debes asignar el queryset de regiones permitidas
    )

    def __init__(self, *args, **kwargs):
        regiones = kwargs.pop("regiones", None)
        super().__init__(*args, **kwargs)
        if regiones is not None:
            self.fields["region"].queryset = regiones
