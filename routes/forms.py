from django import forms
from .gpx import GPXError, parse_gpx
from .models import Route


class RouteAdminForm(forms.ModelForm):
    class Meta:
        model = Route
        fields = "__all__"

    def clean_gpx_file(self):
        uploaded = self.cleaned_data.get("gpx_file")
        if not uploaded and not self.instance.gpx_file:
            raise forms.ValidationError("Загрузите GPX-файл.")
        if uploaded and hasattr(uploaded, "read"):
            position = uploaded.tell() if hasattr(uploaded, "tell") else 0
            try:
                parse_gpx(uploaded)
            except GPXError as exc:
                raise forms.ValidationError(str(exc)) from exc
            finally:
                if hasattr(uploaded, "seek"):
                    uploaded.seek(position)
        return uploaded
