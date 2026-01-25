# orders/views.py - Corrected version without undefined functions

from urllib import response
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .serializers import CheckoutSerializer
from .models import Order
from django.core.mail import EmailMessage
from django.conf import settings
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer, Image
from reportlab.lib.units import inch
import os
import requests
from tempfile import NamedTemporaryFile
from django.http import HttpResponse
import logging
import cloudinary

logger = logging.getLogger(__name__)

@api_view(['POST'])
def checkout(request):
    serializer = CheckoutSerializer(data=request.data)
    if serializer.is_valid():
        order = serializer.save()
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4,
                                leftMargin=50, rightMargin=50,
                                topMargin=50, bottomMargin=50)
        elements = []
        styles = getSampleStyleSheet()

        # --- Title ---
        title_style = ParagraphStyle(
            name='Title',
            fontSize=22,
            textColor=colors.HexColor("#e65c00"),
            alignment=1,
            spaceAfter=12,
            fontName="Helvetica-Bold"
        )
        elements.append(Paragraph("FT FASHION INVOICE", title_style))
        elements.append(Spacer(1, 10))

        # --- Order Info ---
        info_style = ParagraphStyle(name='Info', fontSize=11, leading=15, leftIndent=0)
        info_table_data = [
            [Paragraph(f"<b>Order Code:</b> {order.code}", info_style)],
            [Paragraph(f"<b>Customer Name:</b> {order.customer_name}", info_style)],
            [Paragraph(f"<b>Contact Number:</b> {order.customer_phone}", info_style)],
            [Paragraph(f"<b>Email:</b> {order.customer_email}", info_style)],
            [Paragraph(f"<b>Total Items:</b> {order.items.count()}", info_style)],
        ]

        info_table = Table(info_table_data, colWidths=[480])
        info_table.setStyle(TableStyle([
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 12))

        # --- Table Header ---
        data = [["SL", "Image", "Code", "Product Name", "Size", "Quantity", "Unit Price", "TOTAL"]]

        # --- Table Content ---
        total = 0
        serial_no = 1

        # Style for product name cell (wrap text)
        product_name_style = ParagraphStyle(
            name="ProductName",
            fontSize=10,
            leading=12,
            alignment=0,  # left align
            wordWrap="CJK",  # ensures word wrapping works properly
        )

        for item in order.items.all():
            subtotal = item.product.price * item.quantity

            img = Paragraph("-", styles["Normal"])

            if item.product.image:
                try:
                    # Get the image URL
                    image_url = item.product.image.url
                    
                    # If it's a local path, try to construct the Cloudinary URL
                    if image_url.startswith('/media/'):
                        # Extract filename
                        filename = image_url.replace('/media/', '')
                        
                        # Construct Cloudinary URL using your Cloudinary configuration
                        cloud_name = os.environ.get("CLOUDINARY_CLOUD_NAME")
                        if cloud_name:
                            # Try to create a Cloudinary URL
                            image_url = f"https://res.cloudinary.com/{cloud_name}/image/upload/{filename}"
                    
                    # Make sure we have a valid URL
                    if not image_url.startswith('http'):
                        # If still not valid, use a placeholder
                        logger.warning(f"Invalid image URL: {image_url}")
                        img = Paragraph("-", styles["Normal"])
                    else:
                        # Download with timeout
                        response = requests.get(image_url, timeout=30)
                        response.raise_for_status()
                        
                        # Create image from bytes
                        img = Image(BytesIO(response.content), width=0.7 * inch, height=0.7 * inch)
                        
                except Exception as e:
                    logger.error(f"Error loading image for product {item.product.name}: {e}")
                    img = Paragraph("-", styles["Normal"])

            product_name_text = item.product.name
            if len(product_name_text) > 60:
                product_name_text = product_name_text[:57] + "..."

            product_name = Paragraph(product_name_text, product_name_style)

            data.append([
                str(serial_no),
                img,
                item.product.code or "-",
                product_name,
                item.size or "-",
                str(item.quantity),
                f"{item.product.price:.2f}",
                f"{subtotal:.2f}"
            ])

            total += subtotal
            serial_no += 1

        # --- Add Total Row ---
        data.append(["", "", "", "", "", "", "Total:", f"{total:.2f} BDT"])
        
        # --- Table Style ---
        table = Table(data, colWidths=[30, 60, 60, 150, 40, 40, 80, 80])
        table_style = TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#ff6600")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("BACKGROUND", (0, 1), (-1, -2), colors.whitesmoke),
            ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#f9f9f9")),
            ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ])
        table.setStyle(table_style)

        elements.append(table)
        doc.build(elements)

        pdf_bytes = buffer.getvalue()
        buffer.close()

        print("Checkout completed — email skipped to avoid worker timeout")

        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="invoice_{order.code}.pdf"'
        return response

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Only add this test function if you want to test Cloudinary connection
def test_cloudinary_connection(request):
    """Test Cloudinary connection and configuration"""
    try:
        # Ping Cloudinary
        ping_result = cloudinary.api.ping()
        
        # Get a sample product with image
        from products.models import Product
        product = Product.objects.first()
        
        image_url = None
        is_cloudinary = False
        
        if product and product.image:
            image_url = product.image.url
            is_cloudinary = 'cloudinary' in image_url.lower() or 'res.cloudinary.com' in image_url.lower()
        
        return JsonResponse({
            'success': True,
            'ping_result': ping_result,
            'image_url': image_url,
            'is_cloudinary': is_cloudinary,
            'message': 'Cloudinary connection successful'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'message': 'Cloudinary connection failed'
        })


# Add this import at the top of the file if you use the test function
from django.http import JsonResponse