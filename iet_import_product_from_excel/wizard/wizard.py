from odoo import fields, models, api
import logging
import pandas as pd
import base64

# Create a logger
logger = logging.getLogger(__name__)


class ImportExcel(models.Model):
    _name = "import.excel"

    import_excel = fields.Binary()

    def import_sale_orders(self):
        # Get the uploaded file from the view
        binary_data = self.import_excel
        logger.info("Binary Data: %s", binary_data)

        # Convert the binary data to a regular string
        excel_data = base64.b64decode(binary_data)
        logger.info("Excel Data: %s", excel_data)

        try:
            # Create a DataFrame from the Excel data
            df = pd.read_excel(excel_data, engine='openpyxl')
            logger.info("Number of rows in DataFrame: %d", len(df))

            for _, row in df.iterrows():
                # Find the category records based on the name
                main_category = self.env['main.category'].search([('name', '=', row['Main Category'])])
                vendor_category = self.env['vendor.category'].search(
                    [('name', '=', row['Manufacture Category']), ('parent', '=', row['Main Category'])])
                sub_category = self.env['sub.category'].search(
                    [('name', '=', row['Sub Category']), ('parent', '=', row['Manufacture Category'])])
                serial_category = self.env['serial.category'].search(
                    [('name', '=', row['Serial']), ('parent', '=', row['Sub Category'])])
                uom = self.env['uom.uom'].search([('name', '=', row['Unit'])])

                # Find the product
                product = self.env['product.template'].search([('arabic_name', '=', row['اسم الصنف'])])
                print(product, "proooduct")
                print(main_category.name, "main_category")
                print(vendor_category.name, "vendor_category")
                print(sub_category.name, "sub")
                print(serial_category.name, "serial")
                print(uom.name, "uom")
                if product:
                    product.write({
                        'name': row['اسم الصنف'],
                        'check': False,
                        'arabic_name': row['اسم الصنف'],
                        'main_category_id': main_category.id if main_category else False,
                        'vendor_category_id': vendor_category.id if vendor_category else False,
                        'sub_category_id': sub_category.id if sub_category else False,
                        'serial_category_id': serial_category.id if serial_category else False,
                        'uom_id': uom.id if uom else False,
                        'uom_po_id': uom.id if uom else False,
                        'detailed_type': 'product',
                    })
                    print("write")

                else:
                    product = self.env['product.template'].create({
                        'name': row['اسم الصنف'],
                        'check': False,
                        'arabic_name': row['اسم الصنف'],
                        'main_category_id': main_category.id if main_category else False,
                        'vendor_category_id': vendor_category.id if vendor_category else False,
                        'sub_category_id': sub_category.id if sub_category else False,
                        'serial_category_id': serial_category.id if serial_category else False,
                        'uom_id': uom.id if uom else False,
                        'uom_po_id': uom.id if uom else False,
                        'detailed_type': 'product',

                    })
                    print("create")

            logger.info("Successfully imported %d sale orders from Excel file.", len(df))

        except pd.errors.ParserError as pe:
            logger.exception("Error parsing Excel file: %s", str(pe))
            return
        except Exception as e:
            logger.exception("Error processing Excel file: %s", str(e))
            return


class ImportLog(models.Model):
    _name = "import.log"

    message = fields.Text(string="Message", required=True)
    type = fields.Selection([
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('error', 'Error')
    ], string="Type", default='info', required=True)
