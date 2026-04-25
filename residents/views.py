from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import (
    csrf_exempt,
)  # for demo; use proper CSRF in production
from .forms import AccessCodeRequestForm
from .models import Resident, VisitorAccessRequest
from .services import send_access_code, send_gate_confirmation


def request_access_code(request):
    if request.method == "POST":
        form = AccessCodeRequestForm(request.POST)
        if form.is_valid():
            resident_email = form.cleaned_data["resident_email"]
            resident = Resident.objects.get(email=resident_email)
            visitor_name = form.cleaned_data["visitor_name"]
            visitor_phone = form.cleaned_data["visitor_phone"]
            # Create access request (code generated automatically)
            access_request = VisitorAccessRequest.objects.create(
                resident=resident,
                visitor_name=visitor_name,
                visitor_phone=visitor_phone,
            )
            # Send code via SMS & email
            send_access_code(access_request)
            messages.success(
                request, f"Access code sent to {resident.email} and {resident.phone}"
            )
            return redirect("request_access_code")
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
