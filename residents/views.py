from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import (
    csrf_exempt,
)  # for demo; use proper CSRF in production
from .forms import AccessCodeRequestForm
from .models import Resident, VisitorAccessRequest, BlacklistedAddress
from .services import send_access_code, send_gate_confirmation

# add /upload residents
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .forms import ResidentForm, CSVUploadForm
from .models import Resident
import csv
import io


def request_access_code(request):
    if request.method == "POST":
        form = AccessCodeRequestForm(request.POST)
        if form.is_valid():
            resident_email = form.cleaned_data["resident_email"]
            visitor_name = form.cleaned_data["visitor_name"]
            visitor_phone = form.cleaned_data["visitor_phone"]

            try:
                resident = Resident.objects.get(email=resident_email)
            except Resident.DoesNotExist:
                messages.error(request, "No resident found with this email.")
                return redirect("residents:request_access_code")

            # Check if resident is active
            if not resident.is_active:
                messages.error(
                    request,
                    "Your account is inactive. You cannot request access codes.",
                )
                return redirect("residents:request_access_code")

            # Check if resident's address is blacklisted
            if resident.address:
                if BlacklistedAddress.objects.filter(
                    address__iexact=resident.address
                ).exists():
                    messages.error(
                        request,
                        "Your address is blacklisted. You cannot request access codes.",
                    )
                    return redirect("residents:request_access_code")

            # *** CREATE THE ACCESS REQUEST (generates unique code automatically) ***
            access_request = VisitorAccessRequest.objects.create(
                resident=resident,
                visitor_name=visitor_name,
                visitor_phone=visitor_phone,
            )

            # *** SEND THE CODE VIA EMAIL & SMS ***
            send_access_code(access_request)

            messages.success(
                request, f"Access code sent to {resident.email} and {resident.phone}"
            )
            return redirect("residents:request_access_code")
    else:
        form = AccessCodeRequestForm()
    return render(request, "residents/request_code.html", {"form": form})


def verify_access_code(request):
    """Gate endpoint: POST with 'code' to validate and use."""
    if request.method == "POST":
        code = request.POST.get("code")
        if not code:
            return JsonResponse({"error": "Code required"}, status=400)
        access_request = get_object_or_404(VisitorAccessRequest, access_code=code)
        if access_request.is_valid():
            access_request.use()
            send_gate_confirmation(access_request)
            return JsonResponse(
                {
                    "status": "granted",
                    "message": f"Access granted for {access_request.visitor_name}",
                    "resident": access_request.resident.name,
                }
            )
        else:
            return JsonResponse({"error": "Code expired or already used"}, status=403)
    # GET shows simple form for testing
    return render(request, "residents/verify_form.html")


@staff_member_required
def add_resident(request):
    if request.method == "POST":
        form = ResidentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Resident added successfully.")
            return redirect("residents:add_resident")
    else:
        form = ResidentForm()
    return render(request, "residents/add_resident.html", {"form": form})


@staff_member_required
def upload_residents_csv(request):
    if request.method == "POST":
        form = CSVUploadForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES["csv_file"]
            # Decode and parse
            data = csv_file.read().decode("utf-8")
            io_string = io.StringIO(data)
            reader = csv.reader(io_string)
            header = next(reader)  # skip header row: name,email,phone
            created = 0
            errors = []
            for row_num, row in enumerate(reader, start=2):
                if len(row) < 3:
                    errors.append(
                        f"Row {row_num}: insufficient columns (need name, email, phone)"
                    )
                    continue
                name, email, phone = row[0].strip(), row[1].strip(), row[2].strip()
                try:
                    obj, is_new = Resident.objects.get_or_create(
                        email=email,
                        defaults={"name": name, "phone": phone, "is_active": True},
                    )
                    if is_new:
                        created += 1
                    else:
                        errors.append(
                            f"Row {row_num}: resident with email {email} already exists"
                        )
                except Exception as e:
                    errors.append(f"Row {row_num}: {str(e)}")
            messages.success(request, f"{created} new residents added.")
            for err in errors:
                messages.warning(request, err)
            return redirect("residents:upload_residents_csv")
    else:
        form = CSVUploadForm()
    return render(request, "residents/upload_csv.html", {"form": form})
