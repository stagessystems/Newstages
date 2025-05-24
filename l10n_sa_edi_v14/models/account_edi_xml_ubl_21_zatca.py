# -*- coding: utf-8 -*-
from hashlib import sha256
from base64 import b64encode
from lxml import etree
from odoo import models, fields, _
from odoo.modules.module import get_module_resource
from odoo.tools import html2plaintext, cleanup_xml_node
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_round
from odoo.tools import float_repr
import re

TAX_EXEMPTION_CODES = ['VATEX-SA-29', 'VATEX-SA-29-7', 'VATEX-SA-30']
TAX_ZERO_RATE_CODES = ['VATEX-SA-32', 'VATEX-SA-33', 'VATEX-SA-34-1', 'VATEX-SA-34-2', 'VATEX-SA-34-3', 'VATEX-SA-34-4',
                       'VATEX-SA-34-5', 'VATEX-SA-35', 'VATEX-SA-36', 'VATEX-SA-EDU', 'VATEX-SA-HEA']

UOM_TO_UNECE_CODE = {
    'uom.product_uom_unit': 'C62',
    'uom.product_uom_dozen': 'DZN',
    'uom.product_uom_kgm': 'KGM',
    'uom.product_uom_gram': 'GRM',
    'uom.product_uom_day': 'DAY',
    'uom.product_uom_hour': 'HUR',
    'uom.product_uom_ton': 'TNE',
    'uom.product_uom_meter': 'MTR',
    'uom.product_uom_km': 'KTM',
    'uom.product_uom_cm': 'CMT',
    'uom.product_uom_litre': 'LTR',
    'uom.product_uom_cubic_meter': 'MTQ',
    'uom.product_uom_lb': 'LBR',
    'uom.product_uom_oz': 'ONZ',
    'uom.product_uom_inch': 'INH',
    'uom.product_uom_foot': 'FOT',
    'uom.product_uom_mile': 'SMI',
    'uom.product_uom_floz': 'OZA',
    'uom.product_uom_qt': 'QT',
    'uom.product_uom_gal': 'GLL',
    'uom.product_uom_cubic_inch': 'INQ',
    'uom.product_uom_cubic_foot': 'FTQ',
}

PAYMENT_MEANS_CODE = {
    'bank': 42,
    'card': 48,
    'cash': 10,
    'transfer': 30,
    'unknown': 1
}


class AccountEdiXmlUBL21Zatca(models.AbstractModel):
    _name = "account.edi.xml.ubl_21.zatca"
    _description = "UBL 2.1 (ZATCA)"

    def _l10n_sa_get_namespaces(self):
        """
            Namespaces used in the final UBL declaration, required to canonalize the finalized XML document of the Invoice
        """
        return {
            'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2',
            'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2',
            'ext': 'urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2',
            'sig': 'urn:oasis:names:specification:ubl:schema:xsd:CommonSignatureComponents-2',
            'sac': 'urn:oasis:names:specification:ubl:schema:xsd:SignatureAggregateComponents-2',
            'sbc': 'urn:oasis:names:specification:ubl:schema:xsd:SignatureBasicComponents-2',
            'ds': 'http://www.w3.org/2000/09/xmldsig#',
            'xades': 'http://uri.etsi.org/01903/v1.3.2#'
        }

    def _l10n_sa_generate_invoice_xml_sha(self, xml_content):
        """
            Transform, canonicalize then hash the invoice xml content using the SHA256 algorithm,
            then return the hashed content
        """

        def _canonicalize_xml(content):
            """
                Canonicalize XML content using the c14n method. The specs mention using the c14n11 canonicalization,
                which is simply calling etree.tostring and setting the method argument to 'c14n'. There are minor
                differences between c14n11 and c14n canonicalization algorithms, but for the purpose of ZATCA signing,
                c14n is enough
            """
            return etree.tostring(content, method="c14n", exclusive=False, with_comments=False,
                                  inclusive_ns_prefixes=self._l10n_sa_get_namespaces())

        def _transform_and_canonicalize_xml(content):
            """ Transform XML content to remove certain elements and signatures using an XSL template """
            invoice_xsl = etree.parse(get_module_resource('l10n_sa_edi_v14', 'data', 'pre-hash_invoice.xsl'))
            transform = etree.XSLT(invoice_xsl)
            return _canonicalize_xml(transform(content))

        root = etree.fromstring(xml_content)
        # Transform & canonicalize the XML content
        transformed_xml = _transform_and_canonicalize_xml(root)
        # Get the SHA256 hashed value of the XML content
        return sha256(transformed_xml)

    def _l10n_sa_generate_invoice_xml_hash(self, xml_content, mode='hexdigest'):
        """
            Generate the b64 encoded sha256 hash of a given xml string:
                - First: Transform the xml content using a pre-hash_invoice.xsl file
                - Second: Canonicalize the transformed xml content using the c14n method
                - Third: hash the canonicalized content using the sha256 algorithm then encode it into b64 format
        """
        xml_sha = self._l10n_sa_generate_invoice_xml_sha(xml_content)
        if mode == 'hexdigest':
            xml_hash = xml_sha.hexdigest().encode()
        elif mode == 'digest':
            xml_hash = xml_sha.digest()
        return b64encode(xml_hash)

    def _l10n_sa_get_previous_invoice_hash(self, invoice):
        """ Function that returns the Base 64 encoded SHA256 hash of the previously submitted invoice """
        if invoice.company_id.l10n_sa_api_mode == 'sandbox' or not invoice.journal_id.l10n_sa_latest_submission_hash:
            # If no invoice, or if using Sandbox, return the b64 encoded SHA256 value of the '0' character
            return "NWZlY2ViNjZmZmM4NmYzOGQ5NTI3ODZjNmQ2OTZjNzljMmRiYzIzOWRkNGU5MWI0NjcyOWQ3M2EyN2ZiNTdlOQ=="
        return invoice.journal_id.l10n_sa_latest_submission_hash

    def _get_delivery_vals_list(self, invoice):
        """ Override to include/update values specific to ZATCA's UBL 2.1 specs """
        shipping_address = False
        if 'partner_shipping_id' in invoice._fields and invoice.partner_shipping_id:
            shipping_address = invoice.partner_shipping_id
        return [{'actual_delivery_date': invoice.l10n_sa_delivery_date,
                 'delivery_address_vals': self._get_partner_address_vals(shipping_address) if shipping_address else {},}]

    def _get_partner_party_identification_vals_list(self, partner):
        """ Override to include/update values specific to ZATCA's UBL 2.1 specs """
        return [{
            'id_attrs': {'schemeID': partner.l10n_sa_additional_identification_scheme},
            'id': partner.l10n_sa_additional_identification_number if partner.l10n_sa_additional_identification_scheme != 'TIN' else partner.vat
        }]

    def _l10n_sa_get_payment_means_code(self, invoice):
        """ Return payment means code to be used to set the value on the XML file """
        return 'unknown'

    def _get_invoice_payment_means_vals_list(self, invoice):
        vals = {
            'payment_means_code': PAYMENT_MEANS_CODE.get(self._l10n_sa_get_payment_means_code(invoice), PAYMENT_MEANS_CODE['unknown']),
            'payment_means_code_attrs': {'listID': 'UN/ECE 4461'},
            'payment_due_date': invoice.invoice_date_due or invoice.invoice_date,
            'adjustment_reason': invoice.ref,
            'instruction_id': invoice.payment_reference,
            'payment_id_vals': [invoice.payment_reference or invoice.name],
        }

        if invoice.partner_bank_id:
            vals['payee_financial_account_vals'] = self._get_financial_account_vals(invoice.partner_bank_id)

        return [vals]

    def _get_country_vals(self, country):
        return {
            'country': country,
            'identification_code': country.code,
            'name': country.name,
        }

    def _get_partner_address_vals(self, partner):
        """ Override to include/update values specific to ZATCA's UBL 2.1 specs """
        return {
            'street_name': partner.street,
            'additional_street_name': partner.street2,
            'city_name': partner.city,
            'postal_zone': partner.zip,
            'country_subentity': partner.state_id.name,
            'country_subentity_code': partner.state_id.code,
            'country_vals': self._get_country_vals(partner.country_id),
            'building_number': partner.l10n_sa_edi_building_number,
            'neighborhood': partner.street2,
            'plot_identification': partner.l10n_sa_edi_plot_identification,
        }

    def _export_invoice_filename(self, invoice):
        """
            Generate the name of the invoice XML file according to ZATCA business rules:
            Seller Vat Number (BT-31), Date (BT-2), Time (KSA-25), Invoice Number (BT-1)
        """
        vat = invoice.company_id.partner_id.commercial_partner_id.vat
        invoice_number = re.sub("[^a-zA-Z0-9 -]", "-", invoice.name)
        invoice_date = fields.Datetime.context_timestamp(self.with_context(tz='Asia/Riyadh'), invoice.l10n_sa_confirmation_datetime)
        return '%s_%s_%s.xml' % (vat, invoice_date.strftime('%Y%m%dT%H%M%S'), invoice_number)

    def _l10n_sa_get_invoice_transaction_code(self, invoice):
        """
            Returns the transaction code string to be inserted in the UBL file follows the following format:
                - NNPNESB, in compliance with KSA Business Rule KSA-2, where:
                    - NN (positions 1 and 2) = invoice subtype:
                        - 01 for tax invoice
                        - 02 for simplified tax invoice
                    - E (position 5) = Exports invoice transaction, 0 for false, 1 for true
        """
        return '0%s00%s00' % (
            '2' if invoice._l10n_sa_is_simplified() else '1',
            '1' if invoice.commercial_partner_id.country_id != invoice.company_id.country_id and not invoice._l10n_sa_is_simplified() else '0'
        )

    def _l10n_sa_get_invoice_type(self, invoice):
        """
            Returns the invoice type string to be inserted in the UBL file
                - 383: Debit Note
                - 381: Credit Note
                - 388: Invoice
        """
        return 383 if invoice.debit_origin_id else 381 if invoice.move_type == 'out_refund' else 388

    def _l10n_sa_get_billing_reference_vals(self, invoice):
        """ Get the billing reference vals required to render the BillingReference for credit/debit notes """
        if self._l10n_sa_get_invoice_type(invoice) != 388:
            return {
                'id': (invoice.reversed_entry_id.name or invoice.ref) if invoice.move_type == 'out_refund' else invoice.debit_origin_id.name,
                'issue_date': None,
            }
        return {}

    def _get_partner_party_tax_scheme_vals_list(self, partner, role):
        """
            Override to return an empty list if the partner is a customer and their country is not KSA.
            This is according to KSA Business Rule BR-KSA-46 which states that in the case of Export Invoices,
            the buyer VAT registration number or buyer group VAT registration number must not exist in the Invoice
        """
        if role != 'customer' or partner.country_id.code == 'SA':
            return [{
                'registration_name': partner.name,
                'company_id': partner.vat,
                'registration_address_vals': self._get_partner_address_vals(partner),
                'TaxScheme_vals': {},
                'tax_scheme_id': 'VAT',
            }]
        return []

    def _apply_invoice_tax_filter(self, tax_values):
        """ Override to filter out withholding tax """
        res = not tax_values['tax_id'].l10n_sa_is_retention
        # If the move that is being sent is not a down payment invoice, and the sale module is installed
        # we need to make sure the line is neither retention, nor a down payment line
        if not tax_values['base_line_id'].move_id._is_downpayment():
            return not tax_values['tax_id'].l10n_sa_is_retention and not tax_values['base_line_id']._get_downpayment_lines()
        return res

    def _apply_invoice_line_filter(self, invoice_line):
        """ Override to filter out down payment lines """
        if not invoice_line.move_id._is_downpayment():
            return not invoice_line._get_downpayment_lines()
        return True

    def _l10n_sa_get_prepaid_amount(self, invoice):
        """ Calculate the down-payment amount according to ZATCA rules """
        downpayment_lines = False if invoice._is_downpayment() else invoice.line_ids.filtered(lambda l: l._get_downpayment_lines())
        if downpayment_lines:
            tax_vals = invoice._prepare_edi_tax_details(filter_to_apply=lambda t: not t['tax_id'].l10n_sa_is_retention)
            base_amount = abs(sum(tax_vals['invoice_line_tax_details'][l]['base_amount_currency'] for l in downpayment_lines))
            tax_amount = abs(sum(tax_vals['invoice_line_tax_details'][l]['tax_amount_currency'] for l in downpayment_lines))
            return {
                'total_amount': base_amount + tax_amount,
                'base_amount': base_amount,
                'tax_amount': tax_amount
            }

    def _l10n_sa_get_monetary_vals(self, invoice, taxes_vals):
        """ Calculate the invoice monteray amount values, including prepaid amounts (down payment) """
        # We use base_amount_currency + tax_amount_currency instead of amount_total because we do not want to include
        # withholding tax amounts in our calculations
        total_amount = abs(taxes_vals['base_amount_currency'] + taxes_vals['tax_amount_currency'])

        tax_inclusive_amount = total_amount
        tax_exclusive_amount = abs(taxes_vals['base_amount_currency'])
        prepaid_amount = 0
        payable_amount = total_amount

        # - When we calculate the tax values, we filter out taxes and invoice lines linked to downpayments.
        #   As such, when we calculate the TaxInclusiveAmount, it already accounts for the tax amount of the downpayment
        #   Same goes for the TaxExclusiveAmount, and we do not need to add the Tax amount of the downpayment
        # - The payable amount does not account for the tax amount of the downpayment, so we add it
        downpayment_vals = self._l10n_sa_get_prepaid_amount(invoice)

        if downpayment_vals:
            # Makes no sense, but according to ZATCA, if there is a downpayment, the TotalInclusiveAmount
            # should include the total amount of the invoice (including downpayment amount) PLUS the downpayment
            # total amount, AGAIN.
            prepaid_amount = tax_inclusive_amount + downpayment_vals['total_amount']
            payable_amount = - downpayment_vals['total_amount']

        return {
            'currency': invoice.currency_id,
            'currency_dp': invoice.currency_id.decimal_places,
            'tax_inclusive_amount': tax_inclusive_amount,
            'tax_exclusive_amount': tax_exclusive_amount,
            'prepaid_amount': prepaid_amount,
            'payable_amount': payable_amount
        }

    def _get_tax_category_list(self, invoice, taxes):
        """ Override to filter out withholding taxes """
        non_retention_taxes = taxes.filtered(lambda t: not t.l10n_sa_is_retention)
        res = []
        for tax in non_retention_taxes:
            tax_unece_codes = self._get_tax_unece_codes(invoice, tax)
            res.append({
                'id': tax_unece_codes.get('tax_category_code'),
                'percent': tax.amount if tax.amount_type == 'percent' else False,
                'name': tax_unece_codes.get('tax_exemption_reason'),
                **tax_unece_codes,
            })
        return res

    def _get_invoice_line_tax_totals_vals_list(self, invoice, taxes_vals):
        tax_totals_vals = {
            'currency': invoice.currency_id,
            'currency_dp': invoice.currency_id.decimal_places,
            'tax_amount':  abs(taxes_vals['tax_amount_currency']),
            'tax_subtotal_vals': [],
        }
        for grouping_key, vals in taxes_vals['tax_details'].items():
            continue
            if ('tax_amount_type' in vals and vals['tax_amount_type'] != 'fixed') or vals['_tax_category_vals_'].get('percent'):
                tax_totals_vals['tax_subtotal_vals'].append({
                    'currency': invoice.currency_id,
                    'currency_dp': invoice.currency_id.decimal_places,
                    'taxable_amount': abs(vals['base_amount_currency']),
                    'tax_amount': abs(vals['tax_amount_currency']),
                    'percent': vals['_tax_category_vals_']['percent'],
                    'tax_category_vals': vals['_tax_category_vals_'],
                })
        return [tax_totals_vals]

    def _get_invoice_line_tax_totals_vals_list2(self, invoice, taxes_vals):
        tax_totals_vals = {
            'currency': invoice.currency_id,
            'currency_dp': invoice.currency_id.decimal_places,
            'tax_amount': abs(taxes_vals['tax_amount_currency']),
            'tax_subtotal_vals': [],
        }
        for grouping_key, vals in taxes_vals['tax_details'].items():
            # continue
            if ('tax_amount_type' in vals and vals['tax_amount_type'] != 'fixed') or vals['_tax_category_vals_'].get(
                    'percent'):
                tax_totals_vals['tax_subtotal_vals'].append({
                    'currency': invoice.currency_id,
                    'currency_dp': invoice.currency_id.decimal_places,
                    'taxable_amount': abs(vals['base_amount_currency']),
                    'tax_amount': abs(vals['tax_amount_currency']),
                    'percent': vals['_tax_category_vals_']['percent'],
                    'tax_category_vals': vals['_tax_category_vals_'],
                })
        return [tax_totals_vals]

    def _get_invoice_tax_totals_vals_list(self, invoice, taxes_vals):
        res = self._get_invoice_line_tax_totals_vals_list2(invoice, taxes_vals)
        curr_amount = abs(taxes_vals['tax_amount_currency'])
        if invoice.currency_id != invoice.company_currency_id:
            curr_amount = abs(taxes_vals['tax_amount'])
        return res + [{
            'currency': invoice.company_currency_id,
            'currency_dp': invoice.company_currency_id.decimal_places,
            'tax_amount': curr_amount,
        }]

    def _get_document_allowance_charge_vals_list(self, invoice):
        """
        https://docs.peppol.eu/poacc/billing/3.0/bis/#_document_level_allowance_or_charge
        """
        return []

    def _validate_taxes(self, invoice):
        """ Validate the structure of the tax repartition lines (invalid structure could lead to unexpected results)
        """
        for tax in invoice.invoice_line_ids.tax_ids:
            try:
                tax._validate_repartition_lines()
            except ValidationError as e:
                error_msg = _("Tax '%s' is invalid: %s", tax.name, e.args[0])  # args[0] gives the error message
                raise ValidationError(error_msg)

    def _export_invoice_vals(self, invoice):

        def grouping_key_generator(tax_values):
            tax = tax_values['tax_id']
            tax_category_vals = self._get_tax_category_list(invoice, tax)[0]
            grouping_key = {
                'tax_category_id': tax_category_vals['id'],
                'tax_category_percent': tax_category_vals['percent'],
                '_tax_category_vals_': tax_category_vals,
                'tax_amount_type': tax.amount_type,
            }
            # If the tax is fixed, we want to have one group per tax
            # s.t. when the invoice is imported, we can try to guess the fixed taxes
            if tax.amount_type == 'fixed':
                grouping_key['tax_name'] = tax.name
            return grouping_key

        # Validate the structure of the taxes
        self._validate_taxes(invoice)

        # Compute the tax details for the whole invoice and each invoice line separately.
        taxes_vals = invoice._prepare_edi_tax_details(grouping_key_generator=grouping_key_generator,
                                                      filter_to_apply=self._apply_invoice_tax_filter,
                                                      filter_invl_to_apply=self._apply_invoice_line_filter)

        # Fixed Taxes: filter them on the document level, and adapt the totals
        # Fixed taxes are not supposed to be taxes in real live. However, this is the way in Odoo to manage recupel
        # taxes in Belgium. Since only one tax is allowed, the fixed tax is removed from totals of lines but added
        # as an extra charge/allowance.
        fixed_taxes_keys = [k for k, v in taxes_vals['tax_details'].items() if v['tax_amount_type'] == 'fixed']
        for key in fixed_taxes_keys:
            fixed_tax_details = taxes_vals['tax_details'].pop(key)
            taxes_vals['tax_amount_currency'] -= fixed_tax_details['tax_amount_currency']
            taxes_vals['tax_amount'] -= fixed_tax_details['tax_amount']
            taxes_vals['base_amount_currency'] += fixed_tax_details['tax_amount_currency']
            taxes_vals['base_amount'] += fixed_tax_details['tax_amount']

        # Compute values for invoice lines.
        line_extension_amount = 0.0

        invoice_lines = invoice.invoice_line_ids.filtered(lambda line: not line.display_type)
        document_allowance_charge_vals_list = self._get_document_allowance_charge_vals_list(invoice)
        invoice_line_vals_list = []
        for line in invoice_lines:
            line_taxes_vals = taxes_vals['invoice_line_tax_details'][line]
            line_vals = self._get_invoice_line_vals(line, line_taxes_vals)
            invoice_line_vals_list.append(line_vals)

            line_extension_amount += line_vals['line_extension_amount']

        # Compute the total allowance/charge amounts.
        allowance_total_amount = 0.0
        for allowance_charge_vals in document_allowance_charge_vals_list:
            if allowance_charge_vals['charge_indicator'] == 'false':
                allowance_total_amount += allowance_charge_vals['amount']

        supplier = invoice.company_id.partner_id.commercial_partner_id
        customer = invoice.commercial_partner_id

        # OrderReference/SalesOrderID (sales_order_id) is optional
        sales_order_id = 'sale_line_ids' in invoice.invoice_line_ids._fields \
                         and ",".join(invoice.invoice_line_ids.sale_line_ids.order_id.mapped('name'))
        # OrderReference/ID (order_reference) is mandatory inside the OrderReference node !
        order_reference = invoice.ref or invoice.name if sales_order_id else invoice.ref

        vals = {
            'builder': self,
            'invoice': invoice,
            'supplier': supplier,
            'customer': customer,
            'taxes_vals': taxes_vals,
            'format_float': self.format_float,
            'vals': {
                'ubl_version_id': 2.1,
                'profile_id': 'reporting:1.0',
                'id': invoice.name,
                'note_vals': [html2plaintext(invoice.narration)] if invoice.narration else [],
                'order_reference': order_reference,
                'sales_order_id': sales_order_id,
                'accounting_supplier_party_vals': {
                    'party_vals': self._get_partner_party_vals(supplier, role='supplier'),
                },
                'accounting_customer_party_vals': {
                    'party_vals': self._get_partner_party_vals(customer, role='customer'),
                },
                'delivery_vals_list': self._get_delivery_vals_list(invoice),
                'payment_means_vals_list': self._get_invoice_payment_means_vals_list(invoice),
                'payment_terms_vals': self._get_invoice_payment_terms_vals_list(invoice),
                # allowances at the document level, the allowances on invoices (eg. discount) are on invoice_line_vals
                'allowance_charge_vals': document_allowance_charge_vals_list,
                'legal_monetary_total_vals': self._l10n_sa_get_monetary_vals(invoice, taxes_vals),
                'invoice_line_vals': invoice_line_vals_list,
                'currency_dp': invoice.currency_id.decimal_places,  # currency decimal places
                'invoice_type_code_attrs': {'name': self._l10n_sa_get_invoice_transaction_code(invoice)},
                'invoice_type_code': self._l10n_sa_get_invoice_type(invoice),
                'issue_date': fields.Datetime.context_timestamp(self.with_context(tz='Asia/Riyadh'),
                                                                invoice.l10n_sa_confirmation_datetime),
                'previous_invoice_hash': self._l10n_sa_get_previous_invoice_hash(invoice),
                'billing_reference_vals': self._l10n_sa_get_billing_reference_vals(invoice),
                'tax_total_vals': self._get_invoice_tax_totals_vals_list(invoice, taxes_vals),
                # Due date is not required for ZATCA UBL 2.1
                'due_date': None,
            },
        }

        vals['vals']['legal_monetary_total_vals']['line_extension_amount'] = line_extension_amount

        return vals

    def _get_financial_account_vals(self, partner_bank):
        vals = {
            'bank_account': partner_bank,
            'id': partner_bank.acc_number.replace(' ', ''),
        }

        if partner_bank.bank_id:
            vals['financial_institution_branch_vals'] = self._get_financial_institution_branch_vals(partner_bank.bank_id)

        return vals

    def _get_financial_institution_branch_vals(self, bank):
        return {
            'bank': bank,
            'id': bank.bic,
            'id_attrs': {'schemeID': 'BIC'},
            'financial_institution_vals': self._get_financial_institution_vals(bank),
        }

    def _get_financial_institution_vals(self, bank):
        return {
            'bank': bank,
            'id': bank.bic,
            'id_attrs': {'schemeID': 'BIC'},
            'name': bank.name,
            'address_vals': self._get_bank_address_vals(bank),
        }

    def _get_bank_address_vals(self, bank):
        return {
            'street_name': bank.street,
            'additional_street_name': bank.street2,
            'city_name': bank.city,
            'postal_zone': bank.zip,
            'country_subentity': bank.state.name,
            'country_subentity_code': bank.state.code,
            'country_vals': self._get_country_vals(bank.country),
        }

    def _check_required_fields(self, record, field_names, custom_warning_message=""):
        """
        This function check that a field exists on a record or dictionaries
        returns a generic error message if it's not the case or a custom one if specified
        """
        if not record:
            return custom_warning_message or _("The element %s is required on %s.", record, ', '.join(field_names))

        if not isinstance(field_names, list):
            field_names = [field_names]

        has_values = any(record[field_name] for field_name in field_names)
        # field is present
        if has_values:
            return

        # field is not present
        if custom_warning_message or isinstance(record, dict):
            return custom_warning_message or _("The element %s is required on %s.", record, ', '.join(field_names))

        display_field_names = record.fields_get(field_names)
        if len(field_names) == 1:
            display_field = f"'{display_field_names[field_names[0]]['string']}'"
            return _("The field %s is required on %s.", display_field, record.display_name)
        else:
            display_fields = ', '.join(f"'{display_field_names[x]['string']}'" for x in display_field_names)
            return _("At least one of the following fields %s is required on %s.", display_fields, record.display_name)

    def _export_invoice_constraints(self, invoice, vals):
        constraints = self._invoice_constraints_common(invoice)
        constraints.update({
            'ubl20_supplier_name_required': self._check_required_fields(vals['supplier'], 'name'),
            'ubl20_customer_name_required': self._check_required_fields(vals['customer'], 'name'),
            'ubl20_commercial_customer_name_required': self._check_required_fields(vals['customer'].commercial_partner_id, 'name'),
            'ubl20_invoice_name_required': self._check_required_fields(invoice, 'name'),
            'ubl20_invoice_date_required': self._check_required_fields(invoice, 'invoice_date'),
        })
        return constraints

    def _export_invoice(self, invoice):
        vals = self._export_invoice_vals(invoice)
        errors = [constraint for constraint in self._export_invoice_constraints(invoice, vals).values() if constraint]
        xml_content = self.env['ir.qweb']._render('l10n_sa_edi_v14.ubl_21_Invoice_zatca', vals)
        return etree.tostring(cleanup_xml_node(xml_content), xml_declaration=True, encoding='UTF-8'), set(errors)

    def _invoice_constraints_common(self, invoice):
        # check that there is a tax on each line
        for line in invoice.invoice_line_ids.filtered(lambda x: not x.display_type):
            if not line.tax_ids:
                return {'tax_on_line': _("Each invoice line should have at least one tax.")}
        return {}

    def _get_partner_party_vals(self, partner, role):
        return {
            'partner': partner,
            'party_identification_vals': self._get_partner_party_identification_vals_list(partner),
            'party_name_vals': [{'name': partner.name}],
            'postal_address_vals': self._get_partner_address_vals(partner),
            'party_tax_scheme_vals': self._get_partner_party_tax_scheme_vals_list(partner, role),
            'party_legal_entity_vals': self._get_partner_party_legal_entity_vals_list(partner),
            'contact_vals': self._get_partner_contact_vals(partner),
        }

    def _get_partner_contact_vals(self, partner):
        return {
            'id': partner.id,
            'name': partner.name,
            'telephone': partner.phone or partner.mobile,
            'electronic_mail': partner.email,
        }

    def _get_partner_party_legal_entity_vals_list(self, partner):
        commercial_partner = partner.commercial_partner_id
        return [{
            'commercial_partner': commercial_partner,

            'registration_name': commercial_partner.name,
            'company_id': commercial_partner.vat,
            'registration_address_vals': self._get_partner_address_vals(commercial_partner),
        }]

    def _get_invoice_line_item_vals(self, line, taxes_vals):
        """ Method used to fill the cac:InvoiceLine/cac:Item node.
                It provides information about what the product you are selling.

                :param line:        An invoice line.
                :param taxes_vals:  The tax details for the current invoice line.
                :return:            A python dictionary.

                """
        product = line.product_id
        taxes = line.tax_ids.flatten_taxes_hierarchy().filtered(lambda t: t.amount_type != 'fixed')
        tax_category_vals_list = self._get_tax_category_list(line.move_id, taxes)
        description = line.name and line.name.replace('\n', ', ')

        return {
            # Simple description about what you are selling.
            'description': description,

            # The name of the item.
            'name': product.name,

            # Identifier of the product.
            'sellers_item_identification_vals': {'id': product.code},

            # The main tax applied. Only one is allowed.
            'classified_tax_category_vals': tax_category_vals_list,

            'sellers_item_identification_vals': {'id': line.product_id.code or line.product_id.default_code}
        }

    def _get_invoice_line_allowance_vals_list(self, line, tax_values_list=None):
        """ Method used to fill the cac:InvoiceLine>cac:AllowanceCharge node.

        Allowances are distinguished from charges using the ChargeIndicator node with 'false' as value.

        Note that allowance charges do not exist for credit notes in UBL 2.0, so if we apply discount in Odoo
        the net price will not be consistent with the unit price, but we cannot do anything about it

        :param line:    An invoice line.
        :return:        A list of python dictionaries.
        """
        fixed_tax_charge_vals_list = []
        balance_sign = -1 if line.move_id.is_inbound() else 1
        for grouping_key, tax_details in tax_values_list['tax_details'].items():
            if tax_details['tax_amount_type'] == 'fixed':
                fixed_tax_charge_vals_list.append({
                    'currency_name': line.currency_id.name,
                    'currency_dp': line.currency_id.decimal_places,
                    'charge_indicator': 'true',
                    'allowance_charge_reason_code': 'AEO',
                    'allowance_charge_reason': tax_details['group_tax_details'][0]['tax_id'].name,
                    'amount': balance_sign * tax_details['tax_amount_currency'],
                })

        if not line.discount:
            return fixed_tax_charge_vals_list

        # Price subtotal without discount:
        net_price_subtotal = line.price_subtotal
        # Price subtotal with discount:
        if line.discount == 100.0:
            gross_price_subtotal = 0.0
        else:
            gross_price_subtotal = line.currency_id.round(net_price_subtotal / (1.0 - (line.discount or 0.0) / 100.0))

        allowance_vals = {
            'currency_name': line.currency_id.name,
            'currency_dp': line.currency_id.decimal_places,

            # Must be 'false' since this method is for allowances.
            'charge_indicator': 'false',

            # A reason should be provided. In Odoo, we only manage discounts.
            # Full code list is available here:
            # https://docs.peppol.eu/poacc/billing/3.0/codelist/UNCL5189/
            'allowance_charge_reason_code': 95,

            # The discount should be provided as an amount.
            'amount': gross_price_subtotal - net_price_subtotal,
        }

        return [allowance_vals] + fixed_tax_charge_vals_list

    def _l10n_sa_get_line_prepayment_vals(self, line, taxes_vals):
        """
            If an invoice line is linked to a down payment invoice, we need to return the proper values
            to be included in the UBL
        """
        if not line.move_id._is_downpayment() and line.sale_line_ids and all(sale_line.is_downpayment for sale_line in line.sale_line_ids):
            prepayment_move_id = line.sale_line_ids.invoice_lines.move_id.filtered(lambda m: m._is_downpayment())
            return {
                'prepayment_id': prepayment_move_id.name,
                'issue_date': fields.Datetime.context_timestamp(self.with_context(tz='Asia/Riyadh'),
                                                                prepayment_move_id.l10n_sa_confirmation_datetime),
                'document_type_code': 386
            }
        return {}

    def _get_invoice_line_price_vals(self, line):
        """ Method used to fill the cac:InvoiceLine/cac:Price node.
        It provides information about the price applied for the goods and services invoiced.

        :param line:    An invoice line.
        :return:        A python dictionary.
        """
        # Price subtotal without discount:
        net_price_subtotal = line.price_subtotal
        # Price subtotal with discount:
        if line.discount == 100.0:
            gross_price_subtotal = 0.0
        else:
            gross_price_subtotal = net_price_subtotal / (1.0 - (line.discount or 0.0) / 100.0)
        # Price subtotal with discount / quantity:
        gross_price_unit = gross_price_subtotal / line.quantity if line.quantity else 0.0

        uom = self._get_uom_unece_code(line)

        return {
            'currency': line.currency_id,
            'currency_dp': line.currency_id.decimal_places,

            # The price of an item, exclusive of VAT, after subtracting item price discount.
            'price_amount': gross_price_unit,
            'product_price_dp': self.env['decimal.precision'].precision_get('Product Price'),

            # The number of item units to which the price applies.
            # setting to None -> the xml will not comprise the BaseQuantity (it's not mandatory)
            'base_quantity': None,
            'base_quantity_attrs': {'unitCode': uom},
        }

    def format_float(self, amount, precision_digits):
        if amount is None:
            return None
        return float_repr(float_round(amount, precision_digits), precision_digits)

    def _get_uom_unece_code(self, line):
        """
        list of codes: https://docs.peppol.eu/poacc/billing/3.0/codelist/UNECERec20/
        or https://unece.org/fileadmin/DAM/cefact/recommendations/bkup_htm/add2c.htm (sorted by letter)
        """
        xmlid = line.product_uom_id.get_external_id()
        if xmlid and line.product_uom_id.id in xmlid:
            return UOM_TO_UNECE_CODE.get(xmlid[line.product_uom_id.id], 'C62')
        return 'C62'

    def _get_invoice_line_vals(self, line, taxes_vals):
        """ Method used to fill the cac:InvoiceLine node.
                It provides information about the invoice line.

                :param line:    An invoice line.
                :return:        A python dictionary.
                """

        def grouping_key_generator(tax_values):
            tax = tax_values['tax_id']
            tax_category_vals = self._get_tax_category_list(line.move_id, tax)[0]
            return {
                'tax_category_id': tax_category_vals['id'],
                'tax_category_percent': tax_category_vals['percent'],
                '_tax_category_vals_': tax_category_vals,
            }

        allowance_charge_vals_list = self._get_invoice_line_allowance_vals_list(line, tax_values_list=taxes_vals)

        uom = self._get_uom_unece_code(line)
        total_fixed_tax_amount = sum([
            vals['amount']
            for vals in allowance_charge_vals_list
            if vals['allowance_charge_reason_code'] == 'AEO'
        ])

        if not line.move_id._is_downpayment() and line._get_downpayment_lines():
            # When we initially calculate the taxes_vals, we filter out the down payment lines, which means we have no
            # values to set in the TaxableAmount and TaxAmount nodes on the InvoiceLine for the down payment.
            # This means ZATCA will return a warning message for the BR-KSA-80 rule since it cannot calculate the
            # TaxableAmount and the TaxAmount nodes correctly. To avoid this, we re-caclculate the taxes_vals just before
            # we set the values for the down payment line, and we do not pass any filters to the _prepare_edi_tax_details
            # method
            line_taxes = line.move_id._prepare_edi_tax_details(grouping_key_generator=grouping_key_generator)
            taxes_vals = line_taxes['invoice_line_tax_details'][line]

        line_vals = {
            'currency': line.currency_id,
            'currency_dp': line.currency_id.decimal_places,

            # The requirement is the id has to be unique by invoice line.
            'id': line.id,

            'invoiced_quantity': line.quantity,
            'invoiced_quantity_attrs': {'unitCode': uom},

            # 'line_extension_amount': line.price_subtotal + total_fixed_tax_amount,
            'line_extension_amount': line.price_subtotal + total_fixed_tax_amount,

            'allowance_charge_vals': allowance_charge_vals_list,
            'tax_total_vals': self._get_invoice_line_tax_totals_vals_list(line.move_id, taxes_vals),
            'item_vals': self._get_invoice_line_item_vals(line, taxes_vals),
            'price_vals': self._get_invoice_line_price_vals(line),
        }

        total_amount_sa = abs(taxes_vals['tax_amount_currency'] + taxes_vals['base_amount_currency'])
        extension_amount = abs(line.price_subtotal + total_fixed_tax_amount)
        if not line.move_id._is_downpayment() and line._get_downpayment_lines():
            total_amount_sa = extension_amount = 0
            line_vals['price_vals']['price_amount'] = 0
            line_vals['tax_total_vals'][0]['tax_amount'] = 0
            line_vals['prepayment_vals'] = self._l10n_sa_get_line_prepayment_vals(line, taxes_vals)
        line_vals['tax_total_vals'][0]['total_amount_sa'] = total_amount_sa
        line_vals['invoiced_quantity'] = abs(line_vals['invoiced_quantity'])
        line_vals['line_extension_amount'] = extension_amount
        return line_vals

    def _get_tax_unece_codes(self, invoice, tax):
        """ Override to include/update values specific to ZATCA's UBL 2.1 specs """

        def _exemption_reason(code, reason):
            return {
                'tax_category_code': code,
                'tax_exemption_reason_code': reason,
                'tax_exemption_reason': exemption_codes[reason].split(reason)[1].lstrip(),
            }

        supplier = invoice.company_id.partner_id.commercial_partner_id
        customer = invoice.commercial_partner_id
        if supplier.country_id == customer.country_id and supplier.country_id.code == 'SA':
            if not tax or tax.amount == 0:
                exemption_codes = dict(tax._fields["l10n_sa_exemption_reason_code"]._description_selection(self.env))
                if tax.l10n_sa_exemption_reason_code in TAX_EXEMPTION_CODES:
                    return _exemption_reason('E', tax.l10n_sa_exemption_reason_code)
                elif tax.l10n_sa_exemption_reason_code in TAX_ZERO_RATE_CODES:
                    return _exemption_reason('Z', tax.l10n_sa_exemption_reason_code)
                else:
                    return {
                        'tax_category_code': 'O',
                        'tax_exemption_reason_code': 'Not subject to VAT',
                        'tax_exemption_reason': 'Not subject to VAT',
                    }
            else:
                return {
                    'tax_category_code': 'S',
                    'tax_exemption_reason_code': None,
                    'tax_exemption_reason': None,
                }

        # Else, fall back to account_edi_common code
        def create_dict(tax_category_code=None, tax_exemption_reason_code=None, tax_exemption_reason=None):
            return {
                'tax_category_code': tax_category_code,
                'tax_exemption_reason_code': tax_exemption_reason_code,
                'tax_exemption_reason': tax_exemption_reason,
            }

        supplier = invoice.company_id.partner_id.commercial_partner_id
        customer = invoice.commercial_partner_id

        # add Norway, Iceland, Liechtenstein
        european_economic_area = self.env.ref('base.europe').country_ids.mapped('code') + ['NO', 'IS', 'LI']

        if customer.country_id.code == 'ES' and customer.zip:
            if customer.zip[:2] in ('35', '38'):  # Canary
                # [BR-IG-10]-A VAT breakdown (BG-23) with VAT Category code (BT-118) "IGIC" shall not have a VAT
                # exemption reason code (BT-121) or VAT exemption reason text (BT-120).
                return create_dict(tax_category_code='L')
            if customer.zip[:2] in ('51', '52'):
                return create_dict(tax_category_code='M')  # Ceuta & Mellila

        # see: https://anskaffelser.dev/postaward/g3/spec/current/billing-3.0/norway/#_value_added_tax_norwegian_mva
        if customer.country_id.code == 'NO':
            if tax.amount == 25:
                return create_dict(tax_category_code='S', tax_exemption_reason=_('Output VAT, regular rate'))
            if tax.amount == 15:
                return create_dict(tax_category_code='S', tax_exemption_reason=_('Output VAT, reduced rate, middle'))
            if tax.amount == 11.11:
                return create_dict(tax_category_code='S', tax_exemption_reason=_('Output VAT, reduced rate, raw fish'))
            if tax.amount == 12:
                return create_dict(tax_category_code='S', tax_exemption_reason=_('Output VAT, reduced rate, low'))

        if supplier.country_id == customer.country_id:
            if not tax or tax.amount == 0:
                # in theory, you should indicate the precise law article
                return create_dict(tax_category_code='E', tax_exemption_reason=_('Articles 226 items 11 to 15 Directive 2006/112/EN'))
            else:
                return create_dict(tax_category_code='S')  # standard VAT

        if supplier.country_id.code in european_economic_area:
            if tax.amount != 0:
                # otherwise, the validator will complain because G and K code should be used with 0% tax
                return create_dict(tax_category_code='S')
            if customer.country_id.code not in european_economic_area:
                return create_dict(
                    tax_category_code='G',
                    tax_exemption_reason_code='VATEX-EU-G',
                    tax_exemption_reason=_('Export outside the EU'),
                )
            if customer.country_id.code in european_economic_area:
                return create_dict(
                    tax_category_code='K',
                    tax_exemption_reason_code='VATEX-EU-IC',
                    tax_exemption_reason=_('Intra-Community supply'),
                )

        if tax.amount != 0:
            return create_dict(tax_category_code='S')
        else:
            return create_dict(tax_category_code='E', tax_exemption_reason=_('Articles 226 items 11 to 15 Directive 2006/112/EN'))

    def _get_invoice_payment_terms_vals_list(self, invoice):
        """ Override to include/update values specific to ZATCA's UBL 2.1 specs """
        return []
