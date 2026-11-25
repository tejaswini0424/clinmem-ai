from io import BytesIO
from xml.sax.saxutils import escape
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer
from reportlab.lib.styles import getSampleStyleSheet
from backend.database.models import now
from config.settings import DISCLAIMER
def generate(title,sections):
 buffer=BytesIO();styles=getSampleStyleSheet();story=[Paragraph(escape(title),styles['Title']),Paragraph(escape(now()),styles['Normal'])]
 for heading,text in sections:
  story.extend([Spacer(1,12),Paragraph(escape(str(heading)),styles['Heading2']),Paragraph(escape(str(text)).replace('\n','<br/>'),styles['BodyText'])])
 story.append(Paragraph(escape(DISCLAIMER),styles['BodyText']));SimpleDocTemplate(buffer).build(story);return buffer.getvalue()
