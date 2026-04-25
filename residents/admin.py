import csv
import io
from django.contrib import admin
from django.urls import path
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Resident, VisitorAccessRequest
from .forms import CSVUploadForm


class VisitorAccessRequestInline(admin.TabularInline):
    model = VisitorAccessRequest
    extra = 0
    readonly_fields = ("access_code", "created_at", "used_at", "expires_at")
    fields = (
        "visitor_name",
        "visitor_phone",
        "access_code",
        "created_at",
        "used_at",
        "expires_at",
    )
    can_delete = False
    max_num = 0


@admin.register(Resident)
class ResidentAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "phone")
    search_fields = ("name", "email", "phone")
    inlines = [VisitorAccessRequestInline]

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [path("upload-csv/", self.upload_csv, name="upload-csv")]
        return custom_urls + urls

    def upload_csv(self, request):
        if request.method == "POST":
            form = CSVUploadForm(request.POST, request.FILES)
            if form.is_valid():
                csv_file = request.FILES["csv_file"]
                data = csv_file.read().decode("utf-8")
                io_string = io.StringIO(data)
                reader = csv.reader(io_string)
                next(reader)  # skip header (assumes first row is header)
                created = 0
                errors = []
                for row_num, row in enumerate(reader, start=2):
                    if len(row) < 3:
                        errors.append(f"Row {row_num}: need name, email, phone")
                        continue
                    name, email, phone = row[0].strip(), row[1].strip(), row[2].strip()
                    try:
                        obj, is_new = Resident.objects.get_or_create(
                            email=email, defaults={"name": name, "phone": phone}
                        )
                        if is_new:
                            created += 1
                    except Exception as e:
                        errors.append(f"Row {row_num}: {str(e)}")
                messages.success(
                    request, f"{created} residents added. Errors: {len(errors)}"
                )
                for err in errors:
                    messages.warning(request, err)
                return redirect("admin:residents_resident_changelist")
        else:
            form = CSVUploadForm()
        context = {"form": form, "title": "Upload CSV"}
        return render(request, "admin/csv_upload.html", context)


@admin.register(VisitorAccessRequest)
class VisitorAccessRequestAdmin(admin.ModelAdmin):
    list_display = (
        "access_code",
        "resident",
        "visitor_name",
        "visitor_phone",
        "created_at",
        "expires_at",
        "used_at",
    )
    list_filter = ("used_at", "expires_at")
    search_fields = ("access_code", "visitor_name", "resident__email")
    readonly_fields = ("access_code", "created_at", "expires_at", "used_at")
