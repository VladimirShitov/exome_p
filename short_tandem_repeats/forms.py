from django import forms
from django.forms import ModelForm
from django.utils.translation import gettext_lazy as _

from loguru import logger

from short_tandem_repeats.models import STRFile, ShortTandemRepeat, STRRegion, NRepeats


class ListTextWidget(forms.TextInput):
    """Widget that allows to choose from variants or to type one"""
    def __init__(self, data_list, name, *args, **kwargs):
        super(ListTextWidget, self).__init__(*args, **kwargs)

        self.name = name
        self._list = data_list
        self.attrs.update({"list": f"list__{self.name}"})

        logger.debug("ListTextWidget attrs: {}", self.attrs)

    def render(self, name, value, attrs=None, renderer=None):
        text_html = super(ListTextWidget, self).render(name, value, attrs=attrs)
        data_list = f'<datalist id="list__{self.name}">'

        for item in self._list:
            data_list += f'<option value="{item}">'

        data_list += "</datalist>"

        return text_html + data_list


class STRFileForm(ModelForm):
    class Meta:
        model = STRFile
        fields = ["file"]
        labels = {"file": _("Excel file with short tandem repeats")}


class STRSearchForm(forms.Form):
    region = forms.ModelChoiceField(
        queryset=STRRegion.objects.all(),
        empty_label=None,
        required=True,
        label=_("Region"),
    )
    n_repeats = forms.ModelChoiceField(
        queryset=NRepeats.objects.all(),
        empty_label=None,
        required=True,
        label=_("Number of repeats"),
    )

    def __init__(self, *args, **kwargs):
        super(STRSearchForm, self).__init__()

        repeats_list = kwargs.pop("repeats_list")

        self.fields["n_repeats"].widget = ListTextWidget(data_list=repeats_list,
                                                         name="repeats-list")
