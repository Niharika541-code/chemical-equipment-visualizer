from django.http import HttpResponse
from django.contrib.auth import authenticate
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from django.contrib.auth.models import User

import pandas as pd

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.authtoken.models import Token

from .models import UploadHistory


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_csv(request):
    file = request.FILES['file']
    df = pd.read_csv(file)

    summary = {
        "total_equipment": len(df),
        "avg_flowrate": float(df["Flowrate"].mean()),
        "avg_pressure": float(df["Pressure"].mean()),
        "avg_temperature": float(df["Temperature"].mean()),
        "type_distribution": df["Type"].value_counts().to_dict()
    }

    UploadHistory.objects.create(
        total_equipment=summary["total_equipment"],
        avg_flowrate=summary["avg_flowrate"],
        avg_pressure=summary["avg_pressure"],
        avg_temperature=summary["avg_temperature"],
        type_distribution=str(summary["type_distribution"])
    )

    return Response({"summary": summary})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def history(request):
    records = UploadHistory.objects.all().order_by('-created_at')[:5]
    data = []

    for r in records:
        data.append({
            "time": r.created_at.strftime("%d-%m-%Y %H:%M"),
            "total_equipment": r.total_equipment,
            "avg_flowrate": r.avg_flowrate,
            "avg_pressure": r.avg_pressure,
            "avg_temperature": r.avg_temperature,
        })

    return Response(data)


@api_view(['GET'])
@permission_classes([AllowAny])
def generate_report(request):
    latest = UploadHistory.objects.last()
    if not latest:
        return Response({"error": "No data"}, status=404)

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="report.pdf"'

    pdf = canvas.Canvas(response, pagesize=A4)
    pdf.drawString(50, 800, "Chemical Equipment Report")
    pdf.drawString(50, 770, f"Total Equipment: {latest.total_equipment}")
    pdf.drawString(50, 740, f"Avg Flowrate: {latest.avg_flowrate}")
    pdf.drawString(50, 710, f"Avg Pressure: {latest.avg_pressure}")
    pdf.drawString(50, 680, f"Avg Temperature: {latest.avg_temperature}")

    pdf.showPage()
    pdf.save()
    return response


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    user = authenticate(
        username=request.data.get("username"),
        password=request.data.get("password")
    )

    if user is None:
        return Response({"error": "Invalid credentials"}, status=401)

    token, _ = Token.objects.get_or_create(user=user)
    return Response({"token": token.key})

@api_view(["POST"])
@permission_classes([AllowAny])
def create_user(request):
    username = request.data.get("username")
    password = request.data.get("password")

    if not username or not password:
        return Response({"error": "Username and password required"}, status=400)

    if User.objects.filter(username=username).exists():
        return Response({"error": "User already exists"}, status=400)

    User.objects.create_user(username=username, password=password)
    return Response({"message": "User created successfully"})