from django import forms

from .models import Lavoura
from .models import Propriedade
from .models import LoteDeCafe


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


class LoteForm(forms.ModelForm):

    class Meta:

        model = LoteDeCafe

        fields = [
        'lavoura',
        'codigo',
        'quantidade_sacas',
        'qualidade',
        'preco_saca',
        'etapa',
        'observacoes'
        ]

        widgets = {

            'lavoura': forms.Select(attrs={
                'class': 'form-select'
            }),

            'codigo': forms.TextInput(attrs={
                'class': 'form-control'
            }),

            'quantidade_sacas': forms.NumberInput(attrs={
                'class': 'form-control'
            }),

            'etapa': forms.Select(attrs={
                'class': 'form-select'
            }),
            'qualidade': forms.NumberInput(attrs={
            'class': 'form-control'
            }),

            'preco_saca': forms.NumberInput(attrs={
            'class': 'form-control'
            }),

            'observacoes': forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3
            }),

    
        }