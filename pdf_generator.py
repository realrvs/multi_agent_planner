# utils/pdf_generator.py
import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import logging

class PDFGenerator:
    def __init__(self, output_dir="reports"):
        self.output_dir = output_dir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Пытаемся зарегистрировать шрифт с поддержкой кириллицы
        try:
            # Ищем системные шрифты
            font_paths = [
                "C:/Windows/Fonts/arial.ttf",  # Windows
                "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",  # Linux
                "/System/Library/Fonts/Helvetica.ttf",  # macOS
            ]
            font_found = False
            for font_path in font_paths:
                if os.path.exists(font_path):
                    pdfmetrics.registerFont(TTFont('CustomFont', font_path))
                    font_found = True
                    break
            
            if not font_found:
                logging.warning("Шрифт с поддержкой кириллицы не найден, используется стандартный")
        except Exception as e:
            logging.warning(f"Не удалось зарегистрировать шрифт: {e}")
    
    def generate_report(self, state, filename=None):
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"plan_{timestamp}.pdf"
        
        filepath = os.path.join(self.output_dir, filename)
        
        doc = SimpleDocTemplate(
            filepath,
            pagesize=A4,
            leftMargin=2*cm,
            rightMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        styles = getSampleStyleSheet()
        
        # Создаем стили с поддержкой кириллицы
        try:
            font_name = 'CustomFont'
            # Проверяем, зарегистрирован ли шрифт
            try:
                pdfmetrics.getFont(font_name)
            except:
                font_name = 'Helvetica'
        except:
            font_name = 'Helvetica'
        
        styles.add(ParagraphStyle(
            name='RussianNormal',
            parent=styles['Normal'],
            fontName=font_name,
            fontSize=11,
            leading=14,
            alignment=0
        ))
        
        styles.add(ParagraphStyle(
            name='RussianHeading1',
            parent=styles['Heading1'],
            fontName=font_name,
            fontSize=18,
            leading=22,
            spaceAfter=12,
            textColor=colors.HexColor('#1a5276')
        ))
        
        styles.add(ParagraphStyle(
            name='RussianHeading2',
            parent=styles['Heading2'],
            fontName=font_name,
            fontSize=14,
            leading=18,
            spaceAfter=10,
            spaceBefore=10,
            textColor=colors.HexColor('#2e86c1')
        ))
        
        story = []
        
        # Заголовок
        story.append(Paragraph("План действий", styles['RussianHeading1']))
        story.append(Spacer(1, 0.5*cm))
        story.append(Paragraph(f"Дата: {datetime.now().strftime('%d.%m.%Y %H:%M')}", styles['RussianNormal']))
        story.append(Spacer(1, 0.5*cm))
        
        # Исходный запрос
        story.append(Paragraph("1. Исходный запрос", styles['RussianHeading2']))
        story.append(Paragraph("-"*50, styles['RussianNormal']))
        query = state.get('user_query', 'Не указан')
        story.append(Paragraph(self._clean_text(query), styles['RussianNormal']))
        story.append(Spacer(1, 0.3*cm))
        
        # Результаты исследования
        story.append(Paragraph("2. Результаты исследования", styles['RussianHeading2']))
        story.append(Paragraph("-"*50, styles['RussianNormal']))
        research = state.get('research_data', 'Нет данных')
        story.append(Paragraph(self._clean_text(research), styles['RussianNormal']))
        story.append(Spacer(1, 0.3*cm))
        
        # Анализ
        story.append(Paragraph("3. Анализ данных", styles['RussianHeading2']))
        story.append(Paragraph("-"*50, styles['RussianNormal']))
        analysis = state.get('analysis_result', 'Нет данных')
        story.append(Paragraph(self._clean_text(analysis), styles['RussianNormal']))
        story.append(Spacer(1, 0.3*cm))
        
        # План выполнения
        story.append(Paragraph("4. План выполнения", styles['RussianHeading2']))
        story.append(Paragraph("-"*50, styles['RussianNormal']))
        plan = state.get('execution_plan', 'Нет данных')
        story.append(Paragraph(self._clean_text(plan), styles['RussianNormal']))
        story.append(Spacer(1, 0.3*cm))
        
        # Футер
        story.append(Spacer(1, 1*cm))
        story.append(Paragraph("-" * 60, styles['RussianNormal']))
        story.append(Paragraph(
            "Документ создан мультиагентной системой планирования на базе LangGraph и YandexGPT",
            styles['RussianNormal']
        ))
        
        doc.build(story)
        return filepath
    
    def _clean_text(self, text):
        """Очищает текст для безопасного использования в PDF."""
        if not text:
            return "Нет данных"
        
        # Заменяем проблемные символы
        replacements = {
            '\n': '<br/>',
            '•': '-',
            '★': '*',
            '✅': '[OK]',
            '📊': '[Data]',
            '📋': '[Plan]',
            '🔍': '[Search]',
            '❌': '[Error]',
            '⚠️': '[Warning]',
            '💡': '[Idea]',
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        # Удаляем другие эмодзи
        import re
        emoji_pattern = re.compile("["
            u"\U0001F600-\U0001F64F"  # emoticons
            u"\U0001F300-\U0001F5FF"  # symbols & pictographs
            u"\U0001F680-\U0001F6FF"  # transport & map symbols
            u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
            u"\U00002702-\U000027B0"
            u"\U000024C2-\U0001F251"
            "]+", flags=re.UNICODE)
        text = emoji_pattern.sub(r'', text)
        
        return text