from datetime import date, datetime
from django import forms

from .utils import MESES_CHOICES

from .models import ArchivoSubido, Region


class PlanillaValidadoraForm(forms.ModelForm):
    ahora = date.today()
    ANIOS_CHOICES = [(anio, anio) for anio in range(2018, ahora.year + 2)]

    anio = forms.ChoiceField(choices=ANIOS_CHOICES)
    mes = forms.ChoiceField(choices=MESES_CHOICES)

    class Meta:
        model = ArchivoSubido
        fields = ["anio", "mes", "archivo"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        ahora = date.today()
        anio_actual = ahora.year
        mes_actual = ahora.month

        if not self.data:
            self.fields["anio"].initial = anio_actual
            self.fields["mes"].initial = mes_actual

        # Tailwind styles
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
    PROCESOS_CHOICES = ArchivoSubido.PROCESOS

    anio = forms.ChoiceField(
        choices=[(str(y), str(y)) for y in range(2018, date.today().year + 1)],
        label="Año",
    )
    mes_inicio = forms.ChoiceField(
        choices=MESES_CHOICES,
        label="Mes Inicio",
    )
    mes_termino = forms.ChoiceField(
        choices=MESES_CHOICES,
        label="Mes Término",
    )
    region = forms.ModelChoiceField(queryset=Region.objects.none(), label="Región")
    proceso = forms.ChoiceField(choices=PROCESOS_CHOICES, label="Proceso")

    def __init__(self, *args, **kwargs):
        regiones = kwargs.pop("regiones", None)
        super().__init__(*args, **kwargs)

        if regiones is not None:
            self.fields["region"].queryset = regiones

        hoy = date.today()
        if not self.data:
            self.fields["anio"].initial = str(hoy.year)
            self.fields["mes_inicio"].initial = f"{hoy.month:02d}"
            self.fields["mes_termino"].initial = f"{hoy.month}"
            self.fields["proceso"].initial = "planilla_validadora"

        for field in self.fields.values():
            field.widget.attrs.update(
                {
                    "class": "w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                }
            )


class SemestreAnteriorForm(forms.Form):
    anio = forms.ChoiceField(
        choices=[(str(y), str(y)) for y in range(2018, date.today().year + 1)],
        label="Año",
    )
    mes = forms.ChoiceField(
        choices=MESES_CHOICES,
        label="Mes",
    )
    region = forms.ModelChoiceField(
        queryset=Region.objects.none(),  # Se asigna dinámicamente
        label="Región",
        required=True,
    )

    def __init__(self, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        hoy = date.today()
        if not self.data:
            self.fields["anio"].initial = str(hoy.year)
            self.fields["mes"].initial = hoy.month

        if user:
            if user.is_superuser:
                # Admin ve todas las regiones
                self.fields["region"].queryset = Region.objects.all()
                self.fields["region"].widget.attrs.update(
                    {
                        "class": "w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    }
                )
            else:
                # Usuario normal: sólo su región, campo readonly
                if hasattr(user, "perfilusuario") and user.perfilusuario.region:
                    region = user.perfilusuario.region
                    self.fields["region"].queryset = Region.objects.filter(id=region.id)
                    self.fields["region"].initial = region
                    self.fields["region"].widget.attrs.update(
                        {
                            "class": "bg-gray-100 w-full rounded px-3 py-2 cursor-not-allowed",
                            "readonly": "readonly",
                        }
                    )
                else:
                    self.fields["region"].queryset = Region.objects.none()
                    self.fields["region"].widget.attrs.update(
                        {
                            "class": "w-full border border-gray-300 rounded px-3 py-2",
                        }
                    )
        else:
            self.fields["region"].queryset = Region.objects.none()

        # Añadir estilos comunes a anio y mes
        for field_name in ("anio", "mes"):
            self.fields[field_name].widget.attrs.update(
                {
                    "class": "w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                }
            )


class ParametroRemuneracionalForm(forms.Form):
    anio = forms.ChoiceField(
        choices=[(str(y), str(y)) for y in range(2020, date.today().year + 2)],
        label="Año",
    )
    archivo = forms.FileField(
        label="Archivo Parámetro Remuneracional (CSV)",
        widget=forms.ClearableFileInput(
            attrs={
                "class": "block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-green-100 file:text-green-700 hover:file:bg-green-200 cursor-pointer border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
            }
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.is_bound:
            self.fields["anio"].initial = datetime.now().year
