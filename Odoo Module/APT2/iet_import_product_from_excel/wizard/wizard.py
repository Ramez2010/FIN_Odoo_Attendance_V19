from odoo import fields, models, api
import logging
import pandas as pd
import base64
import io  # ضروري جداً للتعامل مع الملفات في بايثون الحديث

logger = logging.getLogger(__name__)


class ImportExcel(models.TransientModel):
    _name = "import.excel"
    _description = "Import Products Wizard"

    import_excel = fields.Binary(string="Upload File", required=True)
    file_name = fields.Char(string="File Name")

    def import_sale_orders(self):
        if not self.import_excel:
            return

        # 1. تحويل البيانات من Base64 لكي يقرأها Pandas
        try:
            file_data = base64.b64decode(self.import_excel)
            data_io = io.BytesIO(file_data)
            df = pd.read_excel(data_io, engine='openpyxl')

            # تنظيف أسماء الأعمدة من المسافات الزائدة
            df.columns = df.columns.str.strip()

            logger.info(f"Processing {len(df)} rows...")

        except Exception as e:
            raise models.ValidationError(f"Failed to read Excel file: {str(e)}")

        # 2. التكرار على الصفوف
        for index, row in df.iterrows():
            try:
                # قراءة القيم وتنظيفها (strip لإزالة المسافات الخفية)
                main_cat_name = str(row.get('Main Category', '')).strip()
                vendor_cat_name = str(row.get('Manufacture Category', '')).strip()
                sub_cat_name = str(row.get('Sub Category', '')).strip()
                serial_cat_name = str(row.get('Serial', '')).strip()
                uom_name = str(row.get('Unit', '')).strip()
                product_name_ar = str(row.get('اسم الصنف', '')).strip()

                if not product_name_ar:
                    continue  # تخطي الصفوف الفارغة

                # --- البحث المتسلسل (تصحيح الخطأ الرئيسي) ---

                # 1. البحث عن Main Category
                main_category = self.env['main.category'].search([('name', '=', main_cat_name)], limit=1)
                if not main_category:
                    logger.warning(f"Main Category not found: {main_cat_name}")
                    # يمكنك هنا إنشاء التصنيف إذا لم يوجد، أو تركه فارغاً

                # 2. البحث عن Vendor Category (باستخدام ID الأب)
                vendor_category = False
                if main_category:
                    vendor_category = self.env['vendor.category'].search([
                        ('name', '=', vendor_cat_name),
                        ('parent', '=', main_category.id)  # استخدام ID وليس الاسم
                    ], limit=1)

                # 3. البحث عن Sub Category (باستخدام ID الأب)
                sub_category = False
                if vendor_category:
                    sub_category = self.env['sub.category'].search([
                        ('name', '=', sub_cat_name),
                        ('parent', '=', vendor_category.id)
                    ], limit=1)

                # 4. البحث عن Serial Category (باستخدام ID الأب)
                serial_category = False
                if sub_category:
                    serial_category = self.env['serial.category'].search([
                        ('name', '=', serial_cat_name),
                        ('parent', '=', sub_category.id)
                    ], limit=1)

                # البحث عن الوحدة
                uom = self.env['uom.uom'].search([('name', '=', uom_name)], limit=1)

                # --- تجهيز البيانات ---
                vals = {
                    'name': product_name_ar,  # مبدئياً الاسم العربي، وسيتم تغييره عند توليد الباركود
                    'arabic_name': product_name_ar,
                    'detailed_type': 'product',
                    'check': False,  # لكي يسمح بإعادة توليد الباركود
                    'main_category_id': main_category.id if main_category else False,
                    'vendor_category_id': vendor_category.id if vendor_category else False,
                    'sub_category_id': sub_category.id if sub_category else False,
                    'serial_category_id': serial_category.id if serial_category else False,
                    'uom_id': uom.id if uom else False,
                    'uom_po_id': uom.id if uom else False,
                }

                # --- الإنشاء أو التحديث ---
                product = self.env['product.template'].search([('arabic_name', '=', product_name_ar)], limit=1)

                if product:
                    product.write(vals)
                    logger.info(f"Updated product: {product_name_ar}")
                else:
                    product = self.env['product.template'].create(vals)
                    logger.info(f"Created product: {product_name_ar}")

                # --- خطوة هامة جداً: استدعاء دالة توليد الباركود يدوياً ---
                # لأن onchange لا يعمل تلقائياً عند الإنشاء بالكود
                if hasattr(product, '_onchange_generate_barcode'):
                    product._onchange_generate_barcode()

            except Exception as e:
                logger.error(f"Error processing row {index}: {str(e)}")
                # يمكنك رفع الخطأ لإيقاف العملية أو الاستمرار
                # raise models.ValidationError(f"Error in row {index}: {e}")

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Import Success',
                'message': 'Products have been imported and barcodes generated successfully.',
                'type': 'success',
                'sticky': False,
            }
        }


class ImportLog(models.Model):
    _name = "import.log"
    _description = "Import Log History"

    message = fields.Text(string="Message", required=True)
    type = fields.Selection([
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('error', 'Error')
    ], string="Type", default='info', required=True)