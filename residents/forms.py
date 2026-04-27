from django import forms


class CSVUploadForm(forms.Form):
    csv_file = forms.FileField(label="CSV file (columns: name, email, phone)")


class AccessCodeRequestForm(forms.Form):
    resident_email = forms.EmailField(label="Your email address")
    visitor_name = forms.CharField(label="Visitor name", max_length=100)
    visitor_phone = forms.CharField(label="Visitor phone number", max_length=20)

    def clean_resident_email(self):
        email = self.cleaned_data["resident_email"]
        from .models import Resident

        if not Resident.objects.filter(email=email).exists():
            raise forms.ValidationError("No resident found with this email.")
        return email


# Upload users via manual entry and csv file (admin-only)
from django import forms
from .models import Resident


class ResidentForm(forms.ModelForm):
    class Meta:
        model = Resident
        fields = ["name", "email", "phone", "address", "is_active"]

    def clean_address(self):
        address = self.cleaned_data.get("address")
        if address:
            instance = self.instance
            count = Resident.objects.filter(address__iexact=address)
            if instance.pk:
                count = count.exclude(pk=instance.pk)
            if count.count() >= 4:
                raise forms.ValidationError(
                    "This address already has 4 residents. Cannot add more."
                )
        return address


class CSVUploadForm(forms.Form):
    csv_file = forms.FileField(label="CSV file (columns: name, email, phone)")
