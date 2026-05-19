from django import forms
from .models import Lavoura


class LavouraForm(forms.ModelForm):

    class Meta:
        model = Lavoura

        fields = [
            'nome',
            'area',
            'variedade',
            'data_plantio',
            'propriedade'
        ]

        widgets = {
            'data_plantio': forms.DateInput(
                attrs={'type': 'date'}
            )
        }