from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Image, Spacer, TableStyle, Table
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle


def register_font():
    # 注册一个中文字体，这里我使用了思源黑体(你需要提供字体的文件路径)
    font_path = "./fonts/OPPO Sans 3.0/OPPOSans-Bold.ttf"  # 请替换为你本地的中文字体路径
    pdfmetrics.registerFont(TTFont('PPOSans-Bold', font_path))


def create_pdf(file_path, contents):
    register_font()

    # 创建PDF文档对象，设置页面大小为信纸大小
    doc = doc = SimpleDocTemplate(
        file_path, pagesize=letter,
        rightMargin=72, leftMargin=72,
        topMargin=72, bottomMargin=18
    )
    elements = []

    # 获取默认样式，并增加中文字体支持
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='PPOSans-Bold', fontName='PPOSans-Bold', fontSize=12))

    title_style = ParagraphStyle(
        'Title',
        parent=styles['Title'],
        fontName='PPOSans-Bold',
        fontSize=24,
    )
    body_style = styles['PPOSans-Bold']
    styleN = styles['PPOSans-Bold']

    # 创建内容列表
    content = []

    # 添加标题
    title = Paragraph("这是一个图文排版的PDF示例", title_style)
    content.append(title)
    content.append(Spacer(1, 0.5 * inch))

    # 添加段落
    paragraph = Paragraph(
        "这段文字是使用ReportLab库创建的。接下来我们将插入一张图片。",
        body_style
    )
    content.append(paragraph)
    content.append(Spacer(1, 0.2 * inch))

    # 添加图片
    image_path = "image 20.png"  # 请替换为你本地的图片路径
    image = Image(image_path)
    image.drawHeight = 1.25 * inch  # 设置图片高度
    image.drawWidth = 1.25 * inch  # 设置图片宽度
    content.append(image)
    content.append(Spacer(1, 0.5 * inch))

    # 添加另一段段落
    paragraph2 = Paragraph(
        "图片上方是我们插入的一张图片。报告生成成功！",
        body_style
    )
    content.append(paragraph2)

    # 水平排布

    for item in contents:
        image_path = item['image']
        text_content = item['text']

        im = Image(image_path)
        ratio = im.imageWidth / im.imageHeight
        target_width = 200  # target width, you can adjust
        im.drawHeight = target_width / ratio
        im.drawWidth = target_width

        text = Paragraph(text_content, styleN)

        spacer = Spacer(1, 12)

        data = [[im, text]]
        table = Table(data, colWidths=[target_width + 10, None])
        table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))

        content.append(table)
        content.append(spacer)

    # 制作PDF
    doc.build(content)


if __name__ == "__main__":
    content = [
        {
            'image': "image 20.png",
            'text': '图片上方是我们插入的一张图片。报告生成成功！图片上方是我们插入的一张图片。报告生成成功！'
        },
        {
            'image': "image 20.png",
            'text': '图片上方是我们插入的一张图片。报告生成成功！图片上方是我们插入的一张图片。报告生成成功！图片上方是我们插入的一张图片。报告生成成功！图片上方是我们插入的一张图片。报告生成成功！'
        },
        {
            'image': "image 20.png",
            'text': '图片上方是我们插入的一张图片。报告生成成功！图片上方是我们插入的一张图片。报告生成成功！图片上方是我们插入的一张图片。报告生成成功！'
        },
    ]
    create_pdf("example.pdf", content)
