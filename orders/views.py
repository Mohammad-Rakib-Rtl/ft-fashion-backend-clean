# orders/views.py - ONLY THE CHECKOUT FUNCTION

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
    # === DEBUG LOGS START ===
    logger.info("🔍 [CHECKOUT] Function called")
    logger.info(f"🔍 [CHECKOUT] Request method: {request.method}")
    logger.info(f"🔍 [CHECKOUT] Request  {request.data}")
    logger.info(f"🔍 [CHECKOUT] CLOUDINARY_CLOUD_NAME env: {os.environ.get('CLOUDINARY_CLOUD_NAME')}")
    # === DEBUG LOGS END ===

    serializer = CheckoutSerializer(data=request.data)
    
    # === DEBUG LOGS START ===
    if not serializer.is_valid():
        logger.error(f"❌ [CHECKOUT] Serializer errors: {serializer.errors}")
    else:
        logger.info("✅ [CHECKOUT] Serializer is valid")
    # === DEBUG LOGS END ===
    
    if serializer.is_valid():
        order = serializer.save()
        
        # === DEBUG LOGS START ===
        logger.info(f"✅ [CHECKOUT] Order saved: code={order.code}, customer={order.customer_name}")
        logger.info(f"✅ [CHECKOUT] Order items count: {order.items.count()}")
        # === DEBUG LOGS END ===
        
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
        data = [["SL", "Image", "Code", "Name", "Size", "Quantity", "Unit Price", "TOTAL"]]

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
            # === DEBUG LOGS START ===
            logger.info(f"📦 [ITEM] Processing: product_id={item.product.id if item.product else 'None'}")
            # === DEBUG LOGS END ===
            
            subtotal = item.product.price * item.quantity

            img = Paragraph("-", styles["Normal"])

            if item.product.image:
                try:
                    # Get the image URL
                    image_url = item.product.image.url
                    
                    # === DEBUG LOGS START ===
                    logger.info(f"🖼️ [IMAGE] Original image_url: {image_url}")
                    # === DEBUG LOGS END ===
                    
                    # If it's a local path, try to construct the Cloudinary URL
                    if image_url.startswith('/media/'):
                        # Extract filename
                        filename = image_url.replace('/media/', '')
                        
                        # Construct Cloudinary URL using your Cloudinary configuration
                        cloud_name = os.environ.get("CLOUDINARY_CLOUD_NAME")
                        
                        # === DEBUG LOGS START ===
                        logger.info(f"🖼️ [IMAGE] Filename: {filename}")
                        logger.info(f"🖼️ [IMAGE] Cloud name from env: {cloud_name}")
                        # === DEBUG LOGS END ===
                        
                        if cloud_name:
                            # Try to create a Cloudinary URL
                            image_url = f"https://res.cloudinary.com/  {cloud_name}/image/upload/{filename}"
                            # === DEBUG LOGS START ===
                            logger.info(f"🖼️ [IMAGE] Constructed Cloudinary URL: '{image_url}'")
                            logger.warning(f"⚠️ [IMAGE] URL contains spaces! This will cause download to fail.")
                            # === DEBUG LOGS END ===
                    
                    # Make sure we have a valid URL
                    if not image_url.startswith('http'):
                        # If still not valid, use a placeholder
                        logger.warning(f"Invalid image URL: {image_url}")
                        img = Paragraph("-", styles["Normal"])
                    else:
                        # === DEBUG LOGS START ===
                        logger.info(f"🖼️ [IMAGE] Attempting to download from: {image_url}")
                        # === DEBUG LOGS END ===
                        
                        # Download with timeout
                        response = requests.get(image_url, timeout=30)
                        response.raise_for_status()
                        
                        # Create image from bytes
                        img = Image(BytesIO(response.content), width=0.7 * inch, height=0.7 * inch)
                        # === DEBUG LOGS START ===
                        logger.info(f"✅ [IMAGE] Successfully loaded image")
                        # === DEBUG LOGS END ===
                        
                except Exception as e:
                    logger.error(f"Error loading image for product {item.product.name}: {e}")
                    img = Paragraph("-", styles["Normal"])
                    # === DEBUG LOGS START ===
                    logger.warning(f"⚠️ [IMAGE] Using placeholder due to error")
                    # === DEBUG LOGS END ===

            # === DEBUG LOGS START ===
            logger.info(f"📝 [NAME] Raw name: '{item.product.name}', code: '{item.product.code}'")
            # === DEBUG LOGS END ===
            
            product_name_text = item.product.name or item.product.code
            
            # === DEBUG LOGS START ===
            logger.info(f"📝 [NAME] After fallback: '{product_name_text}'")
            if product_name_text is None:
                logger.error(f"❌ [NAME] product_name_text is None! This will crash on len()")
            # === DEBUG LOGS END ===
            
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
        
        # === DEBUG LOGS START ===
        logger.info("📄 [PDF] Building PDF document...")
        # === DEBUG LOGS END ===
        
        doc.build(elements)

        pdf_bytes = buffer.getvalue()
        buffer.close()

        # === DEBUG LOGS START ===
        logger.info(f"✅ [PDF] PDF generated, size: {len(pdf_bytes)} bytes")
        # === DEBUG LOGS END ===

        print("Checkout completed — email skipped to avoid worker timeout")

        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="invoice_{order.code}.pdf"'
        
        # === DEBUG LOGS START ===
        logger.info(f"✅ [CHECKOUT] Returning PDF response for order {order.code}")
        # === DEBUG LOGS END ===
        
        return response

    # === DEBUG LOGS START ===
    logger.error(f"❌ [CHECKOUT] Returning 400 - serializer errors: {serializer.errors}")
    # === DEBUG LOGS END ===
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
