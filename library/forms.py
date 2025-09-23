from django import forms
from django.utils import timezone

from .models import Borrowing


class BorrowingAdminForm(forms.ModelForm):
    class Meta:
        model = Borrowing
        fields = "__all__"

    def clean_returned_at(self):
        value = self.cleaned_data.get("returned_at")
        # Для DateField:
        if value and value != timezone.localdate():
            raise forms.ValidationError("Дата возврата должна быть сегодняшним днём.")
        return value
