from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib.colors import HexColor, black, white
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from io import BytesIO
import base64
from PIL import Image, ImageDraw
import io
import os
import tempfile



def get_default_avatar_for_pdf():
    """Load default avatar from assets for PDF"""
    # Try multiple possible paths
    possible_paths = [
        os.path.join('assets', 'default_avatar.png'),
        os.path.join('assets', 'default_avatar.jpg'),
        'assets/default_avatar.png',
        'assets/default_avatar.jpg'
    ]
    
    for avatar_path in possible_paths:
        if os.path.exists(avatar_path):
            try:
                with open(avatar_path, 'rb') as f:
                    return f.read()
            except Exception as e:
                print(f"Error loading {avatar_path}: {e}")
                continue
    
    print("Warning: No default avatar found in assets folder")
    return None



def create_circular_image_simple(image_bytes, size=70):
    """Create circular image - save as temp file for reportlab"""
    try:
        # Open and resize
        img = Image.open(io.BytesIO(image_bytes))
        img = img.convert('RGB')
        img = img.resize((size, size), Image.Resampling.LANCZOS)
        
        # Create circular mask
        mask = Image.new('L', (size, size), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, size, size), fill=255)
        
        # Apply mask
        output = Image.new('RGB', (size, size), (255, 255, 255))
        output.paste(img, (0, 0))
        
        # Make corners white (circular mask)
        for x in range(size):
            for y in range(size):
                dist = ((x - size/2)**2 + (y - size/2)**2)**0.5
                if dist > size/2:
                    output.putpixel((x, y), (255, 255, 255))
        
        # Save to temp file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
        output.save(temp_file.name, 'JPEG', quality=95)
        temp_file.close()
        
        return temp_file.name
    except Exception as e:
        print(f"Error creating circular image: {e}")
        return None



def export_tree_to_pdf_visual(tree_data):
    """Export family tree as visual PDF with images"""
    
    pdf_buffer = BytesIO()
    page_width, page_height = landscape(A4)
    
    c = canvas.Canvas(pdf_buffer, pagesize=landscape(A4))
    c.setTitle("Family Tree")
    
    # White background
    c.setFillColor(white)
    c.rect(0, 0, page_width, page_height, fill=1, stroke=0)
    
    # Title
    c.setFont("Helvetica-Bold", 24)
    c.setFillColor(black)
    c.drawString(inch, page_height - 0.5*inch, "Family Tree")
    
    nodes = tree_data.get('nodes', [])
    edges = tree_data.get('edges', [])
    
    if not nodes:
        c.save()
        pdf_buffer.seek(0)
        return pdf_buffer.getvalue()
    
    person_nodes = [n for n in nodes if n.get('type') == 'person']
    
    if not person_nodes:
        c.save()
        pdf_buffer.seek(0)
        return pdf_buffer.getvalue()
    
    # Calculate bounds
    min_x = min(n.get('x', 0) for n in person_nodes)
    max_x = max(n.get('x', 0) for n in person_nodes)
    min_y = min(n.get('y', 0) for n in person_nodes)
    max_y = max(n.get('y', 0) for n in person_nodes)
    
    tree_width = max_x - min_x if max_x > min_x else 100
    tree_height = max_y - min_y if max_y > min_y else 100
    
    padding = 100
    tree_width += padding * 2
    tree_height += padding * 2
    
    available_width = page_width - 2*inch
    available_height = page_height - 2*inch
    
    scale_x = available_width / tree_width if tree_width > 0 else 1
    scale_y = available_height / tree_height if tree_height > 0 else 1
    scale = min(scale_x, scale_y, 1.2)
    
    offset_x = inch + (available_width - tree_width*scale) / 2
    offset_y = page_height - inch - (available_height - tree_height*scale) / 2
    
    def transform_point(x, y):
        scaled_x = (x - min_x + padding) * scale
        scaled_y = (y - min_y + padding) * scale
        return offset_x + scaled_x, offset_y - scaled_y
    
    # Draw edges
    c.setStrokeColor(black)
    c.setLineWidth(2)
    
    for edge in edges:
        edge_type = edge.get('type', 'spouse')
        source_node = next((n for n in nodes if n['id'] == edge['source']), None)
        target_node = next((n for n in nodes if n['id'] == edge['target']), None)
        
        if source_node and target_node:
            x1, y1 = transform_point(source_node.get('x', 0), source_node.get('y', 0))
            x2, y2 = transform_point(target_node.get('x', 0), target_node.get('y', 0))
            
            if edge_type == 'child_to_parent':
                mid_y = (y1 + y2) / 2
                c.bezier(x1, y1, x1, mid_y, x2, mid_y, x2, y2)
            elif edge_type in ['spouse', 'parent_to_junction']:
                c.line(x1, y1, x2, y2)
    
    # Draw nodes
    node_radius = 35 * scale
    default_avatar_bytes = get_default_avatar_for_pdf()
    temp_files = []
    
    for node in person_nodes:
        x, y = transform_point(node.get('x', 0), node.get('y', 0))
        name = node.get('name', 'Unknown')
        
        # Get image - prioritize user photo, fallback to default avatar
        image_bytes = None
        photo_b64 = node.get('photo')
        
        if photo_b64:
            try:
                image_bytes = base64.b64decode(photo_b64)
            except:
                pass
        
        # Use default avatar if no photo
        if not image_bytes:
            image_bytes = default_avatar_bytes
        
        # Draw white circle background
        c.setFillColor(white)
        c.setStrokeColor(black)
        c.setLineWidth(3)
        c.circle(x, y, node_radius, fill=1, stroke=1)
        
        # Draw image (either user photo or default avatar)
        if image_bytes:
            temp_image_path = create_circular_image_simple(image_bytes, int(node_radius * 2))
            if temp_image_path:
                temp_files.append(temp_image_path)
                try:
                    c.drawImage(
                        temp_image_path,
                        x - node_radius,
                        y - node_radius,
                        width=node_radius * 2,
                        height=node_radius * 2,
                        preserveAspectRatio=True
                    )
                    # Redraw circle border
                    c.setStrokeColor(black)
                    c.setLineWidth(3)
                    c.circle(x, y, node_radius, fill=0, stroke=1)
                except Exception as e:
                    print(f"Error drawing image for {name}: {e}")
                    draw_initial(c, x, y, node_radius, name)
            else:
                draw_initial(c, x, y, node_radius, name)
        else:
            # Only show initial if everything failed (rare)
            draw_initial(c, x, y, node_radius, name)
        
        # Draw name with background box
        font_size = max(8, int(10 * scale))
        c.setFont("Helvetica", font_size)
        
        # Prepare text lines
        text_lines = []
        if len(name) > 15:
            words = name.split()
            if len(words) > 1:
                mid = len(words) // 2
                line1 = " ".join(words[:mid])
                line2 = " ".join(words[mid:])
                text_lines.append(line1)
                text_lines.append(line2)
            else:
                text_lines.append(name[:15])
        else:
            text_lines.append(name)
        
        # Add date range
        from utils.data_handler import format_date_range
        birth = node.get('birth_date', node.get('date', ''))
        death = node.get('death_date', '')
        date_range = format_date_range(birth, death)
        if date_range:
            text_lines.append(date_range)
        
        # Calculate background box size - FIXED POSITIONING
        max_text_width = max(c.stringWidth(line, "Helvetica", font_size) for line in text_lines)
        box_width = max_text_width + 12
        line_height = 13 * scale
        box_height = len(text_lines) * line_height + 8
        box_x = x - box_width / 2
        box_y = y - node_radius - 18 * scale - box_height
        
        # Draw white background box with border
        c.setFillColor(white)
        c.setStrokeColor(black)
        c.setLineWidth(1)
        c.roundRect(box_x, box_y, box_width, box_height, 3, fill=1, stroke=1)
        
        # Draw text on top - FIXED Y OFFSET
        c.setFillColor(black)
        y_offset = y - node_radius - 18 * scale - box_height + line_height - 2
        for i, line in enumerate(text_lines):
            if i == len(text_lines) - 1 and date_range and line == date_range:
                c.setFont("Helvetica", max(7, int(8 * scale)))
            else:
                c.setFont("Helvetica", font_size)
            c.drawCentredString(x, y_offset - i * line_height, line)
    
    # Footer
    c.setFont("Helvetica", 10)
    c.setFillColor(HexColor("#666666"))
    c.drawString(0.5*inch, 0.3*inch, "Generated by Family Tree Maker")
    
    c.save()
    
    # Cleanup temp files
    for temp_file in temp_files:
        try:
            os.unlink(temp_file)
        except:
            pass
    
    pdf_buffer.seek(0)
    return pdf_buffer.getvalue()



def draw_initial(c, x, y, radius, name):
    """Draw initial letter fallback"""
    initial = name[0].upper() if name else '?'
    c.setFont("Helvetica-Bold", int(radius * 0.6))
    c.setFillColor(black)
    c.drawCentredString(x, y - radius * 0.2, initial)



def export_tree_to_pdf_list(tree_data):
    """Fallback text list export"""
    pdf_buffer = BytesIO()
    
    doc = SimpleDocTemplate(
        pdf_buffer,
        pagesize=landscape(A4),
        rightMargin=0.5*inch,
        leftMargin=0.5*inch,
        topMargin=0.75*inch,
        bottomMargin=0.5*inch,
    )
    
    story = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=black,
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    story.append(Paragraph("Family Tree", title_style))
    
    nodes = tree_data.get('nodes', [])
    person_nodes = [n for n in nodes if n.get('type') == 'person']
    person_nodes.sort(key=lambda n: (n.get('level', 0), n.get('x', 0)))
    
    table_data = [['Name', 'Date of Birth', 'Generation']]
    
    for node in person_nodes:
        level = node.get('level', 0)
        name = node.get('name', 'Unknown')
        date = node.get('date', 'N/A')
        gen = f"Gen {level + 1}"
        table_data.append([name, date, gen])
    
    table = Table(table_data, colWidths=[3*inch, 2*inch, 1.5*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), black),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), white),
        ('GRID', (0, 0), (-1, -1), 1, black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
    ]))
    
    story.append(table)
    doc.build(story)
    
    pdf_buffer.seek(0)
    return pdf_buffer.getvalue()
