from django import forms

from .models import (
    Lavoura,
    Propriedade
)


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

            'nome': forms.TextInput(attrs={
                'class': 'form-control'
            }),

            'area': forms.NumberInput(attrs={
                'class': 'form-control'
            }),

            'variedade': forms.TextInput(attrs={
                'class': 'form-control'
            }),

            'data_plantio': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),

            'propriedade': forms.Select(attrs={
                'class': 'form-select'
            }),
        }


class PropriedadeForm(forms.ModelForm):

    class Meta:

        model = Propriedade

        fields = [
            'nome',
            'cidade',
            'hectares'
        ]

        widgets = {

            'nome': forms.TextInput(attrs={
                'class': 'form-control'
            }),

            'cidade': forms.TextInput(attrs={
                'class': 'form-control'
            }),

            'hectares': forms.NumberInput(attrs={
                'class': 'form-control'
            }),
        }